import streamlit as st
import pandas as pd
import os
import json
import hashlib
from datetime import datetime
from streamlit_mic_recorder import speech_to_text  # This has the correct function!

# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(page_title="Takti Stats Tracker", layout="centered")

# ---------------------- SESSION STATE ----------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "data_rows" not in st.session_state:
    st.session_state.data_rows = []

# ---------------------- PASSWORD ----------------------
HASHED_PASSWORD = hashlib.sha256("1234567".encode()).hexdigest()

# ---------------------- KEYWORDS ----------------------
KEYWORDS = {
    "shot","shoots","fires","strikes","header","volley","scores","goal",
    "assist","cross","pass","through","tackle","interception","clearance",
    "dribble","beats","run","press","counter","wide","saved","blocked"
}
KEYWORDS = {k.lower() for k in KEYWORDS}

# ---------------------- TEAM FILE ----------------------
TEAM_FILE = "team_data.json"

def load_team():
    if os.path.exists(TEAM_FILE):
        with open(TEAM_FILE, "r") as f:
            return json.load(f)
    return {"coach": "", "assistant": "", "players": []}

def save_team(team):
    with open(TEAM_FILE, "w") as f:
        json.dump(team, f)

def get_player_names():
    team = load_team()
    return {p["name"].lower() for p in team["players"] if p["name"].strip()}

# ---------------------- LOGIN ----------------------
def login_page():
    st.title("⚽ Takti Stats Tracker")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "dreamteam" and hashlib.sha256(password.encode()).hexdigest() == HASHED_PASSWORD:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.info("Default: dreamteam / 1234567")

# ---------------------- MAIN APP ----------------------
def main_app():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Select Page", ["Team Sheet", "Match Tracker"])

    PLAYERS = get_player_names()

    # -------- TEAM SHEET --------
    if page == "Team Sheet":
        st.header("📋 Team Sheet")
        team = load_team()
        team["coach"] = st.text_input("Coach", team["coach"])
        team["assistant"] = st.text_input("Assistant", team["assistant"])
        num_players = st.number_input("Number of Players", 11, 30, max(11, len(team["players"])))
        positions = ["GK","CB","RB","LB","DM","CM","AM","RW","LW","ST"]
        players = []
        for i in range(num_players):
            col1, col2, col3 = st.columns(3)
            name = col1.text_input("Name", key=f"name{i}")
            jersey = col2.text_input("Jersey", key=f"jersey{i}")
            pos = col3.selectbox("Position", positions, key=f"pos{i}")
            if name.strip():
                players.append({"name": name, "jersey": jersey, "position": pos})
        team["players"] = players
        if st.button("Save Team"):
            save_team(team)
            st.success("Team saved")
        if players:
            st.dataframe(pd.DataFrame(players), use_container_width=True)

    # -------- MATCH TRACKER --------
    elif page == "Match Tracker":
        st.header("🎙️ Live Commentary Tracker")
        st.markdown("### Click the mic → Allow permission → Speak your commentary → Click again to stop")

        # Browser-based real-time speech-to-text (no API key!)
        text = speech_to_text(
            language="en",                  # Change to 'es' for Spanish, 'fr' for French, etc.
            use_container_width=True,
            just_once=False,                # Keeps listening across reruns
            start_prompt="🎤 Start Recording",
            stop_prompt="⏹️ Stop Recording",
            key="commentary_stt"
        )

        table_placeholder = st.empty()

        if text:
            text = text.lower()
            words = text.split()
            filtered = [w for w in words if w in KEYWORDS or w in PLAYERS]
            if filtered:
                now = datetime.now()
                st.session_state.data_rows.append({
                    "Match Time": now.strftime("%M:%S"),
                    "Real Time": now.strftime("%H:%M:%S"),
                    "Filtered Words": " ".join(filtered),
                    "Full Phrase": text.capitalize()  # Show original phrase nicely
                })
                st.success(f"Captured: {' '.join(filtered)}")

        # Display table and downloads
        if st.session_state.data_rows:
            df = pd.DataFrame(st.session_state.data_rows)
            table_placeholder.dataframe(df, use_container_width=True)

            col1, col2 = st.columns(2)
            col1.download_button(
                "Download CSV",
                df.to_csv(index=False).encode(),
                "commentary_stats.csv",
                "text/csv"
            )

            # Fixed Excel download
            import io
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Stats")
            excel_buffer.seek(0)
            col2.download_button(
                "Download Excel",
                excel_buffer,
                "commentary_stats.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        if st.button("Clear All Data"):
            st.session_state.data_rows = []
            st.rerun()

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# ---------------------- RUN ----------------------
if not st.session_state.logged_in:
    login_page()
else:
    main_app()
