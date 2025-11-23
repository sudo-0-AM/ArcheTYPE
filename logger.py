# logger.py
import json, os, time
from pathlib import Path
CFG = json.load(open('config.json'))
LOGDIR = Path(os.path.expanduser(CFG['log_dir']))
LOGDIR.mkdir(parents=True, exist_ok=True)

def log_interaction(entry):
    ts = int(time.time()*1000)
    fname = LOGDIR / f"{ts}.jsonl"
    # append line
    with open(fname, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\\n")
