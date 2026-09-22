# Google Tag Manager, Built By AI

I stopped hand-building GTM tags. An AI reads the live page, finds the element, and
writes the tag and the trigger into a workspace. **I publish it. Not the AI.**

This folder is the whole setup: what to install, the Google Cloud part that actually
takes the time, the prompts, and the rule that keeps it safe.

**Nothing here is mine to sell you.** The GTM server is `gtm-mcp` by Pouya Nafisi,
MIT licensed. The browser server is Google's `chrome-devtools-mcp`. What I put together
is the combination, the cloud setup so it works on a client's account instead of only my
own, and the QA rule. Credit and links at the bottom.

---

## What it does

You say: *track clicks on the "Get a Quote" button.*

It opens the page, finds that button, works out a selector that will still match
tomorrow, creates the trigger, creates the tag, wires them together, and leaves it in a
workspace.

You look at it. You publish it.

## Why the second server matters

A GTM connector on its own can write a tag, but it is guessing at what to point the tag
at, because it cannot see the page. That is how you end up with a selector built from a
class name a framework regenerates on the next deploy.

Adding a browser lets it read the real DOM on the real page. It picks the selector from
what is actually there. That is the difference between a tag that works and a tag that
worked once.

## The four steps

| Step | What happens | Who does it |
|---|---|---|
| 1 | Connect GTM to a Google Cloud project, once | You, 30-45 minutes the first time |
| 2 | Point the AI at a page and say what to track | You, one sentence |
| 3 | **QA it as a human** | You, every time |
| 4 | Publish | You |

Step 3 is not optional and it is not a formality. See [The rule](#the-rule).

---

## Before you start

- **Node.js 18 or newer.** Everything here runs through `npx`, which comes with Node.
  If `node --version` prints nothing, install Node first.
- **Google Chrome installed**, for the browser half.
- **A GTM container you are allowed to break.** Do the first one on a throwaway
  container on a personal site. It costs nothing and teaches you everything.

## Install

Two MCP servers. In Claude Desktop: Settings → Developer → Edit Config. In Claude Code:
`claude mcp add-json` is the supported route, or edit `~/.claude.json` if you are
comfortable.

```jsonc
{
  "mcpServers": {
    "gtm": {
      "command": "npx",
      "args": ["-y", "gtm-mcp"],
      "env": {
        "GTM_CREDENTIALS_FILE": "/absolute/path/to/credentials.json",
        "GTM_TOKEN_FILE": "/absolute/path/to/token.json"
      }
    },
    "chrome-devtools": {
      "command": "npx",
      "args": ["chrome-devtools-mcp@latest"]
    }
  }
}
```

Both paths must be **absolute**; `~` does not expand here. On Windows, escape the
backslashes: `"C:\\Users\\you\\gtm\\credentials.json"`.

Those two files are also the two you must never commit. See [Security](#security), and
read [SETUP.md](./SETUP.md) for how to create them.

## Authorise

**This does not open a browser for you, and the last step looks like an error.** Read
[SETUP.md § 3](./SETUP.md#3-authorise-once) before running it. Short version:

```bash
GTM_CREDENTIALS_FILE=/absolute/path/to/credentials.json \
GTM_TOKEN_FILE=/absolute/path/to/token.json \
npx gtm-mcp-auth
```

The environment variables have to be on that command. The ones in your MCP config apply
only to the server, not to a command you type in a terminal. Without them the tool looks
for `credentials.json` in whatever folder you happen to be in, and writes `token.json`
there too, which may be a git repo.

---

## The rule

**The AI writes. A human publishes. Always.**

Not because the tags come out bad. They mostly come out fine. Because a wrong tag does
not throw an error. It quietly reports the wrong number, and you find out a quarter
later when someone asks why the figures never matched.

A broken tag announces itself. A tag pointing at the wrong element does not. That is the
failure mode worth designing around, and the only defence is a person looking before it
goes live.

Before you publish:

- Preview the container and click the actual thing. Does the trigger fire?
- Does it fire *only* then? Not on page load, not on every click.
- Is the selector stable, or a generated class name that dies next deploy?
- Is anything personal being collected? Emails in a URL, names in a data layer.
- Is this the right container? There is no undo on a published container, only a
  rollback everybody sees.

---

## Security

Read this part.

**There is no read-only mode.** The token this tool creates always carries
`tagmanager.edit.containers` and `tagmanager.publish`. Those scopes are fixed in the
package; you do not get to choose a narrower set at the consent screen. Every token
produced here can publish to production.

**Nothing technically stops the AI publishing.** The server exposes a publish operation
and the token permits it. "A human publishes" is a rule enforced by your prompts and
your attention, not by a permission setting. If your client tool supports per-tool
approval (Claude Code does), deny the publish and delete operations explicitly. That is
the only hard guardrail available.

**It can also delete.** Containers, workspaces, versions, tags. Deleting a container is
worse than a bad publish and there is no undo. Treat delete the same way as publish.

**Never commit `credentials.json` or `token.json`.** The first is your OAuth client, the
second is a live access token to every GTM container the authorising account can reach.
Anyone holding `token.json` can publish to those containers. There is a `.gitignore`
here and one at the repo root covering both, but the safest thing is to keep those files
outside any repo entirely.

**On a client's account, prefer GTM's own user management.** Have them add your Google
account in GTM → Admin → User Management, then authorise as yourself. This is the
cleanest path: the client can revoke it themselves inside GTM in ten seconds, no
credential of theirs ever touches your machine, and nobody has to send anything
sensitive over chat.

If the client must authorise instead, know what you are asking. If they run the auth on
their machine, the token lands on *their* machine and your server cannot use it. If they
run it on yours, they are typing their Google password into your computer. If they do it
remotely, they have to send you the authorisation code, which is a one-time bearer
secret that should not go over Slack or email. Use GTM user management.

**Revoking is two actions, not one.** The client revokes the grant at
myaccount.google.com → Security → Your connections to third-party apps. That stops new
tokens. You also delete `token.json` from your disk.

---

## Credit

- **`gtm-mcp`** — Pouya Nafisi, MIT. https://github.com/pouyanafisi/gtm-mcp
  99 operations across accounts, containers, workspaces, tags, triggers, variables and
  versions. All the GTM work here is his server doing it.
- **`chrome-devtools-mcp`** — Google. The browser half.

I wrote the cloud setup notes, the prompts and the QA rule. That is all. Those
third-party tools keep their own licenses.
