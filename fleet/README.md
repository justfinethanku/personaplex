# FLEET-335: PersonaPlex prompt length and call setup

Phase 0 measured how long a planted role prompt stays accurate. Phase 1 builds a podcast-producer prompt from the fleet databases and opens the web client with it.

The paragraphs below are the unpinned baseline, from before this branch turned prompt pinning on. The pinned retest, the same-revision flags-off control, and the warmed-server timing are in `phase0/pin-retest.md`.

The word cap is 50. Minute 1 and minute 3 were right in 6 of 6 runs at 50, 150, and 400 words. Longer prompts did not raise that score. They added startup silence, and after 4:30 they scored worse. See `phase0/table.md`.

A 50-word prompt takes about 13 seconds to feed (voice prompt, then one text token per 80 ms). That exceeds the spec's 10-second startup target before browser overhead. A 150-word prompt takes about 26 seconds. A 400-word prompt takes about 67 seconds.

The launcher should say to reconnect around 3.5 minutes. By 4:30 the show name was right in 2 of 6 runs at 50 words, and in 0 of 6 at 150 and 400. Employer and guest were gone by 6:00.

Phase 1, three offline calls, voice NATF2, seeds 101, 202, and 303. A narrative squeeze that merely contained the five phrases scored 2, 3, and 3 (`phase1/narrative.md`). The earlier 48-word template scored 4, 4, and 3 (`phase1/direct.md`). The delivered short-sentence prompt, with the page and the story company each named on their own, scored 3, 3, and 4 (`phase1/round2.md`). Seed 303 kept the name, the employer, and Baseten, and it named News Factory. The company answer was still "it". Seeds 101 and 202 missed the page and the company. The done-when is 4 of 5 on every call. One call met it.

The five fact cues sit at 2:54, 3:04, 3:14, 3:24, and 3:34. A closing line at 3:44 ends the last window. Prompt ingestion on that 40-word prompt was 12.5 to 13.4 seconds, still over the spec's 10-second startup target.

## Run the drift matrix

From the PersonaPlex venv, with the GPU free of other heavy jobs:

`run_drift.py` loads the model once. It refuses to start when memory available is under 28 GB or when a GPU process other than ComfyUI, the remote-desktop daemon, or itself is present.

The harness passes `prefill_system_prompt=True` and `pin_system_prompt=True` into `LMGen`. That class defaults both off, so a run that omitted them would still use the sliding window. `--no-prefill-system-prompt` and `--no-pin-system-prompt` turn them off for a same-revision control. `--max-pinned-frames` defaults to 640 because a 400-word prompt is about 558 frames and the server's 512 cap cannot pin it. Each `drift.jsonl` row records the git revision and those flags.

Run it on this checkout's `moshi`, not the venv copy (that copy is the older install and has no pin arguments). `env.sh` changes directory to the install clone, so change back to this checkout after sourcing it.

```
source ~/clients/LEJ/personaplex/env.sh
cd <this checkout>
export PYTHONPATH="$PWD/moshi${PYTHONPATH:+:$PYTHONPATH}"
python fleet/phase0/build_user_track.py --out .
python fleet/phase0/run_drift.py --track user_track.wav --out runs
python fleet/phase0/score_runs.py --runs runs --manifest user_track.json --out runs
```

## Build a call

```
python fleet/call_setup.py
python fleet/call_setup.py --topic Baseten
```

The delivered path renders each sourced fact as its own short sentence and stops at the Phase 0 cap (50 words). `--topic` replaces the News Factory story keyword. `--squeeze` (Claude, OpenRouter, `fleet get OPENROUTER_API_KEY`) and `--direct` (the earlier 48-word template) are experiment inputs. The page is `producer.html` next to the JSON. The link is `https://spark-3368.tail6e7cfb.ts.net:8998/?text_prompt=...&voice_prompt=NATF2.pt&autostart=1`. A voice in that URL that is not in the picker does not autostart. The Connect button stays.

The client reads `text_prompt` and `voice_prompt` from the page URL. The server only serves that client when started with `--static` pointed at a build of this client. The stock server serves the Hugging Face bundle, which ignores the page URL.

## Live tap

The Spark has no capture device (`arecord -l` lists the header and no devices). A first tap that starts an audible conversation needs a person and a microphone. That call was not made. On a warmed server from this checkout, a websocket silence frame reached first audio in 0.145 seconds. The numbers are in `phase0/pin-retest.md`.

1. The GPU must be free of a fish-speech restart or a video-lab render. ComfyUI on ports 8191 and 8192 can stay up.
2. `~/clients/LEJ/personaplex/start-server.sh`
3. Open `https://spark-3368.tail6e7cfb.ts.net:8998/producer.html`
4. Tap "Producer: next episode" and allow the microphone. NATF2 is a picker preset, so the page tries to start on that tap. If the browser blocks the start, press Connect. The prompt is already filled in.
5. An unknown `voice_prompt` does not autostart. Connect stays, on NATF0.
6. The page says to reconnect around 3.5 minutes.
7. Stop the server when the call is over so the GPU is free.
