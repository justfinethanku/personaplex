W=/home/lej/.t3/scratch/2026-11-23-fleet-335-phase2/personaplex
V=/home/lej/clients/LEJ/personaplex/var/fleet-335/phase2
source /home/lej/clients/LEJ/personaplex/env.sh
cd $W
export PYTHONPATH=$W/moshi
PY=/home/lej/clients/LEJ/personaplex/.venv/bin/python
$PY -m moshi.server --host 127.0.0.1 --port 8999 --ssl $PP/ssl --static $PP/client-dist > $V/server-test.log 2>&1 &
SP=$!
for i in $(seq 1 90); do
  if grep -q "Access the Web UI\|Running on\|http" $V/server-test.log 2>/dev/null && curl -sk -o /dev/null https://127.0.0.1:8999/ ; then break; fi
  sleep 5
done
echo "server pid $SP ready"
timeout 150 $PY fleet/phase2/note_client.py --url https://127.0.0.1:8999 --note "Reminder. The page is called News Factory. AI Cred is Jon's company." --note-at 5 --seconds 45 > $V/server-test-client.log 2>&1
echo "client exit $?"
kill $SP; wait $SP 2>/dev/null
echo "server stopped"
