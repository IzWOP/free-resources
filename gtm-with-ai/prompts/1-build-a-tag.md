# Prompt 1 — build a tag

Paste this, fill in the bracketed bits, and let it run. It is written to make the
model look at the page before it writes anything, because a tag built without looking at
the DOM is a guess.

---

```
I want to track [WHAT, in plain words, e.g. clicks on the "Get a Quote" button in the
header] on [URL].

Container: [GTM CONTAINER NAME, e.g. "example.com - Web". If you are not sure, list my
accounts and containers first and ask me which one.]
Tag type: [e.g. GA4 Event. Name the destination too: which existing GA4 configuration
tag or measurement ID it should use, and what the event name should be.]

Work in this order and do not skip ahead.

1. Open the page in the browser and find the element. Tell me what you found: the tag
   name, its visible text, its id, its classes, and anything nearby that identifies it.

2. Propose a selector, and tell me WHY it will still match after a redeploy. If the only
   thing available is a generated or hashed class name, say so and stop, rather than
   shipping something that dies on the next build. Prefer, in this order: a stable id,
   a data attribute, a form or link target, text content, structural position. Tell me
   which one you used.

3. Check whether this is already tracked. List the existing tags, triggers and variables
   in the container and tell me if something already fires on this. Do not create a
   duplicate.

4. Create the trigger. Then create the tag, of the type named above, pointed at the
   destination named above. Wire them together. Use a naming convention that matches
   what is already in the container; look at the existing names first and follow them
   rather than inventing your own. If I did not give you enough to pick the tag type or
   the destination, ask. Do not choose for me.

   If the trigger is a click, link click or form trigger: gtm-mcp cannot save conditions
   on those types, so it will be created with none and fire on everything. After
   creating it, read the trigger back and tell me whether a condition actually saved. If
   not, give me the exact condition to add by hand in GTM: the trigger type (Some
   Clicks / Some Forms), the variable, the operator, and the value.

5. Leave everything in a workspace. Do NOT publish. Do not create a container version.

6. Report back: what you created, the exact selector, the trigger conditions AS SAVED in
   the container (read them back, do not repeat what you intended), and what I should
   click to test it.

If anything is ambiguous, ask me instead of choosing for me.
```

---

## Why each step is in there

**Step 1 before anything else.** A GTM connector on its own cannot see the page. Left to
itself it will write something plausible from the URL and the element name you gave it.
Forcing it to look first is the entire reason the browser server is in the stack.

**Step 2's "tell me why it will survive."** This is the one that saves you. Frameworks
regenerate class names on build. A tag keyed to `css-1x9fk2p` works today and is dead on
Thursday, silently, with no error anywhere.

**Step 3, the duplicate check.** Containers accumulate. Two tags firing on the same click
double-count, and double-counted conversions are worse than none because you act on them.

**Step 4's naming convention.** Whoever opens this container next is a human, possibly
you in eight months. Matching the existing names costs nothing now and saves an hour
later.

**The click and form trigger check in step 4.** `gtm-mcp` writes conditions into a field
Google only honours on custom event triggers. On a click trigger they silently disappear
and the trigger fires on every click. Reading the trigger back is the only way to catch
it before Preview does. See the README's Known limitation section.

**Step 5, no publishing.** Non-negotiable. See the QA prompt.

**Why the container and tag type are placeholders.** The server needs to know which
container it is working in, and "make a tag" is not a complete instruction. GA4 event,
conversion linker and custom HTML are different things pointed at different
destinations. Leave these blank and the model either asks you (fine) or picks for you
(not fine).

**If the page needs a login**, `chrome-devtools-mcp` runs its own Chrome profile that is
signed in to nothing. Client staging sites and member areas will not load unless you
connect it to your existing Chrome.
