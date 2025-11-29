# retriever.py
from sentence_transformers import SentenceTransformer
import faiss, numpy as np, json, os
from pathlib import Path
CFG = json.load(open('/home/piyush/ArcheTYPE/config.json'))
OUTDIR = Path(os.path.expanduser(CFG['distill_dir']))
model = SentenceTransformer('all-MiniLM-L6-v2')  # small CPU-friendly

def build_index():
    pairs_file = OUTDIR / "supervised_pairs.jsonl"
    texts = []
    with open(pairs_file, 'r', encoding='utf-8') as f:
        for line in f:
            obj = json.loads(line)
            texts.append(obj['prompt'] + " -> " + obj['response'])
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    faiss.write_index(index, str(Path(CFG['faiss_index']).expanduser()))
    # save texts
    with open(OUTDIR / "index_texts.json", 'w', encoding='utf-8') as fh:
        json.dump(texts, fh, ensure_ascii=False)
    print("Built faiss index with", len(texts), "entries")
