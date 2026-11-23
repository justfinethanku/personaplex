W=/home/lej/.t3/scratch/2026-11-23-fleet-335-phase2/personaplex
V=/home/lej/clients/LEJ/personaplex/var/fleet-335
source /home/lej/clients/LEJ/personaplex/env.sh
cd $W
export PYTHONPATH=$W/moshi
for S in 101 202 303; do
  /home/lej/clients/LEJ/video-lab/shared/bin/gpu-run fleet335-phase2-C-stealth-$S -- /home/lej/clients/LEJ/personaplex/.venv/bin/python fleet/phase2/run_notes.py --track $V/phase1/check_track.wav --prompt-file $V/phase2/prompt.txt --note-file $V/phase2/note-B-short.txt --note-mode stealth --runs NATF2:$S --out $V/phase2/runs-C-stealth >> $V/phase2/runs-C-stealth.log 2>&1
done
echo ALLDONE >> $V/phase2/runs-C-stealth.log
