#!/usr/bin/env python3
"""Build the search index over everything in library/.

    python3 tools/build_index.py

Reads:
    library/transcripts/*.txt    written by fetch_transcripts.py
    library/books/*.md           written by add_book.py
Writes:
    index/bm25.json              what search.py reads
    index/catalog.txt            one line per source: type | words | title

Plain BM25 ranking in standard-library Python. No model download, no API calls,
no per-query cost. Re-run it any time you add or remove material.
"""
import os, re, json, glob, math, collections

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIBRARY = os.path.join(SKILL_ROOT, "library")
INDEX_DIR = os.path.join(SKILL_ROOT, "index")
INDEX = os.path.join(INDEX_DIR, "bm25.json")
CATALOG = os.path.join(INDEX_DIR, "catalog.txt")

CHUNK_WORDS = 220
OVERLAP = 60

STOP = set("""a an and are as at be been but by for from had has have he her his i if in
into is it its of on or she that the their them they this to was were what when which who
will with you your we us our not no so do does did can could would should here there then
than just like get got go going really very much many more most all any some out up down
about over under again only also even still back way thing things know think see say said
i'm i've you're don't that's it's we're they're gonna okay yeah right actually""".split())

TOKEN = re.compile(r"[a-z0-9']+")
PAGE_MARK = re.compile(r"^page\s+(\d+)$", re.I)


def normalise(s):
    """Books use curly apostrophes, captions use straight ones. Without this,
    don't with a curly quote splits into "don" + "t" and never matches."""
    return s.replace("\u2019", "'").replace("\u02bc", "'").replace("\u2018", "'")


def tokenize(s):
    return [t for t in TOKEN.findall(normalise(s).lower()) if t not in STOP and len(t) > 1]


def chunk_words(words, size, overlap):
    step = size - overlap
    for i in range(0, max(1, len(words)), step):
        piece = words[i:i + size]
        if len(piece) < 40 and i:
            break
        yield i, " ".join(piece)


def header_of(text):
    """The '# ...' lines at the top of a file, before the first blank line."""
    return text.split("\n\n", 1)[0] if text.startswith("#") else ""


def load_timing(fp):
    """Word-offset to seconds checkpoints written by fetch_transcripts.py."""
    stem = os.path.basename(fp)[:-4]
    tp = os.path.join(os.path.dirname(fp), ".timing", stem + ".json")
    if not os.path.exists(tp):
        return None
    try:
        with open(tp, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def heading_marks(text):
    """[(word_offset, heading)] for every '## ...' line in a book file."""
    marks, running = [], 0
    for line in text.split("\n"):
        if line.startswith("## "):
            marks.append((running, line[3:].strip()))
        running += len(line.split())
    return marks


def hms(x):
    return f"{x // 3600:d}:{(x % 3600) // 60:02d}:{x % 60:02d}"


def book_locator(off, end, marks):
    """Page or chapter the passage sits in. A range if it crosses a marker."""
    first = [t for mo, t in marks if mo <= off][-1:] or [t for mo, t in marks if mo < end][:1]
    last = [t for mo, t in marks if mo < end][-1:]
    if not first:
        return "front matter (before the first page or chapter marker)"
    a, b = first[0], (last[0] if last else first[0])
    pa, pb = PAGE_MARK.match(a), PAGE_MARK.match(b)
    if pa and pb:
        return f"page {pa.group(1)}" if a == b else f"pages {pa.group(1)}-{pb.group(1)}"
    return f"chapter: {a}" if a == b else f"chapter: {a} (continues into: {b})"


def transcript_locator(off, end_off, timing, video_id):
    if not video_id:
        return f"word {off} (no video id in the file name)"
    if not timing:
        return f"word {off} (no timing file) https://youtu.be/{video_id}"

    def at(target):
        secs = 0
        for wo, sec in timing["checkpoints"]:
            if wo <= target:
                secs = sec
            else:
                break
        return int(secs)

    a, b = at(off), at(end_off)
    span = f"{hms(a)}-{hms(b)}" if b > a else hms(a)
    return f"{span} https://youtu.be/{video_id}?t={a}"


def video_id_of(header):
    m = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", header)
    return m.group(1) if m else ""


def sources():
    out = []
    for fp in sorted(glob.glob(os.path.join(LIBRARY, "transcripts", "*.txt"))):
        out.append(("transcript", fp))
    for fp in sorted(glob.glob(os.path.join(LIBRARY, "books", "*.md"))):
        out.append(("book", fp))
    return out


def title_of(fp, text):
    first = text.split("\n", 1)[0]
    if first.startswith("# "):
        return first[2:].strip()
    return os.path.splitext(os.path.basename(fp))[0]


def main():
    srcs = sources()
    if not srcs:
        raise SystemExit(
            f"Nothing to index. The library folder is empty: {LIBRARY}\n"
            "Add material first with fetch_transcripts.py or add_book.py.")

    chunks, df, catalog = [], collections.Counter(), []
    for corpus, fp in srcs:
        with open(fp, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        title = title_of(fp, text)
        header = header_of(text)
        body = text[len(header):] if header else text  # never index the '# title' lines
        words = body.split()
        catalog.append(f"{corpus:10s} | {len(words):7d} words | {title} | "
                       f"{os.path.relpath(fp, SKILL_ROOT)}")
        marks = heading_marks(body) if corpus == "book" else []
        timing = load_timing(fp) if corpus == "transcript" else None
        video_id = video_id_of(header) if corpus == "transcript" else ""

        for off, piece in chunk_words(words, CHUNK_WORDS, OVERLAP):
            toks = tokenize(piece)
            if len(toks) < 20:
                continue
            end = off + len(piece.split())
            if corpus == "book":
                loc = book_locator(off, end, marks)
            else:
                loc = transcript_locator(off, end, timing, video_id)
            tf = collections.Counter(toks)
            chunks.append({
                "c": corpus,
                "f": os.path.relpath(fp, SKILL_ROOT),
                "t": title,
                "o": off,
                "loc": loc,
                "x": re.sub(r"\s*## Page \d+\s*", " ", piece).strip(),
                "tf": tf,
                "len": len(toks),
            })
            for term in tf:
                df[term] += 1

    N = len(chunks)
    avgdl = sum(c["len"] for c in chunks) / max(1, N)
    postings = collections.defaultdict(list)
    for i, c in enumerate(chunks):
        for term, f in c["tf"].items():
            postings[term].append([i, f])
        del c["tf"]

    idf = {t: math.log(1 + (N - n + 0.5) / (n + 0.5)) for t, n in df.items()}

    os.makedirs(INDEX_DIR, exist_ok=True)
    with open(INDEX, "w", encoding="utf-8") as fh:
        json.dump({"N": N, "avgdl": avgdl, "chunks": chunks,
                   "postings": postings, "idf": idf}, fh)
    with open(CATALOG, "w", encoding="utf-8") as fh:
        fh.write("\n".join(catalog) + "\n")

    size = os.path.getsize(INDEX) / 1e6
    by = collections.Counter(c["c"] for c in chunks)
    files = collections.Counter(k for k, _ in srcs)
    print(f"indexed {N} passages from {files['transcript']} transcripts and "
          f"{files['book']} books ({dict(by)}), vocab {len(idf)}, index {size:.1f} MB")
    print(f"index:   {INDEX}")
    print(f"catalog: {CATALOG}")


if __name__ == "__main__":
    main()
