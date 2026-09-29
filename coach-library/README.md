# Coach Library

You keep asking AI what some expert would say. It answers from memory. That memory is a
blur of everything written about them online, so sometimes it's right, sometimes it's
made up, and you can't tell which.

This kit fixes that. Your Claude builds a searchable library of one person's actual
material, and a rule that it has to search that library before it answers.

Think of a file cabinet. The stuff goes in: transcripts of their videos, and the books
you bought. The tabs say where everything is. Before answering, the AI pulls the right
folder, answers from it, and tells you which folder it used: the video and the second
it was said, or the book and the page.

It's the same setup my Hormozi coach runs on. This version works for anyone with a
YouTube channel.

---

## What you get

- **A Claude skill named after your person.** For example `alex-hormozi-library`.
- **Their YouTube transcripts, with timestamps.** Every answer from a video links to the
  moment it was said, so you can click and hear it.
- **Any of their books you own.** Pages kept for PDFs, chapters kept for EPUBs, so book
  answers cite a page or chapter.
- **The rule, built into the skill.** Search before answering. Answer from what came back.
  Cite it. If the library doesn't have it, say so instead of guessing.

## The three steps

| Step | What happens | Who does it |
|---|---|---|
| 1 | Pick the person or topic you keep asking AI about | You |
| 2 | Get the material: transcripts of their videos, and the books you bought | Claude fetches the transcripts. You point it at your book files. |
| 3 | Build the search, plus the rule that it has to search before it answers | Claude |

A topic works too. Point it at a YouTube playlist URL instead of a channel.

---

## Quickstart

Open Claude Code and paste in the prompt from [SETUP-PROMPT.md](./SETUP-PROMPT.md).

It asks you who, how many videos, and whether you have any of their books as files.
Then it installs the kit, fetches the transcripts, adds your books, builds the search,
and runs a test search so you can see the citations work.

When it's done, open a new Claude Code session and ask something like *"What does Alex
Hormozi say about pricing?"* Claude searches the library and answers with links.

## Doing it by hand

If you'd rather run it yourself, this is everything the setup prompt does. Hormozi is
just the example here. Swap in anyone.

```bash
# get the folder into your Claude skills
git clone --depth 1 https://github.com/IzWOP/free-resources.git /tmp/free-resources
cp -R /tmp/free-resources/coach-library ~/.claude/skills/alex-hormozi-library
rm -rf /tmp/free-resources
cd ~/.claude/skills/alex-hormozi-library

# name the skill after your person
python3 tools/name_library.py --name "Alex Hormozi" --topics "offers, pricing, lead generation" --channel @AlexHormozi

# 20 videos, 10 minutes or longer, no interviews or podcasts
python3 tools/fetch_transcripts.py --channel @AlexHormozi --max 20 --min-minutes 10 --exclude-title-words "interview,podcast"

# any books of theirs you own
python3 tools/add_book.py ~/Downloads/some-book.epub
python3 tools/add_book.py ~/Downloads/another-book.pdf

# build the search, then try it
python3 tools/build_index.py
python3 tools/search.py "how do i price my offer"
```

Search results look like this. The book here is Benjamin Franklin's *The Way to
Wealth*, which is public domain, so it's the one I tested with:

```
=== [ 14.20] transcript: <the video's title>
    SOURCE: 0:16:28-0:17:26 https://youtu.be/<video id>?t=988
    FILE:   library/transcripts/<title>-<video id>.txt (word 3120)
    <the words said in that minute of the video>

=== [ 10.84] book: The Way to Wealth
    SOURCE: chapter: Chapter Two: Of Frugality
    FILE:   library/books/the-way-to-wealth.md (word 160)
    my friends, and attention to one's own business; but to these we must add frugality...
```

The link opens the video at that second. The book line tells you where to turn.

Run `fetch_transcripts.py` again any time to add newer videos. It skips what you already
have. Rebuild the index after adding anything.

---

## What it costs

**$0.** No API keys, no subscriptions, no paid transcription. The transcripts are the
captions YouTube already has. The search runs on your own computer and takes a fraction
of a second.

