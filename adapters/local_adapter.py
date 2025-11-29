# adapters/local_adapter.py
"""
Local adapter for llama-run (your version).
- Combined raw prompt (persona + rules + examples + user).
- No system-prompt arguments (unsupported).
- No chat template mode.
- Clean output.
"""

import os
import json
import shlex
import subprocess
from pathlib import Path

# Load config
CFG = json.load(open("/home/piyush/ArcheTYPE/config.json"))

# Use llama-run for raw generation
BINARY = Path(os.path.expanduser("~/ArcheTYPE/llama.cpp/build/bin/llama-run"))


# Distillation / retrieval files
DISTILL_DIR = os.path.expanduser(CFG.get("distill_dir"))
INDEX_TEXTS_PATH = os.path.join(DISTILL_DIR, "index_texts.json")
FAISS_INDEX_PATH = os.path.expanduser(CFG.get("faiss_index"))


def _load_index_texts():
    if not os.path.exists(INDEX_TEXTS_PATH):
        return []
    try:
        return json.load(open(INDEX_TEXTS_PATH, "r", encoding="utf-8"))
    except:
        return []


def _faiss_search(query, k=3):
    try:
        import faiss
        from sentence_transformers import SentenceTransformer
        texts = _load_index_texts()
        if not texts:
            return []
        model = SentenceTransformer("all-MiniLM-L6-v2")
        q = model.encode([query], convert_to_numpy=True)
        idx = faiss.read_index(FAISS_INDEX_PATH)
        D, I = idx.search(q, k)
        return [texts[i] for i in I[0] if 0 <= i < len(texts)]
    except:
        return []


def search_topk(query, k=3):
    if os.path.exists(FAISS_INDEX_PATH):
        r = _faiss_search(query, k)
        if r:
            return r
    texts = _load_index_texts()
    return texts[-k:][::-1] if texts else []


def _build_combined_prompt(persona, examples, user_text):
    """Build ONE combined prompt. Clean. Raw. No SYSTEM, no chat template."""

    strict = (
        "Respond EXACTLY with:\n"
        "DIAGNOSIS: <one-sentence diagnosis>\n"
        "ACTION: <one timeboxed action>\n"
        "METRIC: <one measurable metric>\n"
        "(Total <= 60 words)\n\n"
    )

    fs = []
    for ex in examples:
        if " -> " in ex:
            p, r = ex.split(" -> ", 1)
            fs.append("EXAMPLE PROMPT: " + p.strip())
            fs.append("TEACHER: " + r.strip())
        else:
            fs.append("EXAMPLE: " + ex.strip())

    few_shot = "\n".join(fs) if fs else ""

    combined = (
        persona.strip()
        + "\n\n"
        + strict
        + (few_shot + "\n\n" if few_shot else "")
        + "USER:\n"
        + user_text.strip()
    )

    return combined.strip()


def call_local_model(user_text, model_key="local_fast"):
    model_path = CFG["models"].get(model_key)
    if not model_path:
        return "[local adapter] Model path missing."

    model_path = os.path.expanduser(model_path)
    if not os.path.exists(model_path):
        return f"[local adapter] Model not found: {model_path}"

    # Load persona
    persona_src = os.path.expanduser(CFG.get("persona_source"))
    try:
        persona = open(persona_src, "r", encoding="utf-8").read()
    except Exception as e:
        persona = f"ArcheTYPE persona missing: {e}"

    # Retrieval
    examples = search_topk(user_text, k=3)

    # Build final combined prompt
    prompt = _build_combined_prompt(persona, examples, user_text)

    # Run llama-run
    cmd = (
        f"{shlex.quote(str(BINARY))} "
        f"--threads 10"
        f"--temp 0.2 "
        f"{shlex.quote(model_path)} "
        f"{shlex.quote(prompt)}"
    )

    try:
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        if proc.returncode != 0:
            return f"[local adapter error] {proc.stderr}"
        return proc.stdout.strip()
    except Exception as e:
        return f"[local adapter error] {e}"
