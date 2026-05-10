# ⚔️ HabitQuest — Gamified Habit Tracker

A full-stack productivity app with gamification mechanics. Build streaks, earn XP, and level up your habits.

---

## 🏗️ Architecture

```
┌─────────────────────┐        HTTP/REST        ┌──────────────────────┐
│  Streamlit Frontend │ ◄─────────────────────► │  FastAPI Backend     │
│   (app.py :8501)    │   JWT Bearer Token       │   (api.py :8000)     │
└─────────────────────┘                         └──────────────────────┘
                                                         │
                                                  SQLite Database
                                                 (habitquest.db)
```

**Tech Stack:**
- **Frontend:** Python Streamlit with custom CSS (Google Fonts, CSS animations)
- **Backend:** FastAPI with Pydantic data models
- **Auth:** JWT (JSON Web Tokens) via PyJWT — SHA-256 hashed passwords
- **Storage:** SQLite (`habitquest.db`) — persistent across restarts, zero setup
- **State:** `st.cache_data` in Streamlit for fast reruns without redundant API calls

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run both servers
chmod +x run.sh && ./run.sh

# OR manually:
uvicorn api:app --reload --port 8000 &
streamlit run app.py --server.port 8501
```

Open **http://localhost:8501** in your browser. Register an account and start tracking.

---

## ✨ Features

| Feature | Description |
|---|---|
| **Auth** | Register / login with JWT — passwords SHA-256 hashed |
| **Habit Management** | Add/delete habits with custom emoji & color |
| **Daily Check-ins** | Toggle habits complete/incomplete — idempotent |
| **XP System** | Earn 10 XP per habit completion |
| **Leveling** | Progressive XP thresholds (level × 50 XP per level) |
| **Streaks** | Per-habit consecutive day tracking |
| **Achievements** | 6 unlockable badges with conditions |
| **7-Day Activity** | Bar chart showing daily completion rates |
| **SQLite Storage** | All data persists in a local DB — survives restarts |
| **API Docs** | Auto-generated Swagger UI at `/docs` |

---

## 📡 API Endpoints

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/register` | Create a new account |
| POST | `/login` | Login and receive JWT token |
| POST | `/logout` | Clear auth token |
| GET | `/me` | Get current user info |

### Habits & Data
| Method | Endpoint | Description |
|---|---|---|
| GET | `/data` | Load all habits & completions for logged-in user |
| POST | `/habits` | Add a new habit |
| DELETE | `/habits/{id}` | Remove a habit |
| POST | `/complete` | Toggle habit completion for a date |
| GET | `/stats` | Per-habit streaks, rates, 7-day summary |
| DELETE | `/reset` | Clear all habit data for logged-in user |

Full interactive docs: http://localhost:8000/docs

---

## 🎯 Resume Talking Points

> **"Built a full-stack gamified habit tracker using Python Streamlit and FastAPI, with SQLite persistence and JWT authentication."**

**Key technical decisions to highlight:**

1. **JWT Authentication** — Implemented register/login with `PyJWT`. Passwords are SHA-256 hashed before storing. The token is sent as a Bearer header on every API request, and decoded server-side using FastAPI's `Depends` pattern for clean route protection.

2. **SQLite Persistence** — Used Python's built-in `sqlite3` to store users, habits, and completions in a local database. No ORM — raw SQL with parameterised queries to prevent injection. Data survives server restarts and is fully isolated per user.

3. **Decoupled Architecture** — Separated concerns cleanly: FastAPI handles all business logic (XP calculation, streak computation, level progression) while Streamlit handles UI rendering. Communication is via REST with JSON payloads and JWT auth headers.

4. **Performance — `st.cache_data`** — Streamlit reruns the entire script on every interaction. Wrapping `/data` and `/stats` fetches in `st.cache_data(ttl=2)` means only one API call per page load instead of one per widget. Cache is explicitly cleared after any write action.

5. **Gamification Mechanics** — Designed a progressive XP/level system with `level × 50 XP` thresholds, per-habit streak tracking using date arithmetic, and conditional achievement unlocking.

6. **Refactoring Story** — Originally built with cookie-based storage (no database). Identified that data was lost on server restart and there was no user separation. Refactored to SQLite + JWT — a real-world example of recognising architectural limits and improving them.

---

## 🗂️ Project Structure

```
habit-tracker/
├── api.py           # FastAPI backend — auth, business logic, SQLite I/O
├── app.py           # Streamlit frontend — UI, API calls, custom CSS
├── habitquest.db    # SQLite database (auto-created on first run)
├── requirements.txt
├── run.sh           # Convenience script to start both servers
└── README.md
```

---

## 🔧 Extending the Project

- **Add OAuth:** FastAPI's `Depends` + Google OAuth for one-click login
- **Deploy:** Streamlit Cloud (frontend) + Railway/Render (FastAPI backend), swap SQLite → PostgreSQL
- **Charts:** Add Plotly charts in Streamlit for deeper analytics
- **Mobile:** Wrap the FastAPI backend with a React Native or Flutter frontend