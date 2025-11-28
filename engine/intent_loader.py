import os
import json
from pathlib import Path

INTENTS_DIR = os.path.expanduser("~/ArcheTYPE/intents")

def load_all_intents():
    intents = {}

    # load default intents
    for file in os.listdir(INTENTS_DIR):
        if file.endswith(".json"):
            path = os.path.join(INTENTS_DIR, file)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                intents[data["name"]] = data

    # load custom intents
    custom_dir = os.path.join(INTENTS_DIR, "custom")
    os.makedirs(custom_dir, exist_ok=True)
    for file in os.listdir(custom_dir):
        if file.endswith(".json"):
            path = os.path.join(custom_dir, file)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                intents[data["name"]] = data

    return intents
