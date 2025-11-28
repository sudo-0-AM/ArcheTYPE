#!/usr/bin/env python3
import json
import time
import psutil
import os
import subprocess
from datetime import datetime
import sys

ROOT = os.path.expanduser("~/ArcheTYPE")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from router import archetype_respond

BASE = os.path.expanduser("~/ArcheTYPE/flow_lock")
LOG_FILE = os.path.join(BASE, "flow_lock.log")

def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} {msg}\n")
    print(msg)

def load_json(name):
    path = os.path.join(BASE, name)
    try:
        return json.load(open(path))
    except:
        return []

def notify(title, body):
    subprocess.Popen(["notify-send", title, body])

def kill_process(pid):
    try:
        psutil.Process(pid).kill()
    except:
        pass

def get_idle_ms():
    """Wayland KDE idle time via KWin's IdleTime interface."""
    try:
        import dbus
        bus = dbus.SessionBus()
        obj = bus.get_object("org.kde.KWin", "/org/kde/KWin/IdleTime")
        props = dbus.Interface(obj, "org.freedesktop.DBus.Properties")
        idle = props.Get("org.kde.KWin.IdleTime", "IdleTime")
        return int(idle)
    except Exception:
        return 0


def flow_lock_loop():
    log("Flow Lock Mode ACTIVE.")
    blacklist = load_json("blacklist.json")
    whitelist = load_json("whitelist.json")
    policy = load_json("policy.json")

    while True:
        try:
            # 1. Idle detection
            idle_ms = get_idle_ms()
            if idle_ms >= policy["idle_limit_minutes"] * 60 * 1000:
                if policy["correction_on_violation"]:
                    resp = archetype_respond(
                        f"I am idle for {policy['idle_limit_minutes']} minutes.",
                    )
                    log("IDLE Correction: " + resp.replace("\n", " | "))
                notify("ArcheTYPE — Idle", "Wake up.")
                time.sleep(20)
                continue

            # 2. Process scan
            for proc in psutil.process_iter(attrs=["pid", "name", "cmdline"]):
                name = proc.info["name"].lower()

                # Skip whitelisted
                if any(wl in name for wl in whitelist):
                    continue

                # Check blacklist
                if any(bl in name for bl in blacklist):
                    log(f"VIOLATION: {name} (pid={proc.pid}) → killed")

                    if policy["kill_distracting_immediately"]:
                        kill_process(proc.pid)

                    notify("ArcheTYPE Flow Lock", f"Blocked: {name}")

                    if policy["correction_on_violation"]:
                        resp = archetype_respond(
                            f"I attempted to open {name} during flow lock."
                        )
                        log("Correction: " + resp.replace("\n", " | "))

            time.sleep(3)

        except KeyboardInterrupt:
            log("Flow Lock stopped by user.")
            break
        except Exception as e:
            log(f"ERROR: {e}")
            time.sleep(3)

if __name__ == "__main__":
    flow_lock_loop()
