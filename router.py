#!/usr/bin/env python3
# router.py - auto-switch online/offline

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
CFG = json.load(open("/home/piyush/ArcheTYPE/config.json"))

SOUL_PATH = "/home/piyush/ArcheTYPE/ascetic_soul.jaon"

def load_soul():
    try:
        return json.load(open(SOUL_PATH, "r", encoding="utf-8"))
    except:
        return {}

def apply_soul_tone(user_text, soul):
    text = user_text.lower()

    if "shadow" in text:
        return soul["dialogue"]["enter_shadow"]

    if "why" in text or "reason" in text:
        return soul["dialogue"]["seek_truth"]

    if "stuck" in text:
        return "Strip the confusion. What is the smallest precise step you can take?"

    if "tired" in text or "low" in text:
        return "Withdraw from noise. Still yourself. Focus on the smallest next action."

    return None

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


def _internet_available():
    try:
        socket.create_connection(("api.groq.com", 443), timeout=1)
        return True
    except:
        return False


def choose_engine():
    api_key_name = CFG.get("online_api_env_var", "")
    api_key = os.getenv(api_key_name)

    if not api_key:
        return "local"
    if _internet_available():
        return "online"
    return "local"


def archetype_respond(user_text, force_offline=False, local_model="local_fast"):

    # Command Mode
    cmd = try_parse_command(user_text)
    if cmd:
        return cmd

    # ----------------------------------------
    # SOUL LAYER (Ascetic tone + rituals)
    # ----------------------------------------
    soul = load_soul()

    ritual_msg = apply_ritual(user_text, soul)
    if ritual_msg:
        user_text = ritual_msg + " " + user_text

    tone_override = apply_soul_tone(user_text, soul)
    if tone_override:
        user_text = tone_override

    # ----------------------------------------
    # ENGINE SELECT
    # ----------------------------------------
    engine = "local" if force_offline else choose_engine()
    timestamp = int(time.time())

    if engine == "online":
        try:
            resp = call_online_model(user_text)
        except Exception:
            print("[router] Online failed → using offline model.")
            resp = call_local_model(user_text, model_key=local_model)
            engine = "local"
    else:
        resp = call_local_model(user_text, model_key=local_model)

    # Log
    log_interaction({
        "ts": timestamp,
        "engine": engine,
        "user": user_text,
        "response": resp
    })

    return resp


if __name__ == "__main__":
    import sys
    user_text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else input("You: ")
    ans = archetype_respond(user_text)
    print(ans)
