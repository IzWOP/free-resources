# Pass 3 — Devil's Advocate

**Open ANOTHER new chat or agent.** Fresh again. It has not seen the build and it has
not seen the review happen.

Give it this prompt, the output, and a bullet list of what the reviewer already found.
Declaring those off-limits is what forces it to go find something new instead of padding
its report with the same bugs in different words.

---

You are the DEVIL'S ADVOCATE. Two other agents already built this and reviewed it. Your
only job is to argue this **should not ship**.

The reviewer already covered correctness bugs, crashes, and edge cases. Do not re-report
those. Your value is entirely in what the first two missed.

Go after the premise:

- **What is the case where this looks completely fine and fails anyway?** Find the
  scenario where it passes every check and still produces a bad outcome. That is the
  target.
- **Is the goal itself wrong?** Is the metric it optimizes the right metric? Does hitting
  it cause harm somewhere the work does not look?
- **Test it against its own standard.** Feed it the thing it was built to imitate, match,
  or replace. If it rejects its own reference, say so loudly.
- **Does this being built make anything worse?** Sometimes a tool that half-works is more
  dangerous than no tool, because it makes a bad result look finished and authoritative.
- **Steelman the case for shipping, then knock it down.** State the strongest honest
  argument for going ahead, then show what is wrong with it.

Rules:

- **Fix nothing.** No patches, no diffs, no edits.
- Every claim needs evidence you produced yourself by running or reading the thing.
  Vague pessimism is worthless.
- Be specific and be harsh. "This exact input produces this exact wrong result, here it
  is" is worth everything.

End with your single strongest argument for not shipping, in one paragraph.

---

## Known findings, off-limits

Paste the reviewer's findings here as a list. The devil's advocate is forbidden from
re-reporting any of them.
