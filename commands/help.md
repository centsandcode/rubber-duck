---
description: "Rubber Duck: what it does, how to steer it, how to stop it"
---

Print this reference to the user, as-is, and nothing else. Do not add
commentary, do not start ducking, do not ask a question at the end. Translate
it into the language the user has been writing in.

---

**🦆 Rubber Duck** — you reach the answer, the duck only asks.

**Start**

- `/rubber-duck:rubber-duck` — starts at the default level
- `/rubber-duck:rubber-duck ultra` — starts at the level you name

It never starts on its own. "I'm stuck" is a normal question and gets a normal
answer.

**Levels** — how much scaffolding you get

| Level | For whom |
|-------|----------|
| `lite` | Learning to code. Warm, each question says why it is being asked. A hint after 1 stuck exchange. |
| `full` | The default. Neutral questions that stand alone. A hint after 3. |
| `ultra` | You want pure friction. Terse questions, no hints, ever. |

Change level mid-conversation by saying so: "go ultra", "modo lite".

**Stop**

- `/rubber-duck:duck-off`
- or just say it: "just tell me the answer", "dime la solución". Any clear
  request to stop wins, in any language.

**While it is running**

- One question per reply. Never two.
- No code, no snippets, no commands to run — not even a diagnostic one.
- Hints point at where to look, never at what the cause is.
- When you land it, it says so and stops asking.
- Anything destructive (`rm -rf`, `DROP TABLE`, force-push) is answered
  straight, never behind a question.

Full spec: `skills/rubber-duck/SKILL.md` in the repo.
