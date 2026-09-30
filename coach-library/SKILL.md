---
name: {{SLUG}}-library
description: "Search {{NAME}}'s own material (YouTube transcripts and books the user owns) before answering any question about what {{NAME}} teaches or says, including {{TOPICS}}. Answers come from the retrieved passages and cite the source, a video timestamp link or a book page or chapter. Local search, no API calls, no cost per query."
---

# {{NAME}} library

A searchable file cabinet of {{NAME}}'s material. The transcripts and books sit in
`library/`. The index in `index/` says where everything is. Your job is to pull the
right folder before you answer.

## The rule

When the user asks what {{NAME}} says, thinks, teaches or recommends, or asks for
{{NAME}}'s take on something:

1. **Search before you answer.** Run the search below. Do this even if you think you
   already know the answer. Your memory of {{NAME}} is not the source. The library is.
2. **Answer from the passages.** Build the answer from what came back. Do not fill gaps
   with general knowledge and present it as {{NAME}}'s view. If you add your own
   reasoning, label it as yours.
3. **Cite every claim.** Use the `SOURCE:` line of the passage you used:
   - Video: the title plus the timestamp link, e.g. *"Video Title (0:16:28)
     https://youtu.be/VIDEOID?t=988"*. The link opens at that second.
   - Book: the title plus the page or chapter, e.g. *"Book Title, page 77"* or
     *"Book Title, chapter: Pricing"*.
4. **If nothing relevant comes back, say so.** Say "I couldn't find that in the
   {{NAME}} library" and stop, or offer a general answer clearly marked as not from
   {{NAME}}. Never guess and attribute the guess to them.

## How to search

```bash
python3 ~/.claude/skills/{{SLUG}}-library/tools/search.py "your question here"
python3 ~/.claude/skills/{{SLUG}}-library/tools/search.py -n 12 "pricing"
python3 ~/.claude/skills/{{SLUG}}-library/tools/search.py -c book "pricing"
python3 ~/.claude/skills/{{SLUG}}-library/tools/search.py -c transcript "first hire"
```

| Flag | What it does |
|---|---|
| `-n N` | How many passages come back (default 8) |
| `-c book` or `-c transcript` | Search only books, or only video transcripts |
| `--per-file N` | Max passages from any one video or book (default 3) |
| `--chars N` | Cut each passage to N characters (default: print in full) |

Each result looks like this:

```
=== [ 14.20] transcript: Video Title
    SOURCE: 0:16:28-0:17:26 https://youtu.be/VIDEOID?t=988
    FILE:   library/transcripts/video-title-VIDEOID.txt (word 3120)
    ...the passage text...
```

Books are the most precise source for what a framework *is*. Videos are better for
stories, examples and elaboration. When both answer the question, lead with the book.

## When results look thin

The search matches words, not meanings. A question phrased in words {{NAME}} doesn't
use will score worse than the same question in their words. If results look weak:

- Restate the query in {{NAME}}'s own vocabulary and search again.
- Try two or three shorter queries instead of one long one.
- For a rare exact phrase, grep the files directly:
  `grep -ril "exact phrase" ~/.claude/skills/{{SLUG}}-library/library/`

Two or three searches is fine. It costs nothing. If they all come back empty, the
answer is not in the library. Say so.

## What is in the library

`index/catalog.txt` lists every video and book, one per line. Read it when the user
asks what's in here, or to pick a specific video.

Never read a whole transcript or book into context. They are long. Search, then read
a narrow range around a hit if you need more.

Transcripts are auto-generated YouTube captions. They have no punctuation and some
misheard words. Quote them lightly and link the timestamp so the user can check.
Some videos have other people talking (guests, callers, interviewers). Before you
attribute a quote to {{NAME}}, check the timestamp or say it may be someone else.

## Adding more

```bash
cd ~/.claude/skills/{{SLUG}}-library
python3 tools/fetch_transcripts.py --channel {{CHANNEL}} --max 20   # more videos
python3 tools/add_book.py ~/path/to/book-you-own.epub           # a book (.epub .pdf .txt .md)
python3 tools/build_index.py                                    # always rebuild after adding
```
