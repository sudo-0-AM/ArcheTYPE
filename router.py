#!/usr/bin/env python3
# router.py — Adaptive Context Router (Ascetic v1)

import os
import json
import time
import socket
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

from adapters.online_adapter import call_online_model
from adapters.local_adapter import call_local_model
from logger import log_interaction
from engine.comand_mode import try_parse_command

load_dotenv()

ROOT = Path("/home/piyush/ArcheTYPE")
CFG = json.load(open(ROOT / "config.json"))

SOUL_PATH = ROOT / "soul/ascetic_soul.json"
FLOW_STATE_PATH = ROOT / "flow_lock/state.json"


# -------------------------------------------------------
# LOAD SOUL
# -------------------------------------------------------
def load_soul():
    try:
        return json.load(open(SOUL_PATH, "r", encoding="utf-8"))
    except:
        return {}

def compute_tone_intensity(state):
    """
    Returns a float 0.0 → 1.0 representing how intense the Ascetic tone should be.
    XP increases long-term sharpness.
    FlowScore increases short-term pressure.
    Streak increases commitment pressure.
    """

    xp = state.get("total_xp", 0)
    flow = state.get("daily_score", 0)
    streak = state.get("streak", "low")

    # Normalize numbers
    xp_norm = min(1.0, xp / 2000000)          # 0–2M XP → 0–1
    flow_norm = min(1.0, flow / 2000)       # 0–2000 score → 0–1
    streak_boost = {
        "low": 0.0,
        "medium": 0.15,
        "high": 0.3,
        "apex": 0.5
    }.get(streak, 0.0)

    base = (xp_norm * 0.4) + (flow_norm * 0.4) + streak_boost
    return min(1.0, base)


# -------------------------------------------------------
# ASCETIC TONE LAYER (INTELLIGENCE BOOSTER)
# -------------------------------------------------------
def apply_soul_tone(user_text, soul):
    """
    Returns either:
      - A DIRECT ascetic message (if user triggers a pure-soul condition)
      - OR a tone directive for the LLM
    
    Pure-soul triggers ignore the LLM and return a finished message.
    Otherwise, we inject a tone directive that scales with user performance.
    """

    state = load_flow_state()
    text = user_text.lower()

    dialogue = soul.get("dialogue", {})
    tone_cfg = soul.get("tone", {})

    # ---------- 1. PURE SOUL RESPONSES (LLM bypass) ----------
    if "shadow" in text:
        return dialogue.get("enter_shadow", "Speak.")
    
    if any(k in text for k in ["why", "reason"]):
        return dialogue.get("seek_truth", "What is the real root of this?")

    if "stuck" in text:
        return "Strip the hesitation. Name the smallest possible action."

    if any(k in text for k in ["tired", "exhausted", "drained"]):
        return "Withdraw. Breathe. Remove noise. Then take one step."

    # ---------- 2. ADAPTIVE INTENSITY LAYER ----------
    intensity = compute_tone_intensity(state)

    # Map intensity → verbal style
    if intensity < 0.25:
        style = tone_cfg.get("minor_drift", "brief, cold, minimal")
    elif intensity < 0.55:
        style = "precise, sharpened, uncomfortably direct"
    else:
        style = tone_cfg.get("major_drift", "severe, ascetic, ego-cutting")

    # Build tone directive for the LLM
    return f"[TONE: {style}; intensity={intensity:.2f}]"


def apply_ritual(user_text, soul):
    hour = datetime.now().hour
    rituals = soul.get("rituals", {})

    if hour == 6:
        return rituals["morning"]["phrase"]
    if hour == 12:
        return rituals["midday"]["phrase"]
    if hour == 22:
        return rituals["night"]["phrase"]

    return None


# -------------------------------------------------------
# BUILD ADAPTIVE USER STATE PACKET
# -------------------------------------------------------
def load_flow_state():
    try:
        return json.load(open(FLOW_STATE_PATH))
    except:
        return {}


def compute_streak(flow):
    xp = flow.get("total_xp", 0)
    if xp > 40000:
        return "apex"
    if xp > 20000:
        return "high"
    if xp > 5000:
        return "medium"
    return "low"


def detect_emotion_from_history():
    # crude heuristic; we upgrade later
    try:
        mem = open(ROOT / "agent_state/memory.jsonl").read().lower()
        if "tired" in mem or "exhausted" in mem:
            return "fatigue"
        if "stuck" in mem:
            return "frustration"
        if "win" in mem or "locked in" in mem:
            return "drive"
    except:
        pass
    return "neutral"


def build_user_state_packet():
    flow = load_flow_state()

    packet = {
        "flow_score": flow.get("daily_score", 0),
        "xp": flow.get("total_xp", 0),
        "level": flow.get("level", 1),
        "profile": flow.get("current_profile", "none"),
        "locked_in": flow.get("lock_enabled", False),
        "streak": compute_streak(flow),
        "emotion": detect_emotion_from_history(),
        "timestamp": datetime.now().isoformat(),
    }

    return packet


# -------------------------------------------------------
# NETWORK CHECK
# -------------------------------------------------------
def _internet_available():
    try:
        socket.create_connection(("api.groq.com", 443), timeout=1)
        return True
    except:
        return False


def choose_engine():
    api_key = os.getenv(CFG.get("online_api_env_var", ""))
    if not api_key:
        return "local"
    return "online" if _internet_available() else "local"


# -------------------------------------------------------
# MAIN RESPONSE PIPELINE
# -------------------------------------------------------
def archetype_respond(user_text, force_offline=False, local_model="local_fast"):

    # Step 1: Command mode
    cmd = try_parse_command(user_text)
    if cmd:
        return cmd

    soul = load_soul()

    # Step 2: Ritual layer
    ritual = apply_ritual(user_text, soul)
    if ritual:
        user_text = ritual + " " + user_text

    # Step 3: Soul tone override (pure response, no LLM call)
    tone_directive = apply_soul_tone(user_text, soul)
    tone_block = f"\nASCETIC_TONE: {tone_directive}" if tone_directive else ""


    # Step 4: Build adaptive packet
    packet = build_user_state_packet()

    # Build final LLM input
    adaptive_prompt = (
        "SYSTEM_USER_STATE:\n" +
        json.dumps(packet, indent=2) +
        "\n\n"
        "INSTRUCTIONS:\n"
        "- Use an ascetic, precise tone scaled by flow_score, xp, and streak.\n"
        "- If emotion='fatigue' → stabilizing tone.\n"
        "- If emotion='frustration' → clarifying tone.\n"
        "- If streak='apex' → aggressive tone.\n"
        "- Give DIAGNOSIS / ACTION / METRIC.\n" + tone_block +"\n"
        "\nUSER:\n" +
        user_text
    )

    # Step 5: Engine selection
    engine = "local" if force_offline else choose_engine()
    timestamp = int(time.time())

    # Step 6: Model call
    if engine == "online":
        try:
            resp = call_online_model(adaptive_prompt)
        except Exception:
            print("[router] Online failed → offline fallback.")
            resp = call_local_model(adaptive_prompt, model_key=local_model)
            engine = "local"
    else:
        resp = call_local_model(adaptive_prompt, model_key=local_model)

    # Step 7: Logging
    log_interaction({
        "ts": timestamp,
        "engine": engine,
        "user": user_text,
        "adaptive_packet": packet,
        "response": resp
    })

    return resp


if __name__ == "__main__":
    import sys
    t = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else input("You: ")
    print(archetype_respond(t))
