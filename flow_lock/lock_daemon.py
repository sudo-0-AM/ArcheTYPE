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
CHECK_INTERVAL = 3

# ------------------------------
# CLEAN LOG: PRINT ONLY
# ------------------------------
def log(msg):
    line = f"{datetime.now().isoformat()} {msg}"
    print(line)   # systemd will log this automatically

# ------------------------------

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
            "last_score_date": str(date.today()),
            "total_xp": 0,
            "level": 0
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


# --------------------------------------------------
# SCORE + XP ENGINE
# --------------------------------------------------
def add_score(st, amount, profile):
    today = str(date.today())

    # daily reset
    if st.get("last_score_date") != today:
        st["last_score_date"] = today
        st["daily_score"] = 0

    reward_mult = profile.get("score_reward_mult", 1.0)
    xp_mult = profile.get("xp_mult", 1.0)
    penalty_mult = profile.get("score_penalty_mult", 1.0)

    # SCORE update
    if amount >= 0:
        st["daily_score"] += amount * reward_mult
    else:
        st["daily_score"] += amount * penalty_mult

    # XP update
    if amount > 0:
        streak = st.get("streak_seconds", 0)
        if streak < 300:
            streak_mult = 1.0
        elif streak < 1200:
            streak_mult = 1.2
        elif streak < 3600:
            streak_mult = 1.5
        else:
            streak_mult = 2.0

        xp_gain = amount * xp_mult * streak_mult
    else:
        xp_gain = amount * 0.2

    st["total_xp"] = max(0, st.get("total_xp", 0) + xp_gain)

    # Level formula
    st["level"] = int((st["total_xp"] ** 0.15))

    write_state(st)

    log(
        f"Score +{amount:.3f} → {st['daily_score']:.2f}, "
        f"XP +{xp_gain:.3f} → {st['total_xp']:.2f}, "
        f"Level F{st['level']}"
    )


# --------------------------------------------------
# ENFORCE RULES
# --------------------------------------------------
def enforce(profile):
    blacklist = [x.lower() for x in profile.get("blacklist", [])]
    whitelist = [x.lower() for x in profile.get("whitelist", [])]
    violations = []

    for p in psutil.process_iter(["name", "cmdline", "pid"]):
        name = (p.info["name"] or "").lower()
        cmd = " ".join(p.info["cmdline"] or []).lower()

        if not name:
            continue

        if any(w in name or w in cmd for w in whitelist):
            continue

        if any(b in name or b in cmd for b in blacklist):
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


# --------------------------------------------------
# MAIN LOOP
# --------------------------------------------------
def flow_lock():
    log("Flow Lock daemon starting.")
    last_profile = None
    last_notification = 0
    NOTIFY_INTERVAL = 20 * 60

    while True:
        st = read_state()

        if not st.get("lock_enabled"):
            last_profile = None   # reset
            time.sleep(CHECK_INTERVAL)
            continue

        # NEW: trigger intents when entering a profile for the first time
        if st.get("current_profile") != last_profile:
            last_profile = st.get("current_profile")
            try:
                subprocess.Popen([
                    "/usr/bin/python3",
                    os.path.expanduser("~/ArcheTYPE/archetype_intent.py"),
                    f"prepare {last_profile} mode"
                ])
                log(f"Intent triggered for profile {last_profile}")
            except Exception as e:
                log(f"[intent error] {e}")


        profname = st.get("current_profile", "strict")
        if profname != last_profile:
            log(f"Using profile → {profname}")
            last_profile = profname

        profile = load_profile(profname)

        # Idle correction
        idle_ms = get_idle_ms()
        if idle_ms >= profile.get("idle_limit_minutes", 10) * 60000:
            log("Idle detected.")
            resp = archetype_respond(f"Idle detected under profile {profname}.")
            log("Correction: " + resp)
            time.sleep(20)
            continue

        # Violations
        vio = enforce(profile)
        if vio:
            for name, pid in vio:
                notify("Violation", f"Killed: {name}")
                log(f"Violation: {name} (pid={pid})")
                st = read_state()
                add_score(st, -abs(profile.get("score_penalty", 10)), profile)
            time.sleep(3)
            continue

        # Reward
        st = read_state()
        reward = profile.get("score_reward", 5)
        add_score(st, reward * (CHECK_INTERVAL / 60), profile)

        time.sleep(CHECK_INTERVAL)

        # Periodic feedback
        now = time.time()
        if now - last_notification >= NOTIFY_INTERVAL:
            st2 = read_state()
            notify(
                "FlowScore",
                f"Level F{st2['level']} | XP {round(st2['total_xp'],2)} | Score {round(st2['daily_score'],2)}"
            )
            last_notification = now


if __name__ == "__main__":
    flow_lock()
