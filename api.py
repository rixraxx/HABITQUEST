from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import sqlite3, uuid, hashlib, os
from datetime import date, timedelta, datetime, timezone
import jwt  # pip install PyJWT

# ── Config ───────────────────────────────────────────────────────────────────

SECRET_KEY = os.getenv("HABITQUEST_SECRET", "change-this-in-production-please")
ALGORITHM  = "HS256"
TOKEN_EXPIRE_DAYS = 30
DB_PATH    = "habitquest.db"
TOKEN_COOKIE = "habitquest_token"

app = FastAPI(title="HabitQuest API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Database Setup ────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id       TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            xp       INTEGER DEFAULT 0,
            level    INTEGER DEFAULT 1,
            created  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS habits (
            id      TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name    TEXT NOT NULL,
            emoji   TEXT DEFAULT '⭐',
            color   TEXT DEFAULT '#6366f1',
            created TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS completions (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id  TEXT NOT NULL,
            habit_id TEXT NOT NULL,
            date     TEXT NOT NULL,
            UNIQUE(user_id, habit_id, date),
            FOREIGN KEY (user_id)  REFERENCES users(id),
            FOREIGN KEY (habit_id) REFERENCES habits(id)
        );
    """)
    conn.commit()
    conn.close()


init_db()

# ── Models ────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class Habit(BaseModel):
    name:  str
    emoji: str = "⭐"
    color: str = "#6366f1"

class HabitCompletion(BaseModel):
    habit_id: str
    date: str  # ISO YYYY-MM-DD

# ── Auth Helpers ──────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def make_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> str:
    """Returns user_id or raises HTTPException."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired — please log in again")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(request: Request) -> str:
    """Dependency: extract user_id from JWT cookie or Authorization header."""
    # Try cookie first
    token = request.cookies.get(TOKEN_COOKIE)
    # Fall back to Bearer header
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return decode_token(token)


def set_token_cookie(response: JSONResponse, token: str) -> JSONResponse:
    response.set_cookie(
        key=TOKEN_COOKIE,
        value=token,
        max_age=60 * 60 * 24 * TOKEN_EXPIRE_DAYS,
        httponly=False,   # False so Streamlit can read it via JS if needed
        samesite="lax",
    )
    return response

# ── Gamification Helpers ──────────────────────────────────────────────────────

def calc_level(xp: int) -> int:
    level, needed, remaining = 1, 50, xp
    while remaining >= needed:
        remaining -= needed
        level += 1
        needed = level * 50
    return level


def calc_streak(conn, user_id: str, habit_id: str) -> int:
    rows = conn.execute(
        "SELECT date FROM completions WHERE user_id=? AND habit_id=? ORDER BY date DESC",
        (user_id, habit_id)
    ).fetchall()
    dates = [r["date"] for r in rows]
    if not dates:
        return 0
    today = date.today()
    streak, check = 0, today
    for d in dates:
        ddate = date.fromisoformat(d)
        if ddate == check or (streak == 0 and ddate == today - timedelta(days=1)):
            streak += 1
            check = ddate - timedelta(days=1)
        elif ddate < check:
            break
    return streak

# ── Auth Routes ───────────────────────────────────────────────────────────────

@app.post("/register")
def route_register(body: RegisterRequest):
    if len(body.username.strip()) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    conn = get_db()
    try:
        user_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO users (id, username, password, xp, level, created) VALUES (?,?,?,0,1,?)",
            (user_id, body.username.strip(), hash_password(body.password), date.today().isoformat())
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Username already taken")
    finally:
        conn.close()

    token = make_token(user_id)
    resp = JSONResponse({"status": "registered", "username": body.username.strip()})
    return set_token_cookie(resp, token)


@app.post("/login")
def route_login(body: LoginRequest):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (body.username.strip(), hash_password(body.password))
    ).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = make_token(row["id"])
    resp = JSONResponse({"status": "ok", "username": row["username"], "xp": row["xp"], "level": row["level"]})
    return set_token_cookie(resp, token)


@app.post("/logout")
def route_logout():
    resp = JSONResponse({"status": "logged out"})
    resp.delete_cookie(TOKEN_COOKIE)
    return resp


@app.get("/me")
def route_me(user_id: str = Depends(get_current_user)):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": row["username"], "xp": row["xp"], "level": row["level"]}

# ── Data Routes ───────────────────────────────────────────────────────────────

