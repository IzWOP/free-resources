# Three-Pass Review

Your AI reviewing its own work will tell you it's fine. It is checking with the same
head that made the mistake, so it carries the same assumptions and the same blind spots
into the review. Telling it to be brutally honest does not fix that. It already thinks
it was honest.

This is the setup I use instead. Three passes, three separate agents, and the reviewer
never sees how the builder thinks.

## The three passes

| Pass | Job | Rule |
|---|---|---|
| **1. Builder** | Make the thing. | Verify it runs before reporting. |
| **2. Reviewer** | Find every problem, worst first. | Must be a FRESH agent. Fixes nothing. |
| **3. Devil's advocate** | Argue it should not ship. | Fresh again. Gets the reviewer's findings declared off-limits. |

The whole thing rests on one rule: **pass 2 and pass 3 must be new agents that have
never seen the builder's reasoning.** If you paste "now review this" into the same chat
that just built it, you get pass 1 again wearing a different hat.

## Why pass 3 exists

The reviewer finds bugs. The devil's advocate attacks the premise. They catch different
things, and the second one is usually the more expensive miss.

Real example from the run this came out of. A tool was built to turn written copy into
spoken video scripts. The builder reviewed itself and wrote out twelve honest-looking
limitations. The reviewer, fresh, found fourteen problems the builder missed, including
a dollar figure mangled into something nobody could say out loud. Then the devil's
advocate found the thing that actually mattered: the reference script the whole tool was
built to imitate failed the tool's own quality gate. Neither of the first two caught it,
because both of them had accepted the gate as correct.

## How to run it

1. Give `prompts/1-builder.md` to your build agent along with the task.
2. Open a **new chat or agent** and give it `prompts/2-reviewer.md` plus the output.
3. Open **another new one** and give it `prompts/3-devils-advocate.md`, the output, and
   a list of what the reviewer already found so it cannot pad by repeating them.

Works in Claude, ChatGPT, or anything else. Nothing here is tool-specific.

If you use Claude Code, `SKILL.md` wires the same thing up as a skill so you can run it
with one command.

## Model split that works for me

Build on the strongest model you have. Review on a different one if you can, because a
different model brings different failure modes. Same model is still fine. Different
context is what matters, not different weights.

---

Built by Isaac Vazquez. I post real builds as I do them: https://instagram.com/isaacbuildsai
