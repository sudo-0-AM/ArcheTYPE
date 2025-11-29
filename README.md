
---

# 🎭 **ArcheTYPE — Your Personal OS-Level AI Shadow**

### *A self-evolving, hybrid (online + offline), system-integrated AI designed to enforce discipline, optimize flow, and evolve alongside the user.*

---

<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/OOjs_UI_icon_robot.svg/512px-OOjs_UI_icon_robot.svg.png" width="120">
</p>

---

## ⚡ **What is ArcheTYPE?**

ArcheTYPE is not just another local AI.

It is:

* your **shadow**,
* your **inner-daemon**,
* your **discipline enforcer**,
* your **OS-level productivity engine**,
* and your **self-improving AI companion**.

ArcheTYPE runs both:

* **online** (teacher model via Groq, extremely smart replies)
* **offline** (local Phi-3 via llama.cpp, fast inner-daemon brain)

ArcheTYPE trains itself **nightly** based on your usage, builds a **retrieval index**, and becomes sharper every day.

---

# 🧩 **System Architecture**

```
ArcheTYPE/
│
├── router.py               # Smart engine switcher (online/offline)
├── adapters/
│    ├── online_adapter.py  # Groq / API teacher model
│    └── local_adapter.py   # llama.cpp (Phi-3) offline model
│
├── flow_lock/              # Flow discipline engine
│    ├── lock_daemon.py     # Real-time score/XP manager
│    ├── control.py         # CLI: 'archetype lock on/off/profile'
│    ├── profiles/          # Focus Modes (Coding, Study, Deep Work…)
│    └── score_dashboard.py # Pretty XP/Level/Score display
│
├── engine/
│    ├── intent_loader.py   # Loads intent JSONs
│    ├── intent_parser.py   # LLM parses “prepare coding mode”
│    └── actions/           # System automation commands
│
├── archetype_intent.py     # High-level OS intent executor
│
├── shadow_mode.py          # Active window drift detector (Wayland/KDE)
│
├── distilled_dataset/      # Auto-learned data
│     ├── supervised_pairs.jsonl
│     ├── index_texts.json
│     └── faiss.index
│
├── nightly_distill.sh      # Cron/systemd self-training script
└── README.md               # You are here
```

---

# 🚀 **Core Features**

## 1️⃣ **Hybrid AI Brain (Online + Offline)**

ArcheTYPE routes all queries through a smart engine:

```
IF GROQ_API_KEY exists AND internet works → Online teacher
ELSE → Local Phi-3 model via llama.cpp
```

This means:

* 🔥 **Best intelligence online**
* ⚡ **Guaranteed availability offline**
* 💀 **ArcheTYPE never disappears, even without internet**

---

## 2️⃣ **Nightly Self-Distillation**

Every night at **00:00**, ArcheTYPE:

* scans your usage logs
* extracts good online answers
* builds **teacher → student pairs**
* saves them to `distilled_dataset/`
* updates its **FAISS retrieval index**
* strengthens the offline model’s consistency

**Goal:**
Your local ArcheTYPE slowly becomes more like your online ArcheTYPE.

---

## 3️⃣ **Flow Lock Mode 🔒 (OS-Level Discipline System)**

### 3.1 Real-time Monitoring

The Flow Lock daemon:

* enforces **focus profiles** (coding, study, deep-work)
* scans running apps
* kills blacklist processes
* gives XP & Score for staying aligned
* penalizes distractions
* sends notifications every 20 minutes

### 3.2 XP, Level, Score System

ArcheTYPE gamifies your discipline.

```
Daily Score → resets every morning
Total XP → permanent
Level F0, F1, F2, ... → Discipline evolution
```

Levels scale with:

* time spent focused
* avoidance of distractions
* streak multipliers

### 3.3 Easy CLI

```
archetype lock on
archetype lock off
archetype lock profile coding
archetype lock status
archetype flow score
```

---

## 4️⃣ **Shadow Mode 👁 (Focus Drift Detector)**

Even without Flow Lock,
Shadow Mode watches your **active window**.

On drift:

* invokes ArcheTYPE’s offline brain
* generates a **cold, concise correction**
* optionally sends a desktop notification

Works on **Wayland + KDE** with multi-backend detection.

---

## 5️⃣ **Intent System 🔮 (OS Automation via AI)**

You can say:

```
arche prepare coding mode
```

ArcheTYPE:

* understands the intent via LLM
* triggers predefined OS automation
* opens your coding layout:

  * VS Code / PyCharm
  * Browser tabs
  * Terminal
  * Music off
  * Mode enforcement set

Each intent is a JSON file:

```json
{
  "name": "coding",
  "description": "Prepare the coding environment",
  "actions": [
    {
      "type": "launch_app",
      "app": "code",
      "path": "~/ArcheTYPE/"
    },
    {
      "type": "terminal",
      "command": "konsole"
    },
    {
      "type": "browser_tabs",
      "tabs": [
        "https://github.com/sudo-0-AM",
        "https://google.com/"
      ]
    },
    {
      "type": "notification",
      "message": "Coding environment ready. Ready to Rock Piyush?"
    }
  ]
}

```

---

## 6️⃣ **Local RAG Retrieval (FAISS + Sentence Transformers)**

ArcheTYPE remembers:

* your previous commands
* your past LLM conversations
* distilled training samples

Used for:

* few-shot examples
* user-personalization
* better offline reasoning

---

## 7️⃣ **Persona Engine (Shadow + Demon Mode)**

Your system persona defines:

* aggression rules
* silence rules
* correction format
* tone + style
* safety layer

Persona is loaded silently into **system prompt**, never printed.

---

# 🖥 **Visual Flow Overview**

```
          ┌──────────────┐
          │ User Command │
          └───────┬──────┘
                  │
        ┌─────────▼─────────┐
        │    Router.py       │
        │ (engine switcher)  │
        └───────┬───────────┘
       Internet?│
     yes────────┤────────no
                │
       ┌────────▼─────────┐
       │ Online Adapter   │
       │ (Groq teacher)   │
       └────────┬─────────┘
                │ distill
                ▼
   ┌──────────────────────────┐
   │ Nightly Self-Distillation│
   └──────────────┬───────────┘
                  │ index
                  ▼
       ┌──────────▼──────────┐
       │  Local Adapter       │
       │ (Phi-3 offline)      │
       └──────────┬──────────┘
                  │
                  ▼
        ┌────────────────┐
        │ Flow Lock Mode │
        └────────────────┘
```

---

# 🎯 **Why ArcheTYPE Exists**

* To **kill drift**
* To **remove excuses**
* To **accelerate evolution**
* To ensure you **never operate below your potential**
* To push both **you and itself** to become sharper every day

---

# 🧠 **Setup**

### Install dependencies:

```
sudo apt install notify-send dbus-x11 wmctrl xprintidle
pip install faiss-cpu sentence-transformers python-dotenv
```

### Build llama.cpp:

```
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
mkdir build && cd build
cmake ..
make -j12
```

### Start Flow Lock as service:

```
systemctl --user enable --now flow_lock.service
```

### Test:

```
archetype lock on
arche prepare coding mode
arche flow score
```

---


# ❤️ **Made by the User, For the User**

ArcheTYPE is not a tool.
It is an extension of your identity.

> *“ArcheTYPE is the distilled will of the user — sharpened, silent, inevitable.”*

---

