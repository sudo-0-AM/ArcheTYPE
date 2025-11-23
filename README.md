# ArcheTYPE Core (initial seed)

This folder contains the first-step implementation artifacts for ArcheTYPE, created by ArcheTYPE itself.

Files:
- system_prompt.txt  : Combined SYSTEM persona and embedded uploaded README (source: /mnt/data/README.txt)
- rules_engine.py    : Simple rule-based decision engine
- archetype_cli.py   : Minimal CLI wrapper using the rules engine and a local deterministic responder
- config.json        : Basic configuration referencing the uploaded README path
- memory.json        : Seeded memory with initial user goals

How to run (Linux):
1. cd /mnt/data/archetype_core
2. python3 archetype_cli.py "I'm stuck on X"
3. Inspect memory.json for last_interaction.

Notes:
- This is the first engineering step: a deterministic local core that enforces ArcheTYPE persona constraints.
- Next step is LLM integration and wake-word hooking (Vosk/ORBIT was discarded per user).
