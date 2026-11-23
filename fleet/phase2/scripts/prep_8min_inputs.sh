set -e
W=/home/lej/.t3/scratch/2026-11-23-fleet-335-phase2/personaplex
V=/home/lej/clients/LEJ/personaplex/var/fleet-335
cd $W/fleet/phase0
/home/lej/clients/LEJ/personaplex/.venv/bin/python - <<PY
from prompts import PROMPTS
open("$V/phase2/prompt-phase0-50.txt","w").write(PROMPTS[50].strip()+"\n")
print(len(PROMPTS[50].split()), PROMPTS[50])
PY
printf 'Reminder. Your name is Ruby. You work for Limited Edition Jonathan. The show is called Signal Desk. It launches November 12. Your favorite guest so far was Todd.\n' > $V/phase2/note-P0.txt
ls $V/user_track.wav $V/user_track.json
