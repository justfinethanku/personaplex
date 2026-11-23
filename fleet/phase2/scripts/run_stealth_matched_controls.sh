W=/home/lej/.t3/scratch/2026-11-23-fleet-335-phase2/personaplex
V=/home/lej/clients/LEJ/personaplex/var/fleet-335
source /home/lej/clients/LEJ/personaplex/env.sh
cd $W
export PYTHONPATH=$W/moshi
# Matched controls: stealth mode, 3 s lull, same notes at 30/90/150 s as stealth3, but no note after 160 s.
for S in 303 202; do
  /home/lej/clients/LEJ/video-lab/shared/bin/gpu-run fleet335-phase2-F-no4th-$S -- /home/lej/clients/LEJ/personaplex/.venv/bin/python fleet/phase2/run_notes.py --track $V/phase1/check_track.wav --prompt-file $V/phase2/prompt.txt --note-file $V/phase2/note-B-short.txt --note-mode stealth --last-note-s 160 --runs NATF2:$S --out $V/phase2/runs-F-no4th >> $V/phase2/runs-F-no4th.log 2>&1
done
echo ALLDONE >> $V/phase2/runs-F-no4th.log
