# Setup

The install is five minutes. Google Cloud is the rest of it, and it is the only fiddly
part. Do it once and it works for every container you are granted access to.

Budget 30-45 minutes the first time. Anyone telling you twenty has done it before.

**You need Node.js 18+** (`node --version`). Everything here runs through `npx`.

---

## 1. Google Cloud

You are creating an OAuth app that asks a Google account for permission to touch its Tag
Manager. That is all this is. **No billing account is required** for the Tag Manager API,
so if you get prompted for a card, you took a wrong turn.

Google renamed this area of the console in 2025. You may land on **Google Auth Platform**
with pages called Branding, Audience, Clients and Data Access, rather than the older
"OAuth consent screen". Both routes end in the same place; the names below note the new
labels where they differ.

1. **Create a project.** Name it something you will recognise in a year.

2. **APIs & Services → Library.** Search **Tag Manager API**. Enable it.
   Skip this and auth succeeds while every call fails with a confusing permission error.
   That is a miserable hour to spend.

3. **OAuth consent screen** (new: Google Auth Platform → Branding).
   - **External**, unless every user will be inside your own Google Workspace org.
     Internal has no 7-day token expiry; External does. See the gotcha below.
   - App name, support email, developer email. Nothing else is needed to get moving.

4. **Add yourself as a test user.** (New: Google Auth Platform → Audience → Test users.)
   Do it now, while you are here. If you skip it, your own login is refused later with a
   message that the app is blocked, and it is not obvious why.

5. **Credentials → Create credentials → OAuth client ID** (new: Clients → Create client).
   - Application type: **Desktop app**. Not Web.
   - Download the JSON.

6. **Rename it.** Google names the download something like
   `client_secret_1234-abcd.apps.googleusercontent.com.json`. Rename it to
   `credentials.json`, or keep the long name and point the env var at that exact name.
   Either works; mismatching them is the common mistake.

7. **Put it somewhere outside any git repo.** A folder in your home directory is fine.

### The gotcha nobody mentions

A new OAuth app sits in **Testing** publishing status. While it does:

- **Only accounts added as test users can authorise it** (max 100). Add the client's
  Google account before asking them to log in, or they hit a wall saying the app is
  blocked.
- **Refresh tokens expire after 7 days.** The connection stops working about a week
  later and you re-run the auth command *and restart your MCP client*. This is the
  single most common "it worked last week" complaint. It applies to External apps
  requesting scopes beyond name, email and profile, which these are.

Publishing the app removes both limits. Tag Manager scopes are sensitive, so Google will
want the app verified. An unverified app still works in Production for up to 100 users,
with a "Google hasn't verified this app" interstitial the user has to click past. For a
handful of clients, staying in Testing and re-authing weekly is usually less friction
than verification. Know which trade you are making.

---

## 2. Install the servers

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

- **Claude Desktop:** Settings → Developer → Edit Config. Then **fully quit and reopen**
  the app. Closing the window is not enough.
- **Claude Code:** `claude mcp add-json` is the supported route. `~/.claude.json` holds
  other state, so hand-editing it is fragile.
- Paths must be **absolute**. `~` does not expand. On Windows escape backslashes:
  `"C:\\Users\\you\\gtm\\credentials.json"`.
- `token.json` does not exist yet. The next step writes it.

---

## 3. Authorise, once

**Read this whole section before running the command. The last step looks like an error
page and it is supposed to.**

```bash
GTM_CREDENTIALS_FILE=/absolute/path/to/credentials.json \
GTM_TOKEN_FILE=/absolute/path/to/token.json \
npx gtm-mcp-auth
```

Those variables must be on the command. The `env` block in your MCP config applies only
to the server process, not to something you type in a terminal. Without them the tool
looks for `credentials.json` in your current folder and writes `token.json` there, which
might be a repo.

What happens, in order:

1. **It prints a URL.** Nothing opens automatically. Copy it into a browser yourself.
2. **Sign in** as the Google account that has access to the containers you want.
3. You will see **"Google hasn't verified this app"**. That is your own app. Click
   Advanced, then continue.
4. Grant the permissions. It will ask to edit and publish container versions. There is
   no narrower option; those scopes are fixed in the tool.
5. **The browser lands on an error page** at `http://localhost/?code=...` saying the
   site can't be reached. **This is expected.** Nothing is listening on localhost. Do
   not close the tab.
6. **Copy the `code` value out of the address bar**: everything after `code=` and
   before the next `&`. Paste it back into the terminal.
   **If what you copied contains `%2F`, replace it with `/` before pasting.** Chrome
   copies the URL-encoded form, and a code beginning `4%2F0A...` fails the exchange
   with `invalid_grant`. It should begin `4/0A...`.
7. The token is written to `GTM_TOKEN_FILE`.

Restart your MCP client so it picks up the servers.

**Test it read-only before letting it write anything:**

> List my GTM accounts and containers.

Containers back means you are done. A permission error almost always means the Tag
Manager API is not enabled on the project.

If the server ever complains that it cannot find a token and tells you to run
`npm run auth`, ignore that wording. That message is written for people who installed
from source. Re-run the command above.

---

## 4. Working on a client's container

**Preferred: the client adds you in GTM.**

GTM → Admin → User Management → add your Google account, with Edit or Publish as
appropriate. Then you authorise as yourself using your own credentials.

This is the clean path. No credential of theirs touches your machine, nothing sensitive
gets sent over chat, and they can revoke you inside GTM in ten seconds without involving
Google account settings at all.

**If they must authorise instead,** understand what each version costs:

- On *their* machine: `token.json` lands on their disk, and your server cannot use it.
- On *your* machine: they type their Google password into your computer.
- Remotely: they have to send you the authorisation code from step 6. That code is a
  one-time bearer secret. Not over Slack. Not over email.

Use GTM user management.

**Whichever path, tell them:**

- what access this grants (edit and publish on their Tag Manager)
- that a token will sit on whichever machine ran the auth
- how to revoke: myaccount.google.com → Security → Your connections to third-party apps,
  or simply remove the user in GTM if you went the preferred route

Access a client cannot withdraw on their own is not access they meaningfully agreed to.

---

## 5. First real tag

Use [`prompts/1-build-a-tag.md`](./prompts/1-build-a-tag.md), then
[`prompts/2-qa-before-publish.md`](./prompts/2-qa-before-publish.md), then publish it
yourself.

Do the first one on a container that does not matter.

**One thing about the browser half:** `chrome-devtools-mcp` launches its own Chrome
profile, which is not logged in to anything. Pages behind a login will not load unless
you connect it to your existing Chrome. That means client staging sites and member
areas. Check
that project's README for the flag. Public pages work out of the box.
