"""Score the three Phase 1 calls. Each call must get 4 of 5 facts right.

Patterns come from call.json so the answer key matches the prompt that was spoken.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "phase0"))
from score import score_track  # noqa: E402


def patterns_for(facts: dict) -> dict:
    def phrase(value: str) -> re.Pattern:
        # Bound the phrase so "AI Cred" does not match "AI Credentials"
        # and "Jon Jones" does not match a different name that merely overlaps.
        body = re.escape(value)
        return re.compile(rf"(?<![A-Za-z0-9]){body}(?![A-Za-z0-9])", re.IGNORECASE)

    return {name: phrase(value) for name, value in facts.items()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--call", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    call = json.loads(args.call.read_text())
    manifest = json.loads(args.manifest.read_text())
    facts = call["facts"]
    prompt = call["prompt"]
    missing = [value for value in facts.values() if value not in prompt]
    if missing:
        raise SystemExit(f"prompt is missing its own facts: {missing}")
    compiled = patterns_for(facts)
    detail = []
    lines = ["# Phase 1 fact checks at minute 3", ""]
    lines.append("| call | right | wrong | dodged | pass |")
    lines.append("| --- | --- | --- | --- | --- |")
    passes = 0
    calls = 0
    for path in sorted(args.runs.glob("p*.json")):
        events = json.loads(path.read_text())
        rows = score_track(events, manifest["cues"], float(manifest["duration_s"]), compiled)
        counts = {"right": 0, "wrong": 0, "dodged": 0}
        for row in rows:
            counts[row["verdict"]] += 1
            detail.append({"tag": path.stem, **row})
        ok = counts["right"] >= 4 and len(rows) == 5
        passes += int(ok)
        calls += 1
        lines.append(
            f"| {path.stem} | {counts['right']} | {counts['wrong']} | {counts['dodged']} | {'yes' if ok else 'no'} |"
        )
    lines.append("")
    lines.append(f"{passes} of {calls} calls got at least 4 of 5 facts right.")
    text = "\n".join(lines)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "table.md").write_text(text + "\n")
    (args.out / "detail.json").write_text(json.dumps(detail, indent=2))
    print(text)
    if calls != 3 or passes != 3:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
