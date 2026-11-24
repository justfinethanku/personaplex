"""Negated and unrelated phrases are not right answers."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from score import score_fact  # noqa: E402


def phrase(value: str) -> re.Pattern:
    body = re.escape(value)
    return re.compile(rf"(?<![A-Za-z0-9]){body}(?![A-Za-z0-9])", re.IGNORECASE)


PATTERNS = {
    "desk": phrase("News Factory"),
    "company": phrase("AI Cred"),
    "name": phrase("Ruby"),
    "story": phrase("Baseten"),
}


def main() -> None:
    assert score_fact("desk", "The page is News Factory.", PATTERNS) == "right"
    assert score_fact("desk", "It's not News Factory, it's the homepage.", PATTERNS) == "wrong"
    assert score_fact("desk", "I don know.", PATTERNS) == "dodged"
    assert score_fact("desk", "I don't know, maybe News Factory.", PATTERNS) == "dodged"
    assert score_fact("desk", "homepage, under the headline.", PATTERNS) == "wrong"
    assert score_fact("company", "Jon Jones. They met in college.", PATTERNS) == "wrong"
    assert score_fact("company", "AI Credentials are unrelated.", PATTERNS) == "wrong"
    assert score_fact("company", "AI Cred.", PATTERNS) == "right"
    assert score_fact("company", "He did not co-found AI Cred.", PATTERNS) == "wrong"
    assert score_fact("name", "No, the producer is Ruby.", PATTERNS) == "right"
    assert score_fact("name", "", PATTERNS) == "dodged"
    assert score_fact("story", "The story is about Baseten.", PATTERNS) == "right"
    print("ok")


if __name__ == "__main__":
    main()
