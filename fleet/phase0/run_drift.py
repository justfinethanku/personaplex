"""Phase 0 drift runs. Loads PersonaPlex once, then runs the matrix.

The model code is the installed moshi package (unchanged). This harness
only times the prompt phase and writes frame-timed text. Stock offline
JSON has no timestamps, and the accuracy-by-minute table needs them.
Frame time is frame_index / frame_rate (12.5 Hz in this model).

Leaves other GPU work alone. Aborts if the GPU is busy with anything
other than the idle ComfyUI servers, or if memory gets tight.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import sphn
import torch
from huggingface_hub import hf_hub_download

sys.path.insert(0, str(Path(__file__).resolve().parent))
from moshi.models import LMGen, loaders  # noqa: E402
from moshi.models.lm import _iterate_audio as lm_iterate_audio  # noqa: E402
from moshi.models.lm import encode_from_sphn as lm_encode_from_sphn  # noqa: E402
from moshi.models.lm import load_audio as lm_load_audio  # noqa: E402
from moshi.offline import (  # noqa: E402
    decode_tokens_to_pcm,
    seed_all,
    warmup,
    wrap_with_system_tags,
)
from prompts import PROMPTS  # noqa: E402

VOICES = ("NATF2", "NATM1")
SEEDS = (101, 202, 303)
PAD_TOKENS = {0, 3}
PAD_NAMES = {0: "EPAD", 1: "BOS", 2: "EOS", 3: "PAD"}
# ComfyUI on 8191 and the video-lab server on 8192 stay up. They were idle.
# Idle ComfyUI keeps weights loaded. The GNOME remote-desktop daemon is the
# desktop, a few hundred MB, and it is always there. Neither is a job to stop.
ALLOWED_CMDLINE_MARKERS = (
    "--port 8191",
    "--port 8192",
    "gnome-remote-desktop-daemon",
)


def mem_available_gb() -> float:
    with open("/proc/meminfo", encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) / (1024 * 1024)
    raise RuntimeError("MemAvailable missing")


def gpu_strangers() -> list[str]:
    import subprocess

    strangers = []

    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-compute-apps=pid,process_name,used_memory",
                "--format=csv,noheader",
            ],
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise RuntimeError(f"nvidia-smi failed: {exc}") from exc
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        pid = line.split(",", 1)[0].strip()
        try:
            cmdline = Path(f"/proc/{pid}/cmdline").read_bytes().replace(b"\0", b" ").decode()
        except OSError:
            strangers.append(line)
            continue
        if any(marker in cmdline for marker in ALLOWED_CMDLINE_MARKERS):
            continue
        if "run_drift.py" in cmdline:
            continue
        strangers.append(f"{line} :: {cmdline[:180]}")
    return strangers


def preflight() -> None:
    available = mem_available_gb()
    print(f"mem_available_gb={available:.1f}", flush=True)
    if available < 28:
        raise SystemExit(f"refusing to load PersonaPlex: only {available:.1f} GB available")
    strangers = gpu_strangers()
    if strangers:
        raise SystemExit("GPU is in use by another job:\n" + "\n".join(strangers))
    print("gpu preflight ok; leaving idle ComfyUI servers running", flush=True)


def load_stack(voice_dir: Path):
    preflight()
    device = "cuda"
    repo = loaders.DEFAULT_REPO
    t0 = time.perf_counter()
    print("loading mimi", flush=True)
    mimi_weight = hf_hub_download(repo, loaders.MIMI_NAME)
    mimi = loaders.get_mimi(mimi_weight, device)
    other_mimi = loaders.get_mimi(mimi_weight, device)
    print("loading tokenizer and moshi", flush=True)
    tokenizer_path = hf_hub_download(repo, loaders.TEXT_TOKENIZER_NAME)
    import sentencepiece

    text_tokenizer = sentencepiece.SentencePieceProcessor(tokenizer_path)
    moshi_weight = hf_hub_download(repo, loaders.MOSHI_NAME)
    lm = loaders.get_moshi_lm(moshi_weight, device=device)
    lm.eval()
    frame_size = int(mimi.sample_rate / mimi.frame_rate)
    lm_gen = LMGen(
        lm,
        audio_silence_frame_cnt=int(0.5 * mimi.frame_rate),
        sample_rate=mimi.sample_rate,
        device=device,
        frame_rate=mimi.frame_rate,
        save_voice_prompt_embeddings=False,
        use_sampling=True,
        temp=0.8,
        temp_text=0.7,
        top_k=250,
        top_k_text=25,
    )
    mimi.streaming_forever(1)
    other_mimi.streaming_forever(1)
    lm_gen.streaming_forever(1)
    print("warming up", flush=True)
    warmup(mimi, other_mimi, lm_gen, device, frame_size)
    load_s = time.perf_counter() - t0
    print(f"model_ready_s={load_s:.1f} frame_rate={mimi.frame_rate}", flush=True)
    return {
        "mimi": mimi,
        "other_mimi": other_mimi,
        "lm_gen": lm_gen,
        "tokenizer": text_tokenizer,
        "voice_dir": voice_dir,
        "load_s": load_s,
    }


def run_one(stack, prompt: str, voice: str, seed: int, user_pcm: np.ndarray, out_wav: Path, out_json: Path) -> dict:
    if mem_available_gb() < 8:
        raise RuntimeError(f"stopping: only {mem_available_gb():.1f} GB available")
    mimi = stack["mimi"]
    other = stack["other_mimi"]
    lm_gen = stack["lm_gen"]
    tokenizer = stack["tokenizer"]
    voice_path = stack["voice_dir"] / f"{voice}.pt"
    if not voice_path.exists():
        raise FileNotFoundError(voice_path)

    seed_all(seed)
    lm_gen.load_voice_prompt_embeddings(str(voice_path))
    tokens = tokenizer.encode(wrap_with_system_tags(prompt))
    lm_gen.text_prompt_tokens = tokens
    mimi.reset_streaming()
    other.reset_streaming()
    lm_gen.reset_streaming()

    torch.cuda.synchronize()
    t0 = time.perf_counter()
    lm_gen.step_system_prompts(mimi)
    torch.cuda.synchronize()
    startup_s = time.perf_counter() - t0
    mimi.reset_streaming()

    frame_rate = float(mimi.frame_rate)
    events = []
    generated = []
    frame_idx = 0
    wall0 = time.perf_counter()
    with torch.inference_mode():
        for user_encoded in lm_encode_from_sphn(
            mimi,
            lm_iterate_audio(user_pcm, sample_interval_size=lm_gen._frame_size, pad=True),
            max_batch=1,
        ):
            steps = user_encoded.shape[-1]
            for c in range(steps):
                step_in = user_encoded[:, :, c : c + 1]
                tokens_out = lm_gen.step(step_in)
                t = frame_idx / frame_rate
                frame_idx += 1
                if tokens_out is None:
                    continue
                pcm = decode_tokens_to_pcm(mimi, other, lm_gen, tokens_out)
                generated.append(pcm)
                text_token = int(tokens_out[0, 0, 0].item())
                if text_token in PAD_TOKENS:
                    events.append({"t": t, "pad": True, "text": PAD_NAMES.get(text_token, "")})
                else:
                    piece = tokenizer.id_to_piece(text_token).replace("▁", " ")
                    events.append({"t": t, "pad": False, "text": piece})
    torch.cuda.synchronize()
    gen_s = time.perf_counter() - wall0

    if not generated:
        raise RuntimeError("no audio frames")
    output_pcm = np.concatenate(generated, axis=-1)
    target = int(user_pcm.shape[-1])
    if output_pcm.shape[-1] > target:
        output_pcm = output_pcm[:target]
    elif output_pcm.shape[-1] < target:
        output_pcm = np.concatenate(
            [output_pcm, np.zeros(target - output_pcm.shape[-1], dtype=output_pcm.dtype)]
        )
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    sphn.write_wav(str(out_wav), output_pcm, mimi.sample_rate)
    out_json.write_text(json.dumps(events))
    audio_s = target / float(mimi.sample_rate)
    return {
        "startup_s": round(startup_s, 3),
        "prompt_tokens": len(tokens),
        "text_feed_s_nominal": round(len(tokens) / frame_rate, 3),
        "generate_s": round(gen_s, 3),
        "audio_s": round(audio_s, 3),
        "realtime_factor": round(gen_s / audio_s, 3) if audio_s else None,
        "frames": frame_idx,
        "text_events": sum(1 for e in events if not e["pad"]),
    }


def parse_runs(spec: str | None) -> list[tuple[int, str, int]]:
    lengths = list(PROMPTS)
    voices = list(VOICES)
    seeds = list(SEEDS)
    if not spec:
        return [(n, v, s) for n in lengths for v in voices for s in seeds]
    runs = []
    for item in spec.split(","):
        n_s, voice, seed_s = item.split(":")
        runs.append((int(n_s), voice, int(seed_s)))
    return runs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--track", type=Path, required=True, help="24 kHz user wav")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--runs", default="", help="Comma list of length:voice:seed. Default is the full matrix.")
    parser.add_argument("--prompt-file", type=Path, default=None, help="Use this text for every run instead of the planted prompts.")
    parser.add_argument("--max-audio-seconds", type=float, default=0)
    parser.add_argument("--voice-dir", type=Path, default=None)
    args = parser.parse_args()

    os.environ.setdefault("TRITON_PTXAS_PATH", "/usr/local/cuda/bin/ptxas")
    voice_dir = args.voice_dir
    if voice_dir is None:
        voices_tgz = Path(hf_hub_download(loaders.DEFAULT_REPO, "voices.tgz"))
        voice_dir = voices_tgz.parent / "voices"
    user = lm_load_audio(str(args.track), 24000)
    if args.max_audio_seconds:
        keep = int(args.max_audio_seconds * 24000)
        user = user[:, :keep]
    print(f"user_samples={user.shape[-1]} voice_dir={voice_dir}", flush=True)

    stack = load_stack(voice_dir)
    # Resample note: load_audio already resampled to the rate we passed.
    # The model rate is mimi.sample_rate. Reload at the model rate.
    model_sr = int(stack["mimi"].sample_rate)
    if model_sr != 24000:
        user = lm_load_audio(str(args.track), model_sr)
        if args.max_audio_seconds:
            user = user[:, : int(args.max_audio_seconds * model_sr)]

    args.out.mkdir(parents=True, exist_ok=True)
    log_path = args.out / "drift.jsonl"
    runs = parse_runs(args.runs or None)
    custom_prompt = args.prompt_file.read_text() if args.prompt_file else ""
    print(f"runs={len(runs)}", flush=True)
    for length, voice, seed in runs:
        tag = f"p{length}_{voice}_s{seed}"
        print(f"START {tag}", flush=True)
        t0 = time.perf_counter()
        try:
            meta = run_one(
                stack,
                custom_prompt or PROMPTS[length],
                voice,
                seed,
                user,
                args.out / f"{tag}.wav",
                args.out / f"{tag}.json",
            )
            row = {
                "tag": tag,
                "length": length,
                "voice": voice,
                "seed": seed,
                "ok": True,
                "wall_s": round(time.perf_counter() - t0, 3),
                **meta,
            }
        except torch.cuda.OutOfMemoryError as exc:
            row = {"tag": tag, "ok": False, "error": f"oom: {exc}"}
            print(f"OOM {tag}: {exc}", flush=True)
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row) + "\n")
            raise SystemExit(2) from exc
        except Exception as exc:  # one bad seed should not hide the rest
            row = {"tag": tag, "length": length, "voice": voice, "seed": seed, "ok": False, "error": str(exc)}
            print(f"FAIL {tag}: {exc}", flush=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row) + "\n")
        print(f"DONE {tag} {json.dumps(row)}", flush=True)
    print("batch_complete", flush=True)


if __name__ == "__main__":
    main()
