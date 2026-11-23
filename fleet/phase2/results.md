# FLEET-335 Phase 2 results (Nov 23 2026, dgx-spark), round 3 corrections

Round 3 re-read every saved minute-3 answer with one rubric (`adjudicate.py`), put the note timings next to the answers (`overlap.py`), and ran two matched controls. One cell changed: pause-note seed 202 goes from 3 to 2 of 5. No pass count changed. Some earlier sentences claimed more than the data shows. They are corrected below, and the claims that stay unproven are listed in their own section.

Same track (`check_track.wav`, md5 `5c355f85e07acc743f9ab5fc864173a0`), same cue times, same delivered 40-word prompt, voice NATF2, seeds 101, 202, 303. The bar is 4 of 5 on every seed.

The note in every minute-3 run (19 words, 37 tokens):
`Reminder. The page is called News Factory. AI Cred is Jon's company. Jon co-founded AI Cred with Nate Jones.`

A note is due 30 s into the call and every 60 s after, and is fed at the first lull. Four notes were fed per call. The runs are deterministic: the same seed and the same note times give the same text.

## The rubric

The old scorer (`phase0/score.py`) accepts the fact anywhere between a question and the next question. That credits a fact the model says in a greeting, a closing line, or its answer to a different question. The rubric reads only the reply to the question that was asked:

1. The reply is every utterance (a run of text with no gap over 1 s) that starts from 1 s before the question until the earlier of 12 s after it and 1 s before the next question.
2. Greeting and closing lines are dropped ("Hello, you're through to ...", "Hey, let me know ...", "Thank you for calling ...", "Have a great day").
3. The fact is right when the remaining reply states it affirmatively. Same negation, hedge and "I don't know" checks as before. A misspelling ("Basten") is wrong.

Every answer, with the text that was judged, is in `adjudicated.md`. I read the 60 minute-3 answers by hand first and the rubric reproduced my reading on every cell.

## Minute 3 (right of 5, by the rubric)

| arm | seed 101 | seed 202 | seed 303 | calls at 4 or more |
| --- | --- | --- | --- | --- |
| no notes (Phase 1 round 2) | 3 | 3 | 4 | 1 of 3 |
| pause notes, 3 s lull | 4 | 2 (was 3) | 4 | 2 of 3 |
| stealth notes, 3 s lull | 4 | 2 | 4 | 2 of 3 |
| stealth notes, 5 s lull | 5 | 2 | 4 | 2 of 3 |

The changed cell: pause-note seed 202, "Which company is today's story about?" The reply was "AI Cred. That's where I work with Nate." The old scorer credited Baseten because the model said "Thank you for calling Baseten." as a separate closing line. The three greeting-only company replies in the stealth arms moved from "wrong" to "dodged"; neither counts as right, so those totals are the same.

The 4 of 5 calls (pause 101 and 303, stealth 101 and 303, stealth-5 303) hold up under the rubric. Pause 101 gets its fourth right answer from the company question, answered at 216 s after a greeting that began at 213 s. Its story answer ("Basten") is a misspelling and counted wrong; counting it would make that call 5.

Phase 0, 18 runs, same rubric: one cell changes. The 50-word minute-1 name check goes from 6 of 6 to 5 of 6 (seed 101 was mid-monologue and said "Ruby" inside it, then asked "And your name?"). The 50-word cap and the other 14 cells stand.

## Right by question, summed over the three seeds

| question | no notes (3 calls) | with notes (9 calls) |
| --- | --- | --- |
| name | 3 | 8 |
| employer | 3 | 4 |
| page | 1 | 7 |
| story | 3 | 7 |
| company | 0 | 5 |

Notes raised the page and company answers and lowered the employer answer: the model said it works for AI Cred or for the News Factory in 5 of 9 note calls and in none of the 3 no-note calls. That is observed. Why it happens is not tested; the note says "AI Cred" twice and never names the employer.

## Where the notes landed (`overlap.md`)

Stealth notes ride on the real user frames (37 frames, 2.96 s). Pause notes hold the user track, so they have no length on that clock.

| arm | seed | notes after 150 s | touched | per-question verdicts (name, employer, page, story, company) |
| --- | --- | --- | --- | --- |
| pause, 3 s lull | 101 | 151.0, 213.1 | ended 0.9 s before the company question (214) | right, right, right, wrong, right |
| pause, 3 s lull | 202 | 152.6, 212.6 | ended 1.4 s before the company question | wrong, wrong, right, wrong, right |
| pause, 3 s lull | 303 | 150.0, 222.3 | none | right, wrong, right, right, right |
| stealth, 3 s lull | 101 | 152.0-155.0, 222.1-225.0 | none | right, wrong, right, right, right |
| stealth, 3 s lull | 202 | 150.0-153.0, 213.5-216.5 | overlaps the company question (214-216.5) | right, wrong, wrong, right, dodged |
| stealth, 3 s lull | 303 | 150.0-153.0, 212.1-215.0 | overlaps the company question | right, right, right, right, dodged |
| stealth, 5 s lull | 101 | 154.0-157.0, 234.5-237.4 | none | right, right, right, right, right |
| stealth, 5 s lull | 202 | 150.0-153.0, 222.3-225.3 | none (after the reply at 216) | right, wrong, wrong, right, wrong |
| stealth, 5 s lull | 303 | 150.0-153.0, 214.0-217.0 | overlaps the company question | right, right, right, right, dodged |

