import streamlit as st
import pandas as pd
import os
import json
import hashlib
from datetime import datetime
from streamlit_mic_recorder import speech_to_text

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

            if name:
                players.append({"name": name, "jersey": jersey, "position": pos})

        team["players"] = players

        if st.button("Save Team"):
            save_team(team)
            st.success("Team saved")

        if players:
            st.dataframe(pd.DataFrame(players), use_container_width=True)

    # -------- MATCH TRACKER --------
    elif page == "Match Tracker":
        st.header("🎙️ Live Commentary")

        st.markdown("### Speak commentary")
        text = speech_to_text(
            language="en",
            use_container_width=True,
            just_once=False,
            key="mic"
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
                    "Full Phrase": text
                })

        if st.session_state.data_rows:
            df = pd.DataFrame(st.session_state.data_rows)
            table_placeholder.dataframe(df, use_container_width=True)

            col1, col2 = st.columns(2)
            col1.download_button(
                "Download CSV",
                df.to_csv(index=False).encode(),
                "commentary.csv",
                "text/csv"
            )
            excel = pd.ExcelWriter("commentary.xlsx", engine="openpyxl")
            df.to_excel(excel, index=False)
            excel.close()
            with open("commentary.xlsx", "rb") as f:
                col2.download_button("Download Excel", f, "commentary.xlsx")

        if st.button("Clear Data"):
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
