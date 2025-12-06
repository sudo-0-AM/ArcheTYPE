#!/usr/bin/env bash
# ~/ArcheTYPE/scripts/nightly_distill.sh
# Nightly distillation (safe, silent, FAISS-aware)

set -euo pipefail

PROJ="$HOME/ArcheTYPE"
VENV="$PROJ/venv"
LOG_DIR="$PROJ/archetype_logs"
RUN_LOG="$LOG_DIR/nightly-distill-$(date +%F).log"
LOCKFILE="/tmp/archetype_nightly_distill.lock"
DISTILL_PY="$PROJ/distill.py"
RETRIEVER_PY="$PROJ/retriever.py"
PERSONA_PATH="$PROJ/system_prompt.txt"
FAISS_DIR="$(dirname $(readlink -f $PROJ/faiss.index))"

mkdir -p "$LOG_DIR"
mkdir -p "$FAISS_DIR"

# ---- LOCKFILE ----
if [ -e "$LOCKFILE" ]; then
  echo "$(date -Iseconds) - Another distill run already active. Skipping." >> "$RUN_LOG"
  exit 0
fi

trap 'rm -f "$LOCKFILE"' EXIT
touch "$LOCKFILE"

echo "=== NIGHTLY DISTILL START: $(date -Iseconds) ===" >> "$RUN_LOG"

# ---- HEALTH CHECKS ----
for f in "$DISTILL_PY" "$RETRIEVER_PY" "$PERSONA_PATH"; do
  if [ ! -f "$f" ]; then
    echo "[WARN] Missing file: $f" >> "$RUN_LOG"
  fi
done

# ---- VENV ----
if [ -d "$VENV" ]; then
  # avoid printing "deactivate" errors
  source "$VENV/bin/activate" >/dev/null 2>&1 || true
else
  echo "[WARN] venv missing, continuing with system python" >> "$RUN_LOG"
fi


# ---- RUN DISTILL ----
echo "[INFO] Running distill.py..." >> "$RUN_LOG"
cd "$PROJ"

python3 "$DISTILL_PY" >> "$RUN_LOG" 2>&1 || echo "[ERROR] distill failed!" >> "$RUN_LOG"

# If no pairs were saved, skip retriever
PAIR_FILE="$PROJ/distilled_dataset/supervised_pairs.jsonl"

if [ ! -s "$PAIR_FILE" ]; then
  echo "[WARN] No distilled pairs found, skipping FAISS rebuild." >> "$RUN_LOG"
  echo "=== NIGHTLY DISTILL END: $(date -Iseconds) ===" >> "$RUN_LOG"
  exit 0
fi

# ---- RUN RETRIEVER ----
echo "[INFO] Running retriever.py (FAISS rebuild)..." >> "$RUN_LOG"

python3 "$RETRIEVER_PY" >> "$RUN_LOG" 2>&1 || echo "[ERROR] retriever failed!" >> "$RUN_LOG"


echo "=== NIGHTLY DISTILL END: $(date -Iseconds) ===" >> "$RUN_LOG"
echo "" >> "$RUN_LOG"
