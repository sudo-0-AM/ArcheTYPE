"""rules_engine.py
Simple rule engine for ArcheTYPE decision-making.
Provides:
- detect_drift(text)
- decide_mode(text, context)
- build_prompt(mode, user_text, context)
"""

def detect_drift(text):
    """Return True if text indicates drift or being stuck."""
    if not text:
        return False
    kws = ["stuck","bored","procrastin","lost","demotiv","can't","cant","blocked","overwhelmed","demotivated"]
    text_l = text.lower()
    return any(k in text_l for k in kws)

def decide_mode(text, context=None):
    """Decide which mode to use based on input text and optional context."""
    if text is None:
        return "silence"
    text_l = text.lower()
    if any(w in text_l for w in ["summon archetype", "wake archetype", "archetype", "voice archetype"]) and len(text_l.split()) < 10:
        return "voice"
    if detect_drift(text) or any(w in text_l for w in ["help", "motivate", "stuck", "blocked"]):
        return "text"
    # default to text to be safely responsive
    return "text"

def build_prompt(mode, user_text, system_prompt_text):
    """Construct a compact prompt to be sent to the LLM or local policy.
    For now returns a structured string; LLM integration is a separate step.
    """
    header = "[ArcheTYPE RESPONSE - MODE: {}]\n".format(mode.upper())
    instruction = "Respond as ArcheTYPE: one-line diagnosis (<=1 sentence), one high-impact next action (timeboxed), one measurable metric. Keep under 60 words.\n\n"
    return header + instruction + "SYSTEM:\n" + system_prompt_text + "\nUSER:\n" + user_text
