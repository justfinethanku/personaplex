"""Score a timed model transcript against the five planted facts.

A fact is right when the answer states it. A mention inside a negation,
a hedge, or an "I don't know" does not count. An empty window, or a
window that only says it does not know, is dodged. Any other reply is wrong.
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

# The few words immediately before the fact. Bare "no" is only a negation
# when it is the word right before the fact ("no News Factory").
NEGATION = re.compile(
    r"\b(?:not|never|without|isn'?t|aren'?t|wasn'?t|weren'?t|"
    r"don'?t|doesn'?t|didn'?t|cannot)\b",
    re.IGNORECASE,
)
HEDGE = re.compile(r"\b(?:maybe|perhaps|probably|might be|could be)\b", re.IGNORECASE)


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


def _local_words(text: str, start: int, end: int, before: int, after: int) -> tuple[str, str]:
    prefix = " ".join(text[max(0, start - 80):start].split()[-before:])
    suffix = " ".join(text[end:end + 80].split()[:after])
    return prefix, suffix


def affirmative_mention(pattern: re.Pattern, text: str) -> bool:
    """True when the pattern is stated as the answer.

    Skips a hit whose nearby words negate it ("not News Factory") or hedge
    it ("maybe News Factory"), and a hit inside a sentence that says the
    model does not know. A longer unrelated token does not match when the
    pattern itself is bounded; this function only judges the hits it gets.
    """
    sentences = re.split(r"(?<=[.!?])\s+", text.strip()) or [text]
    for sentence in sentences:
        if DODGED.search(sentence):
            continue
        for match in pattern.finditer(sentence):
            prefix, _suffix = _local_words(sentence, match.start(), match.end(), 3, 0)
            if NEGATION.search(prefix) or HEDGE.search(prefix):
                continue
            if re.match(r"\s+(?:is|was|are|were)\s+not\b|\s*,?\s*not\b", sentence[match.end():], re.IGNORECASE):
                continue
            previous = sentence[:match.start()].split()
            if previous and previous[-1].lower().strip(".,!?") in {"no", "nope"}:
                continue
            return True
    return False


def score_fact(fact: str, text: str, patterns: dict | None = None) -> str:
    cleaned = text.strip()
    table = patterns or RIGHT
    if affirmative_mention(table[fact], cleaned):
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
