import asyncio
import json
import os
import re
import time
from datetime import datetime, timedelta

import nest_asyncio
import streamlit as st
from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from fitness_agent.agent import root_agent
from fitness_agent.utils.calculations import calculate_bmi, calculate_tdee, calculate_macros
from auth import is_authenticated, render_login_page, render_user_badge

nest_asyncio.apply()
load_dotenv("fitness_agent/.env")

APP_NAME = "fitness_agent"
USER_ID = "default_user"
HISTORY_FILE = "fitness_agent/data/user_history.json"


# ── Persistence: Workout Log + Streaks ───────────────────────────────────────

def _load_history() -> dict:
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return {"sessions": [], "workout_log": [], "weight_log": []}


def _save_history(data: dict):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=2)


def log_session():
    history = _load_history()
    today = datetime.now().strftime("%Y-%m-%d")
    if today not in history["sessions"]:
        history["sessions"].append(today)
    _save_history(history)


def log_weight(weight: float):
    history = _load_history()
    today = datetime.now().strftime("%Y-%m-%d")
    history["weight_log"] = [
        e for e in history["weight_log"] if e["date"] != today
    ]
    history["weight_log"].append({"date": today, "weight": weight})
    _save_history(history)


def get_streak() -> int:
    history = _load_history()
    sessions = sorted(set(history.get("sessions", [])), reverse=True)
    if not sessions:
        return 0
    streak = 0
    today = datetime.now().date()
    for i, date_str in enumerate(sessions):
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        expected = today - timedelta(days=i)
        if d == expected:
            streak += 1
        else:
            break
    return streak


def get_weight_history() -> list:
    history = _load_history()
    return history.get("weight_log", [])


# ── Styling ──────────────────────────────────────────────────────────────────

def inject_css():
    st.markdown("""
    <style>
        .main .block-container { max-width: 920px; padding-top: 1.5rem; }

        .hero-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.8rem 2.2rem;
            border-radius: 16px;
            margin-bottom: 1.2rem;
            color: white;
        }
        .hero-header h1 { margin: 0; font-size: 1.8rem; font-weight: 700; }
        .hero-header p { margin: 0.4rem 0 0 0; opacity: 0.9; font-size: 0.95rem; }

        .stats-row {
            display: flex; gap: 0.8rem; margin-bottom: 1rem; flex-wrap: wrap;
        }
        .stat-card {
            flex: 1; min-width: 120px;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 1rem 1.2rem;
            border-radius: 12px;
            text-align: center;
            color: white;
        }
        .stat-card .stat-value {
            font-size: 1.6rem; font-weight: 700;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .stat-card .stat-label { font-size: 0.75rem; opacity: 0.7; margin-top: 0.2rem; }

        .profile-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 1rem 1.3rem;
            border-radius: 12px;
            margin-bottom: 1rem;
            border-left: 4px solid #667eea;
        }
        .profile-card h4 { margin: 0 0 0.2rem 0; color: #333; font-size: 0.9rem; }
        .profile-card p { margin: 0; color: #555; font-size: 0.8rem; }

        .stChatMessage { border-radius: 12px !important; }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        }
        section[data-testid="stSidebar"] .stMarkdown { color: #e0e0e0; }
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 { color: #ffffff !important; }
        section[data-testid="stSidebar"] label { color: #ccc !important; }

        div[data-testid="stStatusWidget"] { display: none; }

        .yt-embed { border-radius: 12px; margin: 0.5rem 0; }
    </style>
    """, unsafe_allow_html=True)


# ── ADK Session Management ───────────────────────────────────────────────────

def get_runner():
    if "adk_runner" not in st.session_state:
        session_service = InMemorySessionService()
        runner = Runner(
            agent=root_agent,
            app_name=APP_NAME,
            session_service=session_service,
        )
        st.session_state["adk_runner"] = runner
        st.session_state["adk_session_service"] = session_service
    return st.session_state["adk_runner"]


def get_or_create_session(runner: Runner):
    if "adk_session_id" not in st.session_state:
        session_id = f"session_{int(time.time())}_{os.urandom(4).hex()}"
        st.session_state["adk_session_id"] = session_id

        session_service = st.session_state["adk_session_service"]
        loop = asyncio.get_event_loop()
        loop.run_until_complete(session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session_id,
            state={},
        ))
    return st.session_state["adk_session_id"]


async def _run_agent(runner: Runner, session_id: str, message: str) -> str:
    content = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=message)],
    )
    final_text = ""
    try:
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=session_id,
            new_message=content,
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        if event.is_final_response():
                            final_text += part.text
    except Exception as e:
        return f"Error: {e}"
    return final_text or "I'm sorry, I couldn't process that. Could you try again?"


