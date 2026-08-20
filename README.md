# rubber-duck

> *Don't give me the answer. Help me find it.*

A plugin for Claude Code that inverts the agent's role: instead of handing you
solutions, it asks questions until **you** reach the answer yourself. Inspired
by the classic rubber duck debugging technique.

## Why

By default, coding agents solve. You say "I have a weird bug" and they hand
back the fix before you've finished thinking. Fast — but it erodes learning and
makes you depend on the agent to understand your own code.

Rubber Duck turns the agent into a Socratic interlocutor. It listens, asks,
guides. It does not solve until you explicitly ask. You learn, you understand,
you solve.

## Install

**Claude Code:**

```bash
claude plugin marketplace add centsandcode/rubber-duck
```

```bash
claude plugin install rubber-duck@rubber-duck
```

Restart Claude Code to load it, then check it landed:

```bash
claude plugin list
```

**Any other agent** (Cursor, Copilot, Windsurf, …): copy
[`AGENTS.md`](AGENTS.md) into your project, or append it to the one you have.

## Use

Activation is **explicit only** in Claude Code — the skill never hijacks a
normal request. Turn it on with:

- `/rubber-duck` or `/duck`
- or ask for it directly: "rubber duck mode", "socratic mode", "ask me
  questions instead of giving me the answer"

Natural phrases like "I'm stuck" or "weird bug" do **not** activate it in
Claude Code by design. (Other agents that read [`AGENTS.md`](AGENTS.md) may
honor those phrases too; see that file.)

Exit any time with `/duck-off`, "just tell me the answer", or the same request
in your own language.

### Intensity levels

Match the amount of scaffolding to your experience:

| Command | For whom | Behavior |
|---------|----------|----------|
| `/duck lite` | Beginners | Warm questions with context, hint after 1 stuck exchange |
| `/duck full` | Default | Neutral standalone questions, hint after 3 |
| `/duck ultra` | Advanced | Terse questions, no hints ever |

The duck replies in whatever language you write in.

## Before / after

**Without rubber-duck:**

> **You:** My React component re-renders on every keystroke and it's slow.
> **Agent:** You're creating a new function on each render, so the child's
> props change every time. Wrap the callback in `useCallback`. Here's the fix: …

**With rubber-duck:**

> **You:** My React component re-renders on every keystroke and it's slow.
> **Duck:** When you say it re-renders — which component, the one with the
> input, or its children?
> **You:** The children. The list below the input.
> **Duck:** What props are you passing down to that list?
> **You:** An array I filter, and an onSelect handler.
> **Duck:** Of those two, which has the same value across renders, and which is
> built fresh each time?
> **You:** …the handler is an inline arrow function. It's new every render.
> **Duck:** That's it — a new function reference makes the memoized child see
> changed props and re-render. You found it.

## Benchmarks

The same 16 cases, run twice against `claude-opus-5`: once with the skill as
the system prompt, once with no system prompt at all (the control). Each case
replays a real conversation and grades the next reply. 42 gradeable
assertions per arm.

| Gate | Skill | Control |
|------|-------|---------|
| Exactly one question per reply | **100%** | 44% |
| No code block while active | **100%** | 33% |
| No runnable command handed over | **100%** | 40% |
| Withholds the solution while active | **100%** | 56% |
| No hint where the level forbids one | **100%** | 0% |
| Question does not smuggle the diagnosis | **100%** | 0% |
| Hint present where the level calls for one | **100%** | 50% |
| Replies in the user's language | 100% | 100% |
| Hands over the answer on exit | 100% | 100% |
| **Total** | **42/42 — 100%** | **24/42 — 57%** |

The row that matters is *withholds the solution*. The control is not broken
when it fails that one — solving is what a coding agent is for. The point is
that you can now choose.

**What these numbers are not.** Two gates are excluded from the totals above
because the measurement, not the model, was at fault:

- *Confirms the landing* — the judge was asked whether the reply validates the
  user's answer "and stops", while the spec tells the duck to validate and
  then offer a next step. Both arms were marked down for following the spec.
  The criterion is fixed in `grade.py`, but the run above predates the fix, so
  the gate is left out rather than reported from a broken measurement.
- *Warns directly about destructive commands* — on the `rm -rf /` case the
  control came back with `stop_reason: refusal`: the safety classifier
  declined the prompt, so there was no reply to grade. Reporting that as 0%
  would claim the control ignores destructive commands, which is not what
  happened. Refusals are now skipped rather than scored.

Two more caveats worth knowing before you trust the gap:

- The judge for the semantic gates is the same model family being graded.
- The control receives the same replayed transcript, in which the assistant
  has been asking Socratic questions. That can pull it toward the same style
  by imitation, which shrinks the measured gap rather than inflating it.

Reproduce any of it with the commands below.

## Reproducing the benchmark

The suite lives in [`skills/rubber-duck/evals/`](skills/rubber-duck/evals/).
Each case replays a real conversation and grades the next reply: mechanical
properties (how many questions, any code block, which language) in code, and
judgment calls (is this really not the solution?) with an LLM judge.

```bash
cd skills/rubber-duck/evals
pip install anthropic
export ANTHROPIC_API_KEY=...
python grade.py --self-check          # checkers only, no API calls
python run_evals.py                   # the duck
python run_evals.py --baseline        # the control
```

The quality gates each release has to clear are in
[`checkpoints.yaml`](skills/rubber-duck/checkpoints.yaml).

## Compatibility

Works with any agent that reads `AGENTS.md`. See that file for the portable
rules and [`SKILL.md`](skills/rubber-duck/SKILL.md) for the full spec.

## License

MIT
