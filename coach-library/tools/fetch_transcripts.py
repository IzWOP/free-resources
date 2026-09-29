#!/usr/bin/env python3
"""Download the captions of a YouTube channel's videos into library/transcripts/.

    python3 tools/fetch_transcripts.py --channel @AlexHormozi --max 20
    python3 tools/fetch_transcripts.py --channel @SomeCoach --max 50 --min-minutes 10
    python3 tools/fetch_transcripts.py --channel @SomeCoach --exclude-title-words "interview,podcast,shorts"
    python3 tools/fetch_transcripts.py --channel "https://www.youtube.com/playlist?list=..." --max 10

Uses the caption tracks YouTube already has, through yt-dlp. Free. No API key, no
transcription service, no video or audio is downloaded. Videos with no captions are
skipped and reported. Videos already in the library are skipped by video id, so you
can run it again later to add more.

For each video it writes:
    library/transcripts/<title-slug>-<videoid>.txt        the caption text
    library/transcripts/.timing/<same name>.json          word position -> second
The timing file is what lets a search result link to the exact second.
"""
import os, re, sys, json, html, time, shutil, argparse, subprocess, tempfile

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(SKILL_ROOT, "library", "transcripts")
TIMING = os.path.join(DEST, ".timing")

CUE = re.compile(r"^(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s+-->")
SOUND_TAG = re.compile(r"\[(?:music|applause|laughter|laughs|__)\]\s*", re.I)


def slug(t):
    s = re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", t.lower())).strip("-")
    return s[:80].strip("-") or "video"


def channel_url(ch):
    ch = ch.strip()
    if ch.startswith("http"):
        return ch
    if not ch.startswith("@"):
        ch = "@" + ch
    return f"https://www.youtube.com/{ch}/videos"


def have_ids():
    if not os.path.isdir(DEST):
        return set()
    return {f[:-4][-11:] for f in os.listdir(DEST) if f.endswith(".txt")}


