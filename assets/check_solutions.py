#!/usr/bin/env python3
"""Coverage gate for worked solutions: every audit exercise that has a
solutions page must have a complete, bidirectionally linked answer.

Checks per chapter with assets/solutions/chN/ (or chN.json):
  - solution count/numbers match assets/exercise-audit.json
  - ch<folder>/solutions.html has id="sol-N" anchors, backlinks to
    index.html#exercise-N and ../exercise-audit.html#chX-exY
  - chapter index links solutions.html#sol-N (added by build_exercise_audit)
  - audit page links <folder>/solutions.html#sol-N
  - diagram pages exist and pass fitcheck with 0 FAILs
  - no placeholder text (TODO/TBD/lorem) in sources or output
  - required bilingual fields present (fa/en pairs, followups answered)

Chapters without solutions yet are listed as PENDING (not a failure)
so the rollout can proceed chapter by chapter.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "assets"))
from build_solutions import load_chapter, solution_diagrams  # noqa: E402
from fitcheck import check as fitcheck  # noqa: E402

PLACEHOLDERS = ["TODO", "TBD", "lorem", "placeholder", "FIXME"]
import re as _re
PLACEHOLDER_RES = [_re.compile(r"\b" + _re.escape(w) + r"\b", _re.IGNORECASE) for w in PLACEHOLDERS]
REQUIRED_PAIRS = ["interview_q", "answer", "mental", "reasoning"]
REQUIRED_LISTS = ["assumptions", "steps", "followups", "mistakes"]


def main():
    audit = json.loads((ROOT / "assets" / "exercise-audit.json").read_text())
    by_chapter = {}
    for e in audit["exercises"]:
        by_chapter.setdefault(e["chapter"], []).append(e)
    fails, pending = [], []
    done = [p for p in sorted((ROOT / "assets" / "solutions").glob("ch*"))
            if p.is_dir() or p.suffix == ".json"]
    done_ch = set()
    for src in done:
        try:
            d = load_chapter(src)
        except Exception as e:  # noqa: BLE001 — concurrent authorship may leave a half-written file
            fails.append(f"{src}: unparseable ({e}); re-run after authors finish")
            continue
        ch = d["chapter"]
        done_ch.add(ch)
        items = {e["number"]: e for e in by_chapter[ch]}
        sols = d["solutions"]
        if sorted(s["number"] for s in sols) != sorted(items):
            fails.append(f"ch{ch}: solution numbers {sorted(s['number'] for s in sols)} != audit {sorted(items)}")
            continue
        page_p = ROOT / items[sols[0]["number"]]["folder"] / "solutions.html"
        if not page_p.exists():
            fails.append(f"ch{ch}: {page_p} not built — run build_solutions.py")
            continue
        page = page_p.read_text()
        folder = items[sols[0]["number"]]["folder"]
        for s in sols:
            n = s["number"]
            for base in REQUIRED_PAIRS:
                if not s.get(base + "_fa") or not s.get(base + "_en"):
                    fails.append(f"ch{ch}-sol{n}: missing {base}_fa/en")
            for lst in REQUIRED_LISTS:
                if not s.get(lst):
                    fails.append(f"ch{ch}-sol{n}: empty {lst}")
            for f in s.get("followups", []):
                for k in ("q_fa", "q_en", "a_fa", "a_en"):
                    if not f.get(k):
                        fails.append(f"ch{ch}-sol{n}: followup missing {k}")
            if not s.get("sources"):
                fails.append(f"ch{ch}-sol{n}: sources missing")
            code = s.get("code")
            if code:
                if code.get("status") not in ("verified", "not-executed"):
                    fails.append(f"ch{ch}-sol{n}: bad code status")
                if code.get("lang") != "java":
                    fails.append(f"ch{ch}-sol{n}: code must be java")
            if f'id="sol-{n}"' not in page:
                fails.append(f"ch{ch}: page missing #sol-{n}")
            if f'index.html#exercise-{n}' not in page:
                fails.append(f"ch{ch}-sol{n}: no backlink to exercise")
            if f'exercise-audit.html#ch{ch}-ex{n}' not in page:
                fails.append(f"ch{ch}-sol{n}: no backlink to audit")
            for di, diag in enumerate(solution_diagrams(s)):
                where = f"ch{ch}-sol{n}.diagrams[{di}]"
                made = diag.get("made", "hand")
                if made not in ("hand", "archify"):
                    fails.append(f"{where}: bad made")
                if made == "archify":
                    if not diag.get("source"):
                        fails.append(f"{where}: archify needs source")
                    elif not (ROOT / diag["source"]).exists():
                        fails.append(f"{where}: missing source {diag['source']}")
                nar = diag.get("narration", {})
                for k in ("scenario_fa", "scenario_en", "point_fa", "point_en",
                          "failure_fa", "failure_en", "guarantee_fa", "guarantee_en",
                          "nonguarantee_fa", "nonguarantee_en"):
                    if not nar.get(k):
                        fails.append(f"{where}: narration missing {k}")
                if not nar.get("steps"):
                    fails.append(f"{where}: narration.steps empty")
                if not diag.get("selfcheck", {}).get("q_fa"):
                    fails.append(f"{where}: selfcheck missing")
                dp = ROOT / folder / diag["file"]
                if not dp.exists():
                    fails.append(f"{where}: missing diagram {dp}")
                elif made == "hand":
                    ff, _, _ = fitcheck(str(dp))
                    for x in ff:
                        fails.append(f"{where} diagram FAIL: {x}")
        idx = (ROOT / folder / "index.html").read_text()
        for s in sols:
            if f'solutions.html#sol-{s["number"]}' not in idx:
                fails.append(f"ch{ch}: index missing solution link #sol-{s['number']}")
        audit_page = (ROOT / "exercise-audit.html").read_text()
        for s in sols:
            if f'{folder}/solutions.html#sol-{s["number"]}' not in audit_page:
                fails.append(f"ch{ch}: audit missing solution link #sol-{s['number']}")
        for w, rx in zip(PLACEHOLDERS, PLACEHOLDER_RES):
            if rx.search(page):
                fails.append(f"ch{ch}: placeholder '{w}' in built page")
    for ch in sorted(by_chapter):
        if ch not in done_ch:
            pending.append(ch)
    print(f"solutions cover chapters: {sorted(done_ch) or 'none'}")
    print(f"pending chapters: {pending or 'none'}")
    for f in fails:
        print("FAIL", f)
    if fails:
        return 1
    print(f"PASS: {sum(len(load_chapter(p)['solutions']) for p in done)} solutions, "
          f"bidirectional links, diagrams fitcheck-clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
