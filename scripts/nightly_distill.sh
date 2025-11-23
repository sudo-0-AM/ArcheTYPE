#!/usr/bin/env bash
# ~/ArcheTYPE/scripts/nightly_distill.sh
# Nightly distillation script with correct persona path

set -euo pipefail

PROJ="$HOME/ArcheTYPE"
VENV="$PROJ/venv"
LOG_DIR="$PROJ/archetype_logs"
RUN_LOG="$LOG_DIR/nightly-distill-$(date +%F).log"
LOCKFILE="/tmp/archetype_nightly_distill.lock"
DISTILL_PY="$PROJ/distill.py"
RETRIEVER_PY="$PROJ/retriever.py"

# Correct persona path (your actual file)
PERSONA_PATH="$PROJ/system_prompt.txt"

mkdir -p "$LOG_DIR"

# Lockfile for safety
if [ -e "$LOCKFILE" ]; then
  echo "$(date -Iseconds) - another run is in progress. Exiting." >> "$RUN_LOG"
  exit 0
fi

trap 'rm -f "$LOCKFILE"' EXIT
touch "$LOCKFILE"

echo "=== ArcheTYPE nightly distill started: $(date -Iseconds) ===" >> "$RUN_LOG"

# Health checks
if [ ! -d "$PROJ" ]; then
  echo "Project dir missing: $PROJ" >> "$RUN_LOG"
  exit 1
fi

if [ ! -f "$DISTILL_PY" ]; then
  echo "distill.py not found at $DISTILL_PY" >> "$RUN_LOG"
  exit 1
fi

if [ ! -f "$RETRIEVER_PY" ]; then
  echo "retriever.py not found at $RETRIEVER_PY" >> "$RUN_LOG"
  exit 1
fi

# Activate venv if available
if [ -d "$VENV" ]; then
  source "$VENV/bin/activate"
else
  echo "Virtualenv not found at $VENV" >> "$RUN_LOG"
fi

# Persona debug check (now correct)
if [ -f "$PERSONA_PATH" ]; then
  echo "Persona present at $PERSONA_PATH" >> "$RUN_LOG"
else
  echo "WARNING: Persona NOT found at $PERSONA_PATH" >> "$RUN_LOG"
fi

# Run distill
echo "Running distill.py ..." >> "$RUN_LOG"
( cd "$PROJ" && python3 "$DISTILL_PY" >> "$RUN_LOG" 2>&1 )

# Run retriever
echo "Running retriever.py ..." >> "$RUN_LOG"
( cd "$PROJ" && python3 "$RETRIEVER_PY" >> "$RUN_LOG" 2>&1 )

echo "=== ArcheTYPE nightly distill finished: $(date -Iseconds) ===" >> "$RUN_LOG"
echo "" >> "$RUN_LOG"