#!/usr/bin/env python3
"""Add a book you own to library/books/, keeping pages or chapters for citations.

    python3 tools/add_book.py ~/Downloads/some-book.epub
    python3 tools/add_book.py ~/Downloads/some-book.pdf --title "Some Book"
    python3 tools/add_book.py notes.md

Formats:
    .txt .md   copied in. Markdown headings and lines like "Chapter 3" become chapter markers.
    .epub      read with the standard library. One marker per chapter, named from the
               book's own table of contents. DRM-free files only.
    .pdf       text pulled with pdftotext if installed, otherwise the pypdf package.
               One "## Page N" marker per page. N is the PDF's page count, which can
               differ from the number printed on the page by the length of the front matter.

Kindle files (.azw, .azw3, .mobi, .kfx) are not supported. Export a DRM-free EPUB or
PDF of a book you own, or convert one you already have with Calibre.

Writes library/books/<title-slug>.md. Run tools/build_index.py afterwards.
"""
import os, re, sys, shutil, argparse, posixpath, subprocess, zipfile
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import unquote

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(SKILL_ROOT, "library", "books")

CHAPTER_LINE = re.compile(r"^\s*((chapter|part|book|section)\s+([0-9]+|[ivxlcdm]+)\b.*)$", re.I)


def slug(t):
    s = re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", t.lower())).strip("-")
    return s[:80].strip("-") or "book"


# ---------- plain text and markdown ----------

