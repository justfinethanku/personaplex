"""Phase 2 runs: the same offline call as Phase 0 and Phase 1, plus text notes fed mid-call.

FLEET-335 Phase 2 (spec project_context 4385): "feed it notes during the call".
The model code is the fork's moshi (PYTHONPATH must put the worktree's moshi first, so
LMGen.step_text_note exists). Everything else is the Phase 0 harness: same model load,
same frame loop, same frame-timed text events, so score_calls.py and score_runs.py read
the output unchanged.

How a note lands: a note is due every --every-s seconds of call time (first one at
--first-s). It is fed at the first lull, when the model has said nothing and the user has
been silent for --lull-s. The user track is paused while the note is fed, as a live server
would buffer the user's audio, so cue times in the score stay on the user's clock.
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

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "phase0"))
import moshi  # noqa: E402
from moshi.models.lm import _iterate_audio as lm_iterate_audio  # noqa: E402
from moshi.models.lm import encode_from_sphn as lm_encode_from_sphn  # noqa: E402
from moshi.models.lm import load_audio as lm_load_audio  # noqa: E402
from moshi.offline import decode_tokens_to_pcm, seed_all, wrap_with_system_tags  # noqa: E402
from run_drift import PAD_NAMES, PAD_TOKENS, load_stack, mem_available_gb  # noqa: E402

USER_QUIET_RMS = 0.004


def run_one(stack, prompt, note, voice, seed, user_pcm, out_wav, out_json, cfg) -> dict:
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
    lm_gen.text_prompt_tokens = tokenizer.encode(wrap_with_system_tags(prompt))
    note_tokens = tokenizer.encode(wrap_with_system_tags(note)) if note else []
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
    frame_size = int(lm_gen._frame_size)
    lull_frames = int(round(cfg["lull_s"] * frame_rate))
    user_mono = user_pcm[0] if user_pcm.ndim == 2 else user_pcm
    events = []
    generated = []
    injections = []
    frame_idx = 0
    pad_run = 0
    user_quiet_run = 0
    next_due_s = cfg["first_s"] if note_tokens else None
    pending = False
    stealth = cfg["mode"] == "stealth"
    feed = []  # stealth mode: note tokens still to go in, one per real user frame
    feed_started = None
    wall0 = time.perf_counter()
    with torch.inference_mode():
        for user_encoded in lm_encode_from_sphn(
            mimi,
            lm_iterate_audio(user_pcm, sample_interval_size=frame_size, pad=True),
            max_batch=1,
        ):
            steps = user_encoded.shape[-1]
            for c in range(steps):
                t = frame_idx / frame_rate
                # The lull gate looks at the frames just before this one.
                if next_due_s is not None and t >= next_due_s:
                    pending = True
                if pending and pad_run >= lull_frames and user_quiet_run >= lull_frames:
                    if stealth:
                        # The note rides on the real user frames: no pause, no sine frames, no trailing silence.
                        feed = list(note_tokens)
                        feed_started = (t, time.perf_counter())
                        injections.append(
                            {"t_track": round(t, 2), "note_tokens": len(note_tokens), "frames": len(note_tokens),
                             "inject_s": 0.0, "events_before": len(events)}
                        )
                    else:
                        ti = time.perf_counter()
                        used = lm_gen.step_text_note(note_tokens)
                        torch.cuda.synchronize()
                        injections.append(
                            {
                                "t_track": round(t, 2),
                                "note_tokens": len(note_tokens),
                                "frames": used,
                                "inject_s": round(time.perf_counter() - ti, 3),
                                "events_before": len(events),
                            }
                        )
                    pending = False
                    next_due_s = t + cfg["every_s"]
                    if cfg["last_note_s"] and next_due_s > cfg["last_note_s"]:
                        next_due_s = None  # matched control: no note after this time
                    pad_run = 0
                    user_quiet_run = 0
                step_in = user_encoded[:, :, c : c + 1]
                if feed:
                    tokens_out = lm_gen.step(step_in, moshi_tokens=lm_gen._encode_zero_frame(), text_token=feed.pop(0))
                    if not feed:
                        torch.cuda.synchronize()
                        injections[-1]["wall_s"] = round(time.perf_counter() - feed_started[1], 3)
                    frame_idx += 1
                    lo = frame_idx * frame_size - frame_size
                    chunk = user_mono[lo : lo + frame_size]
                    rms = float(np.sqrt(np.mean(np.square(chunk)))) if len(chunk) else 0.0
                    user_quiet_run = user_quiet_run + 1 if rms < USER_QUIET_RMS else 0
                    continue
                tokens_out = lm_gen.step(step_in)
                frame_idx += 1
                lo = frame_idx * frame_size - frame_size
                chunk = user_mono[lo : lo + frame_size]
                rms = float(np.sqrt(np.mean(np.square(chunk)))) if len(chunk) else 0.0
                user_quiet_run = user_quiet_run + 1 if rms < USER_QUIET_RMS else 0
                if tokens_out is None:
                    continue
                pcm = decode_tokens_to_pcm(mimi, other, lm_gen, tokens_out)
                generated.append(pcm)
                text_token = int(tokens_out[0, 0, 0].item())
                if text_token in PAD_TOKENS:
                    pad_run += 1
                    events.append({"t": t, "pad": True, "text": PAD_NAMES.get(text_token, "")})
                else:
                    pad_run = 0
                    piece = tokenizer.id_to_piece(text_token).replace("▁", " ")
                    events.append({"t": t, "pad": False, "text": piece})
    torch.cuda.synchronize()
    gen_s = time.perf_counter() - wall0

    if not generated:
        raise RuntimeError("no audio frames")
    # What the model said in the six seconds after each note, to see whether it read the note out.
    for inj in injections:
        start = inj["t_track"]
        words = "".join(e["text"] for e in events if not e["pad"] and start <= e["t"] < start + 6.0)
        inj["said_next_6s"] = " ".join(words.split())
        del inj["events_before"]
    output_pcm = np.concatenate(generated, axis=-1)
    target = int(user_pcm.shape[-1])
    if output_pcm.shape[-1] > target:
        output_pcm = output_pcm[:target]
    elif output_pcm.shape[-1] < target:
        output_pcm = np.concatenate([output_pcm, np.zeros(target - output_pcm.shape[-1], dtype=output_pcm.dtype)])
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    sphn.write_wav(str(out_wav), output_pcm, mimi.sample_rate)
    out_json.write_text(json.dumps(events))
    audio_s = target / float(mimi.sample_rate)
    return {
        "startup_s": round(startup_s, 3),
        "prompt_tokens": len(lm_gen.text_prompt_tokens),
        "note_tokens": len(note_tokens),
        "notes_fed": len(injections),
        "injections": injections,
        "generate_s": round(gen_s, 3),
        "audio_s": round(audio_s, 3),
        "realtime_factor": round(gen_s / audio_s, 3) if audio_s else None,
        "frames": frame_idx,
        "text_events": sum(1 for e in events if not e["pad"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--track", type=Path, required=True, help="24 kHz user wav")
    parser.add_argument("--prompt-file", type=Path, required=True)
    parser.add_argument("--note-file", type=Path, default=None, help="Text fed as a note. Omit for a control run with no notes.")
    parser.add_argument("--runs", required=True, help="Comma list of VOICE:SEED, for example NATF2:101,NATF2:202")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--first-s", type=float, default=30.0)
    parser.add_argument("--every-s", type=float, default=60.0)
    parser.add_argument("--lull-s", type=float, default=3.0)
    parser.add_argument("--last-note-s", type=float, default=0.0,
                        help="No note is due after this many seconds of call time (0 = no limit). For matched controls.")
    parser.add_argument("--note-mode", choices=("pause", "stealth"), default="pause",
                        help="pause: the user track waits while the note is fed, with sine and silence frames like the opening prompt. "
                             "stealth: the note rides on the real user frames, no pause and no sine or silence frames.")
    parser.add_argument("--length-tag", default="50", help="Number in the p<N>_ file tag. The drift scorer reads it as the prompt length.")
    args = parser.parse_args()

    os.environ.setdefault("TRITON_PTXAS_PATH", "/usr/local/cuda/bin/ptxas")
    print(f"moshi={moshi.__file__}", flush=True)
    from huggingface_hub import hf_hub_download
    from moshi.models import loaders

    voices_tgz = Path(hf_hub_download(loaders.DEFAULT_REPO, "voices.tgz"))
    voice_dir = voices_tgz.parent / "voices"
    stack = load_stack(voice_dir)
    model_sr = int(stack["mimi"].sample_rate)
    user = lm_load_audio(str(args.track), model_sr)
    prompt = args.prompt_file.read_text().strip()
    note = args.note_file.read_text().strip() if args.note_file else ""
    cfg = {"first_s": args.first_s, "every_s": args.every_s, "lull_s": args.lull_s, "mode": args.note_mode, "last_note_s": args.last_note_s}
    print(f"user_samples={user.shape[-1]} note_words={len(note.split())} cfg={cfg}", flush=True)

    args.out.mkdir(parents=True, exist_ok=True)
    log_path = args.out / "drift.jsonl"
    for item in args.runs.split(","):
        voice, seed_s = item.split(":")
        seed = int(seed_s)
        tag = f"p{args.length_tag}_{voice}_s{seed}"
        print(f"START {tag}", flush=True)
        t0 = time.perf_counter()
        try:
            meta = run_one(stack, prompt, note, voice, seed, user, args.out / f"{tag}.wav", args.out / f"{tag}.json", cfg)
            row = {"tag": tag, "length": int(args.length_tag), "voice": voice, "seed": seed, "ok": True,
                   "wall_s": round(time.perf_counter() - t0, 3), **meta}
        except torch.cuda.OutOfMemoryError as exc:
            row = {"tag": tag, "ok": False, "error": f"oom: {exc}"}
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row) + "\n")
            raise SystemExit(2) from exc
        except Exception as exc:
            row = {"tag": tag, "length": int(args.length_tag), "voice": voice, "seed": seed, "ok": False, "error": str(exc)}
            print(f"FAIL {tag}: {exc}", flush=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row) + "\n")
        print(f"DONE {tag} {json.dumps(row)}", flush=True)
    print("batch_complete", flush=True)


if __name__ == "__main__":
    main()
