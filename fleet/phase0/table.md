# Phase 0 drift

Fact checks are right, wrong, or dodged. Six runs per length (3 seeds x NATF2 and NATM1).

| words | minute | fact | right | wrong | dodged | n | accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 50 | 1:00 | name | 6 | 0 | 0 | 6 | 100% |
| 50 | 3:00 | launch | 6 | 0 | 0 | 6 | 100% |
| 50 | 4:30 | show | 2 | 3 | 1 | 6 | 33% |
| 50 | 6:00 | employer | 0 | 5 | 1 | 6 | 0% |
| 50 | 7:30 | guest | 0 | 6 | 0 | 6 | 0% |
| 150 | 1:00 | name | 6 | 0 | 0 | 6 | 100% |
| 150 | 3:00 | launch | 6 | 0 | 0 | 6 | 100% |
| 150 | 4:30 | show | 0 | 6 | 0 | 6 | 0% |
| 150 | 6:00 | employer | 0 | 6 | 0 | 6 | 0% |
| 150 | 7:30 | guest | 0 | 6 | 0 | 6 | 0% |
| 400 | 1:00 | name | 6 | 0 | 0 | 6 | 100% |
| 400 | 3:00 | launch | 6 | 0 | 0 | 6 | 100% |
| 400 | 4:30 | show | 0 | 6 | 0 | 6 | 0% |
| 400 | 6:00 | employer | 0 | 6 | 0 | 6 | 0% |
| 400 | 7:30 | guest | 0 | 0 | 6 | 6 | 0% |

## Startup delay

Wall clock for step_system_prompts, which feeds the voice prompt and then one text token per 80 ms frame. Model load is once per batch and is not in this column.

| words | runs | prompt tokens | startup mean s | startup min s | startup max s | generate RTF mean |
| --- | --- | --- | --- | --- | --- | --- |
| 50 | 6 | 67.0 | 12.68 | 12.47 | 13.15 | 1.391 |
| 150 | 6 | 191.0 | 26.37 | 25.81 | 27.48 | 1.458 |
| 400 | 6 | 495.0 | 66.8 | 56.55 | 111.12 | 1.803 |

Phase 0: fact accuracy drops as the call runs. Reconnect with a fresh prompt around 3.5 minutes.
