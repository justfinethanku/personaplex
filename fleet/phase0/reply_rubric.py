"""Reply-window rubric shared with fleet/phase2/adjudicate.py.

The window scorer in score.py credits a fact anywhere between one question and the
next. This rubric reads only the reply to the question that was asked.
"""

from __future__ import annotations

import re

from score import score_fact

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
    for event in events:
        if event.get("pad"):
            continue
        if cur and event["t"] - cur["last"] > GAP_S:
            out.append(cur)
            cur = None
        if cur is None:
            cur = {"start": float(event["t"]), "last": float(event["t"]), "text": ""}
        cur["text"] += event["text"]
        cur["last"] = float(event["t"])
    if cur:
        out.append(cur)
    for item in out:
        item["text"] = " ".join(item["text"].split())
    return out


def reply(events: list[dict], cues: list[dict], index: int) -> tuple[str, str]:
    """Return (kept reply text, dropped text) for the question at cues[index]."""
    cue = cues[index]
    lo = float(cue["t"]) - LEAD_S
    nxt = float(cues[index + 1]["t"]) if index + 1 < len(cues) else float(cue["t"]) + HORIZON_S
    hi = min(float(cue["t"]) + HORIZON_S, nxt - LEAD_S)
    kept, dropped = [], []
    for item in utterances(events):
        if lo <= item["start"] < hi:
            (dropped if DROP.search(item["text"]) else kept).append(item["text"])
    return " ".join(kept), " ".join(dropped)


def adjudicate(events, cues, patterns=None):
    ordered = sorted(cues, key=lambda cue: cue["t"])
    rows = []
    for index, cue in enumerate(ordered):
        if cue.get("kind") != "fact":
            continue
        kept, dropped = reply(events, ordered, index)
        rows.append(
            {
                "fact": cue["fact"],
                "t": cue["t"],
                "verdict": score_fact(cue["fact"], kept, patterns),
                "reply": kept,
                "dropped": dropped,
            }
        )
    return rows
