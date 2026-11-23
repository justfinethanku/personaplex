"""Where did each note land against the five fact questions? Observed timing only, no causal claim.

For every note-arm call: each note's start and end on the user's clock, and which fact question
clip it overlapped or ended within 3 s before. Stealth notes ride on the real user frames, so a
stealth note ends 37 frames (2.96 s) after it starts; a pause note holds the user track still, so
it has no length on that clock. Verdicts come from the same rubric as adjudicate.py.

    python fleet/phase2/overlap.py --var <var/fleet-335> --out overlap.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "phase1"))
from adjudicate import adjudicate  # noqa: E402
from score_calls import patterns_for  # noqa: E402

FRAME_S = 0.08


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--var", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    v = args.var
    cues = json.loads((v / "phase1/check_track.json").read_text())["cues"]
    facts = [c for c in cues if c.get("kind") == "fact"]
    pats = patterns_for(json.loads((v / "call/call.json").read_text())["facts"])
    arms = {
        "pause, 3 s lull": ("pause", v / "phase2/runs-B-short"),
        "stealth, 3 s lull": ("stealth", v / "phase2/runs-C-stealth"),
        "stealth, 5 s lull": ("stealth", v / "phase2/runs-E-lull5"),
        "stealth, no note after 160 s": ("stealth", v / "phase2/runs-F-no4th"),
    }
    lines = [
        "| arm | seed | notes after 150 s (start-end) | question it touched | per-question verdicts (name, employer, page, story, company) |",
        "| --- | --- | --- | --- | --- |",
    ]
    for arm, (mode, d) in arms.items():
        log = d / "drift.jsonl"
        if not log.exists():
            continue
        for row in (json.loads(l) for l in log.read_text().splitlines() if l.strip()):
            if not row.get("ok"):
                continue
            seed = row["seed"]
            ev = json.loads((d / f"p50_NATF2_s{seed}.json").read_text())
            verdicts = [r["verdict"] for r in adjudicate(ev, cues, pats)]
            notes, touched = [], []
            for inj in row["injections"]:
                s = inj["t_track"]
                e = s + (inj["note_tokens"] * FRAME_S if mode == "stealth" else 0.0)
                if s < 150.0:
                    continue
                notes.append(f"{s:.1f}-{e:.1f}")
                for c in facts:
                    if s <= c["t_end"] and e >= c["t"]:
                        touched.append(f"overlaps {c['fact']} question ({c['t']}-{c['t_end']:.1f})")
                    elif s <= c["t_end"] and e + 3.0 >= c["t"]:
                        touched.append(f"ends within 3 s before {c['fact']} question ({c['t']})")
            lines.append(f"| {arm} | {seed} | {', '.join(notes) or 'none'} | {', '.join(touched) or 'none'} | {', '.join(verdicts)} |")
    args.out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
