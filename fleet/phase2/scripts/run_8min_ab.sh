W=/home/lej/.t3/scratch/2026-11-23-fleet-335-phase2/personaplex
V=/home/lej/clients/LEJ/personaplex/var/fleet-335
source /home/lej/clients/LEJ/personaplex/env.sh
cd $W
export PYTHONPATH=$W/moshi
# wait for the stealth batch to finish so two jobs never queue for the lock at once
while ! grep -q ALLDONE $V/phase2/runs-C-stealth.log 2>/dev/null; do sleep 15; done
for S in 101 202 303; do
  /home/lej/clients/LEJ/video-lab/shared/bin/gpu-run fleet335-phase2-D-8min-$S -- /home/lej/clients/LEJ/personaplex/.venv/bin/python fleet/phase2/run_notes.py --track $V/user_track.wav --prompt-file $V/phase2/prompt-phase0-50.txt --note-file $V/phase2/note-P0.txt --note-mode pause --runs NATF2:$S --out $V/phase2/runs-D-8min >> $V/phase2/runs-D-8min.log 2>&1
done
echo ALLDONE >> $V/phase2/runs-D-8min.log