def parse_vtt(path):
    """[(start_seconds, line)] with YouTube's rolling-caption repeats removed."""
    out, start = [], None
    with open(path, encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            m = CUE.match(line)
            if m:
                h, mi, s, ms = (int(x) for x in m.groups())
                start = h * 3600 + mi * 60 + s + ms / 1000.0
                continue
            if line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")):
                continue
            line = html.unescape(re.sub(r"<[^>]+>", "", line))
            line = SOUND_TAG.sub("", line).strip()
            if not line or start is None:
                continue
            if out and (line == out[-1][1] or (len(out) >= 2 and line == out[-2][1])):
                continue
            out.append((start, line))
    return out


def pick_vtt(folder, lang):
    files = [f for f in os.listdir(folder) if f.endswith(".vtt")]
    if not files:
        return None
    # Prefer the plain language track, then the original-language auto track, then anything.
    files.sort(key=lambda f: (0 if f".{lang}.vtt" in f else 1 if f".{lang}-orig." in f else 2, len(f)))
    return os.path.join(folder, files[0])


def _yt_subs(vid, folder, langs):
    r = subprocess.run(
        ["yt-dlp", "--skip-download", "--write-subs", "--write-auto-subs",
         "--sub-langs", langs, "--sub-format", "vtt", "--sleep-requests", "1",
         "-o", os.path.join(folder, "%(id)s.%(ext)s"),
         f"https://www.youtube.com/watch?v={vid}"],
        capture_output=True, text=True, timeout=300)
    return r.stderr


def fetch_captions(vid, folder, lang, pause):
    """Returns (vtt_path, None) or (None, reason). Backs off when YouTube says 429."""
    waits = [0, 30, 90]
    for wait in waits:
        if wait:
            print(f"  YouTube says too many requests. Waiting {wait}s, then retrying...",
                  flush=True)
            time.sleep(wait)
        try:
            # One track first. Asking for several at once is what trips the rate limit.
            err = _yt_subs(vid, folder, lang)
            vtt = pick_vtt(folder, lang)
            if not vtt and "HTTP Error 429" not in err:
                err += _yt_subs(vid, folder, f"{lang}.*")  # e.g. en-US, en-GB, en-orig
                vtt = pick_vtt(folder, lang)
        except subprocess.TimeoutExpired:
            return None, "timed out"
        if vtt:
            time.sleep(pause)
            return vtt, None
        if "HTTP Error 429" not in err:
            last = [l for l in err.splitlines() if l.startswith("ERROR")]
            return None, (last[-1][7:120] if last else "no captions in this language")
    return None, "rate-limited"


def list_videos(url):
    r = subprocess.run(
        ["yt-dlp", "--flat-playlist", "--ignore-errors",
         "--print", "%(id)s\t%(duration)s\t%(title)s", url],
        capture_output=True, text=True)
    rows = []
    for line in r.stdout.splitlines():
        p = line.split("\t")
        if len(p) < 3 or len(p[0]) != 11:
            continue
        try:
            dur = int(float(p[1]))
        except ValueError:
            dur = 0  # live streams and some uploads report no duration
        rows.append((p[0], dur, "\t".join(p[2:])))
    return rows, r.stderr


def main():
    ap = argparse.ArgumentParser(description="Fetch free YouTube captions into the library.")
    ap.add_argument("--channel", required=True,
                    help="channel handle like @AlexHormozi, or any channel/playlist URL")
    ap.add_argument("--max", type=int, default=20, help="how many NEW transcripts to add (default 20)")
    ap.add_argument("--min-minutes", type=float, default=0,
                    help="skip videos shorter than this (default 0 = keep all)")
    ap.add_argument("--exclude-title-words", default="",
                    help='comma-separated words; skip any video whose title contains one, '
                         'e.g. "interview,podcast,reaction"')
    ap.add_argument("--order", choices=["newest", "longest"], default="newest",
                    help="which videos to take first (default newest)")
    ap.add_argument("--lang", default="en", help="caption language code (default en)")
    ap.add_argument("--min-words", type=int, default=300,
                    help="skip caption files shorter than this many words (default 300)")
    ap.add_argument("--pause", type=float, default=3,
                    help="seconds to wait between videos (default 3). Raise it if YouTube "
                         "keeps rate-limiting you")
    a = ap.parse_args()

    if not shutil.which("yt-dlp"):
        sys.exit("yt-dlp is not installed. Install it with one of:\n"
                 "  brew install yt-dlp\n"
                 "  python3 -m pip install --user yt-dlp\n"
                 "then run this again.")

    os.makedirs(TIMING, exist_ok=True)
    url = channel_url(a.channel)
    print(f"listing videos from {url} ...", flush=True)
    rows, err = list_videos(url)
    if not rows:
        tail = "\n".join(err.strip().splitlines()[-5:])
        sys.exit(f"No videos found at {url}.\nCheck the handle is right. yt-dlp said:\n{tail}")

    banned = [w.strip().lower() for w in a.exclude_title_words.split(",") if w.strip()]
    have = have_ids()
    cand, skipped, filtered = [], [], 0
    for vid, dur, title in rows:
        if vid in have:
            continue
        if a.min_minutes and dur and dur < a.min_minutes * 60:
            filtered += 1
            continue
        if any(re.search(r"(?<![a-z0-9])" + re.escape(w) + r"(?![a-z0-9])", title.lower())
               for w in banned):
            filtered += 1
            continue
        cand.append((vid, dur, title))
    if a.order == "longest":
        cand.sort(key=lambda r: -r[1])
    print(f"found {len(rows)} videos; library already has {len(have)}; "
          f"{filtered} left out by your filters; {len(cand)} candidates", flush=True)

    added, blocked = [], False
    with tempfile.TemporaryDirectory() as tmp:
        for vid, dur, title in cand:
            if len(added) >= a.max:
                break
            sub = os.path.join(tmp, vid)
            os.makedirs(sub, exist_ok=True)
            vtt, why = fetch_captions(vid, sub, a.lang, a.pause)
            if why == "rate-limited":
                blocked = True
                break
            if not vtt:
                skipped.append((title, why)); continue
            timed = parse_vtt(vtt)
            body = "\n".join(t for _, t in timed)
            if len(body.split()) < a.min_words:
                skipped.append((title, f"captions under {a.min_words} words")); continue

            stem = f"{slug(title)}-{vid}"
            with open(os.path.join(DEST, stem + ".txt"), "w", encoding="utf-8") as fh:
                fh.write(f"# {title}\n# https://www.youtube.com/watch?v={vid}\n\n{body}\n")
            checkpoints, running = [], 0
            for sec, line in timed:
                checkpoints.append([running, round(sec, 1)])
                running += len(line.split())
            with open(os.path.join(TIMING, stem + ".json"), "w", encoding="utf-8") as fh:
                json.dump({"video_id": vid, "checkpoints": checkpoints}, fh)
            added.append(stem)
            print(f"[{len(added)}/{a.max}] {title}", flush=True)

    print(f"\nadded {len(added)}, skipped {len(skipped)}")
    for title, why in skipped[:40]:
        print(f"  skipped: {title[:70]}  ({why})")
    if len(skipped) > 40:
        print(f"  ...and {len(skipped) - 40} more")
    if blocked:
        print("\nSTOPPED EARLY: YouTube is rate-limiting this connection (HTTP 429, "
              "too many requests).\nEverything above is saved. Wait an hour or so and run "
              "the same command again.\nIt skips what you already have and carries on. "
              "Adding --pause 15 makes it go slower.")
    if added:
        print("\nNext: python3 tools/build_index.py")


if __name__ == "__main__":
    main()
