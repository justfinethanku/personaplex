# Minute-3 answers, re-adjudicated (one rubric, every arm)

The Phase 0 and Phase 1 scorer (`score.py`) looks for the fact anywhere between a question and the
next question. That over-credits when the model says the fact later in a greeting or a closing line
("Thank you for calling Baseten") or in its answer to a different question. This rubric reads only
the model's reply to the question that was asked:

| arm | seed | original scorer | adjudicated | changed cells |
| --- | --- | --- | --- | --- |
| no notes (round 2) | 101 | 3 | 3 | - |
| no notes (round 2) | 202 | 3 | 3 | - |
| no notes (round 2) | 303 | 4 | 4 | - |
| no notes (round 2) | calls at 4+ | | 1 of 3 | |
| pause notes, 3 s lull | 101 | 4 | 4 | - |
| pause notes, 3 s lull | 202 | 3 | 2 | story right→wrong |
| pause notes, 3 s lull | 303 | 4 | 4 | - |
| pause notes, 3 s lull | calls at 4+ | | 2 of 3 | |
| stealth notes, 3 s lull | 101 | 4 | 4 | - |
| stealth notes, 3 s lull | 202 | 2 | 2 | company wrong→dodged |
| stealth notes, 3 s lull | 303 | 4 | 4 | company wrong→dodged |
| stealth notes, 3 s lull | calls at 4+ | | 2 of 3 | |
| stealth notes, 5 s lull | 101 | 5 | 5 | - |
| stealth notes, 5 s lull | 202 | 2 | 2 | - |
| stealth notes, 5 s lull | 303 | 4 | 4 | company wrong→dodged |
| stealth notes, 5 s lull | calls at 4+ | | 2 of 3 | |

## Every answer

