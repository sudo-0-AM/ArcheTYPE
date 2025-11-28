from router import archetype_respond

def parse_intent(user_text):
    """
    Ask ArcheTYPE to classify a user instruction into an intent label.
    """

    prompt = f"""
Classify the following user instruction into ONLY an intent label.

Available intents: coding, research, deep_work, custom.

User: "{user_text}"

Return ONLY: coding / research / deep_work / custom
(no punctuation, no sentences)
"""

    # Router now auto-detects online/offline
    out = archetype_respond(prompt)
    out = out.strip().lower()

    # Cleanup
    out = out.replace("intent:", "").strip()
    out = out.replace(".", "").strip()

    return out if out else None
