"""One answer rubric for every arm, applied to the saved timed transcripts. No GPU needed.

The Phase 0 and Phase 1 scorer (`score.py`) looks for the fact anywhere between a question and the
next question. That over-credits when the model says the fact later in a greeting or a closing line
("Thank you for calling Baseten") or in its answer to a different question. This rubric reads only
the model's reply to the question that was asked:

  1. The reply is every utterance that starts from 1 s before the question starts until the earlier
     of 12 s after it and 1 s before the next question. An utterance is a run of text with no gap
     over 1 s. (Models sometimes start talking just before a question clip finishes loading.)
  2. Greeting and closing lines are dropped: "Hello, you're through to ...", "Hey, let me know ...",
     "Thank you for calling ...", "Have a great day".
  3. The fact is right when the remaining reply states it affirmatively: same negation, hedge and
     "I don't know" checks as `score.py`. A misspelling ("Basten") is wrong.

    python fleet/phase2/adjudicate.py --var <var/fleet-335> --out results-adjudicated.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "phase0"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "phase1"))
from score import affirmative_mention, score_fact  # noqa: E402
from score_calls import patterns_for  # noqa: E402

GAP_S = 1.0
LEAD_S = 1.0
HORIZON_S = 12.0
DROP = re.compile(
    r"thank you for calling|have a great day|let me know if|you'?re (through|calling)|how can i help|"
    r"^>|^hello\b|^hey there|^to the news factory\.?$",
    re.IGNORECASE,
)


def utterances(events: list[dict]) -> list[dict]:
    out, cur = [], None
    for e in events:
        if e.get("pad"):
            continue
        if cur and e["t"] - cur["last"] > GAP_S:
            out.append(cur)
            cur = None
        if cur is None:
            cur = {"start": float(e["t"]), "last": float(e["t"]), "text": ""}
        cur["text"] += e["text"]
        cur["last"] = float(e["t"])
    if cur:
        out.append(cur)
    for u in out:
        u["text"] = " ".join(u["text"].split())
    return out


def reply(events: list[dict], cues: list[dict], index: int) -> tuple[str, str]:
    """Return (kept reply text, dropped text) for the question at cues[index]."""
    cue = cues[index]
    lo = float(cue["t"]) - LEAD_S
    nxt = float(cues[index + 1]["t"]) if index + 1 < len(cues) else float(cue["t"]) + HORIZON_S
    hi = min(float(cue["t"]) + HORIZON_S, nxt - LEAD_S)
    kept, dropped = [], []
    for u in utterances(events):
        if lo <= u["start"] < hi:
            (dropped if DROP.search(u["text"]) else kept).append(u["text"])
    return " ".join(kept), " ".join(dropped)


def adjudicate(events, cues, patterns=None):
    ordered = sorted(cues, key=lambda c: c["t"])
    rows = []
    for i, cue in enumerate(ordered):
        if cue.get("kind") != "fact":
            continue
        kept, dropped = reply(events, ordered, i)
        rows.append({"fact": cue["fact"], "t": cue["t"], "verdict": score_fact(cue["fact"], kept, patterns), "reply": kept, "dropped": dropped})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--var", type=Path, required=True, help="var/fleet-335 on the Spark")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    v = args.var
    call = json.loads((v / "call/call.json").read_text())
    pats = patterns_for(call["facts"])
    m3 = json.loads((v / "phase1/check_track.json").read_text())["cues"]
    m8 = json.loads((v / "user_track.json").read_text())["cues"]
    from score import score_track  # noqa: E402

    arms3 = {
        "no notes (round 2)": v / "phase1/runs-spoken-try5",
        "pause notes, 3 s lull": v / "phase2/runs-B-short",
        "stealth notes, 3 s lull": v / "phase2/runs-C-stealth",
        "stealth notes, 5 s lull": v / "phase2/runs-E-lull5",
    }
    lines = ["# Minute-3 answers, re-adjudicated (one rubric, every arm)", "", __doc__.split("\n\n")[1].strip(), ""]
    lines += ["| arm | seed | original scorer | adjudicated | changed cells |", "| --- | --- | --- | --- | --- |"]
    detail = []
    for arm, d in arms3.items():
        passes = 0
        for seed in (101, 202, 303):
            ev = json.loads((d / f"p50_NATF2_s{seed}.json").read_text())
            old = score_track(ev, m3, 260.0, pats)
            new = adjudicate(ev, m3, pats)
            o = sum(r["verdict"] == "right" for r in old)
            n = sum(r["verdict"] == "right" for r in new)
            changed = [f"{a['fact']} {a['verdict']}→{b['verdict']}" for a, b in zip(old, new) if a["verdict"] != b["verdict"]]
            passes += n >= 4
            lines.append(f"| {arm} | {seed} | {o} | {n} | {', '.join(changed) or '-'} |")
            for r in new:
                detail.append({"arm": arm, "seed": seed, **r})
        lines.append(f"| {arm} | calls at 4+ | | {passes} of 3 | |")
    lines += ["", "## Every answer", "", "| arm | seed | fact | verdict | reply | dropped as greeting or closing |", "| --- | --- | --- | --- | --- | --- |"]
    for r in detail:
        lines.append(f"| {r['arm']} | {r['seed']} | {r['fact']} | {r['verdict']} | {r['reply'][:120]} | {r['dropped'][:80]} |")

    lines += ["", "# 8-minute track, same rubric", "", "| fact | minute | no notes | with notes |", "| --- | --- | --- | --- |"]
    base8, notes8 = v / "runs", v / "phase2/runs-D-8min"
    mins = {60: "1:00", 180: "3:00", 270: "4:30", 360: "6:00", 450: "7:30"}
    tally = {}
    for label, d in (("base", base8), ("notes", notes8)):
        for seed in (101, 202, 303):
            ev = json.loads((d / f"p50_NATF2_s{seed}.json").read_text())
            for r in adjudicate(ev, m8):
                tally.setdefault((r["t"], r["fact"]), {}).setdefault(label, []).append((seed, r["verdict"], r["reply"]))
    for (t, fact), by in sorted(tally.items()):
        b = sum(x[1] == "right" for x in by["base"])
        w = sum(x[1] == "right" for x in by["notes"])
        lines.append(f"| {fact} | {mins[int(t)]} | {b}/3 | {w}/3 |")
    lines += ["", "| fact | arm | seed | verdict | reply |", "| --- | --- | --- | --- | --- |"]
    for (t, fact), by in sorted(tally.items()):
        for label in ("base", "notes"):
            for seed, verdict, text in by[label]:
                lines.append(f"| {fact} | {label} | {seed} | {verdict} | {text[:110]} |")
    # Phase 0 (18 runs, three prompt lengths, two voices) under the same rubric.
    lines += ["", "# Phase 0 drift table, same rubric (6 runs per cell)", "",
              "| words | minute | fact | original right/6 | adjudicated right/6 |", "| --- | --- | --- | --- | --- |"]
    p0 = {}
    for path in sorted((v / "runs").glob("p*_*_s*.json")):
        length = int(path.stem.split("_")[0][1:])
        ev = json.loads(path.read_text())
        for a, b in zip(score_track(ev, m8, 480.0), adjudicate(ev, m8)):
            cell = p0.setdefault((length, int(a["t"]), a["fact"]), [0, 0])
            cell[0] += a["verdict"] == "right"
            cell[1] += b["verdict"] == "right"
    for (length, t, fact), (o, n) in sorted(p0.items()):
        lines.append(f"| {length} | {mins[t]} | {fact} | {o} | {n} |")
    args.out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:22]))


if __name__ == "__main__":
    main()
