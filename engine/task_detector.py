# ~/ArcheTYPE/engine/task_detector.py
from typing import Dict, List, Optional
import re

PRODUCTIVE_KEYWORDS = [
    "vscode", "visual studio code", "pycharm", "clion", "code", ".py", ".c", ".cpp", ".rs",
    "terminal", "tilix", "konsole", "alacritty", "gnome-terminal", "kitty", "bash", "zsh",
    "vim", "nvim", "emacs", "jetbrains", "cargo", "make", "cmake", "git"
]

RESEARCH_KEYWORDS = ["chrome", "firefox", "brave", "edge", "duckduckgo", "browser", "research"]
ENTERTAINMENT_KEYWORDS = ["youtube", "netflix", "prime video", "spotify", "twitch"]
CHAT_KEYWORDS = ["whatsapp", "telegram", "signal", "discord", "slack", "messenger"]
DEVOPS_KEYWORDS = ["docker", "podman", "kubernetes", "kubectl", "helm"]

def _lower(s: Optional[str]) -> str:
    return (s or "").lower()

def detect_task_from_window(title: str) -> Dict:
    t = _lower(title)
    # quick heuristics
    if any(k in t for k in PRODUCTIVE_KEYWORDS):
        return {"task_type": "coding", "task_confidence": 0.9, "source": "window_title"}
    if any(k in t for k in RESEARCH_KEYWORDS):
        return {"task_type": "research", "task_confidence": 0.85, "source": "window_title"}
    if any(k in t for k in ENTERTAINMENT_KEYWORDS):
        return {"task_type": "entertainment", "task_confidence": 0.95, "source": "window_title"}
    if any(k in t for k in CHAT_KEYWORDS):
        return {"task_type": "communication", "task_confidence": 0.9, "source": "window_title"}

    # fallback: try to parse file names (e.g. agent_core.py - ArcheTYPE - Visual Studio Code)
    m = re.search(r"([-\w\.]+\.py|[-\w\.]+\.c|[-\w\.]+\.cpp|[-\w\.]+\.rs)", title, re.I)
    if m:
        fname = m.group(1)
        ext = fname.split(".")[-1].lower()
        if ext in ("py", "c", "cpp", "rs"):
            return {"task_type": "coding", "task_confidence": 0.9, "source": "filename", "filename": fname}

    return {"task_type": "unknown", "task_confidence": 0.2, "source": "window_title"}

def detect_task_from_processes(processes: List[Dict]) -> Dict:
    # processes is expected to be list of dicts with 'name' and 'cmd'
    names = " ".join((p.get("name","") + " " + p.get("cmd","")) for p in processes).lower()
    if any(k in names for k in PRODUCTIVE_KEYWORDS):
        return {"task_type": "coding", "task_confidence": 0.8, "source": "processes"}
    if any(k in names for k in DEVOPS_KEYWORDS):
        return {"task_type": "devops", "task_confidence": 0.9, "source": "processes"}
    if any(k in names for k in CHAT_KEYWORDS):
        return {"task_type": "communication", "task_confidence": 0.9, "source": "processes"}
    if any(k in names for k in ENTERTAINMENT_KEYWORDS):
        return {"task_type": "entertainment", "task_confidence": 0.95, "source": "processes"}
    return {"task_type": "unknown", "task_confidence": 0.1, "source": "processes"}

def detect_task(observation: Dict) -> Dict:
    """
    observation: { 'active_window': str, 'processes': [ {name, cmd, pid}, ... ] }
    returns: task dict -> { task_type, task_confidence, source, ... }
    """
    win = observation.get("active_window", "") or ""
    procs = observation.get("processes", []) or []
    win_det = detect_task_from_window(win)
    proc_det = detect_task_from_processes(procs)

    # choose the more confident
    if win_det["task_confidence"] >= proc_det["task_confidence"]:
        result = win_det
    else:
        result = proc_det

    # If both agree and are productive, boost confidence
    if win_det["task_type"] == proc_det["task_type"] and win_det["task_type"] in ("coding", "devops", "research"):
        result["task_confidence"] = min(1.0, result["task_confidence"] + 0.1)
        result["source"] = "merged"

    return result
