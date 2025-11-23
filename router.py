#!/usr/bin/env python3
# router.py - choose backend, orchestrate calls, log interactions
import os, json, time
from adapters.online_adapter import call_online_model
from adapters.local_adapter import call_local_model
from logger import log_interaction
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
CFG = json.load(open('config.json'))

def choose_engine(user_text, prefer_online=True):
    # Tunable policy: if internet and prefer_online -> online teacher
    if prefer_online and os.getenv(CFG['online_api_env_var']):
        return 'online'
    return 'local'

def archetype_respond(user_text, prefer_online=True, local_model='local_fast'):
    engine = choose_engine(user_text, prefer_online=prefer_online)
    timestamp = int(time.time())
    if engine == 'online':
        resp = call_online_model(user_text)
    else:
        resp = call_local_model(user_text, model_key=local_model)
    log_interaction({
        'ts': timestamp,
        'engine': engine,
        'user': user_text,
        'response': resp
    })
    return resp

if __name__ == '__main__':
    import sys
    user_text = " ".join(sys.argv[1:]) if len(sys.argv)>1 else input("You: ")
    ans = archetype_respond(user_text, prefer_online=True)
    print(ans)
