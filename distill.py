# distill.py
import json, os, glob
from pathlib import Path
CFG = json.load(open('config.json'))
LOGDIR = Path(os.path.expanduser(CFG['log_dir']))
OUTDIR = Path(os.path.expanduser(CFG['distill_dir']))
OUTDIR.mkdir(parents=True, exist_ok=True)

def build_dataset():
    files = sorted(LOGDIR.glob("*.jsonl"))
    pairs = []
    for f in files:
        for line in open(f, encoding='utf-8'):
            try:
                e = json.loads(line)
                user = e.get('user')
                resp = e.get('response')
                engine = e.get('engine')
                if user and resp and engine == 'online':
                    # keep only teacher examples
                    pairs.append({'prompt': user, 'response': resp})
            except:
                pass
    # write newline-separated JSON pairs
    out = OUTDIR / "supervised_pairs.jsonl"
    with open(out, 'w', encoding='utf-8') as fh:
        for p in pairs:
            fh.write(json.dumps(p, ensure_ascii=False) + "\\n")
    print(f"Saved {len(pairs)} pairs to {out}")

if __name__ == '__main__':
    build_dataset()
