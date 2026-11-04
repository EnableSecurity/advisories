#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
mode="${1:-}"
case "$mode" in
  before|after-default) extension=5592 ;;
  after-configured) extension=5593 ;;
  *) echo "usage: $0 <before|after-default|after-configured>" >&2; exit 2 ;;
esac

mkdir -p results
case_name="${mode}-$(date -u +%Y%m%dT%H%M%S)-$$"
attacker="es202607-${case_name}-attacker"

cleanup() {
  docker logs "$attacker" >"results/${case_name}-attacker.log" 2>&1 || true
  docker compose --profile "$mode" --profile probe logs --no-color "$mode" >"results/${case_name}-target.log" 2>&1 || true
  docker rm -f "$attacker" >/dev/null 2>&1 || true
  docker compose --profile "$mode" --profile probe down -v --remove-orphans
}
trap cleanup EXIT

# Only one target is running at a time. No host ports are published.
docker compose --profile "$mode" up -d --no-build "$mode"
ready=0
for _ in $(seq 1 30); do
  if docker compose --profile "$mode" logs --no-color "$mode" 2>/dev/null | grep 'Created ip list domains default' >/dev/null; then
    ready=1
    break
  fi
  sleep 1
done
if [ "$ready" -ne 1 ]; then
  echo "FreeSWITCH did not start; inspect results/${case_name}-target.log after cleanup" >&2
  exit 1
fi
# The profile can accept packets before the core enables new inbound calls.
sleep 8

docker compose --profile probe run -d --name "$attacker" runner attacker --case "$case_name"
docker compose --profile probe run --rm runner legitimate --case "$case_name" --target "$mode" --extension "$extension"
status="$(docker wait "$attacker")"
if [ "$status" != 0 ]; then
  echo "Attacker runner exited with $status; inspect results/${case_name}-attacker.log" >&2
  exit 1
fi

python3 - "$mode" "$case_name" <<'PY'
import json
from pathlib import Path
import sys

mode, case = sys.argv[1:]
root = Path('results')
data = {}
for role in ('legitimate', 'attacker'):
    path = root / f'{case}-{role}.json'
    data[role] = json.loads(path.read_text())
    print(f'{role}: {json.dumps(data[role], sort_keys=True)}')
    print(f'  saved: {path}')

attacker_echo = data['attacker']['echoed_attacker_marker_packets']
legitimate_echo = data['legitimate']['echoed_legitimate_marker_packets']
if mode == 'after-configured':
    good = attacker_echo == 0 and legitimate_echo > 0
else:
    good = attacker_echo > 0 and legitimate_echo == 0
if not good:
    raise SystemExit(f'Unexpected {mode} result; inspect the JSON and target log before drawing conclusions')
print(f'Expected {mode} marker outcome observed')
PY
