#!/usr/bin/env python3
"""archetype_cli.py
Minimal ArcheTYPE CLI. Uses rules_engine to decide mode and build a prompt.
Currently, includes a local deterministic responder for offline testing.
Replace `local_response` with LLM call when integrating with OpenAI/OpenRouter/local LLM.

Usage:
    python3 archetype_cli.py "I'm stuck on implementing linked lists"
"""

import sys, json, os
from pathlib import Path
from rules_engine import decide_mode, build_prompt, detect_drift

BASE = Path(__file__).resolve().parent
SYSTEM_PROMPT_FILE = BASE / 'system_prompt.txt'

def local_response(mode, user_text):
    """A deterministic local response generator for first-step development.
    It follows ArcheTYPE constraints: diagnosis, one action, one metric.
    """
    user_l = user_text.strip()
    # Simple heuristics to craft a terse reply
    if detect_drift(user_l):
        diagnosis = "You're spread thin and pretending progress equals activity."
        action = "Drop all but the single task that moves income or skill forward. 90 minutes focused work now."
        metric = "Produce 1 commit / 1 solved problem or 500 words of progress."
    else:
        diagnosis = "Clarity lacking—prioritise ruthlessly."
        action = "Pick the highest-impact task; timebox 60-90 minutes; report exact output."
        metric = "Deliver one measurable artifact: commit, screenshot, or countable result."
    # Short formatted output
    return f"DIAGNOSIS: {diagnosis}\nACTION: {action}\nMETRIC: {metric}"

def main():
    user_text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else input("You: ")
    system_prompt_text = SYSTEM_PROMPT_FILE.read_text(encoding='utf-8', errors='ignore') if SYSTEM_PROMPT_FILE.exists() else ""
    mode = decide_mode(user_text, context=None)
    prompt = build_prompt(mode, user_text, system_prompt_text)
    print("\n--- ArcheTYPE (local mode) ---\n")
    print(f"MODE: {mode}\n")
    # For first-step development we use local deterministic response
    reply = local_response(mode, user_text)
    print(reply)
    # Store last interaction summary to memory.json
    memory_file = BASE / 'memory.json'
    memory = {}
    if memory_file.exists():
        try:
            memory = json.loads(memory_file.read_text(encoding='utf-8'))
        except Exception:
            memory = {}
    memory['last_interaction'] = {'user': user_text, 'mode': mode, 'reply': reply}
    memory_file.write_text(json.dumps(memory, indent=2), encoding='utf-8')

if __name__ == '__main__':
    main()
