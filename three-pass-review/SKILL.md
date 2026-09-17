---
name: three-pass-review
description: Run build, cold review, and devil's advocate as three separate agents so nothing reviews its own work. Use when finishing a feature, a script, a plan, or any deliverable before it ships.
---

# Three-Pass Review

Run any deliverable through three agents. The reviewer and the devil's advocate must be
FRESH agents that never saw the builder's reasoning. That is the entire mechanism.

## Steps

**1. Build.** Spawn a builder agent with `prompts/1-builder.md` plus the task. Require it
to actually run what it made and to paste real output. Require it to list its own
limitations.

**2. Review.** Wait for step 1 to finish. Spawn a NEW agent with `prompts/2-reviewer.md`,
the output, and the original requirements. Do not pass it the builder's reasoning. It
files problems worst-first with the practical consequence of each, and it fixes nothing.

**3. Devil's advocate.** Spawn ANOTHER new agent with `prompts/3-devils-advocate.md`, the
output, and the reviewer's findings marked off-limits. Its job is to attack the premise
and find the case that passes every check and still fails.

**4. Report.** Show each pass's output as it lands. Do not summarize away the findings.

## Rules

- Never let the builder review itself. A builder that just decided something was fine
  will decide it again.
- Never let pass 3 restate pass 2. Declare the known findings off-limits explicitly.
- Do not fix during review. Reviewing and fixing in the same pass makes the reviewer
  stop looking as soon as it has something to do.
- Run pass 1 to completion before pass 2 starts.

## Model split

Build on your strongest model. Review on a different model where you can, since a
different model fails differently. Same model with fresh context still works. The fresh
context is the part that matters.
