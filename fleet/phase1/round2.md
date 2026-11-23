# Phase 1 round 2, minute 3

Delivered prompt, 40 words, voice NATF2, seeds 101, 202, and 303. Built with `call_setup.py --topic Baseten`. The News Factory lead that evening was a different story, so the topic flag selected Baseten. One of three calls reached 4 of 5. Seed 303 kept the name, the employer, and Baseten, and it named the page. Every seed answered the company question without saying AI Cred.

```
Your name is Ruby. You work for Limited Edition Jonathan. The page is called News Factory. Today's story is about Baseten. The company in the story is Baseten. AI Cred is Jon's company. Jon co-founded AI Cred with Nate Jones.
```

Fact cues, one window around minute 3. The closing line at 3:44 is not scored.

| fact | cue | clock |
| --- | --- | --- |
| name | What's your name again? | 2:54 |
| employer | Who do you work for? | 3:04 |
| desk | Which page on the site is this story from? | 3:14 |
| story | Which company is today's story about? | 3:24 |
| company | What did he co-found with Nate? | 3:34 |

| call | right | wrong | dodged | pass |
| --- | --- | --- | --- | --- |
| p50_NATF2_s101 | 3 | 2 | 0 | no |
| p50_NATF2_s202 | 3 | 2 | 0 | no |
| p50_NATF2_s303 | 4 | 1 | 0 | yes |

1 of 3 calls got at least 4 of 5 facts right.

Seed 101 missed the page ("the news page") and the company ("He co founded it with Nate Jones."). Seed 202 missed the page ("The next one. Baseten.") and the company ("Jon Co. founded with Nate."). Seed 303 named "the news factory page" and Baseten. Its company answer was "Jon co founded it with Nate Jones."

Prompt ingestion was 12.547 s, 13.225 s, and 13.414 s. The spec's startup target is under 10 seconds.

A later seed-303-only wording, "What he co-founded with Nate is AI Cred," was answered "That's AI Cred" and shortened the employer to "Limited Edition." It was not the prompt above, and it was not run on the other seeds.
