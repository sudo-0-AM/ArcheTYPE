#!/usr/bin/env python3
import os, sys, time, json, psutil, subprocess, traceback
from datetime import datetime, date

# Ensure root import
ROOT = os.path.expanduser("~/ArcheTYPE")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from router import archetype_respond

BASE = os.path.expanduser("~/ArcheTYPE/flow_lock")
STATE = os.path.join(BASE, "state.json")
PROFILES_DIR = os.path.join(BASE, "profiles")
LOG = os.path.join(BASE, "flow_lock.log")
CHECK_INTERVAL = 3

def log(msg):
    line = f"{datetime.now().isoformat()} {msg}"
    print(line)
    with open(LOG, "a") as f:
        f.write(line + "\n")

def read_json(path):
    try:
        return json.load(open(path))
    except:
        return None

def read_state():
    st = read_json(STATE)
    if not st:
        st = {
            "lock_enabled": False,
            "current_profile": "strict",
            "daily_score": 0,
            "last_score_date": str(date.today())
        }
    return st

def write_state(st):
    json.dump(st, open(STATE, "w"), indent=2)

def load_profile(name):
    p = os.path.join(PROFILES_DIR, f"{name}.json")
    return read_json(p) or {}

def get_idle_ms():
    try:
        import dbus
        bus = dbus.SessionBus()
        obj = bus.get_object("org.kde.KWin", "/org/kde/KWin/IdleTime")
        props = dbus.Interface(obj, "org.freedesktop.DBus.Properties")
        return int(props.Get("org.kde.KWin.IdleTime", "IdleTime"))
    except:
        return 0

def add_score(st, amount):
    today = str(date.today())
    if st["last_score_date"] != today:
        st["last_score_date"] = today
        st["daily_score"] = 0
    st["daily_score"] += amount
    write_state(st)
    log(f"Score +{amount:.2f} (total={st['daily_score']:.2f})")

def enforce(profile):
    bl = [x.lower() for x in profile.get("blacklist", [])]
    wl = [x.lower() for x in profile.get("whitelist", [])]
    violations = []
    for p in psutil.process_iter(["name", "cmdline", "pid"]):
        name = (p.info["name"] or "").lower()
        cmd = " ".join(p.info["cmdline"] or []).lower()
        if not name:
            continue
        if any(w in name or w in cmd for w in wl):
            continue
        if any(b in name or b in cmd for b in bl):
            violations.append((name, p.pid))
            try:
                p.kill()
            except:
                pass
    return violations

def flow_lock():
    log("Flow Lock daemon starting.")
    last_profile = None

    while True:
        st = read_state()
        if not st.get("lock_enabled"):
            time.sleep(CHECK_INTERVAL)
            continue

        profname = st.get("current_profile", "strict")
        if profname != last_profile:
            log(f"Using profile: {profname}")
            last_profile = profname

        profile = load_profile(profname)

        # Idle
        idle_ms = get_idle_ms()
        limit = profile.get("idle_limit_minutes", 10)
        if idle_ms >= limit * 60000:
            log("Idle detected")
            resp = archetype_respond(f"Idle for {limit} minutes under profile {profname}.")
            log("Correction: " + resp)
            time.sleep(20)
            continue

        # Violations
        vio = enforce(profile)
        if vio:
            for name, pid in vio:
                log(f"Violation: {name} (pid={pid})")
                resp = archetype_respond(f"Tried opening {name}.")
                log("Correction: " + resp)
                st = read_state()
                add_score(st, -abs(profile.get("score_penalty", 10)))
            time.sleep(3)
            continue

        # Reward
        st = read_state()
        reward = profile.get("score_reward", 5)
        add_score(st, reward * (CHECK_INTERVAL / 60))
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    flow_lock()
