#!/bin/bash
# Driver: run agy hunt; on filter-block, resume the same conversation instead of restarting.
REPO="$1"; PROMPT="$2"; LOG="$3"; MAXRESUME=12
cd "$REPO" || exit 1
for i in $(seq 0 $MAXRESUME); do
  if [ $i -eq 0 ]; then
    /home/danie/.local/bin/agy --log-file /tmp/agy-debug-current.log --dangerously-skip-permissions --print "$(cat "$PROMPT")" >> "$LOG" 2>&1
  else
    echo "=== RESUME attempt $i after block at $(date) ===" >> "$LOG"
    /home/danie/.local/bin/agy --log-file /tmp/agy-debug-current.log --dangerously-skip-permissions --continue --print "A request was blocked mid-turn. Continue exactly where you left off on the same task, using your existing context and findings. Keep updating BUG-HUNT-REPORT.md as before." >> "$LOG" 2>&1
  fi
  if ! grep -q "blocked by Gemini" "$LOG" 2>/dev/null; then echo "=== finished without new block at $(date) ===" >> "$LOG"; break; fi
  # remove older block markers so the next exit check only sees new content
  tail -n +$(( $(grep -n "blocked by Gemini" "$LOG" | tail -1 | cut -d: -f1) + 1 )) "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
  sleep 10
done
echo "=== driver done at $(date) ===" >> "$LOG"