def run_agent(runner: Runner, session_id: str, message: str) -> str:
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_run_agent(runner, session_id, message))


# ── YouTube Embed Helper ─────────────────────────────────────────────────────

def _extract_video_id(url: str) -> str | None:
    patterns = [
        r"youtu\.be/([a-zA-Z0-9_-]{11})",
        r"youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})",
        r"youtube\.com/embed/([a-zA-Z0-9_-]{11})",
    ]
    for pat in patterns:
        m = re.search(pat, url)
        if m:
            return m.group(1)
    return None


def render_message_with_embeds(text: str):
    """Render markdown text and convert YouTube URLs into embedded players."""
    url_pattern = r"(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)[a-zA-Z0-9_-]{11}[^\s\)]*)"
    parts = re.split(url_pattern, text)

    seen_ids = set()
    for part in parts:
        vid = _extract_video_id(part)
        if vid and vid not in seen_ids:
            seen_ids.add(vid)
            st.markdown(part)
            st.markdown(
                f'<iframe class="yt-embed" width="100%" height="315" '
                f'src="https://www.youtube.com/embed/{vid}" '
                f'frameborder="0" allow="accelerometer; autoplay; clipboard-write; '
                f'encrypted-media; gyroscope; picture-in-picture" '
                f'allowfullscreen></iframe>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(part)


# ── Sidebar ──────────────────────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        st.markdown("## Your Profile")

        with st.expander("Body Stats", expanded=not st.session_state.get("profile_saved")):
            name = st.text_input("Name", value=st.session_state.get("profile_name", ""), key="inp_name")
            col1, col2 = st.columns(2)
            age = col1.number_input("Age", min_value=14, max_value=80, value=st.session_state.get("profile_age", 25), key="inp_age")
            gender = col2.selectbox("Gender", ["Male", "Female"], index=0, key="inp_gender")
            col3, col4 = st.columns(2)
            weight = col3.number_input("Weight (kg)", min_value=30.0, max_value=200.0, value=st.session_state.get("profile_weight", 70.0), step=0.5, key="inp_weight")
            height = col4.number_input("Height (cm)", min_value=100.0, max_value=220.0, value=st.session_state.get("profile_height", 170.0), step=0.5, key="inp_height")

        with st.expander("Fitness Preferences", expanded=not st.session_state.get("profile_saved")):
            goal = st.selectbox("Fitness Goal", [
                "Fat Loss", "Weight Gain", "Muscle Building", "Health Maintenance",
            ], key="inp_goal")
            col5, col6 = st.columns(2)
            fitness_level = col5.selectbox("Level", ["Beginner", "Intermediate", "Advanced"], key="inp_level")
            equipment = col6.selectbox("Equipment", [
                "None (Home only)", "Basic (Dumbbells, Bands)", "Full Gym",
            ], key="inp_equip")
            workout_days = st.slider("Days / Week", min_value=3, max_value=6, value=st.session_state.get("profile_days", 5), key="inp_days")

        with st.expander("Diet Preferences", expanded=not st.session_state.get("profile_saved")):
            col7, col8 = st.columns(2)
            diet_pref = col7.selectbox("Diet", ["Vegetarian", "Non-Vegetarian", "Vegan", "Eggetarian"], key="inp_diet")
            cuisine_pref = col8.selectbox("Cuisine", ["Indian", "Western", "Flexible"], key="inp_cuisine")

        if st.button("Save Profile", use_container_width=True, type="primary"):
            if name.strip():
                st.session_state["profile_name"] = name
                st.session_state["profile_age"] = age
                st.session_state["profile_weight"] = weight
                st.session_state["profile_height"] = height
                st.session_state["profile_gender"] = gender.lower()
                st.session_state["profile_goal"] = goal
                st.session_state["profile_fitness_level"] = fitness_level
                st.session_state["profile_diet_pref"] = diet_pref
                st.session_state["profile_cuisine_pref"] = cuisine_pref
                st.session_state["profile_days"] = workout_days
                st.session_state["profile_equipment"] = equipment
                st.session_state["profile_saved"] = True
                log_weight(weight)
                log_session()
                st.rerun()
            else:
                st.warning("Please enter your name.")

        if st.session_state.get("profile_saved"):
            st.success(f"Profile saved for {st.session_state['profile_name']}!")

        st.divider()

        # Weight tracker
        if st.session_state.get("profile_saved"):
            with st.expander("Log Today's Weight"):
                new_w = st.number_input("Weight (kg)", min_value=30.0, max_value=200.0,
                                        value=st.session_state.get("profile_weight", 70.0),
                                        step=0.1, key="log_weight_inp")
                if st.button("Log Weight", use_container_width=True):
                    log_weight(new_w)
                    st.session_state["profile_weight"] = new_w
                    st.toast("Weight logged!")

        if st.button("Reset Chat", use_container_width=True):
            for key in ["messages", "adk_session_id", "thinking"]:
                st.session_state.pop(key, None)
            st.rerun()


def get_profile_summary() -> str | None:
    if not st.session_state.get("profile_saved"):
        return None

    goal_map = {"Fat Loss": "fat_loss", "Weight Gain": "weight_gain",
                "Muscle Building": "muscle_building", "Health Maintenance": "health_maintenance"}
    diet_map = {"Vegetarian": "vegetarian", "Non-Vegetarian": "non_vegetarian",
                "Vegan": "vegan", "Eggetarian": "eggetarian"}
    cuisine_map = {"Indian": "indian", "Western": "western", "Flexible": "flexible"}
    equip_map = {"None (Home only)": "none", "Basic (Dumbbells, Bands)": "basic", "Full Gym": "full_gym"}

    return (
        f"My profile: Name={st.session_state['profile_name']}, "
        f"Age={st.session_state['profile_age']}, "
        f"Weight={st.session_state['profile_weight']}kg, "
        f"Height={st.session_state['profile_height']}cm, "
        f"Gender={st.session_state['profile_gender']}, "
        f"Goal={goal_map.get(st.session_state['profile_goal'], 'health_maintenance')}, "
        f"Fitness Level={st.session_state['profile_fitness_level'].lower()}, "
        f"Diet Preference={diet_map.get(st.session_state['profile_diet_pref'], 'vegetarian')}, "
        f"Cuisine={cuisine_map.get(st.session_state['profile_cuisine_pref'], 'indian')}, "
        f"Workout Days/Week={st.session_state['profile_days']}, "
        f"Equipment={equip_map.get(st.session_state['profile_equipment'], 'none')}."
    )


# ── Stats Dashboard ──────────────────────────────────────────────────────────

def render_stats_dashboard():
    if not st.session_state.get("profile_saved"):
        return

    p = st.session_state
    bmi = calculate_bmi(p["profile_weight"], p["profile_height"])
    streak = get_streak()
    weight_hist = get_weight_history()

    goal_map = {"Fat Loss": "fat_loss", "Weight Gain": "weight_gain",
                "Muscle Building": "muscle_building", "Health Maintenance": "health_maintenance"}
    tdee = calculate_tdee(
        p["profile_weight"], p["profile_height"], p["profile_age"],
        p["profile_days"], goal_map.get(p["profile_goal"], "health_maintenance"),
        p.get("profile_gender", "male"),
    )
    macros = calculate_macros(tdee["target_calories"], goal_map.get(p["profile_goal"], "health_maintenance"))

    weight_delta = ""
    if len(weight_hist) >= 2:
        diff = weight_hist[-1]["weight"] - weight_hist[0]["weight"]
        arrow = "↓" if diff < 0 else "↑" if diff > 0 else "→"
        weight_delta = f"<br><span style='font-size:0.7rem;opacity:0.8'>{arrow} {abs(diff):.1f}kg total</span>"

    st.markdown(f"""
    <div class="stats-row">
        <div class="stat-card">
            <div class="stat-value">{bmi['bmi']}</div>
            <div class="stat-label">BMI · {bmi['category']}</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{int(tdee['target_calories'])}</div>
            <div class="stat-label">Daily Calories</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{int(macros['protein_g'])}g</div>
            <div class="stat-label">Protein Target</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{streak}</div>
            <div class="stat-label">Day Streak 🔥</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{p['profile_weight']}kg</div>
            <div class="stat-label">Current Weight{weight_delta}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Main Chat Area ──────────────────────────────────────────────────────────

def render_chat():
    inject_css()

    provider = os.environ.get("MODEL_PROVIDER", "gemini").lower()
    api_key = os.environ.get("GOOGLE_API_KEY")
    if provider == "gemini" and (not api_key or api_key == "your_google_api_key_here"):
        st.error("Please set your `GOOGLE_API_KEY` in `fitness_agent/.env` to get started.")
        st.code("echo 'GOOGLE_API_KEY=your_key' > fitness_agent/.env", language="bash")
        st.stop()

    # Personalized header
    if st.session_state.get("profile_saved"):
        name = st.session_state["profile_name"].split()[0]
        hour = datetime.now().hour
        greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"
        st.markdown(f"""
        <div class="hero-header">
            <h1>{greeting}, {name}!</h1>
            <p>Your FitCoach is ready — let's work towards your {st.session_state['profile_goal'].lower()} goal today.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="hero-header">
            <h1>FitCoach AI</h1>
            <p>Your personal AI fitness coach — workout plans, diet plans, and video recommendations tailored to you.</p>
        </div>
        """, unsafe_allow_html=True)
        st.info("Fill in your profile in the sidebar to get personalized recommendations.")

    # Stats dashboard
    render_stats_dashboard()

    runner = get_runner()
    session_id = get_or_create_session(runner)

    # Profile card
    if st.session_state.get("profile_saved"):
        p = st.session_state
        goal_emoji = {"Fat Loss": "🔥", "Weight Gain": "📈", "Muscle Building": "💪", "Health Maintenance": "🧘"}.get(p.get("profile_goal", ""), "🏋️")
        st.markdown(f"""
        <div class="profile-card">
            <h4>{goal_emoji} {p['profile_name']} — {p['profile_goal']} · {p['profile_fitness_level']}</h4>
            <p>{p['profile_age']}y · {p['profile_weight']}kg · {p['profile_height']}cm · {p['profile_diet_pref']} {p['profile_cuisine_pref']} · {p['profile_days']}d/wk · {p['profile_equipment']}</p>
        </div>
        """, unsafe_allow_html=True)

    # Chat history
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

        profile_summary = get_profile_summary()
        if profile_summary:
            intro_msg = profile_summary + " Please greet me by name and briefly tell me what you can help with."
            with st.status("Setting up your coach...", expanded=True) as status:
                st.write("Analyzing your profile...")
                response = run_agent(runner, session_id, intro_msg)
                status.update(label="Ready!", state="complete", expanded=False)
            st.session_state["messages"].append({"role": "assistant", "content": response})

    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                render_message_with_embeds(msg["content"])
            else:
                st.markdown(msg["content"])

    is_thinking = st.session_state.get("pending_prompt") is not None

    # Quick action buttons
    if st.session_state.get("profile_saved") and len(st.session_state["messages"]) <= 1 and not is_thinking:
        cols = st.columns(4)
        actions = [
            ("🏋️ Workout Plan", "Give me a complete workout plan based on my profile."),
            ("🥗 Diet Plan", "Give me a complete diet plan based on my profile."),
            ("📺 Videos", "Recommend YouTube videos for my goal."),
            ("📋 Everything", "Give me a workout plan, diet plan, and YouTube video recommendations based on my profile."),
        ]
        for col, (label, prompt) in zip(cols, actions):
            if col.button(label, use_container_width=True):
                st.session_state["pending_prompt"] = prompt
                st.rerun()

    # Chat input -- disabled while processing
    user_input = st.chat_input(
        "FitCoach is thinking... please wait" if is_thinking else "Ask me anything about fitness, workouts, or nutrition...",
        disabled=is_thinking,
    )
    if user_input and not is_thinking:
        st.session_state["pending_prompt"] = user_input
        st.rerun()

    # Phase 2: Process pending prompt (runs after rerun with input disabled)
    if is_thinking:
        prompt = st.session_state.pop("pending_prompt")
        _handle_prompt(runner, session_id, prompt)
        st.rerun()


def _handle_prompt(runner: Runner, session_id: str, prompt: str):
    """Render user message, show spinner, get response -- saves to session state."""
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    profile_context = ""
    if st.session_state.get("profile_saved") and len(st.session_state["messages"]) <= 2:
        profile_context = get_profile_summary() + "\n\nUser request: "

    full_message = profile_context + prompt

    with st.chat_message("assistant"):
        with st.spinner("FitCoach is thinking..."):
            response = run_agent(runner, session_id, full_message)
        render_message_with_embeds(response)

    st.session_state["messages"].append({"role": "assistant", "content": response})
    log_session()


# ── Entry Point ──────────────────────────────────────────────────────────────

def main():
    if is_authenticated():
        st.set_page_config(
            page_title="FitCoach AI",
            page_icon="💪",
            layout="wide",
            initial_sidebar_state="expanded",
        )
        render_user_badge()
        render_sidebar()
        render_chat()
    else:
        st.set_page_config(
            page_title="FitCoach AI — Login",
            page_icon="💪",
            layout="centered",
        )
        render_login_page()


if __name__ == "__main__":
    main()
