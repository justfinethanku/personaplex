"""User-side script for the 8-minute drift track.

Fact checks start at 1:00, 3:00, 4:30, 6:00, and 7:30.
Other questions sit between them. A few gaps are shorter or longer than
30-40 seconds because those five clock times are fixed.
"""

from __future__ import annotations

DURATION_S = 480.0

CUES = [
    {"t": 0, "kind": "chat", "text": "Hey, let's prep the next episode. What should we open with?"},
    {"t": 35, "kind": "chat", "text": "Who is this episode for?"},
    {"t": 60, "kind": "fact", "fact": "name", "text": "What's your name again?"},
    {"t": 95, "kind": "chat", "text": "What tone should the cold open have?"},
    {"t": 140, "kind": "chat", "text": "Should we tease the story in the first minute?"},
    {"t": 180, "kind": "fact", "fact": "launch", "text": "When do we launch?"},
    {"t": 215, "kind": "chat", "text": "How long should the episode run?"},
    {"t": 270, "kind": "fact", "fact": "show", "text": "What's the show called?"},
    {"t": 305, "kind": "chat", "text": "What should the episode title be?"},
    {"t": 330, "kind": "chat", "text": "How should I hand it back to the listener at the end?"},
    {"t": 360, "kind": "fact", "fact": "employer", "text": "Who do you work for?"},
    {"t": 395, "kind": "chat", "text": "Do we need a sponsor read, or should we skip it?"},
    {"t": 450, "kind": "fact", "fact": "guest", "text": "Who was your favorite guest so far?"},
]
