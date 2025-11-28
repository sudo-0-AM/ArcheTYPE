#!/usr/bin/env python3
"""
Score Dashboard:
- Reads state.json
- Displays daily_score
- Optionally generates ascii bar chart
"""

import os
import json
from datetime import date

BASE = os.path.expanduser("~/ArcheTYPE/flow_lock")
STATE = os.path.join(BASE, "state.json")

def get_daily_score():
    try:
        st = json.load(open(STATE))
        today = str(date.today())
        if st.get("last_score_date") != today:
            return 0
        return round(st.get("daily_score", 0), 2)
    except:
        return 0

def score_dashboard():
    try:
        st = json.load(open(STATE))
    except:
        return "FlowScore unavailable."

    score = round(st.get("daily_score", 0), 2)
    xp = round(st.get("total_xp", 0), 2)
    level = st.get("level", 0)

    bars = int(min(level, 40))  # Level bar
    bar_graph = "█" * bars + "░" * (40 - bars)

    return (
        f"FlowScore ({date.today()})\n"
        f"Daily Score: {score}\n"
        f"XP: {xp}\n"
        f"Level: F{level}\n"
        f"[{bar_graph}]\n"
    )

