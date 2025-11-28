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
    score = get_daily_score()
    # Simple ASCII bar
    bars = int(min(max(score, 0), 40) // 2)
    bar_graph = "█" * bars + "░" * (40 - bars)

    out = (
        f"FlowScore ({date.today()})\n"
        f"Score: {score}\n"
        f"[{bar_graph}]"
    )
    return out
