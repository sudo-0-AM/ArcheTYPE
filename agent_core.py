#!/usr/bin/env python3
"""
agent_core.py — ArcheTYPE Agent Core (run it; it uses your router and intent system)

Features:
- Sense (processes, active window, flow lock state)
- Think (call archetype_respond as 'reasoner' for diagnosis + plan)
- Plan (turn LLM reply into 1-4 actionable steps)
- Act (optionally execute safe commands based on profile + allow_autonomy)
- Learn (write memory entries for outcomes)
"""

import os
import sys
import time
import json
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# Project root & config
ROOT = Path(os.path.expanduser("~/ArcheTYPE"))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from router import archetype_respond      # LLM responder (router handles online/local)
try:
    from engine.comand_mode import try_parse_command
except Exception:
    # best-effort import; if your intent engine differs adjust path
    try:
        from engine.comand_mode import try_parse_command
    except Exception:
        def try_parse_command(t): return None

STATE_DIR = ROOT / "agent_state"
MEMORY_FILE = STATE_DIR / "memory.jsonl"
LOG_FILE = STATE_DIR / "agent.log"
CONFIG = json.load(open(ROOT / "config.json"))

# Safety and behaviour
ALLOW_AUTONOMY = bool(CONFIG.get("allow_autonomy", False))
SENSE_INTERVAL = int(CONFIG.get("agent_sense_interval", 15))  # seconds between loops
MAX_ACTIONS_PER_CYCLE = int(CONFIG.get("agent_max_actions", 2))

# Helper I/O
STATE_DIR.mkdir(parents=True, exist_ok=True)

def log(msg):
    ts = datetime.now(timezone.utc).astimezone().isoformat()
    line = f"{ts} {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")

