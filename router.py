#!/usr/bin/env python3
# router.py - auto-switch online/offline

import os
import json
import time
import socket
from dotenv import load_dotenv
from pathlib import Path

from adapters.online_adapter import call_online_model
from adapters.local_adapter import call_local_model
from logger import log_interaction

load_dotenv()
CFG = json.load(open("config.json"))

# -------------------------------------------------------
# INTERNET CHECK (NO PING — THIS ALWAYS WORKS)
# -------------------------------------------------------
def _internet_available():
    try:
        socket.create_connection(("api.groq.com", 443), timeout=1)
        return True
    except:
        return False


# -------------------------------------------------------
# ENGINE SELECTION
# -------------------------------------------------------
def choose_engine():
    api_key_name = CFG.get("online_api_env_var", "")
    api_key = os.getenv(api_key_name)

    # If Groq key isn't present → local only
    if not api_key:
        return "local"

    # If internet works → use teacher model
    if _internet_available():
        return "online"

    # Otherwise → offline LLM
    return "local"


# -------------------------------------------------------
# MAIN EXECUTION LOGIC
# -------------------------------------------------------
def archetype_respond(user_text,force_offline=False, local_model="local_fast"):
    if force_offline:
        engine = "local"
    else:
        engine = choose_engine()

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

    # Log response
    log_interaction({
        "ts": timestamp,
        "engine": engine,
        "user": user_text,
        "response": resp
    })

    return resp


# -------------------------------------------------------
# CLI
# -------------------------------------------------------
if __name__ == "__main__":
    import sys
    user_text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else input("You: ")
    ans = archetype_respond(user_text)
    print(ans)
