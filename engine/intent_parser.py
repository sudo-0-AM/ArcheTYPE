from router import archetype_respond

def parse_intent(text):
    prompt = f"""
You are the ArcheTYPE Intent Mapper.
Your ONLY job is to read the user command and output the intent id.

Valid intents: coding, study.

RULES:
- Output EXACTLY one word: the intent id.
- Do NOT output diagnosis/action/metric.
- Do NOT roleplay.
- Do NOT explain.
- Only output raw intent.
User command: "{text}"
"""

    out = archetype_respond(prompt).strip().lower()

    # sanitize
    out = out.replace("intent:", "").strip()

    return out if out else None

