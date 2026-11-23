"""Build the 24 kHz mono user track for the drift test.

Speech comes from edge-tts (en-US-JennyNeural). fish-speech is left alone:
it is not running, and a restart would take the shared GPU for a long warmup.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cues import CUES, DURATION_S  # noqa: E402

VOICE = "en-US-JennyNeural"
SR = 24000


async def synthesize(text: str, mp3_path: Path) -> None:
    import edge_tts

    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(str(mp3_path))


def to_wav(mp3_path: Path, wav_path: Path) -> np.ndarray:
    subprocess.run(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(mp3_path),
            "-ac",
            "1",
            "-ar",
            str(SR),
            "-c:a",
            "pcm_s16le",
            str(wav_path),
        ],
        check=True,
    )
    with wave.open(str(wav_path), "rb") as handle:
        if handle.getframerate() != SR or handle.getnchannels() != 1:
            raise RuntimeError(f"bad wav format: {wav_path}")
        frames = handle.readframes(handle.getnframes())
    return np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0


def write_wav(path: Path, samples: np.ndarray) -> None:
    clipped = np.clip(samples, -1.0, 1.0)
    pcm = (clipped * 32767.0).astype(np.int16)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SR)
        handle.writeframes(pcm.tobytes())


async def build(out_dir: Path, duration_s: float) -> None:
    clip_dir = out_dir / "clips"
    clip_dir.mkdir(parents=True, exist_ok=True)
    total = int(duration_s * SR)
    canvas = np.zeros(total, dtype=np.float32)
    manifest = []
    for index, cue in enumerate(CUES):
        if cue["t"] >= duration_s:
            break
        mp3_path = clip_dir / f"{index:02d}.mp3"
        wav_path = clip_dir / f"{index:02d}.wav"
        if not wav_path.exists():
            await synthesize(cue["text"], mp3_path)
            audio = to_wav(mp3_path, wav_path)
        else:
            audio = _read(wav_path)
        start = int(round(cue["t"] * SR))
        end = start + len(audio)
        if end > total:
            audio = audio[: total - start]
            end = total
        if start < 0 or np.any(canvas[start:end] != 0):
            raise RuntimeError(f"cue {index} at {cue['t']}s overlaps another cue")
        canvas[start:end] = audio
        row = dict(cue)
        row["t_end"] = end / SR
        row["clip"] = wav_path.name
        manifest.append(row)
    name = "probe.wav" if duration_s < DURATION_S else "user_track.wav"
    wav_out = out_dir / name
    write_wav(wav_out, canvas)
    manifest_path = out_dir / (name.replace(".wav", ".json"))
    manifest_path.write_text(
        json.dumps(
            {
                "sample_rate": SR,
                "duration_s": duration_s,
                "voice": VOICE,
                "wav": str(wav_out),
                "cues": manifest,
            },
            indent=2,
        )
    )
    print(f"wrote {wav_out} ({duration_s:.0f}s, {len(manifest)} cues)")


def _read(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as handle:
        frames = handle.readframes(handle.getnframes())
    return np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("/home/lej/clients/LEJ/personaplex/var/fleet-335"),
    )
    parser.add_argument(
        "--seconds",
        type=float,
        default=DURATION_S,
        help="Track length. Use 20 for a speed probe that still includes the opener.",
    )
    args = parser.parse_args()
    asyncio.run(build(args.out, args.seconds))


if __name__ == "__main__":
    main()
