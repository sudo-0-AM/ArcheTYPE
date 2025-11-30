#!/usr/bin/env python3

import os
import json
import faiss
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

# Load config
CFG = json.load(open('/home/piyush/ArcheTYPE/config.json'))
OUTDIR = Path(os.path.expanduser(CFG['distill_dir']))
FAISS_PATH = Path(os.path.expanduser(CFG['faiss_index']))

def build_index():
    # Ensure distill directory exists
    OUTDIR.mkdir(parents=True, exist_ok=True)

    pairs_file = OUTDIR / "supervised_pairs.jsonl"
    if not pairs_file.exists():
        print("No supervised_pairs.jsonl found — nothing to index.")
        return

    texts = []
    with open(pairs_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                obj = json.loads(line)
                prompt = obj.get("prompt", "").strip()
                resp = obj.get("response", "").strip()
                if prompt and resp:
                    texts.append(prompt + " -> " + resp)
            except:
                continue

    if len(texts) == 0:
        print("No valid pairs found — skipping FAISS index build.")
        return

    print(f"[retriever] Loaded {len(texts)} distilled examples.")

    # Load embedding model
    try:
        model = SentenceTransformer("all-MiniLM-L6-v2")
    except Exception as e:
        print("[retriever] ERROR loading embedding model:", e)
        return

    # Encode all pairs
    print("[retriever] Encoding embeddings...")
    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        convert_to_numpy=True
    )

    # Build FAISS index
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    # Save FAISS index
    FAISS_PATH.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(FAISS_PATH))

    # Save index_texts.json
    out_texts = OUTDIR / "index_texts.json"
    json.dump(texts, open(out_texts, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print(f"[retriever] FAISS index built! {len(texts)} entries")
    print(f"[retriever] Saved to {FAISS_PATH}")
    print(f"[retriever] Saved text map to {out_texts}")

def main():
    build_index()

if __name__ == "__main__":
    main()
