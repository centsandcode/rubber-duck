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

<!-- BENCHMARK -->

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
