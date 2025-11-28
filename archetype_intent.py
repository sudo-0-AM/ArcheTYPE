#!/usr/bin/env python3
import sys
from engine.intent_loader import load_all_intents
from engine.intent_parser import parse_intent
from engine.intent_executor import execute_intent

def run_intent(user_text):
    intents = load_all_intents()
    intent = parse_intent(user_text)

    if not intent:
        print("Could not classify intent.")
        return

    if intent not in intents:
        print(f"Intent '{intent}' not found.")
        return

    print(f"[ArcheTYPE Intent] Executing: {intent}")
    execute_intent(intents[intent])

if __name__ == "__main__":
    text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else input("Intent: ")
    run_intent(text)
