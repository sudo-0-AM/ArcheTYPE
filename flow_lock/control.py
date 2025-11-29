#!/usr/bin/env python3
"""
flow_lock/control.py

CLI + Python API to control Flow Lock daemon.
Usage (CLI):
  archetype lock on
  archetype lock off
  archetype lock status
  archetype lock profile coding
Python API:
  from flow_lock.control import set_lock, set_profile, get_status
"""

import os
import sys
import subprocess
import json
from datetime import datetime

BASE = os.path.expanduser("~/ArcheTYPE/flow_lock")
STATE_PATH = os.path.join(BASE, "state.json")
LOG = os.path.join(BASE, "control.log")

def _ensure_dirs():
    os.makedirs(BASE, exist_ok=True)
    if not os.path.exists(STATE_PATH):
        default = {
            "idle_limit_minutes": 15,

            "blacklist": [
                "youtube", "tiktok", "instagram", "steam",
                "vlc", "music", "games"
            ],

            "whitelist": [
                "firefox", "code", "konsole", "journal", "notes", "okular"
            ],

            "score_reward": 3,
            "score_penalty": 5,

            "score_reward_mult": 0.8,
            "score_penalty_mult": 1.0,

            "xp_mult": 1.0
        }
        with open(STATE_PATH, "w", encoding="utf-8") as fh:
            json.dump(default, fh, indent=2)

def read_state():
    _ensure_dirs()
    try:
        return json.load(open(STATE_PATH, "r", encoding="utf-8"))
    except Exception:
        return {}

def write_state(state):
    state["last_update"] = int(datetime.now().timestamp())
    with open(STATE_PATH, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2)

def log(msg):
    ts = datetime.now().isoformat()
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(f"{ts} {msg}\n")
    print(msg)

# ---- Public API ----
def set_lock(enabled: bool):
    state = read_state()
    state["lock_enabled"] = bool(enabled)
    write_state(state)
    log(f"Flow Lock set to {'ON' if enabled else 'OFF'}")
    return state

# ---- Public API ----
def set_profile(profile_name: str):
    state = read_state()
    state["current_profile"] = profile_name
    write_state(state)
    log(f"Profile changed -> {profile_name}")

    # Force venv Python
    VENV_PY = os.path.expanduser("~/ArcheTYPE/venv/bin/python3")
    INTENT = os.path.expanduser("~/ArcheTYPE/archetype_intent.py")

    try:
        subprocess.Popen([VENV_PY, INTENT, f"prepare {profile_name} mode"])
    except Exception as e:
        log(f"[intent error] {e}")

    return state



def get_status():
    st = read_state()
    return st

# ---- CLI ----
def _usage():
    print("Usage: archetype lock on|off|status|profile <name>")
    sys.exit(1)

def main(argv):
    _ensure_dirs()
    if len(argv) < 2:
        _usage()

    cmd = argv[0]
    if cmd != "lock":
        _usage()

    sub = argv[1] if len(argv) > 1 else None
    if sub in ("on", "enable"):
        st = set_lock(True)
        print("OK")
    elif sub in ("off", "disable"):
        st = set_lock(False)
        print("OK")
    elif sub == "status":
        st = get_status()
        print(json.dumps(st, indent=2))
    elif sub == "profile":
        if len(argv) < 3:
            print("profile <name>")
            return
        name = argv[2]
        st = set_profile(name)
        print("OK")
    elif sub == "score":
        from score_dashboard import score_dashboard
        print(score_dashboard())
        return
    else:
        _usage()

if __name__ == "__main__":
    main(sys.argv[1:])