Time is the only cost. Fetching runs at roughly 10 seconds per video, so 20 videos is
three or four minutes. YouTube limits how fast one connection can pull captions, so a
big library can take more than one sitting. See the limits below.

## What you need

- **Claude Code.** The tools are plain Python and work without it, but the "search
  before you answer" part is a Claude Code skill.
- **Python 3.9 or newer.** Standard library only. `python3 --version` to check.
- **yt-dlp**, which fetches the captions. `brew install yt-dlp` on a Mac, or
  `python3 -m pip install --user yt-dlp`.
- **For PDF books only:** `pdftotext` (`brew install poppler`) or `pypdf`
  (`python3 -m pip install --user pypdf`). EPUB, TXT and Markdown need nothing extra.

I've run it on a Mac. It should work on Linux and Windows too, but I haven't tested those.

---

## Limits, honestly

- **It's word search, not meaning search.** It matches the words in your question
  against the words in the library. A question phrased in vocabulary the person doesn't
  use scores worse than the same question in their words. "Getting customers when I'm
  broke" can miss a passage about "warm outreach". Fix: restate the question in their
  words. Claude is good at this and the skill tells it to try.
- **It's only as good as what's in the cabinet.** Ten videos can't answer everything.
  If they never talked about it on camera or in a book you added, it isn't there, and
  the skill is told to say so rather than fill the gap.
- **Transcripts are YouTube's auto-captions.** Expect misheard words, especially names
  and jargon, and sometimes no punctuation. The timestamp link is there so you can check.
- **Other people talk in some videos.** Guests, callers, interviewers. Captions mark a
  speaker change with `>>` and search results flag it, but not every video has the
  marks. Check the timestamp before you quote someone.
- **Books have to be readable files.** DRM-free EPUB or PDF, or plain text. Kindle files
  don't work. A scanned PDF with no text layer needs OCR first. PDF page numbers are the
  file's page count, which can be off from the printed number by the front matter.
- **YouTube says "slow down."** Pull a lot of captions quickly and it starts refusing
  for a while. In my testing that kicked in after roughly 15 to 20 videos in ten
  minutes. The fetcher backs off, then stops and tells you. Everything it got is saved.
  Run the same command later and it carries on where it stopped. `--pause 15` spaces
  the requests out more.
- **English by default.** For another language use `--lang`, for example `--lang es`.

---

## For your own study

**For your own study. Downloading YouTube captions with yt-dlp is against YouTube's terms
of service; use it for personal learning, and don't redistribute what you download.**

Books: only books you own. The kit never downloads a book. It only reads files you
point it at.

Nothing you add is meant to leave your machine. The `.gitignore` in this folder keeps
`library/` and `index/` out of git, so if you build your library inside a clone of this
repo, a `git add .` won't pick up anyone's transcripts or books.

---

## What's in the folder

| File | What it does |
|---|---|
| `SETUP-PROMPT.md` | The prompt you paste into Claude Code. It does everything below. |
| `SKILL.md` | The skill. Tells Claude to search first, answer from the passages, and cite. |
| `tools/name_library.py` | Fills in the skill's name and description for your person. Run once. |
| `tools/fetch_transcripts.py` | Pulls caption text and timestamps for a channel or playlist. |
| `tools/add_book.py` | Adds a book you own: `.epub`, `.pdf`, `.txt` or `.md`. |
| `tools/build_index.py` | Builds the search index. Re-run after adding anything. |
| `tools/search.py` | The search. Every result prints where it came from. |

Your material lands in `library/` and the index in `index/`, both inside the skill
folder.

The search is BM25, a standard ranking formula that search engines have used since the
1990s. About 300 lines of standard-library Python. No model download, no vector
database.

---

## Credit

- **yt-dlp** by the yt-dlp contributors, released under the Unlicense.
  https://github.com/yt-dlp/yt-dlp. Every transcript here is yt-dlp doing the work.
- **pdftotext** (part of Poppler, GPL) and **pypdf** (BSD), if you use one for PDFs.

I wrote the kit: the tools, the skill and the setup prompt. Those third-party tools keep
their own licenses.

---

Built by Isaac Vazquez. I post real builds as I do them: https://instagram.com/isaacbuildsai
