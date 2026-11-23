W=/home/lej/.t3/scratch/2026-11-23-fleet-335-phase2/personaplex
V=/home/lej/clients/LEJ/personaplex/var/fleet-335
source /home/lej/clients/LEJ/personaplex/env.sh
cd $W
export PYTHONPATH=$W/moshi
NOTE=${1:-B-short}
for S in 101 202 303; do
  /home/lej/clients/LEJ/video-lab/shared/bin/gpu-run fleet335-phase2-$NOTE-$S -- /home/lej/clients/LEJ/personaplex/.venv/bin/python fleet/phase2/run_notes.py --track $V/phase1/check_track.wav --prompt-file $V/phase2/prompt.txt --note-file $V/phase2/note-$NOTE.txt --runs NATF2:$S --out $V/phase2/runs-$NOTE >> $V/phase2/runs-$NOTE.log 2>&1
done
echo ALLDONE >> $V/phase2/runs-$NOTE.log
