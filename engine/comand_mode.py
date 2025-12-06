#!/usr/bin/env python3
"""
Command Mode interpreter for ArcheTYPE.
Allows chat commands like:
  lock on
  lock off
  lock profile coding
"""

import re
from flow_lock.control import set_lock, set_profile, get_status
from flow_lock.score_dashboard import score_dashboard

def try_parse_command(text: str):
    t = text.strip().lower()

    # lock on / off
    if t in ("lock on", "activate lock", "enable lock"):
        set_lock(True)
        return "Flow Lock: ON"

    if t in ("lock off", "deactivate lock", "disable lock", "unlock"):
        set_lock(False)
        return "Flow Lock: OFF"

    # lock profile X
    m = re.match(r"lock profile (.+)", t)
    if m:
        prof = m.group(1).strip()
        set_profile(prof)
        return f"Flow Lock profile set to: {prof}"

    # switch to profile
    m = re.match(r"switch profile (.+)", t)
    if m:
        prof = m.group(1).strip()
        set_profile(prof)
        return f"Flow Lock profile set to: {prof}"

    # lock <profile>
    # Example: "lock strict"
    m = re.match(r"lock (strict|coding|study|break|unlocked)", t)
    if m:
        prof = m.group(1).strip()
        set_profile(prof)
        set_lock(True)
        return f"Flow Lock: ON (profile={prof})"

    # status
    if t in ("lock status", "status lock", "flow status"):
        st = get_status()
        return str(st)

    # score dashboard
    if t in ("flow score", "show score"):
        return score_dashboard()
    

    return None
