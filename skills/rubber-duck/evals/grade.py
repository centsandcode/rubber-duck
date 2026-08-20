#!/usr/bin/env python3
"""Grade a rubber-duck reply against the behavioral assertions in evals.json.

The skill is non-deterministic, so we grade properties of a reply, not exact
text. Two tiers of checks:

  - deterministic: decided here from the reply text alone (regex/heuristics)
  - semantic:      need judgment ("is this really not the solution?"). Returned
                   as MANUAL with the question to ask a human or an LLM judge.

Usage:
  # score a single pasted reply against a case
  python grade.py <case_id> < reply.txt
  python grade.py one-question-per-turn "What does that variable hold there?"

  # run the built-in self-check (no input needed)
  python grade.py --self-check

No dependencies. ponytail: language detect is a naive marker heuristic; swap
for a real detector (langid/fasttext) only if it misjudges in practice.
"""

import json
import re
import sys
from pathlib import Path

EVALS = Path(__file__).with_name("evals.json")

# Assertions we can decide from the reply text alone.
DETERMINISTIC = {
    "exactly_one_question",
    "no_code_block",
    "not_only_a_question",
    "language_is_spanish",
    "no_trailing_question_loop",
}
# Assertions that need a human or LLM judge.
SEMANTIC = {
    "no_solution": "Does the reply withhold the actual fix?",
    "gives_solution": "Does the reply contain the actual fix?",
    "has_hint": "Does the reply give ONE small directional hint (not the fix)?",
    "no_hint": "Is the reply free of any hint (pure question)?",
    "not_a_leading_answer": "Does the question avoid smuggling the diagnosis inside it?",
    "confirms_landing": "Does the reply validate the user's correct answer and stop?",
    "warns_directly": "Does the reply warn about the destructive action directly?",
}

_SPANISH_MARKERS = re.compile(
    r"[¿¡áéíóúñ]|\b(qué|cómo|dónde|cuál|por qué|función|cuándo|tú|línea)\b",
    re.IGNORECASE,
)


def count_questions(text: str) -> int:
    """Number of question sentences. '?' clusters collapse to one."""
    collapsed = re.sub(r"\?+", "?", text)
    return collapsed.count("?")


def has_code_block(text: str) -> bool:
    return "```" in text


def is_spanish(text: str) -> bool:
    return bool(_SPANISH_MARKERS.search(text))


def check(assertion: str, reply: str):
    """Return (status, detail). status in PASS/FAIL/MANUAL."""
    if assertion == "exactly_one_question":
        n = count_questions(reply)
        return ("PASS" if n == 1 else "FAIL", f"{n} question(s)")
    if assertion == "no_code_block":
        bad = has_code_block(reply)
        return ("FAIL" if bad else "PASS", "code block present" if bad else "no code")
    if assertion == "not_only_a_question":
        # the reply must do more than ask — exit replies answer the user
        only_q = count_questions(reply) >= 1 and len(re.sub(r"[^?.!]", "", reply)) <= 1
        return ("FAIL" if only_q else "PASS", "only a question" if only_q else "ok")
    if assertion == "no_trailing_question_loop":
        # confirming the landing may offer one next-step question, not a probe chain
        n = count_questions(reply)
        return ("PASS" if n <= 1 else "FAIL", f"{n} question(s)")
    if assertion == "language_is_spanish":
        ok = is_spanish(reply)
        return ("PASS" if ok else "FAIL", "spanish" if ok else "not spanish")
    if assertion in SEMANTIC:
        return ("MANUAL", SEMANTIC[assertion])
    return ("MANUAL", f"unknown assertion: {assertion}")


def load_case(case_id: str) -> dict:
    data = json.loads(EVALS.read_text(encoding="utf-8"))
    for c in data["cases"]:
        if c["id"] == case_id:
            return c
    raise SystemExit(f"no case '{case_id}'. ids: {[c['id'] for c in data['cases']]}")


def grade(case_id: str, reply: str) -> int:
    case = load_case(case_id)
    print(f"# {case_id} ({case['intensity']}, turn {case['turn']})")
    print(f"  {case['description']}")
    failed = 0
    for a in case["assert"]:
        status, detail = check(a, reply)
        mark = {"PASS": "ok ", "FAIL": "XX ", "MANUAL": "?? "}[status]
        print(f"  [{mark}] {a}: {detail}")
        if status == "FAIL":
            failed += 1
    return 1 if failed else 0


def self_check() -> int:
    """Prove the deterministic checkers on known good/bad samples."""
    assert count_questions("What does it hold?") == 1
    assert count_questions("Why? And where?") == 2
    assert count_questions("Right — 80. Now try 200. What returns?") == 1
    assert count_questions("That's it. You found it.") == 0
    assert not has_code_block("just prose here")
    assert has_code_block("here:\n```\nx=1\n```")
    assert is_spanish("¿Qué devuelve esa función?")
    assert is_spanish("Cuando lo ejecutas, qué línea falla")
    assert not is_spanish("What does the last line return?")
    # full assertion path on a good single-question reply
    assert check("exactly_one_question", "What value is x there?") == ("PASS", "1 question(s)")
    assert check("exactly_one_question", "Is it x? Or y?")[0] == "FAIL"
    assert check("no_code_block", "```py\nx\n```")[0] == "FAIL"
    assert check("language_is_spanish", "What returns?")[0] == "FAIL"
    assert check("no_solution", "anything")[0] == "MANUAL"
    print("self-check OK")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if args[0] == "--self-check":
        return self_check()
    case_id = args[0]
    reply = " ".join(args[1:]) if len(args) > 1 else sys.stdin.read()
    if not reply.strip():
        raise SystemExit("no reply text (pass as arg or via stdin)")
    return grade(case_id, reply.strip())


if __name__ == "__main__":
    sys.exit(main())