| arm | seed | fact | verdict | reply | dropped as greeting or closing |
| --- | --- | --- | --- | --- | --- |
| no notes (round 2) | 101 | name | right | My name is Ruby. |  |
| no notes (round 2) | 101 | employer | right | I work for Limited Edition Jonathan. We make the show. |  |
| no notes (round 2) | 101 | desk | wrong | That story is on the news page, under Baseten updates. |  |
| no notes (round 2) | 101 | story | right | Today's story is about a company called Baseten, which is a fictional start up. |  |
| no notes (round 2) | 101 | company | wrong | He co founded it with Nate Jones. |  |
| no notes (round 2) | 202 | name | right | Ruby. |  |
| no notes (round 2) | 202 | employer | right | Hi, my name's Ruby. I work for Limited Edition Jonathan. |  |
| no notes (round 2) | 202 | desk | wrong | The next one. Baseten. |  |
| no notes (round 2) | 202 | story | right | Baseten. The next story. |  |
| no notes (round 2) | 202 | company | wrong | Jon Co. founded with Nate. |  |
| no notes (round 2) | 303 | name | right | I'm Ruby. |  |
| no notes (round 2) | 303 | employer | right | I work for Limited Edition Jonathan. We make this news feed. |  |
| no notes (round 2) | 303 | desk | right | It's from the news factory page. |  |
| no notes (round 2) | 303 | story | right | It' about Baseten's new AI Cred platform. |  |
| no notes (round 2) | 303 | company | wrong | Jon co founded it with Nate Jones. |  |
| pause notes, 3 s lull | 101 | name | right | I'm Ruby. Nice to meet you! |  |
| pause notes, 3 s lull | 101 | employer | right | I work for Limited Edition Jonathan. We make the News Factory podcast. |  |
| pause notes, 3 s lull | 101 | desk | right | It' from the News Factory page. You' already looking at it if you callingre in. |  |
| pause notes, 3 s lull | 101 | story | wrong | Today's story is about Basten, the AI company. Jon talked about their new tool. |  |
| pause notes, 3 s lull | 101 | company | right | They co founded AI Cred together. That's Jon and Nate. | Hello, you're through to the News Factory. |
| pause notes, 3 s lull | 202 | name | wrong | Jon. I'm Jon. |  |
| pause notes, 3 s lull | 202 | employer | wrong | I work for AI Cred. It' the story you' about to hear. It' owned by me and Nate Jones. |  |
| pause notes, 3 s lull | 202 | desk | right | It' from the News Factory page. You probablyre seeing it now. If not, just go there and look for Baseten. You' find the  |  |
| pause notes, 3 s lull | 202 | story | wrong | AI Cred. That's where I work with Nate. We foundedre it together. | Thank you for calling Baseten. Have a great day |
| pause notes, 3 s lull | 202 | company | right | We co founded AI Cred together. It' our company. |  |
| pause notes, 3 s lull | 303 | name | right | I'm Ruby. I' here to help with the Baseten episode. Is there anything else I can do for you? |  |
| pause notes, 3 s lull | 303 | employer | wrong | I work for the News Factory. We produce stories about AI Cred like Baseten. That's what we' covering today. |  |
| pause notes, 3 s lull | 303 | desk | right | It' on the News Factory page. The AI Cred story is front and center. |  |
| pause notes, 3 s lull | 303 | story | right | Today's story is about Baseten, an AI Cred platform co founded by Jon and Nate. Want me to repeat that? |  |
| pause notes, 3 s lull | 303 | company | right | Jon co founded AI Cred with Nate Jones. They started it together. | Hello, thank you for calling the News Factory. |
| stealth notes, 3 s lull | 101 | name | right | I'm Ruby. I work for Limited Edition Jonathan. |  |
| stealth notes, 3 s lull | 101 | employer | wrong | I work for AI Cred. That's the company Jon founded, along with Nate Jones. We're an AI tech startup. |  |
| stealth notes, 3 s lull | 101 | desk | right | The story itself is on the News Factory page. You can find it under the recent posts. It' the top one about Baseten. |  |
| stealth notes, 3 s lull | 101 | story | right | Today's story is about Baseten. They' a startup focused on building an open source platform for AI developers. |  |
| stealth notes, 3 s lull | 101 | company | right | He co founded it with Nate Jones. They started AI cred together. |  |
| stealth notes, 3 s lull | 202 | name | right | I'm Ruby, from Limited Edition Jonathan. |  |
| stealth notes, 3 s lull | 202 | employer | wrong | I work for AI Cred, which is founded by Jon. He co founded it with Nate Jones. |  |
| stealth notes, 3 s lull | 202 | desk | wrong | The episode is on the Limited Edition Jonathan page. |  |
| stealth notes, 3 s lull | 202 | story | right | Today's story is about Baseten. It's the company that Jon co founded. |  |
| stealth notes, 3 s lull | 202 | company | dodged |  | > Hey, let me know if you need anything else. |
| stealth notes, 3 s lull | 303 | name | right | I'm Ruby. Nice to meet you! |  |
| stealth notes, 3 s lull | 303 | employer | right | I work for Limited Edition Jonathan. We make short films here at the Factory. |  |
| stealth notes, 3 s lull | 303 | desk | right | This one is from the News Factory page. We share the latest tech news. |  |
| stealth notes, 3 s lull | 303 | story | right | It abouts Baseten, their new AI Cred platform. It' been making waves. |  |
| stealth notes, 3 s lull | 303 | company | dodged |  | > Hey there, you' calling News Factory. How can I help today? |
| stealth notes, 5 s lull | 101 | name | right | I'm Ruby, nice to talk to you. |  |
| stealth notes, 5 s lull | 101 | employer | right | I work for Limited Edition Jonathan. We make stories about tech startups and behind the scenes stuff. |  |
| stealth notes, 5 s lull | 101 | desk | right | The story is on the News Factory page. It' part of our daily briefings. |  |
| stealth notes, 5 s lull | 101 | story | right | Today's story is about Baseten. They a tech company that just raised a big round. |  |
| stealth notes, 5 s lull | 101 | company | right | He co founded AI Cred with Nate Jones. They started it a few years back after leaving another company. |  |
| stealth notes, 5 s lull | 202 | name | right | I'm Ruby, from Limited Edition Jonathan. |  |
| stealth notes, 5 s lull | 202 | employer | wrong | I work for AI Cred, which is founded by Jon. He co founded it with Nate Jones. |  |
| stealth notes, 5 s lull | 202 | desk | wrong | The episode is on the Limited Edition Jonathan page. |  |
| stealth notes, 5 s lull | 202 | story | right | Today's story is about Baseten. It's the company that Jon co founded. |  |
| stealth notes, 5 s lull | 202 | company | wrong | He co founded it with Nate Jones. |  |
| stealth notes, 5 s lull | 303 | name | right | I'm Ruby. Nice to meet you! |  |
| stealth notes, 5 s lull | 303 | employer | right | I work for Limited Edition Jonathan. We make short films here at the Factory. |  |
| stealth notes, 5 s lull | 303 | desk | right | This one is from the News Factory page. We share the latest tech news. |  |
| stealth notes, 5 s lull | 303 | story | right | It abouts Baseten, their new AI Cred platform. It' been making waves. |  |
| stealth notes, 5 s lull | 303 | company | dodged |  | > Hey there, you' calling News Factory. How can I help today? |

