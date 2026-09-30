# Setup prompt

Open Claude Code, paste everything in the box below, and answer its questions. That's it.

```text
Set up a coach library for me. It's a Claude skill that searches one person's actual
material (their YouTube transcripts and books I own) before it answers, and cites the
source. The kit is the coach-library folder in https://github.com/IzWOP/free-resources.
Do these steps in order. If a step fails, stop and tell me what went wrong.

1. Ask me these in one message, then wait for my answers:
   a. Who is this library for? Their name, and their YouTube channel handle (like
      @AlexHormozi) or a channel or playlist URL.
   b. What do they mainly teach? A few words, like "offers, pricing, lead generation".
   c. How many videos? Suggest 20 to start. More videos means better answers, but
      YouTube limits how fast captions can be pulled, so big batches can take more than
      one sitting.
   d. Skip videos under 10 minutes? Suggest yes, since short clips carry little teaching.
   e. Any title words to skip, like interview, podcast or reaction? Optional.
   f. Do I own any of their books as files (.epub, .pdf, .txt or .md)? If so, where?

2. Check the tools. Run python3 --version (needs 3.9 or newer) and yt-dlp --version.
   If yt-dlp is missing, ask me before installing it. On a Mac that's
   brew install yt-dlp, otherwise python3 -m pip install --user yt-dlp.

3. Make a short lowercase slug from the name, for example Alex Hormozi becomes
   alex-hormozi. The skill folder is ~/.claude/skills/<slug>-library. If that folder
   already exists, stop and ask me. Never overwrite it.

4. Get the kit. Clone https://github.com/IzWOP/free-resources.git with --depth 1 into
   a temporary folder, copy its coach-library folder to ~/.claude/skills/<slug>-library,
   then delete the temporary clone.

5. From inside the skill folder, name the skill:
   python3 tools/name_library.py --name "<name>" --topics "<topics>" --channel "<handle or URL>"

6. Fetch the transcripts:
   python3 tools/fetch_transcripts.py --channel "<handle or URL>" --max <number> --min-minutes 10 --exclude-title-words "<words>"
   Leave out --min-minutes or --exclude-title-words if I said no to them. This takes a
   few minutes. If it stops early because YouTube is rate-limiting, keep going with what
   it got and tell me to run the same command again in an hour.

7. Add my books. For each file I gave you: python3 tools/add_book.py "<path>"
   Only use files I gave you. Never download a book from anywhere. If a PDF needs a
   tool that isn't installed, show me the install command it prints and ask before
   installing anything.

8. Build the search: python3 tools/build_index.py

9. Test it. Pick a topic this person is known for and run:
   python3 tools/search.py -n 3 "<topic>"
   Show me the three results with their SOURCE lines. Check that video results have a
   youtu.be link with ?t= in it, and that book results show a page or chapter.

10. Tell me: the skill folder path, how many videos and books are in it (count the lines
    in index/catalog.txt), and how to use it. I start a new Claude Code session and ask
    "What does <name> say about <topic>?", and Claude searches the library and cites
    what it found. Also give me the command to add more videos later.

Rules for the whole setup:
- Everything downloaded stays on my machine. Don't commit, upload or share any
  transcripts, books or index files.
- Downloading YouTube captions with yt-dlp is against YouTube's terms of service. This
  is for my own study only.
```

Want to do it by hand instead? Every command is in the [README](./README.md#doing-it-by-hand).
