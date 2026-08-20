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

```
npx skills add https://github.com/centsandcode/rubber-duck --skill rubber-duck
```

> Claude Code plugin marketplace install (`/plugin marketplace add …`) is
> coming once the marketplace manifest lands — see Iter 4.

## Use

Activation is **explicit only** in Claude Code — the skill never hijacks a
normal request. Turn it on with:

- `/rubber-duck` or `/duck`
- or ask for it directly: "rubber duck mode", "socratic mode", "ask me
  questions instead of giving me the answer"

Natural phrases like "I'm stuck" or "weird bug" do **not** activate it in
Claude Code by design. (Other agents that read [`AGENTS.md`](AGENTS.md) —
Cursor, Copilot, Windsurf — may honor those phrases too; see that file.)

Exit any time with `/duck-off` or "just tell me the answer".

### Intensity levels

Match the amount of scaffolding to your experience:

| Command | For whom | Behavior |
|---------|----------|----------|
| `/duck lite` | Beginners | Warm questions with context, hint after 1 stuck exchange |
| `/duck full` | Default | Neutral standalone questions, hint after 3 |
| `/duck ultra` | Advanced | Terse questions, no hints ever |

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

## Compatibility

Works with any agent that reads `AGENTS.md` (Cursor, Copilot, Windsurf, …).
See [`AGENTS.md`](AGENTS.md) for the portable rules and
[`skills/rubber-duck/SKILL.md`](skills/rubber-duck/SKILL.md) for the full spec.

## License

MIT
