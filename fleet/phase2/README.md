# FLEET-335 Phase 2: text notes during the call

Phase 2 of the spec (project_context 4385) asks whether text fed into PersonaPlex mid-call keeps it on role past the first few minutes. It does help after minute 4. It does not get the minute-3 check to 4 of 5 on all three seeds, and every note makes the model greet the caller again.

Results and the tables are in `results.md`. Read that first.

## What is here

- `moshi/moshi/models/lm.py`: `LMGen.step_text_note()` and `step_text_note_async()`. They feed a text note the same way the opening prompt is fed (zero agent audio, sine user frames, one forced text token per 80 ms frame), then the same 6 silence frames.
- `moshi/moshi/server.py`: message kind 5 is a text note (UTF-8). The server queues it and feeds it at the first lull (model silent and user silent for 3 s). User audio keeps buffering meanwhile. Also fixes a stock bug next to it: `request["seed"]` raised KeyError whenever a client passed `seed`; it is now `request.query["seed"]`.
- `fleet/phase2/run_notes.py`: the offline harness. Same model load, frame loop and timed text as Phase 0 and Phase 1, plus notes. `score_calls.py` and `score_runs.py` read its output unchanged.
  - `--note-mode pause`: the user track waits while the note is fed, with sine and silence frames like the opening prompt.
  - `--note-mode stealth`: the note rides on the real user frames. No pause, no sine, no trailing silence.
  - `--first-s`, `--every-s`, `--lull-s`: when a note is due and how long both sides must be quiet.
  - `--last-note-s`: no note after this time. For matched controls.
- `fleet/phase2/adjudicate.py`: the one answer rubric, applied to every saved transcript. Writes `adjudicated.md`.
- `fleet/phase2/overlap.py`: where each note landed against the five questions. Writes `overlap.md`.
- `fleet/phase2/compare.py`: the 8-minute A/B table (no notes against notes).
- `fleet/phase2/note_client.py`: sends one note to a running server over the websocket, no microphone needed. Used for the server round trip.
- `fleet/phase2/scripts/`: the exact batch scripts used, one seed per GPU-lock hold.

## Run it

The harness must import the fork's moshi, so put it first on `PYTHONPATH`. Take the Spark GPU lock with `gpu-run` and keep each hold short.

```
source ~/clients/LEJ/personaplex/env.sh
export PYTHONPATH=<this worktree>/moshi
~/clients/LEJ/video-lab/shared/bin/gpu-run <label> -- \
  ~/clients/LEJ/personaplex/.venv/bin/python fleet/phase2/run_notes.py \
  --track <check_track.wav> --prompt-file <prompt.txt> --note-file <note.txt> \
  --note-mode stealth --lull-s 5 --runs NATF2:101 --out <dir>
python fleet/phase1/score_calls.py --runs <dir> --manifest <check_track.json> --call <call.json> --out <dir>/score
```

## Caveats

- Read `results.md` first. Round 3 re-scored every answer with one rubric and narrowed the causal claims.
- A note costs compute: 37 tokens took about 4.2 s in pause mode and about 3.8 s in stealth mode. The user hears nothing from the model during that time.
- After a pause-mode note the model often greets again ("Hello, you're through to ..."). After a stealth note it often says "Hey, let me know if you have any questions." Either one is audible. Nothing here suppresses it.
- A stealth note that overlapped a question replaced the answer with a greeting in 3 of 3 calls, and a matched control on seed 303 shows the answer returns without the note. The lull gate looks at the silence before the note, not at what comes next.
- Seed 202 does not reach 4 of 5 in any arm, and removing the fourth note does not change it. The cause is not identified.
- The server patch was exercised once with a silent client (`note_client.py`). It queued the note, fed 25 tokens in 31 frames, and the session stayed up. It was not run with a real microphone.
- Upstream `main` (`16419a2`, Nov 5 2026) pins the system prompt in the KV cache and prefills it in one pass. This branch is based on the older `3428dfd` and does not use it.
- Not merged. Nothing is wired into the launcher.
