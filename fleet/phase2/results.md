# FLEET-335 Phase 2 results (Nov 23 2026, dgx-spark)

Same scoring script (`fleet/phase1/score_calls.py`), same track (`check_track.wav`, md5 `5c355f85e07acc743f9ab5fc864173a0`), same cue times, same delivered 40-word prompt, voice NATF2, seeds 101, 202, 303. The bar is 4 of 5 on every seed.

The note in every minute-3 run (19 words, 37 tokens):
`Reminder. The page is called News Factory. AI Cred is Jon's company. Jon co-founded AI Cred with Nate Jones.`

A note is due 30 s into the call and every 60 s after, and is fed at the first lull. Four notes landed on every call.

## Minute 3 (right of 5)

| arm | seed 101 | seed 202 | seed 303 | calls at 4 or more |
| --- | --- | --- | --- | --- |
| no notes (Phase 1 round 2, delivered prompt) | 3 | 3 | 4 | 1 of 3 |
| pause notes, 3 s lull | 4 | 3 | 4 | 2 of 3 |
| stealth notes, 3 s lull | 4 | 2 | 4 | 2 of 3 |
| stealth notes, 5 s lull | 5 | 2 | 4 | 2 of 3 |

Phase 2 did not meet the bar. Seed 202 failed in every arm. It names "AI Cred" as its employer and says the page is Limited Edition Jonathan, so the notes do not move that seed.

Where each note landed (seconds into the track): pause and stealth-3 s notes at about 30, 91, 151 and 212-222. The last one falls in the company question (cue at 214) and the model answered with a greeting ("Hey there, you're calling News Factory"). Stealth-5 s moved it to 214-234 and seed 303 still lost the company answer to a note that began as the question did.

## 8-minute track, notes against no notes (NATF2, seeds 101, 202, 303)

Notes: `Reminder. Your name is Ruby. You work for Limited Edition Jonathan. The show is called Signal Desk. It launches November 12. Your favorite guest so far was Todd.` Pause mode, 3 s lull, first at 30 s, then every 60 s. No-notes baseline is the Phase 0 50-word run.

| minute | fact | no notes | with notes |
| --- | --- | --- | --- |
| 1:00 | name | 3/3 | 3/3 |
| 3:00 | launch | 3/3 | 3/3 |
| 4:30 | show | 1/3 | 3/3 |
| 6:00 | employer | 0/3 | 3/3 |
| 7:30 | guest | 0/3 | 0/3 |

6 to 8 notes were fed per call at about 5.0 s each. After a note the model said "Hi, this is Ruby", sometimes with "How are you? ... I don't know you yet." Guest stayed at 0 of 3 (two dodged, one wrong), although the last note before that question was 102 s earlier on seed 101 and 46 to 47 s earlier on seeds 202 and 303. Facts asked 12 to 22 s after a note were right 6 of 6.

Per-seed detail (`compare.py`):


| minute | fact | no notes by seed | with notes by seed |
| --- | --- | --- | --- |
| 4:30 | show | 101 dodged, 202 wrong, 303 right | 101 right, 202 right, 303 right |
| 6:00 | employer | 101 dodged, 202 wrong, 303 wrong | 101 right, 202 right, 303 right |
| 7:30 | guest | 101 wrong, 202 wrong, 303 wrong | 101 dodged, 202 dodged, 303 wrong |

## Server round trip

Silent client (`note_client.py`) against `python -m moshi.server` from this worktree on port 8999, seed passed in the query: handshake, note sent at 5 s, server log `note queued` then `fed a 25-token note in 31 frames`, audio and text kept flowing, session closed cleanly. The first attempt hit the stock `request["seed"]` KeyError (fixed in this branch).

## What it cost

- Model compute for a 37-token note: 4.1 to 4.3 s (pause) or 3.8 to 4.0 s (stealth). 6 to 8 notes in 8 minutes.
- GPU lock: each run held it 6 to 13 minutes. The 8-minute run for seed 101 held it 801 s while two `nfqa-gate-vercel-next-cache-reads-now-billed` reads (16x9 and 9x16) waited and then gave up at 900 s (`gpu-queue.log`, 08:44 and 08:45). I did not restart them.
