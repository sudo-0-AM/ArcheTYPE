#!/usr/bin/env python3
# ~/ArcheTYPE/shadow_mode.py
"""
Robust Shadow Mode daemon (KDE Wayland tolerant).
Detection strategy (priority):
 1) qdbus KWin activeWindowTitle -> clean title (best)
 2) xdotool XWayland getactivewindow + getwindowpid -> map PID -> /proc/<pid>/comm
 3) fallback: unknown (we log limitation)
This script focuses on APP-level detection (good for Wayland) and title detection (when available).
"""

import os
import time
import shlex
import subprocess
import traceback
from datetime import datetime

# Import ArcheTYPE router
try:
    from router import archetype_respond
except Exception:
    PROJECT = os.path.expanduser("~/ArcheTYPE")
    if PROJECT not in os.sys.path:
        os.sys.path.insert(0, PROJECT)
    from router import archetype_respond

LOG_PATH = os.path.expanduser("~/ArcheTYPE/shadow_mode.log")
CHECK_INTERVAL = 6           # seconds
DRIFT_IDLE_MS = 5 * 60 * 1000  # 5 minutes idle threshold

# App-level blacklist (lowercase substrings or process names)
APP_BLACKLIST = [
    "youtube", "netflix", "primevideo", "prime video", "instagram",
    "whatsapp", "discord", "reddit", "spotify", "twitter", "x",
    "tiktok", "steam", "game", "minecraft", "roblox", "facebook",
    "messenger", "snap", "twitch"
]

# Title-level blacklist (for browsers / titles)
TITLE_BLACKLIST = [
    "youtube", "spotify", "tiktok"
]

# Whitelist: if any whitelist token is present in title or proc name -> ignore drift
WHITELIST = [
    "archetype", "shadow_mode.py", "terminal", "konsole", "kitty",
    "python", "code", "pycharm", "vscode", "router.py", "vim",
    "nvim", "kate", "gedit", "intellij"
]

# Map common process names to friendly ids
PROC_TO_APP = {
    "firefox": "firefox",
    "firefox-esr": "firefox",
    "chrome": "chrome",
    "chromium": "chromium",
    "google-chrome": "chrome",
    "discord": "discord",
    "spotify": "spotify",
    "steam": "steam",
    "org.kde.konsole": "konsole",
    "konsole": "konsole",
    "code": "vscode",
    "code-oss": "vscode",
    "sublime_text": "sublime",
    "vlc": "vlc",
    "thunderbird": "thunderbird"
}

def log(msg):
    ts = datetime.now().isoformat()
    line = f"{ts} {msg}\n"
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass
    print(line, end="")

def run_cmd(cmd, timeout=1):
    try:
        out = subprocess.check_output(shlex.split(cmd), stderr=subprocess.DEVNULL, timeout=timeout)
        return out.decode(errors="ignore").strip()
    except Exception:
        return None

# -------------------------
# 1) Try qdbus KWin title
# -------------------------
def get_title_qdbus():
    """Return window title via qdbus KWin (best on some Plasma builds)."""
    title = run_cmd("qdbus org.kde.KWin /KWin org.kde.KWin.activeWindowTitle")
    if title and title.strip():
        return title.strip()
    return None

# ----------------------------------------------------
# 2) XWayland route: get active window pid -> /proc
# ----------------------------------------------------
def get_pid_from_xdotool():
    """
    Uses xdotool to get active window and its PID.
    Only works if the focused window is XWayland (not native Wayland).
    Returns PID (int) or None.
    """
    # Get active window id
    wid = run_cmd("xdotool getactivewindow")
    if not wid or not wid.isdigit():
        return None
    # getwindowpid
    pid = run_cmd(f"xdotool getwindowfocus getwindowpid")
    if pid and pid.isdigit():
        return int(pid)
    # fallback: try using wid->xprop to find PID (rare)
    try:
        out = run_cmd(f"xprop -id {wid} _NET_WM_PID")
        if out and "=" in out:
            pid = out.split("=")[-1].strip()
            if pid.isdigit():
                return int(pid)
    except Exception:
        pass
    return None

def proc_name_from_pid(pid):
    """Return comm or cmdline from /proc/<pid>"""
    try:
        p = f"/proc/{pid}"
        if not os.path.exists(p):
            return None
        # try comm first (short name)
        comm = None
        try:
            with open(os.path.join(p, "comm"), "r", encoding="utf-8") as f:
                comm = f.read().strip()
        except Exception:
            comm = None
        if comm:
            return comm
        # fallback to cmdline
        try:
            with open(os.path.join(p, "cmdline"), "r", encoding="utf-8") as f:
                raw = f.read().split("\0")
                if raw and raw[0]:
                    return os.path.basename(raw[0])
        except Exception:
            pass
    except Exception:
        pass
    return None

