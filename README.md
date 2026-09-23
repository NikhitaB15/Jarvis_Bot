# Jarvis_Bot — Personal AI Assistant & Goal-Oriented AI Coach

A personal voice assistant and multi-device productivity coach that integrates desktop activity monitoring, Android telemetry, persistent memory, and LLM-powered personalized nudges.

---

## Target Architecture

```
Android App
    │
    ├── UsageStatsManager (screen time & app limits)
    ├── Health Connect (sleep, steps & activity metrics)
    ├── Location (geofencing & context detection)
    ├── Calendar (schedule & focus windows)
    └── Notifications (alert triage & notification blocking)
           │
           ▼
     FastAPI Backend (`server/`)
           │
      PostgreSQL / Supabase
           │
      LLM (Groq / OpenAI)
           │
    AI Coach & Memory
```

---

## Overview & Goal-Oriented Personalized Nudges

`Jarvis_Bot` combines desktop monitoring, voice interaction, and a mobile-integrated FastAPI backend to act as a proactive AI Coach. Based on real-time context from both desktop and Android devices, the AI Coach generates actionable, personalized nudges such as:

- **App Limit Enforcement**: *"You've spent 1 hour 45 minutes on Instagram today, exceeding your 30-minute goal."*
- **Focus Window Optimization**: *"You usually study best between 8–10 PM. Shall I block notifications?"*
- **Skill Practice Reminders**: *"You haven't worked on ML interview prep for 3 days. Let's do one interview question now."*
- **Geofenced Goal Nudges**: *"You're at the office. Want to spend 30 minutes on your GCP certification after work?"*

---

## Features

### 1. Voice Assistant (`main.py`)
- Interactive voice assistant powered by `SpeechRecognition` and `pyttsx3`.
- Wake-word listener loop and persistent user profile memory (`data/nick_memory.json`).
- Automated system commands and dynamic plugin loading.

### 2. Desktop Activity Monitoring (`activity_tracker.py`)
- Background monitor tracking active windows, foreground app process names, and system idle time.
- Logs activity snapshots directly into SQLite (`data/jarvis_activity.db`).

### 3. FastAPI Backend Server (`server/`)
- Unified backend API providing telemetry ingestion and AI Coach reasoning.
- Pydantic models for `UsageStats`, `HealthData`, `LocationContext`, `CalendarEvent`, and `NotificationItem`.
- `AICoachNudgeEngine` powered by Groq LLMs (`llama-3.3-70b-versatile`) to generate context-aware nudges.

---

## Project Structure

- `main.py` — Main voice assistant entry point
- `activity_tracker.py` — Background desktop activity tracker & SQLite logger
- `server/` — FastAPI backend server & AI Coach nudge engine
  - `app.py` — FastAPI application & routes (`/api/v1/telemetry/sync`, `/api/v1/nudges/generate`)
  - `schemas.py` — Telemetry & nudge Pydantic data schemas
  - `nudge_engine.py` — AI Coach rule & LLM nudge generator
  - `database.py` — Database abstraction (SQLite / PostgreSQL / Supabase)
- `commands/` — Voice assistant command logic & Groq chat client (`groq_chat.py`)
- `config/` — Assistant configuration & automation managers
- `data/` — Local database files (`jarvis_activity.db`) and persistent memory (`nick_memory.json`)
- `utils/` — System utilities & speech helpers
- `tests/` — Test suite for API endpoints and nudge engine

---

## Setup & Quickstart

1. **Activate Virtual Environment & Install Dependencies**:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**:
   Ensure `.env` contains your Groq API Key:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

3. **Run the Desktop Voice Assistant**:
   ```powershell
   python main.py
   ```

4. **Run the FastAPI Backend Server**:
   ```powershell
   uvicorn server.app:app --reload --port 8000
   ```
   Open `http://localhost:8000/docs` in your browser for interactive API documentation.

---

## Future Mobile Integration Roadmap

- **Android Mobile App**: Kotlin-based client deploying `UsageStatsManager`, `Health Connect SDK`, `Google Calendar API`, location geofencing, and `NotificationListenerService`.
- **Supabase Cloud Sync**: Live sync for cross-device telemetry and persistent goal tracking.
- **Push Nudges**: FCM (Firebase Cloud Messaging) integration for instant phone nudges.
