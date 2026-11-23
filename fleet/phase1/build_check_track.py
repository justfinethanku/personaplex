"""Four-minute user track whose fact checks sit at minute 3.

Questions do not contain the answers. The answer key is the call_setup facts.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

VOICE = "en-US-JennyNeural"
SR = 24000
DURATION_S = 260.0

CUES = [
    {"t": 0, "kind": "chat", "text": "Hey, let's prep the next episode. What should we open with?"},
    {"t": 40, "kind": "chat", "text": "Who is this episode for?"},
    {"t": 80, "kind": "chat", "text": "What should the cold open be?"},
    {"t": 120, "kind": "chat", "text": "What do we cut if this runs long?"},
    {"t": 160, "kind": "chat", "text": "How should we end it?"},
    # One window around minute 3, ten seconds apart:
    # 2:54 name, 3:04 employer, 3:14 page, 3:24 story, 3:34 company.
    # The closing line at 3:44 ends the last answer window. Clips are
    # about three seconds, so these starts do not overlap.
    {"t": 174, "kind": "fact", "fact": "name", "text": "What's your name again?"},
    {"t": 184, "kind": "fact", "fact": "employer", "text": "Who do you work for?"},
    {"t": 194, "kind": "fact", "fact": "desk", "text": "Which page on the site is this story from?"},
    {"t": 204, "kind": "fact", "fact": "story", "text": "Which company is today's story about?"},
    {"t": 214, "kind": "fact", "fact": "company", "text": "What did he co-found with Nate?"},
    {"t": 224, "kind": "chat", "text": "Thanks, that covers the checklist."},
]


async def synthesize(text: str, mp3_path: Path) -> None:
    import edge_tts

    await edge_tts.Communicate(text, VOICE).save(str(mp3_path))


def to_wav(mp3_path: Path, wav_path: Path) -> np.ndarray:
    subprocess.run(
        [
            "ffmpeg", "-loglevel", "error", "-y", "-i", str(mp3_path),
            "-ac", "1", "-ar", str(SR), "-c:a", "pcm_s16le", str(wav_path),
        ],
        check=True,
    )
    with wave.open(str(wav_path), "rb") as handle:
        frames = handle.readframes(handle.getnframes())
    return np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0


async def main() -> None:
    out = Path("/home/lej/clients/LEJ/personaplex/var/fleet-335/phase1")
    clip_dir = out / "clips"
    clip_dir.mkdir(parents=True, exist_ok=True)
    canvas = np.zeros(int(DURATION_S * SR), dtype=np.float32)
    manifest = []
    for index, cue in enumerate(CUES):
        wav_path = clip_dir / f"{index:02d}.wav"
        mp3_path = clip_dir / f"{index:02d}.mp3"
        # The cache key is the spoken text, not the index. A new question
        # at the same slot must be synthesized again.
        key_path = clip_dir / f"{index:02d}.txt"
        cached = key_path.exists() and key_path.read_text() == cue["text"] and wav_path.exists()
        if cached:
            with wave.open(str(wav_path), "rb") as handle:
                frames = handle.readframes(handle.getnframes())
            audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        else:
            await synthesize(cue["text"], mp3_path)
            audio = to_wav(mp3_path, wav_path)
            key_path.write_text(cue["text"])
        start = int(round(cue["t"] * SR))
        end = min(start + len(audio), len(canvas))
        if np.any(canvas[start:end] != 0):
            raise RuntimeError(f"overlap at {cue['t']}")
        canvas[start:end] = audio[: end - start]
        row = dict(cue)
        row["t_end"] = end / SR
        manifest.append(row)
    pcm = (np.clip(canvas, -1, 1) * 32767).astype(np.int16)
    wav_out = out / "check_track.wav"
    with wave.open(str(wav_out), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SR)
        handle.writeframes(pcm.tobytes())
    (out / "check_track.json").write_text(
        json.dumps({"sample_rate": SR, "duration_s": DURATION_S, "wav": str(wav_out), "cues": manifest}, indent=2)
    )
    print(f"wrote {wav_out}")


if __name__ == "__main__":
    asyncio.run(main())