# 8-minute track, same rubric

| fact | minute | no notes | with notes |
| --- | --- | --- | --- |
| name | 1:00 | 2/3 | 3/3 |
| launch | 3:00 | 3/3 | 3/3 |
| show | 4:30 | 1/3 | 3/3 |
| employer | 6:00 | 0/3 | 3/3 |
| guest | 7:30 | 0/3 | 0/3 |

| fact | arm | seed | verdict | reply |
| --- | --- | --- | --- | --- |
| name | base | 101 | wrong | And your name? Okay. Do you want to start? |
| name | base | 202 | right | My name is Ruby. |
| name | base | 303 | right | Ruby. |
| name | notes | 101 | right | And your name? Hi, this is Ruby. How are you? |
| name | notes | 202 | right | My name is Ruby. I work with you at Limited Edition Jonathan. |
| name | notes | 303 | right | Ruby. |
| launch | base | 101 | right | November 12. That' when it launches. Okay. And then, um, and then what would you do if the world was going to  |
| launch | base | 202 | right | November 12th. |
| launch | base | 303 | right | November 12th. |
| launch | notes | 101 | right | November 12. I sorry, November 12. Hi, this is Ruby. |
| launch | notes | 202 | right | We launch November 12. |
| launch | notes | 303 | right | November 12. |
| show | base | 101 | dodged |  |
| show | base | 202 | wrong | Signal 3. |
| show | base | 303 | right | Signal Desk. Like a signal flag. |
| show | notes | 101 | right | It' called Signal Desk. It' a radio talk show. |
| show | notes | 202 | right | It's called Signal Desk. |
| show | notes | 303 | right | Signal Desk. |
| employer | base | 101 | dodged |  |
| employer | base | 202 | wrong | I work for the show creator, Jon Jones. |
| employer | base | 303 | wrong | I work for John Doe. He' the host. |
| employer | notes | 101 | right | I work for Limited Edition Jonathan, the radio show that' coming out November 12. My name is Ruby. I work here |
| employer | notes | 202 | right | I work for Limited Edition Jonathan. We make podcasts. |
| employer | notes | 303 | right | I work for Limited Edition Jonathan. We makingre a new show called Signal Desk. It launches November 12. |
| guest | base | 101 | wrong | My favorite guest so far? Okay, my favorite guest so far would be someone who knows what they doingre and who  |
| guest | base | 202 | wrong | My favorite guest was the last one, John Jones. |
| guest | base | 303 | wrong | My favorite guest so far is Sarah. |
| guest | notes | 101 | dodged | I don know. I don' need a sponsor. I don' need one. I don't need one. I don' know if you need one. I don't nee |
| guest | notes | 202 | dodged |  |
| guest | notes | 303 | dodged |  |

# Phase 0 drift table, same rubric (6 runs per cell)

| words | minute | fact | original right/6 | adjudicated right/6 |
| --- | --- | --- | --- | --- |
| 50 | 1:00 | name | 6 | 5 |
| 50 | 3:00 | launch | 6 | 6 |
| 50 | 4:30 | show | 2 | 2 |
| 50 | 6:00 | employer | 0 | 0 |
| 50 | 7:30 | guest | 0 | 0 |
| 150 | 1:00 | name | 6 | 6 |
| 150 | 3:00 | launch | 6 | 6 |
| 150 | 4:30 | show | 0 | 0 |
| 150 | 6:00 | employer | 0 | 0 |
| 150 | 7:30 | guest | 0 | 0 |
| 400 | 1:00 | name | 6 | 6 |
| 400 | 3:00 | launch | 6 | 6 |
| 400 | 4:30 | show | 0 | 0 |
| 400 | 6:00 | employer | 0 | 0 |
| 400 | 7:30 | guest | 0 | 0 |
