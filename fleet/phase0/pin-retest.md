# Pinned retest, 2026-11-23

Both `prefill_system_prompt` and `pin_system_prompt` are on unless a table says otherwise. `--max-pinned-frames` is 640. The reply rubric is `reply_rubric.py`: the reply is the utterance from 1 second before the question until the earlier of 12 seconds after it and 1 second before the next question, with greeting and closing lines dropped.

The six 50-word flags-on rows were written by revision `70c610ff8feb2f2587b79af6b386eda8983ad4b3`. Every later row was written by `0c34682b6b00a37276db2488e9f629589d320717`. Those two commits differ by the scorer only. Inference is the same. Raw rows, wavs, and the scored markdown live in `~/clients/LEJ/personaplex/var/fleet-335/pin-retest/` on dgx-spark. The paragraphs at the top of `fleet/README.md` and `phase0/table.md` are the older unpinned matrix.

Each cell had its own `gpu-run`. The first attempt held one lock around the whole matrix. Lex stopped that job at 13:20:30 ET (gpu-queue `fleet335-pin-p0` rc=143, wall 5957s) because a News Factory picture stage was waiting. Exit 143 is SIGTERM. The run script, `gpu-run`, and `gpu-prio` have no wall-clock kill, and this was not an out-of-memory exit. The resume that was still wrapping all 12 remaining cells in one lock was stopped before `p150_NATF2_s101` wrote a row. The six finished 50-word runs were kept. Between the per-cell locks, News Factory took the GPU (`nfv-L01` 322s, `nfv-L18` 285s, and two `nfqa-gate` reads).

## Phase 0, flags on

Track `user_track.wav`, 480 seconds, seeds 101, 202, 303, voices NATF2 and NATM1. n=6 per cell.

| words | minute | fact | right | wrong | dodged |
| --- | --- | --- | --- | --- | --- |
| 50 | 1:00 | name | 6 | 0 | 0 |
| 50 | 3:00 | launch | 6 | 0 | 0 |
| 50 | 4:30 | show | 6 | 0 | 0 |
| 50 | 6:00 | employer | 3 | 3 | 0 |
| 50 | 7:30 | guest | 5 | 1 | 0 |
| 150 | 1:00 | name | 5 | 1 | 0 |
| 150 | 3:00 | launch | 6 | 0 | 0 |
| 150 | 4:30 | show | 6 | 0 | 0 |
| 150 | 6:00 | employer | 2 | 4 | 0 |
| 150 | 7:30 | guest | 6 | 0 | 0 |
| 400 | 1:00 | name | 6 | 0 | 0 |
| 400 | 3:00 | launch | 6 | 0 | 0 |
| 400 | 4:30 | show | 6 | 0 | 0 |
| 400 | 6:00 | employer | 4 | 2 | 0 |
| 400 | 7:30 | guest | 6 | 0 | 0 |

Prompt frames after the voice prompt and the half-second of silence: 50 words is 67 tokens and 130 frames, 150 words is 191 tokens and 254 frames, 400 words is 495 tokens and 558 frames. 558 fits under 640. The sliding window on the 400-word runs was 1490 frames.

`startup_s` is the prompt feed after that process has already loaded and warmed the model. Flags on: 50 words 0.211–0.668 seconds, 150 words 0.713–0.804 seconds, 400 words 1.099–1.184 seconds. Generate realtime factor was 1.781–1.836. Loading the model was about 95–105 seconds, and each cell loaded it again because each cell was its own process.

The same tracks re-scored from `var/fleet-335/runs` (unpinned, no revision field, startup about 12.5–13.1 seconds on the 50-word rows) are name/launch/show/employer/guest: 50 words 5, 6, 2, 0, 0; 150 words 6, 6, 0, 0, 0; 400 words 6, 6, 0, 0, 0. All of those are out of 6.

## Phase 0, flags off, same checkout

Six 50-word runs with `--no-prefill-system-prompt --no-pin-system-prompt`. Prompt frames stayed 130. Startup went back to 12.332–13.270 seconds. Generate realtime factor was 1.286–1.370.

| minute | fact | right | wrong | dodged |
| --- | --- | --- | --- | --- |
| 1:00 | name | 5 | 1 | 0 |
| 3:00 | launch | 1 | 1 | 4 |
| 4:30 | show | 0 | 1 | 5 |
| 6:00 | employer | 0 | 4 | 2 |
| 7:30 | guest | 0 | 1 | 5 |

On this checkout, flags off does not reproduce the older unpinned minute-3 launch score of 6/6. The name is still there at minute 1. The launch fact is mostly gone by minute 3.

## Phase 1

Delivered prompt `phase1/prompt-spoken.txt`, 40 words, 64 tokens, 127 frames. Track `phase1/check_track.wav`, 260 seconds. Voice NATF2. Seeds 101, 202, 303. The five facts sit at 2:54, 3:04, 3:14, 3:24, and 3:34.

Flags on, startup 0.592–0.674 seconds, realtime factor 1.828–1.863:

| call | right of 5 | pass (4 of 5) |
| --- | --- | --- |
| seed 101 | 5 | yes |
| seed 202 | 4 | yes |
| seed 303 | 3 | no |

Seed 303 answered the name, the page, and Baseten. It gave AI Cred as the employer and did not say AI Cred when asked what Jon co-founded. Seed 202 missed only that co-founded-company question ("He co founded it with Nate Jones."). Two of three calls reach 4 of 5. The done-when asks for all three.

The earlier spoken runs in `var/fleet-335/phase1/runs-spoken-try5`, scored with this same rubric, were 3, 3, and 4. That is the 3, 3, 4 recorded in `fleet/README.md`.

Flags off, same checkout and same prompt, startup 12.264–12.749 seconds:

| call | right of 5 | pass |
| --- | --- | --- |
| seed 101 | 0 | no |
| seed 202 | 0 | no |
| seed 303 | 0 | no |

## Warmed server, not a microphone

`arecord -l` prints the capture header and no devices. Nobody tapped a microphone.

A server started from this checkout (`PYTHONPATH` on this tree's `moshi`, so the server defaults leave both flags on) was warmed before it accepted a connection. The client then opened `wss://127.0.0.1:8998/api/chat` with the Phase 1 prompt, `NATF2.pt`, and seed 101, waited for the handshake, and sent 0.8 seconds of silence as Opus. The server log shows "Prefilled 127 system prompt frames" and "Pinned 127" at the server default cap of 512.

| interval | seconds |
| --- | --- |
| connect to handshake (prompt prefill on a warm model) | 0.638 |
| silence packet to first audio packet | 0.145 |
| connect to first audio packet | 0.783 |

The server was stopped afterward. ComfyUI stayed on 8191 and 8192. This is not a microphone tap-to-first-audio measurement.

## Done when

Phase 0 now has a by-minute table for 50, 150, and 400 words. Phase 1 does not pass 4 of 5 on all three calls. The microphone measurement was not made. The done-when is not met, and this PR should not be shipped as though it were.

What is useful: after the model is warm, the prompt is in the model in well under a second, and the planted minute-3 fact is 6 of 6 at every length tested with the flags on. A short call that reconnects around 3:30 can use that. It should not promise that every call clears 4 of 5. One of these three scored 3. It also should not promise the employer past four minutes: that fact was 3, 2, and 4 of 6 as the prompt went from 50 to 400 words.

If the bar stays 4 of 5 on every call, or recall past four minutes has to hold every planted fact, that is the Phase 3 turn-based path. The notes experiment on the other pull request was not run again and is not part of this result.
