import streamlit as st
import speech_recognition as sr
from pydub import AudioSegment
from io import BytesIO
import pandas as pd
import os
import json
import time
import hashlib
import threading
import queue

# ---------------------- CONFIG & SESSION STATE ----------------------
st.set_page_config(page_title="Takti Stats Tracker", layout="centered")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "data_rows" not in st.session_state:
    st.session_state.data_rows = []  # List of dicts for the table
if "recording_thread" not in st.session_state:
    st.session_state.recording_thread = None
if "stop_recording" not in st.session_state:
    st.session_state.stop_recording = False

HASHED_PASSWORD = hashlib.sha256("1234567".encode()).hexdigest()

# ---------------------- KEYWORD BANK ----------------------
KEYWORDS = {
    "shot", "shoots", "fires", "strikes", "header", "volley", "curls", "blasts", "taps in", "finishes", "scores", "goal",
    "on target", "off target", "wide", "over the bar", "saved", "blocked",
    "assist", "cross", "through ball", "cut-back", "sets up",
    "pass", "long ball", "switch", "diagonal", "intercepted",
    "dribble", "beats", "takes on", "skips past",
    "tackle", "interception", "block", "clearance", "foul",
    "progressive", "carries", "drives forward", "final third", "breaks lines",
    "left wing", "right wing", "edge of the box", "inside the box",
    "run", "makes a run", "ghosts in", "in behind",
    "high press", "counter-attack", "compact", "high line",
    "sprint", "bursts", "covers ground", "tracks back", "relentless",
    "tired", "leggy", "fading", "heavy legs",
    "dominating", "in control", "camped in",
    "under pressure", "composed", "clinical"
}
KEYWORDS = {kw.lower() for kw in KEYWORDS}

# ---------------------- TEAM SHEET ----------------------
TEAM_FILE = "team_data.json"

def load_team():
    if os.path.exists(TEAM_FILE):
        with open(TEAM_FILE, "r") as f:
            return json.load(f)
    return {"coach": "", "assistant": "", "players": []}

def save_team(data):
    with open(TEAM_FILE, "w") as f:
        json.dump(data, f)

def get_player_names():
    team = load_team()
    return {p["name"].strip().lower() for p in team["players"] if p["name"].strip()}

# ---------------------- LOGIN PAGE ----------------------
def login_page():
    st.title("⚽ Takti Stats Tracker")
    st.markdown("### Professional Football Statistics Management")

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if username == "dreamteam" and hashlib.sha256(password.encode()).hexdigest() == HASHED_PASSWORD:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid credentials")

# ---------------------- MAIN APP ----------------------
def main_app():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Team Sheet", "Match Tracker"])

    PLAYERS = get_player_names()

    if page == "Team Sheet":
        st.header("Team Sheet Setup")
        team = load_team()

        team["coach"] = st.text_input("Coach Name", value=team.get("coach", ""))
        team["assistant"] = st.text_input("Assistant Coach", value=team.get("assistant", ""))

        num_players = st.number_input("Squad Size", min_value=11, max_value=30, value=len(team["players"]) or 18)
        positions = ['GK','CB','RCB','LCB','RB','LB','WB','RWB','LWB','DM','CDM','CM','AM','CAM','RM','LM','WM','RW','LW','ST','CF','SS','WF']

        new_players = []
        jerseys = set()
        for i in range(num_players):
            col1, col2, col3 = st.columns([4,2,3])
            name = col1.text_input("Player Name", key=f"n{i}")
            jersey = col2.text_input("Jersey", key=f"j{i}")
            pos = col3.selectbox("Position", positions, key=f"p{i}")

            if name.strip():
                if jersey and jersey in jerseys:
                    st.error(f"Jersey {jersey} duplicate!")
                else:
                    if jersey:
                        jerseys.add(jersey)
                    new_players.append({"name": name, "jersey": jersey, "position": pos})

        team["players"] = new_players
        if st.button("Save Team Sheet"):
            save_team(team)
            st.success("Team sheet saved!")
            st.rerun()

    elif page == "Match Tracker":
        st.header("Live Commentary Tracker")

        # Timer / Duration settings
        col1, col2 = st.columns(2)
        half_mins = col1.number_input("Half Length (minutes)", min_value=1, value=45)
        halftime_mins = col2.number_input("Halftime (minutes)", min_value=0, value=15)

        total_seconds = (half_mins * 60 * 2) + (halftime_mins * 60)

        st.info(f"Total recording time will be approximately **{total_seconds // 60} minutes** (2 halves + halftime)")

        # Data table placeholder
        table_placeholder = st.empty()
        export_col = st.empty()

        if st.button("Start Recording & Tracking"):
            st.session_state.data_rows = []
            st.session_state.stop_recording = False

            # Queue for thread communication
            audio_queue = queue.Queue()

            def recording_thread():
                r = sr.Recognizer()
                mic = sr.Microphone()

                start_time = time.time()
                half1_end = half_mins * 60
                halftime_end = half1_end + (halftime_mins * 60)
                total_end = halftime_end + (half_mins * 60)

                with mic as source:
                    r.adjust_for_ambient_noise(source)

                st.write("🎙️ Listening... Recording in progress.")

                while time.time() - start_time < total_end and not st.session_state.stop_recording:
                    try:
                        audio = r.listen(source, timeout=5, phrase_time_limit=8)
                        text = r.recognize_google(audio).lower()

                        words = text.split()
                        filtered = [w for w in words if w in KEYWORDS or w in PLAYERS]

                        if filtered:
                            timestamp = time.strftime("%H:%M:%S")
                            match_time = time.strftime("%M:%S", time.gmtime(time.time() - start_time))
                            row = {
                                "Match Time": match_time,
                                "Real Time": timestamp,
                                "Filtered Words": " ".join(filtered)
                            }
                            st.session_state.data_rows.append(row)

                            # Update table live
                            df = pd.DataFrame(st.session_state.data_rows)
                            table_placeholder.dataframe(df, use_container_width=True)

                    except sr.WaitTimeoutError:
                        continue
                    except sr.UnknownValueError:
                        continue
                    except Exception as e:
                        st.error(f"Error: {e}")
                        break

                st.success("Recording finished!")

            # Start thread
            st.session_state.recording_thread = threading.Thread(target=recording_thread, daemon=True)
            st.session_state.recording_thread.start()

        if st.button("Stop Recording Early"):
            st.session_state.stop_recording = True
            st.warning("Stopping...")

        # Live table
        if st.session_state.data_rows:
            df = pd.DataFrame(st.session_state.data_rows)
            table_placeholder.dataframe(df, use_container_width=True)

            # Export buttons
            csv = df.to_csv(index=False).encode()
            excel = BytesIO()
            df.to_excel(excel, index=False)
            excel.seek(0)

            col1, col2 = export_col.columns(2)
            col1.download_button("Download CSV", csv, "commentary_data.csv", "text/csv")
            col2.download_button("Download Excel", excel.getvalue(), "commentary_data.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ---------------------- RUN APP ----------------------
if not st.session_state.logged_in:
    login_page()
else:
    main_app()
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