def map_proc_to_app(proc):
    if not proc:
        return None
    p = proc.lower()
    if p in PROC_TO_APP:
        return PROC_TO_APP[p]
    # check substring match
    for k, v in PROC_TO_APP.items():
        if k in p:
            return v
    return p  # return raw proc name as fallback

# -------------------------
# Idle detection
# -------------------------
def get_idle_ms_xprintidle():
    out = run_cmd("xprintidle", timeout=0.5)
    if out and out.isdigit():
        return int(out)
    return 0

# -------------------------
# Detection logic
# -------------------------
def detect_focus():
    """
    Return a tuple: (source, app_id, title)
      - source: 'qdbus', 'xdotool-pid', or 'unknown'
      - app_id: mapped application id or None
      - title: cleaned title or None
    """
    # 1) try qdbus title
    title = get_title_qdbus()
    if title:
        # try to infer app from title (common patterns)
        tlow = title.lower()
        # if contains youtube, mark app as browser-youtube
        if "youtube" in tlow:
            return ("qdbus", "youtube", title)
        # simple heuristics for browsers
        if "firefox" in tlow or "mozilla" in tlow:
            return ("qdbus", "firefox", title)
        if "chromium" in tlow or "chrome" in tlow:
            return ("qdbus", "chrome", title)
        # otherwise return title only
        return ("qdbus", None, title)

    # 2) try xdotool -> pid -> proc name (XWayland windows)
    pid = get_pid_from_xdotool()
    if pid:
        proc = proc_name_from_pid(pid)
        app = map_proc_to_app(proc) if proc else None
        return ("xdotool-pid", app, None)

    # 3) unknown / native Wayland app we couldn't resolve
    return ("unknown", None, None)

def is_whitelisted(app_id, title):
    if title:
        t = title.lower()
        for s in WHITELIST:
            if s.lower() in t:
                return True
    if app_id:
        for s in WHITELIST:
            if s.lower() in app_id.lower():
                return True
    return False

def is_distracting(app_id, title):
    # check app id first
    if app_id:
        for bad in APP_BLACKLIST:
            if bad in app_id.lower():
                return True
    # check title substrings
    if title:
        tl = title.lower()
        for bad in TITLE_BLACKLIST:
            if bad in tl:
                return True
    return False

def notify(title, body):
    try:
        subprocess.run(["notify-send", title, body], check=False)
    except:
        pass

def handle_drift(source, app_id, title):
    # Compose a compact context for ArcheTYPE
    ctx = []
    if source:
        ctx.append(f"source={source}")
    if app_id:
        ctx.append(f"app={app_id}")
    if title:
        ctx.append(f"title={title}")
    context = " | ".join(ctx)
    log(f"[DRIFT DETECTED] {context}")

    try:
        resp = archetype_respond(f"I am drifting. {context}", force_offline=True)
    except Exception as e:
        resp = f"[shadow error] {e}"

    single_line = resp.replace("\n", " | ")
    log(f"[response] {single_line}")
    notify("ArcheTYPE — Correction", single_line[:300])

# -------------------------
# Main loop
# -------------------------
def shadow_loop():
    log("Shadow Mode (multi-strategy) starting.")
    last_seen = (None, None)  # (app_id, title)
    while True:
        try:
            idle = get_idle_ms_xprintidle()
            if idle >= DRIFT_IDLE_MS:
                handle_drift("idle", None, None)
                # longer sleep after idle correction
                time.sleep(30)
                continue

            source, app_id, title = detect_focus()

            # Logging concise info
            if title:
                log(f"[focus] {source} app={app_id} title={title}")
            else:
                log(f"[focus] {source} app={app_id}")

            # Whitelist check
            if is_whitelisted(app_id, title):
                # no drift if whitelisted
                time.sleep(CHECK_INTERVAL)
                continue

            # Decide drifting
            if is_distracting(app_id, title):
                # avoid repeated prompts for same focus
                if (app_id, title) != last_seen:
                    handle_drift(source, app_id, title)
                    last_seen = (app_id, title)
                time.sleep(20)  # cooldown
            else:
                time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            log("Shadow Mode stopped by user.")
            break
        except Exception:
            log("Exception in shadow loop:\n" + traceback.format_exc())
            time.sleep(5)

if __name__ == "__main__":
    shadow_loop()
