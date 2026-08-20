#!/usr/bin/env python3
"""Run the rubber-duck evals against the live model and score every case.

For each case in evals.json:
  1. build a prompt (SKILL.md as system + the case's user turn)
  2. call Claude to get the duck's reply
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

Needs: pip install anthropic. ponytail: multi-turn state (turn/stuck_exchanges)
is approximated with a synthetic context note, not a real prior transcript —
good enough to probe hint timing; replay real transcripts if a case proves flaky.
"""

import argparse
import json
import sys
from pathlib import Path

import anthropic

import grade  # deterministic checkers + case loader

MODEL = "claude-opus-4-8"
SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"
EVALS = Path(__file__).with_name("evals.json")


def skill_system() -> str:
    """SKILL.md body, frontmatter stripped, as the system prompt."""
    text = SKILL.read_text(encoding="utf-8")
    if text.startswith("---"):
        text = text.split("---", 2)[2]
    return text.strip()


def context_note(case: dict) -> str:
    """Synthetic prior-state note so single-shot calls can probe turn/hint timing."""
    bits = [f"(You are at turn {case['turn']} of an active rubber-duck session"]
    if "stuck_exchanges" in case:
        bits.append(f", and the user has been stuck for {case['stuck_exchanges']} exchanges")
    bits.append(f". Current intensity: {case['intensity']}.)")
    return "".join(bits)


def get_reply(client, case: dict, arm: str) -> str:
    system = skill_system() if arm == "skill" else ""
    if arm == "skill" and case["turn"] > 1:
        system += "\n\n" + context_note(case)
    resp = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system or anthropic.NOT_GIVEN,
        messages=[{"role": "user", "content": case["user"]}],
    )
    return "".join(b.text for b in resp.content if b.type == "text").strip()


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

    total = passed = 0
    print(f"# arm: {arm}  model: {MODEL}  cases: {len(cases)}\n")
    for case in cases:
        reply = get_reply(client, case, arm)
        sem = [a for a in case["assert"] if a in grade.SEMANTIC]
        verdicts = judge(client, reply, sem) if sem else {}
        print(f"## {case['id']} ({case['intensity']}, turn {case['turn']})")
        print(f"   reply: {reply[:100]!r}")
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
