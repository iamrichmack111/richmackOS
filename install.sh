#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
BASE="$HOME/.richmackos"
BIN="$HOME/.local/bin"
UNIT="$HOME/.config/systemd/user"
mkdir -p "$BASE" "$BIN" "$UNIT" "$BASE/skills" "$BASE/plugins"
for f in richmackos.py organize.py watcher.py watchctl youtube_cmd youtube.py youtube_ask.py youtube_chat.py youtube_chat_v2.py youtube_knowledge.py youtube_research.py youtube_summarize.py rebuild_research_md.py rag_cmd rag_scope.py; do
  [ -e "$ROOT/$f" ] && install -m 0755 "$ROOT/$f" "$BASE/$f"
done
[ -d "$ROOT/rag" ] && cp -a "$ROOT/rag" "$BASE/"
[ -d "$ROOT/plugins" ] && cp -a "$ROOT/plugins/." "$BASE/plugins/"
[ -f "$ROOT/youtube-channels.json" ] && cp -n "$ROOT/youtube-channels.json" "$BASE/youtube-channels.json" || true
for f in richmack richmackai richmackrag; do
  [ -e "$ROOT/bin/$f" ] && install -m 0755 "$ROOT/bin/$f" "$BIN/$f"
done
sed "s#%h#$HOME#g" "$ROOT/systemd/richmack-watch.service" > "$UNIT/richmack-watch.service"
if command -v systemctl >/dev/null 2>&1; then systemctl --user daemon-reload || true; fi
echo "RichmackOS v0.6.0 installed."
echo "Add $BIN to PATH if needed: export PATH=\"$BIN:\$PATH\""
echo "Try: richmack version && richmack doctor"
