# adapters/online_adapter.py
import os, json, requests

CFG = json.load(open('config.json'))

def call_online_model(user_text):
    api_key = os.getenv(CFG['online_api_env_var'])
    if not api_key:
        return "[online adapter] GROQ_API_KEY missing"

    # Load persona
    try:
        persona_path = os.path.expanduser(CFG['persona_source'])
        persona = open(persona_path, "r", encoding="utf-8").read()
    except Exception as e:
        return f"[online adapter] persona file error: {e}"

    # System + user messages
    messages = [
        {
            "role": "system",
            "content": (
                persona +
                "\nRespond strictly as ArcheTYPE. "
                "Your output must contain:\n"
                "DIAGNOSIS:\nACTION:\nMETRIC:\n"
                "Keep under 60 words."
            )
        },
        {"role": "user", "content": user_text}
    ]

    # ✔ USE A STILL-SUPPORTED MODEL
    # speedy + stable
    model_name = "llama-3.1-8b-instant"

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model_name,
        "messages": messages,
        "max_tokens": 200,
        "temperature": 0.2,
        "stream": False
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        j = r.json()
        return j["choices"][0]["message"]["content"]

    except requests.exceptions.HTTPError as e:
        return f"[online adapter error] {e}\nResponse: {r.text}"
    except Exception as e:
        return f"[online adapter error] {e}"
