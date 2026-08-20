#!/usr/bin/env python3
"""Run the rubber-duck evals against the live model and score every case.

For each case in evals.json:
  1. replay the case's prior transcript, then its user turn
  2. call Claude to get the duck's reply (skill arm: SKILL.md as the system
     prompt; control arm: no system prompt)
  3. grade deterministic assertions in code (reuses grade.py)
  4. grade semantic assertions with an LLM judge (one call per case)

Two arms:
  --skill     (default) system = SKILL.md   → the duck
  --baseline  no skill prompt               → plain assistant (control)

The baseline arm should FAIL "no_solution" etc. by design — that delta is the
point of the benchmark.

Usage:
  export ANTHROPIC_API_KEY=...      # or `ant auth login`
  python run_evals.py               # skill arm, all cases
  python run_evals.py --baseline    # control arm
  python run_evals.py --case hint-after-3-full   # one case

Needs: pip install anthropic.

Every case past turn 1 carries a `history` of real prior turns, replayed to
both arms. That matters: with only a synthetic "you are at turn 4" note and no
stated problem, assertions like gives_solution and confirms_landing are
unpassable for either arm, and the control answers "I have no context" instead
of handing over a fix — which flatters the skill by understating the gap.
"""

import argparse
import json
import sys
from pathlib import Path

import anthropic

import grade  # deterministic checkers + case loader

# Redirecting this report to a file on Windows encodes it as cp1252, which
# cannot represent the duck emoji the replies tend to open with.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

MODEL = "claude-opus-5"
SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"
EVALS = Path(__file__).with_name("evals.json")


def skill_system() -> str:
    """SKILL.md body, frontmatter stripped, as the system prompt."""
    text = SKILL.read_text(encoding="utf-8")
    if text.startswith("---"):
        text = text.split("---", 2)[2]
    return text.strip()


def get_reply(client, case: dict, arm: str) -> str:
    """One reply for one case. Both arms replay the same conversation."""
    resp = client.messages.create(
        model=MODEL,
        max_tokens=4096,  # adaptive thinking eats budget; 1024 returned empty replies
        system=skill_system() if arm == "skill" else anthropic.NOT_GIVEN,
        messages=case.get("history", []) + [{"role": "user", "content": case["user"]}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    # An empty reply scores 0 on every assertion and looks like a real failure.
    # Make it say so instead of quietly poisoning the benchmark.
    return text or f"<EMPTY REPLY: no text block, stop_reason={resp.stop_reason}>"


JUDGE_SYS = (
    "You grade one assistant reply against yes/no criteria. The assistant is a "
    "Socratic debugging 'rubber duck' that should ask questions, not give answers. "
    'Reply ONLY with JSON: {"<assertion>": true|false, ...}. true = the criterion holds.'
)


def judge(client, reply: str, assertions: list[str]) -> dict:
    questions = {a: grade.SEMANTIC[a] for a in assertions if a in grade.SEMANTIC}
    if not questions:
        return {}
    prompt = (
        f"Reply to grade:\n---\n{reply}\n---\n\nCriteria:\n"
        + "\n".join(f"- {a}: {q}" for a, q in questions.items())
    )
    resp = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=JUDGE_SYS,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = "".join(b.text for b in resp.content if b.type == "text")
    start, end = raw.find("{"), raw.rfind("}")
    return json.loads(raw[start : end + 1]) if start >= 0 else {}


def run(arm: str, only: str | None) -> int:
    client = anthropic.Anthropic()
    data = json.loads(EVALS.read_text(encoding="utf-8"))
    cases = [c for c in data["cases"] if only is None or c["id"] == only]
    if not cases:
        raise SystemExit(f"no case '{only}'")
    for case in cases:
        # A case past turn 1 without its transcript silently breaks the
        # benchmark rather than failing loudly, so refuse to run one.
        expected = 2 * (case["turn"] - 1)
        actual = len(case.get("history", []))
        if actual != expected:
            raise SystemExit(
                f"case '{case['id']}' is at turn {case['turn']} and needs "
                f"{expected} history entries, has {actual}"
            )

    total = passed = 0
    print(f"# arm: {arm}  model: {MODEL}  cases: {len(cases)}\n")
    for case in cases:
        reply = get_reply(client, case, arm)
        sem = [a for a in case["assert"] if a in grade.SEMANTIC]
        verdicts = judge(client, reply, sem) if sem else {}
        print(f"## {case['id']} ({case['intensity']}, turn {case['turn']})")
        for line in reply.splitlines() or [""]:
            print(f"   | {line}")
        for a in case["assert"]:
            if a in grade.SEMANTIC:
                ok = bool(verdicts.get(a))
                status, detail = ("PASS" if ok else "FAIL"), "judge"
            else:
                status, detail = grade.check(a, reply)
            total += 1
            passed += status == "PASS"
            mark = {"PASS": "ok ", "FAIL": "XX ", "MANUAL": "?? "}[status]
            print(f"   [{mark}] {a}: {detail}")
        print()
    print(f"# {passed}/{total} assertions passed")
    return 0 if passed == total else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", action="store_true", help="run without the skill (control arm)")
    ap.add_argument("--case", help="run a single case by id")
    args = ap.parse_args()
    return run("baseline" if args.baseline else "skill", args.case)


if __name__ == "__main__":
    sys.exit(main())
