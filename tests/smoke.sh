#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
python3 -m py_compile "$ROOT"/*.py "$ROOT"/rag/*.py
for f in "$ROOT"/bin/* "$ROOT"/scripts/*.sh "$ROOT"/watchctl "$ROOT"/youtube_cmd "$ROOT"/rag_cmd "$ROOT"/install.sh; do
  [ -f "$f" ] && bash -n "$f"
done
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
HOME="$TMP" python3 "$ROOT/richmackos.py" --version | grep -q '0.6.0'
HOME="$TMP" python3 "$ROOT/richmackos.py" forget abc | grep -q 'integer'
HOME="$TMP" python3 "$ROOT/richmackos.py" search | grep -q 'Usage:'
HOME="$TMP" python3 "$ROOT/richmackos.py" skill add '../bad' 'echo bad' | grep -q 'only contain'
echo "RichmackOS smoke tests: PASS"