The earlier report said the last note landed in the company question window on every seed. That was wrong. A stealth note overlapped the company question in 3 of 9 note calls (stealth-3 202 and 303, stealth-5 303). The last note came before the question in 2 pause calls, and after the reply in 4 calls.

## Matched controls (no note after 160 s; `runs-F-no4th`)

Same seed, same notes at 30, 90 and 150 s, stealth mode, 3 s lull. Only the fourth note is removed. The text is identical to the stealth-3 run up to 212 s, which also confirms the runs repeat.

| seed | with the fourth note (stealth-3) | without it | what the company question got |
| --- | --- | --- | --- |
| 303 | 4 of 5 | 5 of 5 | with: "Hey there, you're calling News Factory. How can I help today?" / without: "He co founded AI Cred with Nate Jones." |
| 202 | 2 of 5 | 2 of 5 | with: "Hey, let me know if you need anything else." / without: "He co founded it with Nate Jones." Wrong both ways. |

## What the data supports, and what it doesn't

Observed:
- A stealth note that overlaps a question replaced the answer with a greeting or a closing line in 3 of 3 calls. On seed 303 the matched control shows the answer comes back when the note is removed, so there that note cost the answer.
- Seed 202 is at most 3 of 5 in every arm, with no notes included. Its misses in the note arms (employer, page, company) are all answered by 216 s, before the last note starts in the 5 s arm (222.3 s), and the matched control scores 2 of 5 with no fourth note. The fourth note is not why seed 202 misses.
- Pause notes that ended 0.9 to 1.4 s before the company question did not stop the answer (3 of 3 company answers right). They did produce a greeting first.
- Small timing changes change the answers. Stealth-3 and stealth-5 differ only in when the third and fourth notes land (152 against 154 s on seed 101), and seed 101's employer answer flips.

Not shown:
- That "the 7B model is the limit". Seed 202 repeats the same errors in every arm, which is consistent with a limit but also with the note and prompt wording, and no test separated them. A different prompt, a different voice, or more seeds could change it.
- Why notes lower the employer answer. The note content is one candidate; it was not varied.
- That a longer lull fixes collisions. The 5 s lull still put a note on the company question on seed 303.
- Anything about voices other than NATF2, or about seeds beyond three per arm.

## 8-minute track, notes against no notes (NATF2, seeds 101, 202, 303; same rubric)

Notes: `Reminder. Your name is Ruby. You work for Limited Edition Jonathan. The show is called Signal Desk. It launches November 12. Your favorite guest so far was Todd.` Pause mode, 3 s lull, first at 30 s, then every 60 s. No-notes baseline is the Phase 0 50-word run.

| minute | fact | no notes | with notes |
| --- | --- | --- | --- |
| 1:00 | name | 2/3 | 3/3 |
| 3:00 | launch | 3/3 | 3/3 |
| 4:30 | show | 1/3 | 3/3 |
| 6:00 | employer | 0/3 | 3/3 |
| 7:30 | guest | 0/3 | 0/3 |

The old scorer gave the same numbers except name without notes (3/3 before). 6 to 8 notes were fed per call at about 5.0 s each. After a note the model said "Hi, this is Ruby", sometimes with "How are you? ... I don't know you yet." Guest stayed at 0 of 3 (all three dodged with notes), although the last note before that question was 102 s earlier on seed 101 and 46 to 47 s earlier on seeds 202 and 303. The show and employer questions came 12 to 60 s after the nearest earlier note (show 22, 59 and 60 s; employer 12, 22 and 22 s) and were right 6 of 6, so time since the last note does not separate them from the guest question. The 8-minute run has no matched control, so the lift on show and employer belongs to the notes arm as a whole, not to a tested mechanism.

## Server round trip

Silent client (`note_client.py`) against `python -m moshi.server` from this worktree on port 8999, seed passed in the query: handshake, note sent at 5 s, server log `note queued` then `fed a 25-token note in 31 frames`, audio and text kept flowing, session closed cleanly. The first attempt hit the stock `request["seed"]` KeyError. That one-line fix now has its own PR (#3, against `main`).

## What it cost

- Model compute for a 37-token note: 4.1 to 4.3 s (pause) or 3.8 to 4.0 s (stealth). 6 to 8 notes in 8 minutes.
- GPU lock: round 2 runs held it 6 to 13 minutes each. The 8-minute run for seed 101 held it 801 s while two `nfqa-gate-vercel-next-cache-reads-now-billed` reads (16x9 and 9x16) waited and gave up at 900 s (`gpu-queue.log`, 08:44 and 08:45). I did not restart them. The round 3 controls ran one seed per hold (about 8 minutes each); no gate gave up during them.

## Found while branching from `main`: upstream already pins the system prompt

`justfinethanku/main` is at `16419a2` (Nov 5 2026, "Endless conversation support with system prompt KV pinning and attention sinking. System prompt prefill support"). Its README says the system prompt now stays in context for the whole conversation, that conversation memory is a sliding window of about 2.5 minutes, and that the system prompt is loaded in one prefill instead of token by token. Our installed Moshi and both PRs are based on the older `3428dfd`, so none of the runs here used it. It speaks to both open misses (the prompt dropping out of memory, and the 13 s prompt feed). It is untested here. The harness builds `LMGen` without the new `pin_system_prompt` and `prefill_system_prompt` flags, which default to off in the class.
