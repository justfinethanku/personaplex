"""Score a timed model transcript against the five planted facts.

A fact is right when the answer window contains it.
It is dodged when the window is empty or the model says it does not know.
Any other reply is wrong.
"""

from __future__ import annotations

import re
from typing import Iterable

FACTS = ("name", "employer", "show", "launch", "guest")

RIGHT = {
    "name": re.compile(r"\bruby\b", re.IGNORECASE),
    "employer": re.compile(r"limited edition jonathan|\blej\b", re.IGNORECASE),
    "show": re.compile(r"signal desk", re.IGNORECASE),
    "launch": re.compile(
        r"november\s+12|november\s+twelve|nov\.?\s*12|11/12|12th of november|"
        r"twelfth of november|november twelfth",
        re.IGNORECASE,
    ),
    "guest": re.compile(r"\btodd\b", re.IGNORECASE),
}

DODGED = re.compile(
    r"don'?t know|don know|do not know|not sure|no idea|can'?t (remember|recall)|"
    r"cannot (remember|recall)|i forget|what was (it|that)|remind me|"
    r"i'?m not sure|hard to say",
    re.IGNORECASE,
)


def join_pieces(pieces: Iterable[str]) -> str:
    text = "".join(pieces)
    text = text.replace("▁", " ")
    return re.sub(r"\s+", " ", text).strip()


def window_text(events: list[dict], t0: float, t1: float) -> str:
    pieces = []
    for event in events:
        if event.get("pad"):
            continue
        t = float(event["t"])
        if t0 <= t < t1:
            pieces.append(event.get("text") or "")
    return join_pieces(pieces)


def score_fact(fact: str, text: str, patterns: dict | None = None) -> str:
    cleaned = text.strip()
    table = patterns or RIGHT
    if table[fact].search(cleaned):
        return "right"
    if len(re.findall(r"[A-Za-z]", cleaned)) < 3 or DODGED.search(cleaned):
        return "dodged"
    return "wrong"


def score_track(
    events: list[dict],
    cues: list[dict],
    duration_s: float,
    patterns: dict | None = None,
) -> list[dict]:
    """Score each fact cue. The window runs from the cue start to the next cue."""
    ordered = sorted(cues, key=lambda c: c["t"])
    rows = []
    for i, cue in enumerate(ordered):
        if cue.get("kind") != "fact":
            continue
        # From the start of the question, so a reply that begins while
        # the question is still playing still counts.
        t0 = float(cue["t"])
        t1 = float(ordered[i + 1]["t"]) if i + 1 < len(ordered) else duration_s
        text = window_text(events, t0, t1)
        fact = cue["fact"]
        rows.append(
            {
                "fact": fact,
                "t": cue["t"],
                "t1": t1,
                "verdict": score_fact(fact, text, patterns),
                "text": text,
                "asked": cue.get("text", ""),
            }
        )
    return rows
