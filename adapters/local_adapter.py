# adapters/local_adapter.py
import subprocess, json, shlex
CFG = json.load(open('config.json'))
from pathlib import Path

def _run_llama_cpp(model_path, prompt):
    # adjust binary path if needed: ./main or ./llama
    binary = Path('llama.cpp') / 'main'  # adjust if you built elsewhere
    if not binary.exists():
        # fallback to plain error
        return "[local adapter] llama.cpp binary not found at " + str(binary)
    cmd = f"{binary} -m {shlex.quote(model_path)} -p {shlex.quote(prompt)} --n_predict 256"
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        return "[local adapter error] " + proc.stderr[:800]
    return proc.stdout

def call_local_model(user_text, model_key='local_fast'):
    path = CFG['models'].get(model_key)
    if not path:
        return "[local adapter] model path not set in config"
    persona = open(CFG['persona_source']).read()
    prompt = f"SYSTEM:{persona}\\nUSER:{user_text}\\nRespond as ArcheTYPE: diagnosis, action, metric, <=60 words."
    return _run_llama_cpp(path, prompt)