@app.get("/data")
def route_get_data(user_id: str = Depends(get_current_user)):
    conn = get_db()
    user    = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    habits  = conn.execute("SELECT * FROM habits WHERE user_id=? ORDER BY created", (user_id,)).fetchall()
    comps   = conn.execute("SELECT * FROM completions WHERE user_id=?", (user_id,)).fetchall()
    conn.close()

    habits_dict = {r["id"]: dict(r) for r in habits}
    completions_dict = {}
    for c in comps:
        completions_dict.setdefault(c["date"], []).append(c["habit_id"])

    return {
        "habits": habits_dict,
        "completions": completions_dict,
        "user": {"xp": user["xp"], "level": user["level"]},
    }


@app.post("/habits")
def route_add_habit(habit: Habit, user_id: str = Depends(get_current_user)):
    conn = get_db()
    habit_id = str(uuid.uuid4())[:8]
    conn.execute(
        "INSERT INTO habits (id, user_id, name, emoji, color, created) VALUES (?,?,?,?,?,?)",
        (habit_id, user_id, habit.name, habit.emoji, habit.color, date.today().isoformat())
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "id": habit_id}


@app.delete("/habits/{habit_id}")
def route_delete_habit(habit_id: str, user_id: str = Depends(get_current_user)):
    conn = get_db()
    conn.execute("DELETE FROM habits WHERE id=? AND user_id=?", (habit_id, user_id))
    conn.execute("DELETE FROM completions WHERE habit_id=? AND user_id=?", (habit_id, user_id))
    conn.commit()
    conn.close()
    return {"status": "ok"}


@app.post("/complete")
def route_complete_habit(completion: HabitCompletion, user_id: str = Depends(get_current_user)):
    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM completions WHERE user_id=? AND habit_id=? AND date=?",
        (user_id, completion.habit_id, completion.date)
    ).fetchone()

    if existing:
        conn.execute("DELETE FROM completions WHERE id=?", (existing["id"],))
        conn.execute("UPDATE users SET xp = MAX(0, xp - 10) WHERE id=?", (user_id,))
        msg = "uncompleted"
    else:
        conn.execute(
            "INSERT INTO completions (user_id, habit_id, date) VALUES (?,?,?)",
            (user_id, completion.habit_id, completion.date)
        )
        conn.execute("UPDATE users SET xp = xp + 10 WHERE id=?", (user_id,))
        msg = "completed"

    conn.commit()
    user = conn.execute("SELECT xp FROM users WHERE id=?", (user_id,)).fetchone()
    new_xp = user["xp"]
    new_level = calc_level(new_xp)
    conn.execute("UPDATE users SET level=? WHERE id=?", (new_level, user_id))
    conn.commit()
    conn.close()

    return {"status": msg, "xp": new_xp, "level": new_level}


@app.get("/stats")
def route_get_stats(user_id: str = Depends(get_current_user)):
    conn = get_db()
    habits  = conn.execute("SELECT * FROM habits WHERE user_id=?", (user_id,)).fetchall()
    comps   = conn.execute("SELECT * FROM completions WHERE user_id=?", (user_id,)).fetchall()
    user    = conn.execute("SELECT xp, level FROM users WHERE id=?", (user_id,)).fetchone()

    completions_dict = {}
    for c in comps:
        completions_dict.setdefault(c["date"], []).append(c["habit_id"])

    stats = {}
    for h in habits:
        hid = h["id"]
        streak = calc_streak(conn, user_id, hid)
        total_days = max(1, (date.today() - date.fromisoformat(h["created"])).days + 1)
        completed_days = sum(1 for day_list in completions_dict.values() if hid in day_list)
        stats[hid] = {
            "streak": streak,
            "total_completions": completed_days,
            "completion_rate": round(completed_days / total_days * 100, 1),
        }

    weekly = []
    for i in range(6, -1, -1):
        d = (date.today() - timedelta(days=i)).isoformat()
        weekly.append({
            "date": d,
            "completed": len(completions_dict.get(d, [])),
            "total": len(habits),
        })

    conn.close()
    return {"habit_stats": stats, "weekly": weekly, "user": dict(user)}


@app.delete("/reset")
def route_reset(user_id: str = Depends(get_current_user)):
    conn = get_db()
    conn.execute("DELETE FROM completions WHERE user_id=?", (user_id,))
    conn.execute("DELETE FROM habits WHERE user_id=?", (user_id,))
    conn.execute("UPDATE users SET xp=0, level=1 WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    return {"status": "reset"}