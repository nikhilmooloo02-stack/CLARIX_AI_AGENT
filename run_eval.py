"""Run CLARIX against eval_questions.json with the live model.

Usage:
    export GROQ_API_KEY=your_key        (Windows PowerShell: $env:GROQ_API_KEY="your_key")
    python run_eval.py                  # all questions
    python run_eval.py 8 9 28           # only these question ids

Each question runs as a fresh conversation. Questions with must_include /
must_not_include get an automatic PASS/FAIL; the rest print the reply for you
to judge against 'expected'. Full results are saved to eval_results.json.
"""
import json
import os
import re
import sys

from groq import Groq

from clarix_core import build_system_prompt, run_agent

MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
DEMO_DATA = True  # keep in step with streamlit_app.py


def normalise(text):
    text = text.lower().replace(" ", " ")
    text = re.sub(r"(?<=\d)[, ](?=\d{3})", "", text)  # 4,350 / 4 350 -> 4350
    return text


def check(reply, q):
    flat = normalise(reply)
    problems = []
    for needle in q.get("must_include", []):
        if normalise(needle) not in flat:
            problems.append(f"missing '{needle}'")
    for needle in q.get("must_not_include", []):
        if normalise(needle) in flat:
            problems.append(f"should not contain '{needle}'")
    return problems


def main():
    if not os.environ.get("GROQ_API_KEY"):
        sys.exit("Set GROQ_API_KEY first.")
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "eval_questions.json"), encoding="utf-8") as f:
        questions = json.load(f)["questions"]

    wanted = {int(a) for a in sys.argv[1:]}
    if wanted:
        questions = [q for q in questions if q["id"] in wanted]

    system = {"role": "system", "content": build_system_prompt(DEMO_DATA)}
    results, passed, failed, manual = [], 0, 0, 0

    for q in questions:
        reply, pdf = run_agent(client, MODEL, [system, {"role": "user", "content": q["question"]}])
        problems = check(reply, q)
        auto = "must_include" in q or "must_not_include" in q

        if auto and not problems:
            status, passed = "PASS", passed + 1
        elif auto:
            status, failed = "FAIL", failed + 1
        else:
            status, manual = "CHECK", manual + 1

        print(f"\n[{status}] #{q['id']} ({q['category']}) {q['question']}")
        print(f"  expected: {q['expected']}")
        print(f"  reply:    {reply[:600]}")
        if problems:
            print(f"  problems: {'; '.join(problems)}")
        if pdf:
            print(f"  pdf:      {pdf}")

        results.append({"id": q["id"], "status": status, "question": q["question"],
                        "reply": reply, "problems": problems, "pdf": pdf})

    with open(os.path.join(here, "eval_results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nAuto-checked: {passed} passed, {failed} failed. {manual} need your judgement.")
    print("Saved to eval_results.json")


if __name__ == "__main__":
    main()
