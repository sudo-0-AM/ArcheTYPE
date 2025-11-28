import os
import subprocess
import shlex

def run_cmd(cmd):
    try:
        subprocess.Popen(cmd, shell=True)
    except Exception as e:
        print("[executor error]", e)

def execute_action(action):
    t = action["type"]

    if t == "launch_app":
        # e.g. "code" or "pycharm" or "firefox"
        app = action["app"]
        path = os.path.expanduser(action.get("path", "~"))
        run_cmd(f'{app} "{path}" &')

    elif t == "terminal":
        cmd = action["command"]
        full = f'"{cmd}"'
        run_cmd(full)

    elif t == "browser_tabs":
        tabs = action["tabs"]
        for t in tabs:
            run_cmd(f'xdg-open "{t}"')

    elif t == "notification":
        msg = action["message"]
        run_cmd(f'notify-send "ArcheTYPE" "{msg}"')

def execute_intent(intent_data):
    for action in intent_data["actions"]:
        execute_action(action)
