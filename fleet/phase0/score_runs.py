"""Turn drift run JSON into the Phase 0 accuracy table.

Reads the user-track manifest and each run's timed tokens.
Writes drift_summary.json (including the reconnect note Phase 1 reads)
and table.md next to the runs.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from score import score_track  # noqa: E402

MINUTES = {
    60: "1:00",
    180: "3:00",
    270: "4:30",
    360: "6:00",
    450: "7:30",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    cues = manifest["cues"]
    duration = float(manifest["duration_s"])
    log_rows = []
    log_path = args.runs / "drift.jsonl"
    if log_path.exists():
        for line in log_path.read_text().splitlines():
            if line.strip():
                log_rows.append(json.loads(line))
    by_tag = {row["tag"]: row for row in log_rows if row.get("ok")}

    detail = []
    buckets = defaultdict(lambda: {"right": 0, "wrong": 0, "dodged": 0})
    for path in sorted(args.runs.glob("p*.json")):
        tag = path.stem
        meta = by_tag.get(tag)
        if meta is None:
            continue
        events = json.loads(path.read_text())
        rows = score_track(events, cues, duration)
        for row in rows:
            key = (meta["length"], int(row["t"]), row["fact"])
            buckets[key][row["verdict"]] += 1
            detail.append({"tag": tag, "length": meta["length"], "voice": meta["voice"], "seed": meta["seed"], **row})

    startup = defaultdict(list)
    for row in by_tag.values():
        startup[row["length"]].append(row)

    lines = ["# Phase 0 drift", "", "Fact checks are right, wrong, or dodged. Six runs per length (3 seeds x NATF2 and NATM1).", ""]
    lines.append("| words | minute | fact | right | wrong | dodged | n | accuracy |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for key in sorted(buckets):
        length, t, fact = key
        counts = buckets[key]
        n = sum(counts.values())
        acc = counts["right"] / n if n else 0
        lines.append(
            f"| {length} | {MINUTES.get(t, str(t))} | {fact} | {counts['right']} | {counts['wrong']} | {counts['dodged']} | {n} | {acc:.0%} |"
        )
    lines.append("")
    lines.append("## Startup delay")
    lines.append("")
    lines.append("Wall clock for step_system_prompts, which feeds the voice prompt and then one text token per 80 ms frame. Model load is once per batch and is not in this column.")
    lines.append("")
    lines.append("| words | runs | prompt tokens | startup mean s | startup min s | startup max s | generate RTF mean |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    startup_summary = {}
    for length, rows in sorted(startup.items()):
        starts = [r["startup_s"] for r in rows]
        tokens = [r["prompt_tokens"] for r in rows]
        rtfs = [r["realtime_factor"] for r in rows]
        startup_summary[str(length)] = {
            "n": len(rows),
            "tokens_mean": round(sum(tokens) / len(tokens), 1),
            "startup_mean_s": round(sum(starts) / len(starts), 2),
            "startup_min_s": round(min(starts), 2),
            "startup_max_s": round(max(starts), 2),
            "rtf_mean": round(sum(rtfs) / len(rtfs), 3),
        }
        s = startup_summary[str(length)]
        lines.append(
            f"| {length} | {s['n']} | {s['tokens_mean']} | {s['startup_mean_s']} | {s['startup_min_s']} | {s['startup_max_s']} | {s['rtf_mean']} |"
        )

    # Phase 0 plants one fact at each clock time. Minute 1 is the name.
    # Minute 3 is the launch date. A length holds when each of those is
    # right in at least 4 of the 6 runs. Longer prompts did not raise that
    # accuracy and they add startup silence, so the cap is the shortest
    # length that holds.
    minute3 = {}
    minute1 = {}
    for length in sorted({k[0] for k in buckets}):
        for t, dest in ((60, minute1), (180, minute3)):
            rights = dodges = wrongs = 0
            for key, counts in buckets.items():
                if key[0] == length and key[1] == t:
                    rights += counts["right"]
                    dodges += counts["dodged"]
                    wrongs += counts["wrong"]
            n = rights + dodges + wrongs
            dest[str(length)] = {"right": rights, "wrong": wrongs, "dodged": dodges, "n": n}

    def holds(length: int, table: dict) -> bool:
        row = table.get(str(length), {})
        n = row.get("n") or 0
        return bool(n) and row["right"] >= 4

    cap = None
    held_until = None
    for length in (50, 150, 400):
        if holds(length, minute1) and holds(length, minute3):
            cap = length
            held_until = length
            break
    if cap is None:
        cap = 50
    # Later minutes on the length we would ship. Other lengths do not
    # decide the warning.
    later_collapse = False
    for key, counts in buckets.items():
        if key[0] == cap and key[1] in (270, 360, 450):
            n = sum(counts.values())
            if n and counts["right"] / n < 0.5:
                later_collapse = True
    if later_collapse or held_until is None:
        note = (
            "Phase 0: fact accuracy drops as the call runs. "
            "Reconnect with a fresh prompt around 3.5 minutes."
        )
    else:
        note = (
            f"Phase 0: a {cap}-word prompt still answered the minute-3 check. "
            "Reconnect around 3.5 minutes on a longer call."
        )
    lines.append("")
    lines.append(note)
    lines.append("")
    text = "\n".join(lines)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "table.md").write_text(text)
    summary = {
        "word_cap": cap,
        "minute1": minute1,
        "minute3": minute3,
        "startup": startup_summary,
        "reconnect_note": note,
        "runs_ok": len(by_tag),
    }
    (args.out / "drift_summary.json").write_text(json.dumps(summary, indent=2))
    (args.out / "detail.json").write_text(json.dumps(detail, indent=2))
    # Phase 1 reads this path.
    shared = Path(__file__).resolve().parent / "drift_summary.json"
    shared.write_text(json.dumps(summary, indent=2))
    print(text)


if __name__ == "__main__":
    main()
