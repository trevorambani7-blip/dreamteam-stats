import streamlit as st
import pandas as pd
import os
import json
import time
import hashlib
from streamlit_mic_recorder import speech_to_text
from datetime import datetime

# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(page_title="Takti Stats Tracker", layout="centered")

# ---------------------- SESSION STATE ----------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "data_rows" not in st.session_state:
    st.session_state.data_rows = []  # Stores filtered commentary rows
if "recording_active" not in st.session_state:
    st.session_state.recording_active = False

# ---------------------- PASSWORD ----------------------
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

# ---------------------- TEAM SHEET FUNCTIONS ----------------------
TEAM_FILE = "team_data.json"

def load_team():
    if os.path.exists(TEAM_FILE):
        try:
            with open(TEAM_FILE, "r") as f:
                return json.load(f)
        except:
            return {"coach": "", "assistant": "", "players": []}
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

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("---")
        username = st.text_input("Username", placeholder="e.g. dreamteam")
        password = st.text_input("Password", type="password", placeholder="Enter password")

        if st.button("🔐 Login", use_container_width=True):
            if username == "dreamteam" and hashlib.sha256(password.encode()).hexdigest() == HASHED_PASSWORD:
                st.session_state.logged_in = True
                st.success("Login successful! Welcome to Takti Stats.")
                st.rerun()
            else:
                st.error("❌ Invalid credentials")

        st.markdown("---")
        st.info("💡 Default: **dreamteam** / **1234567**")

# ---------------------- MAIN APP ----------------------
def main_app():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Select Page", ["Team Sheet", "Match Tracker"])

    PLAYERS = get_player_names()

    if page == "Team Sheet":
        st.header("📋 Team Sheet Setup")
        team = load_team()

        team["coach"] = st.text_input("Coach Name", value=team.get("coach", ""))
        team["assistant"] = st.text_input("Assistant Coach", value=team.get("assistant", ""))

        num_players = st.number_input("Squad Size", min_value=11, max_value=30, value=max(18, len(team.get("players", []))))
        positions = ['GK','CB','RCB','LCB','RB','LB','WB','RWB','LWB','DM','CDM','CM','AM','CAM','RM','LM','WM','RW','LW','ST','CF','SS','WF']

        new_players = []
        used_jerseys = set()

        for i in range(num_players):
            col1, col2, col3 = st.columns([4, 2, 3])
            with col1:
                name = st.text_input("Player Name", key=f"name_{i}")
            with col2:
                jersey = st.text_input("Jersey #", key=f"jersey_{i}", max_chars=3)
            with col3:
                pos = st.selectbox("Position", positions, key=f"pos_{i}")

            if name.strip():
                if jersey and jersey in used_jerseys:
                    st.error(f"Jersey {jersey} already used!")
                else:
                    if jersey:
                        used_jerseys.add(jersey)
                    new_players.append({"name": name.strip(), "jersey": jersey, "position": pos})

        team["players"] = new_players

        if st.button("💾 Save Team Sheet"):
            save_team(team)
            st.success("Team sheet saved successfully!")
            st.rerun()

        if team["players"]:
            st.write("### Current Squad")
            df = pd.DataFrame(team["players"])
            st.dataframe(df[["name", "jersey", "position"]], use_container_width=True)

    elif page == "Match Tracker":
        st.header("🎙️ Live Commentary Tracker")

        col1, col2 = st.columns(2)
        half_mins = col1.number_input("Half Length (minutes)", min_value=1, value=45)
        halftime_mins = col2.number_input("Halftime Duration (minutes)", min_value=0, value=15)

        total_minutes = (half_mins * 2) + halftime_mins
        st.info(f"Match will be tracked for **{total_minutes} minutes** (2 × {half_mins}' + {halftime_mins}' halftime)")

        # Live table
        table_placeholder = st.empty()
        export_placeholder = st.empty()

        # Mic recorder
        st.markdown("### Speak Commentary Below")
        text = speech_to_text(
            language="en",
            use_container_width=True,
            just_once=False,
            key="commentary_recorder"
        )

        if text:
            words = text.lower().split()
            filtered = [word for word in words if word in KEYWORDS or word in PLAYERS]

            if filtered:
                now = datetime.now()
                match_time = now.strftime("%M:%S")  # Simple elapsed-style time; enhance later if needed
                real_time = now.strftime("%H:%M:%S")

                row = {
                    "Match Time": match_time,
                    "Real Time": real_time,
                    "Filtered Words": " ".join(filtered),
                    "Full Phrase": text
                }
                st.session_state.data_rows.append(row)

                # Update live table
                df = pd.DataFrame(st.session_state.data_rows)
                table_placeholder.dataframe(df, use_container_width=True)

        # Show current data
        if st.session_state.data_rows:
            df = pd.DataFrame(st.session_state.data_rows)
            table_placeholder.dataframe(df, use_container_width=True)

            # Export options
            csv = df.to_csv(index=False).encode('utf-8')
            excel_buffer = pd.ExcelWriter("commentary_data.xlsx", engine='openpyxl')
            df.to_excel(excel_buffer, index=False)
            excel_buffer.seek(0)
            excel_data = excel_buffer.getvalue()

            col1, col2 = export_placeholder.columns(2)
            col1.download_button(
                label="📄 Download CSV",
                data=csv,
                file_name=f"commentary_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
            col2.download_button(
                label="📊 Download Excel",
                data=excel_data,
                file_name=f"commentary_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        if st.button("🗑️ Clear All Data"):
            st.session_state.data_rows = []
            st.rerun()

    # Logout
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.rerun()

# ---------------------- RUN APP ----------------------
if not st.session_state.logged_in:
    login_page()
else:
    main_app()
