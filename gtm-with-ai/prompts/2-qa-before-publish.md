# Prompt 2 — QA before you publish

Run this after the tag is built and before anything goes live. Then do the manual checks
yourself. The model can tell you what it built; only you can tell whether it is right.

---

```
Before I publish, walk me through what you created and answer these directly. One line
each, no preamble.

1. What exactly does this tag fire on? Read the trigger back from the container and
   describe the conditions that are actually saved, in plain English. If there are none,
   say so first.
2. What would ALSO make it fire that I might not expect? Page load, other buttons,
   anything matching the selector elsewhere on the site, navigation.
3. Is the selector stable across a redeploy? Say yes or no, and why.
4. Does anything it collects contain personal data? Email addresses in URLs, names,
   phone numbers, anything in the data layer you are reading.
5. Which container and which workspace is this in? Give me the container name, not just
   an ID.
6. What already existed in this container that overlaps with what you built?

Then stop. I will test and publish.
```

---

## The manual checks, which are the ones that matter

Do these yourself in GTM Preview. This is fifteen minutes and it is the difference
between a tag you trust and a number you argue about next quarter.

- [ ] **Preview the container and click the actual thing.** Does the trigger fire?
- [ ] **Does it fire ONLY then?** Load the page and do nothing. Click something that is
      NOT the button; if it fires, the trigger has no condition. Click other things.
      Navigate. A trigger that also fires on page load will quietly inflate everything.
- [ ] **Check a second page.** If the selector matches something unrelated elsewhere on
      the site, you will find out here rather than in a report.
- [ ] **Look at what is being sent.** Open the tag's values in Preview. Is there an email
      address sitting in a URL parameter? That is a GDPR problem, not a tagging problem.
- [ ] **Confirm the container.** Right client, right property, right environment. There
      is no undo on a published container, only a rollback that everybody sees.
- [ ] **Name it like a human will read it.**

## Why a human publishes, always

A broken tag announces itself. Something errors, something obviously stops reporting,
somebody notices within a day.

A tag pointed at the *wrong element* announces nothing. It fires, it reports, the number
looks plausible, and the dashboard is confidently wrong. You find out a quarter later
when someone asks why the conversion count never matched the CRM, and by then every
decision made on that number was made on a wrong number.

That failure mode is why the AI writes and a person publishes. Not because the output is
bad. Because the expensive mistakes here are the silent ones.
