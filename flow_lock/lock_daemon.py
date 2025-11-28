#!/usr/bin/env python3
import os, sys, time, json, psutil, subprocess
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

    # daily reset
    if st.get("last_score_date") != today:
        st["last_score_date"] = today
        st["daily_score"] = 0

    # update score
    st["daily_score"] += amount
    # XP gain (always positive)
    xp_gain = max(amount, 0)
    st["total_xp"] = st.get("total_xp", 0) + xp_gain
    # Level formula
    st["level"] = int((st["total_xp"] ** 0.5) * 2.5)

    write_state(st)
    log(f"Score +{amount:.2f} (total={st['daily_score']:.2f}), XP +{xp_gain:.2f}, Level={st['level']}")


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

def notify(title, body):
    try:
        subprocess.Popen(["notify-send", title, body])
    except:
        pass


def flow_lock():
    log("Flow Lock daemon starting.")
    last_profile = None
    last_notification = 0
    NOTIFY_INTERVAL = 20 * 60  # 20 minutes


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

        # Notification every 20 minutes
        now = time.time()
        if now - last_notification >= NOTIFY_INTERVAL:
            st2 = read_state()
            level = st2.get("level", 0)
            xp = round(st2.get("total_xp", 0), 2)
            score = round(st2.get("daily_score", 0), 2)

            notify("FlowScore Update",
                f"Level: F{level} | XP: {xp} | Score: {score}\nStay aligned.")
            last_notification = now


if __name__ == "__main__":
    flow_lock()
