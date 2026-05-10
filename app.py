import streamlit as st
import requests
from datetime import date, timedelta
import os

# ── Config ────────────────────────────────────────────────────────────────────

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
TODAY        = date.today().isoformat()
TOKEN_COOKIE = "habitquest_token"

EMOJI_OPTIONS = ["⭐", "💪", "📚", "🏃", "🧘", "💧", "🎯", "🍎", "😴", "🎸", "✍️", "🧠"]
COLOR_OPTIONS = {
    "Violet":  "#8b5cf6",
    "Cyan":    "#06b6d4",
    "Rose":    "#f43f5e",
    "Amber":   "#f59e0b",
    "Emerald": "#10b981",
    "Sky":     "#0ea5e9",
}

# ── Page Setup ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="HabitQuest",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@300;400;500&display=swap');

  html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background: #0d0f14;
    color: #e2e8f0;
  }
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding: 2rem 3rem; max-width: 1100px; }

  /* Hero */
  .hero-title {
    font-family: 'Syne', sans-serif; font-weight: 800; font-size: 2.8rem;
    background: linear-gradient(135deg, #a78bfa 0%, #38bdf8 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    letter-spacing: -0.02em; margin: 0;
  }
  .hero-sub { font-size: 0.9rem; color: #64748b; margin-top: 0.25rem;
    letter-spacing: 0.05em; text-transform: uppercase; }

  /* XP bar */
  .xp-bar-wrap { background:#1e2130; border-radius:999px; height:10px; overflow:hidden; margin-top:6px; }
  .xp-bar-fill { height:100%; border-radius:999px;
    background:linear-gradient(90deg,#8b5cf6,#38bdf8); transition:width 0.5s ease; }

  /* Stat cards */
  .stat-card { background:#161924; border:1px solid #1e2130; border-radius:16px;
    padding:1.25rem 1.5rem; text-align:center; }
  .stat-number { font-family:'Syne',sans-serif; font-size:2rem; font-weight:800; color:#a78bfa; }
  .stat-label  { font-size:0.75rem; color:#64748b; text-transform:uppercase; letter-spacing:0.08em; }

  /* Habit card */
  .habit-card { background:#161924; border:1px solid #1e2130; border-radius:16px;
    padding:1rem 1.25rem; margin-bottom:0.6rem;
    display:flex; align-items:center; gap:1rem; }
  .habit-card.done { border-color:#8b5cf6; background:#1a1730; }
  .habit-name  { font-family:'Syne',sans-serif; font-weight:700; font-size:1rem; }
  .habit-meta  { font-size:0.78rem; color:#64748b; margin-top:3px; }
  .xp-badge    { margin-left:auto; background:#1e2130; border-radius:999px;
    padding:3px 12px; font-size:0.75rem; color:#f59e0b; font-weight:600; white-space:nowrap; }

  /* Section title */
  .section-title { font-family:'Syne',sans-serif; font-size:0.7rem; font-weight:700;
    letter-spacing:0.15em; text-transform:uppercase; color:#475569;
    margin-bottom:0.75rem; margin-top:2rem; }

  /* Week grid */
  .week-grid { display:flex; gap:0.5rem; margin-top:0.5rem; }
  .week-day  { flex:1; background:#161924; border-radius:10px; padding:0.5rem;
    text-align:center; font-size:0.7rem; color:#475569; }
  .week-day.active { background:#1a1730; border:1px solid #8b5cf6; color:#a78bfa; }
  .week-bar  { height:48px; border-radius:6px; margin:6px auto 4px; background:#1e2130;
    width:70%; position:relative; overflow:hidden; }
  .week-bar-fill { position:absolute; bottom:0; left:0; right:0;
    background:linear-gradient(180deg,#8b5cf6,#38bdf8); border-radius:6px; }

  /* Buttons */
  .stButton button {
    background:linear-gradient(135deg,#8b5cf6,#38bdf8) !important;
    color:white !important; border:none !important; border-radius:10px !important;
    font-family:'Syne',sans-serif !important; font-weight:700 !important;
    padding:0.5rem 1.5rem !important; transition:opacity 0.2s !important;
  }
  .stButton button:hover { opacity:0.85 !important; }

  /* Auth card */
  .auth-card { max-width:420px; margin:4rem auto; background:#161924;
    border:1px solid #1e2130; border-radius:20px; padding:2.5rem; }
  .auth-title { font-family:'Syne',sans-serif; font-size:1.6rem; font-weight:800;
    background:linear-gradient(135deg,#a78bfa,#38bdf8);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin-bottom:0.25rem; }
  .auth-sub { font-size:0.82rem; color:#64748b; margin-bottom:1.5rem; }

  /* Inputs */
  .stTextInput input {
    background:#0d0f14 !important; border:1px solid #2d3148 !important;
    border-radius:10px !important; color:#e2e8f0 !important;
    font-size:0.95rem !important; padding:0.6rem 0.9rem !important;
  }
  .stTextInput input:focus { border-color:#8b5cf6 !important; }
  .stSelectbox > div > div {
    background:#0d0f14 !important; border:1px solid #2d3148 !important;
    border-radius:10px !important; color:#e2e8f0 !important;
  }

  /* Delete button */
  .del-btn button {
    background:transparent !important; border:1px solid #2d3148 !important;
    color:#f43f5e !important; font-size:0.8rem !important;
    padding:0.25rem 0.75rem !important; border-radius:8px !important;
  }
  .del-btn button:hover { border-color:#f43f5e !important; }

  /* Logout link style */
  .logout-btn button {
    background:transparent !important; border:1px solid #2d3148 !important;
    color:#64748b !important; font-size:0.75rem !important;
    padding:0.25rem 0.9rem !important; border-radius:8px !important;
  }

  hr.divider { border-color:#1e2130; margin:1.5rem 0; }
</style>
""", unsafe_allow_html=True)


# ── API Helpers ───────────────────────────────────────────────────────────────

def _auth_headers() -> dict:
    token = st.session_state.get("token", "")
    return {"Authorization": f"Bearer {token}"} if token else {}


def _save_token(response: requests.Response):
    token = response.cookies.get(TOKEN_COOKIE)
    if token:
        st.session_state["token"] = token


def api_get(path: str) -> dict:
    try:
        r = requests.get(f"{API_BASE}{path}", headers=_auth_headers(), timeout=5)
        _save_token(r)
        if r.status_code == 401:
            st.session_state.pop("token", None)
            st.session_state.pop("username", None)
            st.rerun()
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return {}


def api_post(path: str, payload: dict) -> dict:
    try:
        r = requests.post(f"{API_BASE}{path}", json=payload, headers=_auth_headers(), timeout=5)
        _save_token(r)
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return {}


def api_delete(path: str) -> dict:
    try:
        r = requests.delete(f"{API_BASE}{path}", headers=_auth_headers(), timeout=5)
        _save_token(r)
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return {}


# Cached per-rerun — only called ONCE per page load, not once per widget
@st.cache_data(ttl=2, show_spinner=False)
def fetch_data(token: str):
    """Cache keyed by token so different users don't share data."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        data  = requests.get(f"{API_BASE}/data",  headers=headers, timeout=5).json()
        stats = requests.get(f"{API_BASE}/stats", headers=headers, timeout=5).json()
        return data, stats
    except Exception:
        return {}, {}


# ── XP Utils ─────────────────────────────────────────────────────────────────

def xp_for_level(level: int) -> int:
    return sum(l * 50 for l in range(1, level))

def xp_progress(xp: int, level: int):
    base   = xp_for_level(level)
    needed = level * 50
    return xp - base, needed


# ── Auth Screens ──────────────────────────────────────────────────────────────

def show_auth():
    st.markdown("""
    <div style="text-align:center;margin-top:3rem;">
      <p class="hero-title" style="font-size:2.2rem;">⚔️ HabitQuest</p>
      <p class="hero-sub">Build streaks. Earn XP. Level up your life.</p>
    </div>
    """, unsafe_allow_html=True)

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        st.markdown("<br>", unsafe_allow_html=True)
        col, _, _ = st.columns([1.8, 1, 1])
        with col:
            username = st.text_input("Username", key="login_user", placeholder="your username")
            password = st.text_input("Password", key="login_pass", type="password", placeholder="••••••••")
            if st.button("Login →", use_container_width=True, key="btn_login"):
                if username and password:
                    res = api_post("/login", {"username": username, "password": password})
                    if "status" in res and res["status"] == "ok":
                        st.session_state["username"] = res["username"]
                        st.toast(f"Welcome back, {res['username']}! 🎉")
                        st.rerun()
                    else:
                        st.error(res.get("detail", "Login failed"))
                else:
                    st.warning("Please fill in both fields.")

    with tab_register:
        st.markdown("<br>", unsafe_allow_html=True)
        col, _, _ = st.columns([1.8, 1, 1])
        with col:
            new_user = st.text_input("Choose a username", key="reg_user", placeholder="min. 3 characters")
            new_pass = st.text_input("Choose a password", key="reg_pass", type="password", placeholder="min. 6 characters")
            if st.button("Create Account →", use_container_width=True, key="btn_register"):
                if new_user and new_pass:
                    res = api_post("/register", {"username": new_user, "password": new_pass})
                    if "status" in res and res["status"] == "registered":
                        st.session_state["username"] = res["username"]
                        st.toast(f"Account created! Welcome, {res['username']} 🌱")
                        st.rerun()
                    else:
                        st.error(res.get("detail", "Registration failed"))
                else:
                    st.warning("Please fill in both fields.")


# ── Main App ──────────────────────────────────────────────────────────────────

def main():
    token = st.session_state.get("token", "")
    data, stats = fetch_data(token)

    habits      = data.get("habits", {})
    completions = data.get("completions", {})
    user        = data.get("user", {"xp": 0, "level": 1})
    habit_stats = stats.get("habit_stats", {})
    weekly      = stats.get("weekly", [])

    today_done  = completions.get(TODAY, [])
    xp          = user.get("xp", 0)
    level       = user.get("level", 1)
    xp_cur, xp_next = xp_progress(xp, level)
    best_streak = max((habit_stats.get(h, {}).get("streak", 0) for h in habits), default=0)

    # ── Header ────────────────────────────────────────────────────────────────
    col_title, col_level, col_logout = st.columns([3, 1.2, 0.6])

    with col_title:
        st.markdown('<p class="hero-title">⚔️ HabitQuest</p>', unsafe_allow_html=True)
        username = st.session_state.get("username", "")
        st.markdown(f'<p class="hero-sub">{"Welcome back, " + username + " ·" if username else ""} Build streaks. Earn XP.</p>', unsafe_allow_html=True)

    with col_level:
        pct = min(100, int(xp_cur / xp_next * 100)) if xp_next else 0
        st.markdown(f"""
        <div style="text-align:right;padding-top:0.5rem;">
          <span style="font-family:Syne;font-size:0.75rem;color:#64748b;text-transform:uppercase;letter-spacing:0.1em;">Level</span>
          <span style="font-family:Syne;font-size:2rem;font-weight:800;color:#a78bfa;margin-left:0.5rem;">{level}</span>
          <div style="font-size:0.7rem;color:#64748b;margin-top:2px;">{xp_cur} / {xp_next} XP</div>
          <div class="xp-bar-wrap"><div class="xp-bar-fill" style="width:{pct}%"></div></div>
        </div>
        """, unsafe_allow_html=True)

    with col_logout:
        st.markdown("<div style='padding-top:1.4rem;'>", unsafe_allow_html=True)
        st.markdown('<div class="logout-btn">', unsafe_allow_html=True)
        if st.button("Logout", key="btn_logout"):
            api_post("/logout", {})
            st.session_state.clear()
            st.cache_data.clear()
            st.rerun()
        st.markdown("</div></div>", unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ── Stat Cards ────────────────────────────────────────────────────────────
    s1, s2, s3, s4 = st.columns(4)
    for col, num, label in [
        (s1, len(today_done),  "Done Today"),
        (s2, len(habits),      "Total Habits"),
        (s3, best_streak,      "Best Streak 🔥"),
        (s4, xp,               "Total XP ⚡"),
    ]:
        col.markdown(f"""
        <div class="stat-card">
          <div class="stat-number">{num}</div>
          <div class="stat-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Main Columns ──────────────────────────────────────────────────────────
    left, right = st.columns([3, 2], gap="large")

    # ── LEFT: Today's Habits ──────────────────────────────────────────────────
    with left:
        st.markdown('<div class="section-title">Today\'s Habits</div>', unsafe_allow_html=True)

        if not habits:
            st.markdown("""
            <div style="background:#161924;border:1px dashed #2d3148;border-radius:16px;
                        padding:2.5rem;text-align:center;color:#475569;">
              <div style="font-size:2rem;margin-bottom:0.5rem;">🌱</div>
              <div style="font-family:Syne;font-weight:700;font-size:1rem;">No habits yet</div>
              <div style="font-size:0.82rem;margin-top:0.3rem;">Add your first habit to begin your quest →</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for hid, habit in habits.items():
                is_done   = hid in today_done
                hstats    = habit_stats.get(hid, {})
                streak    = hstats.get("streak", 0)
                rate      = hstats.get("completion_rate", 0)
                done_cls  = "done" if is_done else ""

                col_card, col_btn, col_del = st.columns([6, 1.6, 0.8])

                with col_card:
                    st.markdown(f"""
                    <div class="habit-card {done_cls}">
                      <span style="font-size:1.75rem;">{habit['emoji']}</span>
                      <div style="flex:1;">
                        <div class="habit-name" style="color:{habit['color']};">{habit['name']}</div>
                        <div class="habit-meta">🔥 {streak}-day streak &nbsp;·&nbsp; {rate}% completion</div>
                      </div>
                      <div class="xp-badge">+10 XP</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col_btn:
                    label = "✅ Done" if is_done else "⬜ Mark"
                    if st.button(label, key=f"check_{hid}"):
                        result = api_post("/complete", {"habit_id": hid, "date": TODAY})
                        st.cache_data.clear()
                        if result.get("status") == "completed":
                            st.toast(f"🎉 +10 XP! {habit['name']} done!", icon="⚡")
                        else:
                            st.toast(f"↩️ {habit['name']} unchecked", icon="🔄")
                        st.rerun()

                with col_del:
                    st.markdown('<div class="del-btn">', unsafe_allow_html=True)
                    if st.button("🗑️", key=f"del_{hid}", help="Delete habit"):
                        api_delete(f"/habits/{hid}")
                        st.cache_data.clear()
                        st.toast(f"Deleted: {habit['name']}", icon="🗑️")
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

        # ── 7-Day Activity ────────────────────────────────────────────────────
        st.markdown('<div class="section-title" style="margin-top:2rem;">7-Day Activity</div>', unsafe_allow_html=True)
        if weekly:
            day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            cols = st.columns(7)
            for col, w in zip(cols, weekly):
                day_str  = w["date"]
                done_n   = w["completed"]
                total_n  = max(1, w["total"])
                pct      = int(done_n / total_n * 100)
                is_today = day_str == TODAY
                day_name = day_labels[date.fromisoformat(day_str).weekday()]
                active_cls = "active" if is_today else ""
                col.markdown(f"""
                <div class="week-day {active_cls}">
                  <div class="week-bar">
                    <div class="week-bar-fill" style="height:{pct}%;"></div>
                  </div>
                  <div>{day_name}</div>
                  <div style="color:#a78bfa;font-weight:600;">{done_n}/{total_n}</div>
                </div>
                """, unsafe_allow_html=True)

    # ── RIGHT: Add Habit + Achievements ──────────────────────────────────────
    with right:
        st.markdown('<div class="section-title" style="margin-top:0;">Add New Habit</div>', unsafe_allow_html=True)

        with st.container():
            st.markdown('<div style="background:#161924;border:1px solid #1e2130;border-radius:16px;padding:1.25rem;">', unsafe_allow_html=True)
            habit_name = st.text_input("Habit name", placeholder="e.g. Morning run", label_visibility="collapsed", key="new_habit_name")
            ecol, ccol = st.columns(2)
            with ecol:
                chosen_emoji = st.selectbox("Emoji", EMOJI_OPTIONS, label_visibility="collapsed")
            with ccol:
                chosen_color_name = st.selectbox("Color", list(COLOR_OPTIONS.keys()), label_visibility="collapsed")

            if st.button("➕ Add Habit", use_container_width=True, key="btn_add"):
                if habit_name.strip():
                    api_post("/habits", {
                        "name":  habit_name.strip(),
                        "emoji": chosen_emoji,
                        "color": COLOR_OPTIONS[chosen_color_name],
                    })
                    st.cache_data.clear()
                    st.toast(f"'{habit_name}' added!", icon="🌱")
                    st.rerun()
                else:
                    st.warning("Please enter a habit name.")
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Achievements ──────────────────────────────────────────────────────
        st.markdown('<div class="section-title" style="margin-top:1.5rem;">Achievements</div>', unsafe_allow_html=True)
        achievements = [
            ("🌱", "First Step",   xp >= 10,                           "Complete your first habit"),
            ("🔥", "On Fire",      best_streak >= 3,                   "3-day streak on any habit"),
            ("⚡", "XP Grinder",   xp >= 100,                          "Earn 100 XP total"),
            ("🏆", "Level 5 Hero", level >= 5,                         "Reach level 5"),
            ("💎", "Perfect Day",  any(
                w["completed"] >= w["total"] > 0 for w in weekly),     "Complete all habits in a day"),
            ("🚀", "Habit Master", len(habits) >= 5,                   "Track 5+ habits"),
        ]
        for emoji, title, unlocked, desc in achievements:
            opacity = "1" if unlocked else "0.3"
            badge   = "✅" if unlocked else "🔒"
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:0.75rem;
                        background:#161924;border:1px solid #1e2130;border-radius:12px;
                        padding:0.65rem 0.9rem;margin-bottom:0.5rem;opacity:{opacity};">
              <span style="font-size:1.4rem;">{emoji}</span>
              <div>
                <div style="font-family:Syne;font-size:0.85rem;font-weight:700;">{title} {badge}</div>
                <div style="font-size:0.72rem;color:#64748b;">{desc}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Danger Zone ───────────────────────────────────────────────────────
        st.markdown('<div class="section-title" style="margin-top:1.5rem;">Danger Zone</div>', unsafe_allow_html=True)
        if st.button("🗑️ Reset All Data", use_container_width=True, key="btn_reset"):
            api_delete("/reset")
            st.cache_data.clear()
            st.toast("All data reset.", icon="🗑️")
            st.rerun()


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if "token" not in st.session_state:
        show_auth()
    else:
        main()