"""A/B table for the 8-minute track: Phase 0 baseline (no notes) against the same seeds with notes.

    python fleet/phase2/compare.py --baseline RUNS_DIR --notes RUNS_DIR --manifest user_track.json --voice NATF2
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "phase0"))
from score import score_track  # noqa: E402

MINUTES = {60: "1:00", 180: "3:00", 270: "4:30", 360: "6:00", 450: "7:30"}


def tally(runs: Path, cues, duration, voice, seeds):
    out = {}
    for seed in seeds:
        path = runs / f"p50_{voice}_s{seed}.json"
        if not path.exists():
            continue
        for row in score_track(json.loads(path.read_text()), cues, duration):
            out.setdefault((int(row["t"]), row["fact"]), {})[seed] = row["verdict"]
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--notes", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--voice", default="NATF2")
    parser.add_argument("--seeds", default="101,202,303")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    cues, duration = manifest["cues"], float(manifest["duration_s"])
    seeds = [int(s) for s in args.seeds.split(",")]
    base = tally(args.baseline, cues, duration, args.voice, seeds)
    withn = tally(args.notes, cues, duration, args.voice, seeds)
    lines = [
        f"# 8-minute track, {args.voice}, seeds {args.seeds}: no notes vs notes",
        "",
        "| minute | fact | no notes (right/n) | with notes (right/n) | no notes by seed | with notes by seed |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for key in sorted(set(base) | set(withn)):
        b, w = base.get(key, {}), withn.get(key, {})
        br = sum(v == "right" for v in b.values())
        wr = sum(v == "right" for v in w.values())
        lines.append(
            f"| {MINUTES.get(key[0], key[0])} | {key[1]} | {br}/{len(b)} | {wr}/{len(w)} | "
            f"{', '.join(f'{s}:{b[s]}' for s in sorted(b))} | {', '.join(f'{s}:{w[s]}' for s in sorted(w))} |"
        )
    text = "\n".join(lines) + "\n"
    print(text)
    if args.out:
        args.out.write_text(text)


if __name__ == "__main__":
    main()
