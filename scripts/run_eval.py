"""Run the 10 test questions sequentially and write eval/results.md + the README results block.

Usage: python scripts/run_eval.py [--only 1,5] [--no-readme]
"""
from __future__ import annotations

import argparse
import asyncio
import re
import sys
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from helpdesk.agent import Result, ask  # noqa: E402
from helpdesk.config import get_settings, load_tenant  # noqa: E402

START, END = "<!-- EVAL:START -->", "<!-- EVAL:END -->"


def check(q: dict, r: Result) -> list[str]:
    """Return the list of failed checks (empty = pass)."""
    e, fails = q["expect"], []
    if "verdict" in e and r.verdict["kind"] != e["verdict"]:
        fails.append(f"verdict {r.verdict['kind']} != {e['verdict']}")
    if "sources_any" in e and not any(d in s for d in e["sources_any"] for s in r.sources):
        fails.append(f"no source from {e['sources_any']}")
    if e.get("no_sources") and r.sources:
        fails.append("unexpected sources")
    for t in e.get("tools_all", []):
        if t not in r.tools_called:
            fails.append(f"tool {t} not called")
    for pat in e.get("answer_all", []):
        if not re.search(pat, r.answer):
            fails.append(f"answer missing /{pat}/")
    for pat in e.get("answer_none", []):
        if re.search(pat, r.answer):
            fails.append(f"answer matches forbidden /{pat}/")
    return fails


async def run(only: set[int] | None) -> list[tuple[dict, Result | None, list[str]]]:
    questions = yaml.safe_load((ROOT / "eval" / "questions.yaml").read_text(encoding="utf-8"))
    out = []
    for q in questions:
        if only and q["id"] not in only:
            continue
        print(f"Q{q['id']}: {q['question'][:70]}", flush=True)
        try:
            r = await ask(q["question"], q["as"])
            fails = check(q, r)
        except Exception as ex:  # record, keep going
            r, fails = None, [f"error: {type(ex).__name__}: {ex}"]
        print("   ", "PASS" if not fails else f"FAIL {fails}", flush=True)
        out.append((q, r, fails))
    return out


def one_line(s: str, n: int = 90) -> str:
    s = re.sub(r"\s+", " ", s).replace("|", "\\|")
    return s if len(s) <= n else s[: n - 1] + "…"


def render(rows) -> str:
    s, t = get_settings(), load_tenant()
    done = [(q, r, f) for q, r, f in rows]
    ok = sum(1 for _, r, f in done if r and not f)
    ran = [r for _, r, _ in done if r]
    avg_lat = sum(r.latency_s for r in ran) / max(len(ran), 1)
    avg_in = sum(r.input_tokens for r in ran) / max(len(ran), 1)
    avg_out = sum(r.output_tokens for r in ran) / max(len(ran), 1)
    costs = [r.cost_usd for r in ran if r.cost_usd is not None]
    if costs:
        cost_txt = f"~${sum(costs) / len(costs) * 100:.2f} per 100 questions"
    else:
        cost_txt = f"{(avg_in + avg_out) * 100:,.0f} tokens per 100 questions (set `PRICE_IN_PER_M`/`PRICE_OUT_PER_M` in `.env` for USD)"
    lines = [
        f"**{ok}/{len(done)} passed** · avg latency {avg_lat:.1f}s · avg {avg_in:.0f} in / {avg_out:.0f} out tokens · {cost_txt}",
        "",
        f"Provider `{s.provider}`, model `{s.llm_model}`, guard model `{s.guard_model or 'none (heuristics only)'}`, "
        f"temperature 0 requested (this model ignores it, so wording can vary slightly between runs), tenant `{t.company_name}`, run on {date.today().isoformat()}.",
        "",
        "| # | Question | As | Type | Verdict | Tools | Sources | Latency | Result |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for q, r, f in done:
        if r is None:
            lines.append(f"| {q['id']} | {one_line(q['question'], 60)} | {q['as']} | {q['type']} | error | - | - | - | FAIL |")
            continue
        lines.append(
            f"| {q['id']} | {one_line(q['question'], 60)} | {q['as']} | {q['type']} | {r.verdict['kind']} ({r.verdict['layer']}) "
            f"| {', '.join(sorted(set(r.tools_called))) or '-'} | {one_line('; '.join(r.sources) or '-', 50)} "
            f"| {r.latency_s:.1f}s | {'PASS' if not f else 'FAIL'} |"
        )
    lines += ["", "### Answers", ""]
    for q, r, f in done:
        lines.append(f"**Q{q['id']}** (as {q['as']}): {q['question']}")
        lines.append("")
        if r is None:
            lines += [f"> ERROR: {f[0]}", ""]
            continue
        lines += [f"> {l}" if l.strip() else ">" for l in r.answer.strip().splitlines()]
        meta = f"guard: {r.verdict['kind']} via {r.verdict['layer']} ({r.verdict['reason']})"
        if r.output_actions:
            meta += f"; output guard: {', '.join(r.output_actions)}"
        lines += ["", f"<sub>{meta}; {r.input_tokens}+{r.output_tokens} tokens</sub>", ""]
        if f:
            lines += [f"**Failed checks:** {'; '.join(f)}", ""]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="comma-separated question ids")
    ap.add_argument("--no-readme", action="store_true")
    args = ap.parse_args()
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    only = {int(x) for x in args.only.split(",")} if args.only else None
    rows = asyncio.run(run(only))
    body = render(rows)
    (ROOT / "eval" / "results.md").write_text("# Eval results\n\n" + body + "\n", encoding="utf-8")
    print("Wrote eval/results.md")
    readme = ROOT / "README.md"
    if only is None and not args.no_readme and readme.exists():
        text = readme.read_text(encoding="utf-8")
        if START in text and END in text:
            text = re.sub(f"{re.escape(START)}.*?{re.escape(END)}", lambda _m: f"{START}\n{body}\n{END}", text, flags=re.S)
            readme.write_text(text, encoding="utf-8")
            print("Updated README results block")
    ok = sum(1 for _, r, f in rows if r and not f)
    print(f"{ok}/{len(rows)} passed")
    sys.exit(0 if ok == len(rows) else 1)


if __name__ == "__main__":
    main()
