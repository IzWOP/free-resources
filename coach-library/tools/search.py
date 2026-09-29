#!/usr/bin/env python3
"""Ranked search over your library. Every result says where it came from.

    python3 tools/search.py "how do i price a high ticket offer"
    python3 tools/search.py -n 12 -c book "value equation"
    python3 tools/search.py --per-file 1 "cold outreach"

Each result prints a SOURCE line you can check yourself: a YouTube link that opens
at the second the passage starts, or a page or chapter for books.
No network calls, no per-query cost.
"""
import os, sys, json, argparse, collections, importlib.util

TOOLS = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(TOOLS)
INDEX = os.path.join(SKILL_ROOT, "index", "bm25.json")
K1, B = 1.5, 0.75

# Share the tokenizer with the indexer so the two can never drift apart.
_spec = importlib.util.spec_from_file_location("_bi", os.path.join(TOOLS, "build_index.py"))
_bi = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bi)
TOKEN, STOP, normalise = _bi.TOKEN, _bi.STOP, _bi.normalise

# Question words carry no meaning in a query.
QUERY_STOP = STOP | {"how", "what", "why", "when", "where", "does", "should"}


def main():
    ap = argparse.ArgumentParser(description="Ranked search over your library.")
    ap.add_argument("query", nargs="+")
    ap.add_argument("-n", type=int, default=8, help="passages to return (default 8)")
    ap.add_argument("-c", choices=["book", "transcript"], help="only books, or only transcripts")
    ap.add_argument("--per-file", type=int, default=3,
                    help="max passages from any one source (default 3)")
    ap.add_argument("--chars", type=int, default=0,
                    help="cut each passage to N characters (default 0 = print in full)")
    a = ap.parse_args()

    if not os.path.exists(INDEX):
        sys.exit(f"No index at {INDEX}. Run tools/build_index.py first.")
    with open(INDEX, encoding="utf-8") as fh:
        ix = json.load(fh)
    chunks, postings, idf, avgdl = ix["chunks"], ix["postings"], ix["idf"], ix["avgdl"]

    query = " ".join(a.query)
    terms = [t for t in TOKEN.findall(normalise(query).lower())
             if t not in QUERY_STOP and len(t) > 1]
    terms = list(dict.fromkeys(terms))  # a repeated word must not double its own weight
    if not terms:
        sys.exit("The query had no searchable words left after dropping filler words.")

    scores = collections.defaultdict(float)
    for t in terms:
        for cid, f in postings.get(t, []):
            dl = chunks[cid]["len"]
            scores[cid] += idf[t] * (f * (K1 + 1)) / (f + K1 * (1 - B + B * dl / avgdl))

    shown, seen, per_file = 0, [], collections.Counter()
    for cid, sc in sorted(scores.items(), key=lambda kv: -kv[1]):
        c = chunks[cid]
        if a.c and c["c"] != a.c:
            continue
        if per_file[c["f"]] >= a.per_file:
            continue
        # People repeat themselves across videos. Skip near-identical passages.
        words = set(TOKEN.findall(c["x"].lower()))
        if words and any(len(words & p) / len(words | p) > 0.65 for p in seen):
            continue
        seen.append(words)
        per_file[c["f"]] += 1

        body = c["x"].replace("\n", " ")
        if a.chars and len(body) > a.chars:
            body = body[:a.chars] + f" ...[{len(body) - a.chars} more chars]"
        print(f"\n=== [{sc:6.2f}] {c['c']}: {c['t']}")
        print(f"    SOURCE: {c['loc']}")
        print(f"    FILE:   {c['f']} (word {c['o']})")
        if c["c"] == "transcript" and ">>" in c["x"]:
            print("    NOTE:   '>>' marks a speaker change. Some of these words are someone "
                  "else's. Check the timestamp before quoting.")
        print("    " + body)
        shown += 1
        if shown >= a.n:
            break

    if not shown:
        print("Nothing in the library matched. Try the same question in the words this "
              "person actually uses. If that also comes back empty, the answer is not in "
              "the library: say so instead of guessing.")


if __name__ == "__main__":
    main()
