# ~/ArcheTYPE/engine/task_memory.py
import json, os
from datetime import datetime, timedelta
from typing import Optional, Dict

MEM_PATH = os.path.expanduser("~/ArcheTYPE/agent_task_memory.json")
DEFAULT = {
    "current_task": None,
    "task_start": None,
    "last_seen": None,
    "history": []
}
MAX_HISTORY = 200

def _now_iso():
    return datetime.now().isoformat()

def load_memory() -> Dict:
    try:
        return json.load(open(MEM_PATH, "r", encoding="utf-8"))
    except Exception:
        return DEFAULT.copy()

def save_memory(mem: Dict):
    os.makedirs(os.path.dirname(MEM_PATH), exist_ok=True)
    json.dump(mem, open(MEM_PATH, "w", encoding="utf-8"), indent=2)

def update_task(task: Dict):
    mem = load_memory()
    now = _now_iso()
    cur = mem.get("current_task")
    if not cur or cur.get("task_type") != task.get("task_type"):
        # push previous to history if exists
        if cur:
            mem.setdefault("history", []).append({
                "task": cur,
                "start": mem.get("task_start"),
                "end": now
            })
            # trim
            mem["history"] = mem["history"][-MAX_HISTORY:]
        mem["current_task"] = task
        mem["task_start"] = now
    mem["last_seen"] = now
    save_memory(mem)
    return mem

def get_current_task() -> Optional[Dict]:
    mem = load_memory()
    return mem.get("current_task")

def reset_task():
    mem = load_memory()
    if mem.get("current_task"):
        mem.setdefault("history", []).append({
            "task": mem.get("current_task"),
            "start": mem.get("task_start"),
            "end": _now_iso()
        })
    mem["current_task"] = None
    mem["task_start"] = None
    mem["last_seen"] = _now_iso()
    save_memory(mem)
    return mem