def from_text(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        raw = fh.read()
    out = []
    for line in raw.splitlines():
        m = re.match(r"^#{1,6}\s+(.+)$", line)
        if m:
            out.append("")
            out.append("## " + m.group(1).strip())
            out.append("")
        elif CHAPTER_LINE.match(line) and len(line) < 80:
            out.append("")
            out.append("## " + line.strip())
            out.append("")
        else:
            out.append(line)
    return "\n".join(out)


# ---------- epub ----------

class _Text(HTMLParser):
    """XHTML to plain text with paragraph breaks. Remembers the first heading."""
    BLOCK = {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6",
             "tr", "blockquote", "section", "article", "pre"}
    SKIP = {"script", "style", "head", "title"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.skip, self.heading, self._in_h, self._h = [], 0, "", 0, []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        if tag in self.BLOCK:
            self.parts.append("\n\n")
        if tag in ("h1", "h2", "h3") and not self.heading:
            self._in_h += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip:
            self.skip -= 1
        if tag in self.BLOCK:
            self.parts.append("\n\n")
        if tag in ("h1", "h2", "h3") and self._in_h:
            self._in_h -= 1
            if not self._in_h and not self.heading:
                self.heading = " ".join("".join(self._h).split())

    def handle_data(self, data):
        if self.skip:
            return
        self.parts.append(data)
        if self._in_h:
            self._h.append(data)

    def text(self):
        t = "".join(self.parts)
        t = re.sub(r"[ \t\r\f\v]+", " ", t)
        t = re.sub(r"\n\s*\n+", "\n\n", t)
        return "\n".join(l.strip() for l in t.split("\n")).strip()


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def _toc_labels(z, opf_dir, manifest, spine_toc_id):
    """{href_without_fragment: label} from the EPUB 3 nav doc or the EPUB 2 NCX."""
    labels = {}
    nav = next((it for it in manifest.values() if "nav" in it.get("properties", "").split()), None)
    if nav:
        base = posixpath.dirname(posixpath.join(opf_dir, nav["href"]))
        try:
            doc = z.read(posixpath.join(opf_dir, nav["href"])).decode("utf-8", "replace")
            for href, label in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', doc, re.S):
                label = " ".join(re.sub(r"<[^>]+>", "", label).split())
                key = posixpath.normpath(posixpath.join(base, unquote(href.split("#")[0])))
                if label and key not in labels:
                    labels[key] = label
        except KeyError:
            pass
    ncx = manifest.get(spine_toc_id) if spine_toc_id else None
    if ncx is None:
        ncx = next((it for it in manifest.values()
                    if it.get("media-type") == "application/x-dtbncx+xml"), None)
    if ncx:
        base = posixpath.dirname(posixpath.join(opf_dir, ncx["href"]))
        try:
            root = ET.fromstring(z.read(posixpath.join(opf_dir, ncx["href"])))
            for np in root.iter():
                if _local(np.tag) != "navPoint":
                    continue
                text = next((e.text for e in np.iter() if _local(e.tag) == "text" and e.text), "")
                src = next((e.get("src") for e in np.iter() if _local(e.tag) == "content"), "")
                if text and src:
                    key = posixpath.normpath(posixpath.join(base, unquote(src.split("#")[0])))
                    labels.setdefault(key, " ".join(text.split()))
        except (KeyError, ET.ParseError):
            pass
    return labels


def from_epub(path):
    try:
        z = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        sys.exit("This file is not a valid EPUB (it is not a zip archive).")
    names = set(z.namelist())
    if "META-INF/encryption.xml" in names:
        # Font obfuscation also lives in this file and is harmless. DRM encrypts the pages.
        enc = z.read("META-INF/encryption.xml").decode("utf-8", "replace")
        locked = re.findall(r'CipherReference[^>]*URI="([^"]+)"', enc)
        if any(u.lower().endswith((".html", ".xhtml", ".htm")) for u in locked):
            sys.exit("This EPUB is DRM-protected, so its text cannot be read. "
                     "Use a DRM-free copy of a book you own.")
    container = ET.fromstring(z.read("META-INF/container.xml"))
    opf_path = next(e.get("full-path") for e in container.iter() if _local(e.tag) == "rootfile")
    opf_dir = posixpath.dirname(opf_path)
    opf = ET.fromstring(z.read(opf_path))

    title = next((e.text for e in opf.iter() if _local(e.tag) == "title" and e.text), "")
    manifest, spine, toc_id = {}, [], None
    for e in opf.iter():
        t = _local(e.tag)
        if t == "item":
            manifest[e.get("id")] = {"href": unquote(e.get("href", "")),
                                     "media-type": e.get("media-type", ""),
                                     "properties": e.get("properties", "")}
        elif t == "spine":
            toc_id = e.get("toc")
        elif t == "itemref" and e.get("linear", "yes") != "no":
            spine.append(e.get("idref"))

    labels = _toc_labels(z, opf_dir, manifest, toc_id)
    out, n = [], 0
    for idref in spine:
        item = manifest.get(idref)
        if not item or "html" not in item["media-type"]:
            continue
        full = posixpath.normpath(posixpath.join(opf_dir, item["href"]))
        try:
            doc = z.read(full).decode("utf-8", "replace")
        except KeyError:
            continue
        p = _Text()
        p.feed(doc)
        body = p.text()
        if len(body.split()) < 20:
            continue  # cover pages, image-only pages
        n += 1
        label = labels.get(full) or p.heading or f"Section {n}"
        out.append(f"## {label}\n\n{body}\n")
    if not out:
        sys.exit("No readable text found in this EPUB.")
    return title.strip(), "\n".join(out)


# ---------- pdf ----------

def pdf_pages(path):
    if shutil.which("pdftotext"):
        r = subprocess.run(["pdftotext", "-enc", "UTF-8", path, "-"],
                           capture_output=True, text=True)
        if r.returncode == 0:
            pages = r.stdout.split("\f")
            if pages and not pages[-1].strip():
                pages = pages[:-1]
            return pages, "pdftotext"
        print(f"pdftotext failed ({r.stderr.strip()[:200]}), trying pypdf", file=sys.stderr)
    try:
        from pypdf import PdfReader
    except ImportError:
        sys.exit("Reading a PDF needs one of these, and neither is installed:\n"
                 "  pdftotext:  brew install poppler      (Mac)\n"
                 "              sudo apt install poppler-utils   (Linux)\n"
                 "  pypdf:      python3 -m pip install --user pypdf\n"
                 "Install either one and run this again.")
    return [(pg.extract_text() or "") for pg in PdfReader(path).pages], "pypdf"


def from_pdf(path):
    pages, tool = pdf_pages(path)
    out, empty = [], 0
    for i, text in enumerate(pages, 1):
        text = re.sub(r"[ \t]+", " ", text).strip()
        if not text:
            empty += 1
            text = f"[page {i}: no text on this page, probably an image]"
        out.append(f"## Page {i}\n\n{text}\n")
    if pages and empty > len(pages) / 2:
        print(f"warning: {empty} of {len(pages)} pages had no text. This is probably a "
              "scanned PDF. It needs OCR before it can be searched.", file=sys.stderr)
    return "\n".join(out), tool, len(pages)


def main():
    ap = argparse.ArgumentParser(description="Add a book you own to the library.")
    ap.add_argument("path")
    ap.add_argument("--title", help="book title (default: from the file)")
    a = ap.parse_args()

    path = os.path.expanduser(a.path)
    if not os.path.isfile(path):
        sys.exit(f"No file at {path}")
    ext = os.path.splitext(path)[1].lower()
    title, note = a.title, ""

    if ext in (".txt", ".md", ".markdown"):
        body = from_text(path)
        note = "text"
    elif ext == ".epub":
        found, body = from_epub(path)
        title = title or found
        note = f"epub, {len(re.findall(r'^## ', body, re.M))} chapters"
    elif ext == ".pdf":
        body, tool, n = from_pdf(path)
        note = f"pdf via {tool}, {n} pages"
    elif ext in (".azw", ".azw3", ".mobi", ".kfx"):
        sys.exit("Kindle formats are not supported. Get a DRM-free EPUB or PDF of the "
                 "book, or convert it with Calibre (calibre-ebook.com), then add that.")
    else:
        sys.exit(f"Unsupported file type: {ext or '(none)'}. Use .epub, .pdf, .txt or .md.")

    title = (title or os.path.splitext(os.path.basename(path))[0]).strip()
    os.makedirs(DEST, exist_ok=True)
    out = os.path.join(DEST, slug(title) + ".md")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(f"# {title}\n\n{body.strip()}\n")
    words = len(body.split())
    print(f"added: {title} ({note}, {words:,} words)")
    print(f"  -> {os.path.relpath(out, SKILL_ROOT)}")
    if words < 1000:
        print("warning: under 1,000 words came out of this file. Check it opened correctly.")
    print("Next: python3 tools/build_index.py")


if __name__ == "__main__":
    main()
