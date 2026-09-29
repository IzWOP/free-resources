#!/usr/bin/env python3
"""Fill in SKILL.md with the person this library is about. Run once, during setup.

    python3 tools/name_library.py --name "Alex Hormozi" --topics "offers, pricing, lead generation"

Replaces the {{NAME}}, {{SLUG}}, {{TOPICS}} and {{CHANNEL}} placeholders in SKILL.md. The skill's
name becomes <slug>-library, which should match the folder it lives in, for example
~/.claude/skills/alex-hormozi-library/.
"""
import os, re, sys, argparse

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_MD = os.path.join(SKILL_ROOT, "SKILL.md")


def slug(t):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", t.lower())).strip("-")


def main():
    ap = argparse.ArgumentParser(description="Name this library after the person it covers.")
    ap.add_argument("--name", required=True, help='the person, e.g. "Alex Hormozi"')
    ap.add_argument("--topics", required=True,
                    help='what they teach, e.g. "offers, pricing, lead generation"')
    ap.add_argument("--channel", default="@CHANNEL_HANDLE",
                    help="their YouTube handle or URL, used in the 'adding more' example")
    ap.add_argument("--slug", help="short folder-safe name (default: made from --name)")
    a = ap.parse_args()

    with open(SKILL_MD, encoding="utf-8") as fh:
        text = fh.read()
    if "{{NAME}}" not in text:
        sys.exit("SKILL.md is already filled in. Edit it by hand if you need to change it.")

    s = slug(a.slug or a.name)
    if not s:
        sys.exit("Could not make a folder-safe name. Pass --slug, e.g. --slug jane-doe")
    # Keep the frontmatter valid: no newlines or double quotes in the one-line fields.
    name = " ".join(a.name.replace('"', "'").split())
    topics = " ".join(a.topics.replace('"', "'").split())
    channel = a.channel.strip() or "@CHANNEL_HANDLE"
    text = (text.replace("{{NAME}}", name).replace("{{SLUG}}", s)
            .replace("{{TOPICS}}", topics).replace("{{CHANNEL}}", channel))
    with open(SKILL_MD, "w", encoding="utf-8") as fh:
        fh.write(text)

    folder = os.path.basename(SKILL_ROOT)
    print(f"SKILL.md is now the '{s}-library' skill for {name}.")
    if folder != f"{s}-library":
        print(f"note: this folder is called '{folder}'. Claude Code finds skills by folder, "
              f"so rename it to '{s}-library' to match.")


if __name__ == "__main__":
    main()
