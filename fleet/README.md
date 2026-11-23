# FLEET-335: PersonaPlex prompt length and call setup

Phase 0 measured how long a planted role prompt stays accurate. Phase 1 builds a podcast-producer prompt from the fleet databases and opens the web client with it.

The word cap is 50. Minute 1 and minute 3 were right in 6 of 6 runs at 50, 150, and 400 words. Longer prompts did not raise that score. They added startup silence, and after 4:30 they scored worse. See `phase0/table.md`.

A 50-word prompt takes about 13 seconds to feed (voice prompt, then one text token per 80 ms). That exceeds the spec's 10-second startup target before browser overhead. A 150-word prompt takes about 26 seconds. A 400-word prompt takes about 67 seconds.

The launcher should say to reconnect around 3.5 minutes. By 4:30 the show name was right in 2 of 6 runs at 50 words, and in 0 of 6 at 150 and 400. Employer and guest were gone by 6:00.

Phase 1, three offline calls, voice NATF2, seeds 101, 202, and 303. A narrative squeeze that merely contained the five phrases scored 2, 3, and 3 (`phase1/narrative.md`). Restating each fact as its own sentence scored 4, 4, and 3 (`phase1/direct.md`). The done-when is 4 of 5 on every call. Two calls met it. Seed 303 missed the page and the company.

## Run the drift matrix

From the PersonaPlex venv, with the GPU free of other heavy jobs:

```
python fleet/phase0/build_user_track.py --out .
python fleet/phase0/run_drift.py --track user_track.wav --out runs
python fleet/phase0/score_runs.py --runs runs --manifest user_track.json --out runs
```

`run_drift.py` loads the model once. It refuses to start when memory available is under 28 GB or when a GPU process other than ComfyUI, the remote-desktop daemon, or itself is present.

## Build a call

```
python fleet/call_setup.py --words 50 --direct
```

`--direct` states each database fact as its own sentence. Without it, Claude (OpenRouter, `fleet get OPENROUTER_API_KEY`) writes the paragraph. The page is `producer.html` next to the JSON. The link is `https://spark-3368.tail6e7cfb.ts.net:8998/?text_prompt=...&voice_prompt=NATF2.pt&autostart=1`.

The client reads `text_prompt` and `voice_prompt` from the page URL. The server only serves that client when started with `--static` pointed at a build of this client. The stock server serves the Hugging Face bundle, which ignores the page URL.

## Live tap

These steps need a person and a free GPU. They were not run here.

1. `~/clients/LEJ/personaplex/start-server.sh`
2. Open `https://spark-3368.tail6e7cfb.ts.net:8998/producer.html`
3. Tap "Producer: next episode" and allow the microphone. If the browser blocks the automatic start, press Connect. The prompt and NATF2 are already filled in.
4. Stop the server when the call is over so the GPU is free.
