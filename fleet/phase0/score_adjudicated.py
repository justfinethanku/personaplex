"""Score a drift directory with the reply-window rubric.

Phase 0 (no --call) uses the planted-fact patterns in score.py.
Phase 1 (--call call.json) uses that call's answer key.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "phase1"))
from reply_rubric import adjudicate  # noqa: E402
from score import score_track  # noqa: E402
from score_calls import patterns_for  # noqa: E402

MINUTES = {60: "1:00", 180: "3:00", 270: "4:30", 360: "6:00", 450: "7:30", 174: "2:54", 184: "3:04", 194: "3:14", 204: "3:24", 214: "3:34"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--call", type=Path, default=None)
    parser.add_argument("--title", default="Adjudicated fact checks")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    cues = manifest["cues"]
    duration = float(manifest["duration_s"])
    patterns = None
    if args.call:
        call = json.loads(args.call.read_text())
        patterns = patterns_for(call["facts"])
    log_rows = []
    log_path = args.runs / "drift.jsonl"
    if log_path.exists():
        for line in log_path.read_text().splitlines():
            if line.strip():
                log_rows.append(json.loads(line))
    by_tag = {row["tag"]: row for row in log_rows if row.get("ok")}

    detail = []
    buckets = defaultdict(lambda: {"right": 0, "wrong": 0, "dodged": 0, "old_right": 0})
    per_call = []
    for path in sorted(args.runs.glob("p*.json")):
        meta = by_tag.get(path.stem)
        if meta is None:
            continue
        events = json.loads(path.read_text())
        old = score_track(events, cues, duration, patterns)
        new = adjudicate(events, cues, patterns)
        counts = {"right": 0, "wrong": 0, "dodged": 0}
        for before, row in zip(old, new):
            key = (meta["length"], int(row["t"]), row["fact"])
            buckets[key][row["verdict"]] += 1
            buckets[key]["old_right"] += before["verdict"] == "right"
            counts[row["verdict"]] += 1
            detail.append({"tag": path.stem, "seed": meta["seed"], "voice": meta["voice"], **row, "old": before["verdict"]})
        per_call.append((path.stem, counts, len(new)))

    flags = next(iter(by_tag.values()), {})
    lines = [f"# {args.title}", ""]
    if flags:
        lines.append(
            f"Revision `{flags.get('revision', '?')}`. "
            f"prefill_system_prompt={flags.get('prefill_system_prompt')} "
            f"pin_system_prompt={flags.get('pin_system_prompt')} "
            f"max_pinned_frames={flags.get('max_pinned_frames')}."
        )
        lines.append("")
    lines += [
        "| words | minute | fact | adjudicated right | window-scorer right | wrong | dodged | n |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for key in sorted(buckets):
        length, t, fact = key
        counts = buckets[key]
        n = counts["right"] + counts["wrong"] + counts["dodged"]
        lines.append(
            f"| {length} | {MINUTES.get(t, str(t))} | {fact} | {counts['right']} | {counts['old_right']} | {counts['wrong']} | {counts['dodged']} | {n} |"
        )
    fact_times = [float(cue["t"]) for cue in cues if cue.get("kind") == "fact"]
    minute3_cluster = bool(fact_times) and max(fact_times) - min(fact_times) < 90
    if minute3_cluster and per_call:
        lines += ["", "## Calls", "", "| call | right | wrong | dodged | pass |", "| --- | --- | --- | --- | --- |"]
        passes = 0
        for tag, counts, n in per_call:
            ok = counts["right"] >= 4 and n == 5
            passes += int(ok)
            lines.append(f"| {tag} | {counts['right']} | {counts['wrong']} | {counts['dodged']} | {'yes' if ok else 'no'} |")
        lines.append("")
        lines.append(f"{passes} of {len(per_call)} calls got at least 4 of 5 facts right.")
    lines += ["", "## Startup", "", "| tag | startup s | prompt frames | prompt tokens | generate RTF |", "| --- | --- | --- | --- | --- |"]
    for tag, row in sorted(by_tag.items()):
        lines.append(
            f"| {tag} | {row.get('startup_s')} | {row.get('prompt_frames')} | {row.get('prompt_tokens')} | {row.get('realtime_factor')} |"
        )
    lines += ["", "## Replies", "", "| tag | fact | verdict | reply | dropped |", "| --- | --- | --- | --- | --- |"]
    for row in detail:
        lines.append(
            f"| {row['tag']} | {row['fact']} | {row['verdict']} | {row['reply'][:140]} | {row['dropped'][:80]} |"
        )
    text = "\n".join(lines) + "\n"
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "adjudicated.md").write_text(text)
    (args.out / "adjudicated.json").write_text(json.dumps(detail, indent=2))
    print(text)


if __name__ == "__main__":
    main()