def append_memory(entry: dict):
    entry["ts"] = datetime.now(timezone.utc).astimezone().isoformat()
    with open(MEMORY_FILE, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

# -------------------------
# Perception / Sensing
# -------------------------
def get_active_window():
    # best-effort: prefer qdbus (KDE), fallback to xdotool/wmctrl
    try:
        out = subprocess.check_output(["qdbus", "org.kde.KWin", "/KWin", "org.kde.KWin.activeWindowTitle"], stderr=subprocess.DEVNULL, timeout=1)
        s = out.decode(errors="ignore").strip()
        if s:
            return s
    except Exception:
        pass
    # xdotool fallbacks
    try:
        out = subprocess.check_output(shlex.split("xdotool getactivewindow getwindowname"), stderr=subprocess.DEVNULL, timeout=1)
        return out.decode(errors="ignore").strip()
    except Exception:
        pass
    return "unknown"

def get_process_snapshot(limit=80):
    try:
        import psutil
        procs = []
        for p in psutil.process_iter(["pid", "name", "username", "cmdline"]):
            try:
                info = p.info
                procs.append({
                    "pid": info.get("pid"),
                    "name": (info.get("name") or "")[:60],
                    "cmd": " ".join(info.get("cmdline") or [])[:180],
                    "user": info.get("username")
                })
            except Exception:
                continue
        # sort by pid and limit
        procs = sorted(procs, key=lambda x: x["pid"])[:limit]
        return procs
    except Exception:
        return []

def read_flow_lock_state():
    try:
        s = json.load(open(ROOT / "flow_lock" / "state.json"))
        return s
    except Exception:
        return {}

def recent_events(n=20):
    # read last n memory entries for context
    if not MEMORY_FILE.exists():
        return []
    out = []
    with open(MEMORY_FILE, "r", encoding="utf-8") as fh:
        for line in fh:
            try:
                out.append(json.loads(line))
            except:
                continue
    return out[-n:]

# -------------------------
# Reasoning & Planning
# -------------------------
def build_reason_prompt(obs: dict, short_history: list):
    """
    Build a compact prompt fed to archetype_respond.
    Keep short, include:
     - quick diagnosis request
     - ask for 1-3 step plan, each step with 'ACTION:' and 'COMMAND:' optional
    """
    lines = []
    lines.append("SYSTEM: You are ArcheTYPE's Agent Core. Produce: DIAGNOSIS, PLAN (1-3 steps).")
    lines.append("CONTEXT:")
    lines.append(f"- active_window: {obs.get('active_window')}")
    lines.append(f"- flow_lock: {obs.get('flow_lock', {})}")
    lines.append(f"- top_processes: " + ", ".join([p["name"] for p in obs.get("processes", [])[:6]]))
    lines.append("")
    lines.append("RECENT_EVENTS:")
    for e in short_history[-6:]:
        ts = e.get("ts", "")[0:19] if e.get("ts") else ""
        snippet = (e.get("note") or e.get("user") or "")[:200]
        lines.append(f"- {ts} {snippet}")
    lines.append("")
    lines.append("INSTRUCTIONS: Provide short DIAGNOSIS and then a PLAN with up to 3 steps.")
    lines.append("Each plan step should be one line prefixed STEP N: and, if executable, include a COMMAND: <shell command> on the same line.")
    lines.append("If nothing to do, respond `NO_ACTION`.")
    lines.append("")
    lines.append("USER QUERY: Is the user off-track? Suggest the single highest-impact next action and optionally safe system commands.")
    return "\n".join(lines)

def parse_plan_from_text(txt: str):
    """
    Parse plain text plan into structured steps.
    Very forgiving: looks for lines starting with STEP or numbered lines.
    Finds 'COMMAND:' tokens to extract shell command.
    """
    steps = []
    lines = txt.splitlines()
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        # early NO_ACTION
        if ln.upper().startswith("NO_ACTION"):
            return []
        # look for Step prefix
        if ln.lower().startswith("step") or ln[0].isdigit():
            # find "COMMAND:" occurrence
            cmd = None
            if "COMMAND:" in ln.upper():
                parts = ln.split("COMMAND:")
                text = parts[0].strip()
                cmd = parts[1].strip()
            else:
                text = ln
            steps.append({"text": text[:300], "cmd": cmd})
        else:
            # fallback: accept up to 3 standalone lines as steps
            if len(steps) < 3:
                cmd = None
                if "COMMAND:" in ln.upper():
                    parts = ln.split("COMMAND:")
                    text = parts[0].strip()
                    cmd = parts[1].strip()
                else:
                    text = ln
                steps.append({"text": text[:300], "cmd": cmd})
    return steps[:3]

# -------------------------
# Actions
# -------------------------
def safe_execute_command(cmd: str):
    """
    Execute a shell command in a constrained way.
    - Reject obviously dangerous patterns (rm -rf, sudo without explicit match).
    - If ALLOW_AUTONOMY is False, refuse.
    """
    if not ALLOW_AUTONOMY:
        return {"ok": False, "err": "autonomy disabled in config"}

    blocked = ["rm -rf", ":(){", "dd if=", "mkfs", "sh -c", "wget http", "curl http", "reboot", "shutdown", "pkill -9", "killall -9"]
    low_risk = ["xdg-open", "kwrite", "code", "kitty", "konsole", "alacritty", "firefox", "chromium", "wmctrl", "xdotool", "notify-send", "systemctl --user start"]
    cmd_l = cmd.lower()
    for b in blocked:
        if b in cmd_l:
            return {"ok": False, "err": f"blocked pattern: {b}"}
    # allow only if command contains a known benign program OR explicitly allowed
    if not any(x in cmd_l for x in low_risk):
        # if not obviously allowed, refuse unless explicitly allowed in config
        allowed_list = CONFIG.get("allowed_autonomy_commands", [])
        if cmd not in allowed_list:
            return {"ok": False, "err": "command not in allowlist"}
    try:
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return {"ok": proc.returncode == 0, "stdout": proc.stdout[:2000], "stderr": proc.stderr[:1000], "rc": proc.returncode}
    except Exception as e:
        return {"ok": False, "err": str(e)}

# -------------------------
# Agent loop
# -------------------------
def single_cycle():
    # 1) sense
    obs = {
        "active_window": get_active_window(),
        "processes": get_process_snapshot(60),
        "flow_lock": read_flow_lock_state(),
    }
    history = recent_events(20)
    # store raw observation
    append_memory({"type": "obs", "note": f"active_window={obs['active_window']}", "obs": obs})

    # 2) think (ask archetype_respond for diagnosis+plan)
    prompt = build_reason_prompt(obs, history)
    # force local to avoid network surprises in daemon
    response = archetype_respond(prompt, force_offline=True)
    append_memory({"type": "reason", "note": response})
    log("Reasoner output: " + (response.splitlines()[0] if response else "empty"))

    # 3) parse plan
    steps = parse_plan_from_text(response)
    if not steps:
        log("No plan generated.")
        append_memory({"type": "plan", "note": "NO_ACTION"})
        return

    append_memory({"type": "plan", "steps": steps})
    # 4) act — attempt up to MAX_ACTIONS_PER_CYCLE
    actions_taken = []
    for i, st in enumerate(steps[:MAX_ACTIONS_PER_CYCLE]):
        text = st.get("text")
        cmd = st.get("cmd")
        if cmd:
            result = safe_execute_command(cmd)
            actions_taken.append({"text": text, "cmd": cmd, "result": result})
            append_memory({"type": "action", "text": text, "cmd": cmd, "result": result})
            log(f"Attempted command: {cmd} -> ok={result.get('ok')}")
        else:
            # not executable, just notify
            try:
                subprocess.Popen(["notify-send", "ArcheTYPE plan", text])
            except:
                pass
            actions_taken.append({"text": text, "cmd": None, "result": "not-executed"})
            append_memory({"type": "action", "text": text, "cmd": None, "result": "not-executed"})
            log("Planned action (notify): " + text[:120])

    # 5) Evaluate (ask reasoner to score outcome)
    eval_prompt = "SYSTEM: Evaluate the outcome of recent actions. Provide a 1-line verdict and whether to persist any policy change.\n\nRECENT_ACTIONS:\n" + json.dumps(actions_taken, ensure_ascii=False, indent=2)
    eval_resp = archetype_respond(eval_prompt, force_offline=True)
    append_memory({"type": "eval", "note": eval_resp, "actions": actions_taken})
    log("Eval: " + (eval_resp.splitlines()[0] if eval_resp else "no-eval"))

def run_agent_loop():
    log("Agent Core starting. Autonomy: " + str(ALLOW_AUTONOMY))
    try:
        while True:
            try:
                single_cycle()
            except Exception as e:
                log("cycle exception: " + str(e))
            time.sleep(SENSE_INTERVAL)
    except KeyboardInterrupt:
        log("Agent stopped by user.")

if __name__ == "__main__":
    run_agent_loop()
