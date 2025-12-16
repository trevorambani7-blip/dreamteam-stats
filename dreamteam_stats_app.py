import streamlit as st
from collections import defaultdict
import pandas as pd
import time
from datetime import datetime

st.set_page_config(page_title="DreamTeam Stats Tracker", layout="wide")

# -------------------- LOGIN -------------------- #
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("DreamTeam Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
    if username == "dreamteam" and password == "1234567":
        st.session_state.logged_in = True
        st.success("Logged in successfully! Please reload the app.")
    else:
        st.error("Invalid credentials")

    st.stop()  # stop app execution until login

# -------------------- CONFIGURATION -------------------- #
st.sidebar.header("Match Setup")

game_duration = st.sidebar.number_input("Game Duration (minutes)", min_value=10, max_value=180, value=90)
half_length = st.sidebar.number_input("Half Length (minutes)", min_value=5, max_value=90, value=45)

# Player & formation setup
positions = ['GK','CB','RCB','LCB','RB','LB','WB','RWB','LWB','DM','CDM','CM','AM','CAM','RM','LM','WM','RW','LW','ST','CF','SS','WF']
role_groups = {
    'GK':'Goalkeeper','CB':'Centre-Back','RCB':'Centre-Back','LCB':'Centre-Back',
    'RB':'Full-Back','LB':'Full-Back','WB':'Full-Back','RWB':'Full-Back','LWB':'Full-Back',
    'DM':'Defensive Midfielder','CDM':'Defensive Midfielder',
    'CM':'Central Midfielder','AM':'Attacking Midfielder','CAM':'Attacking Midfielder',
    'RM':'Winger','LM':'Winger','WM':'Winger','RW':'Winger','LW':'Winger',
    'ST':'Striker','CF':'Striker','SS':'Striker','WF':'Striker'
}

actions_per_role = {
    'Goalkeeper': ['Save', 'Claim cross', 'Parry', 'Distribution (short)', 'Distribution (long)', 'Sweeper action', 'Communication'],
    'Centre-Back': ['Tackle', 'Interception', 'Clearance', 'Block', 'Progressive pass', 'Aerial duel'],
    'Full-Back': ['Overlap', 'Underlap', 'Cross', '1v1 defend', 'Recovery run', 'Progressive carry'],
    'Defensive Midfielder': ['Ball recovery', 'Interception', 'Screen pass', 'Turn under pressure', 'Forward pass', 'Press'],
    'Central Midfielder': ['Progressive pass', 'Switch play', 'Carry forward', 'Support angle', 'Defensive duel', 'Press'],
    'Attacking Midfielder': ['Key pass', 'Chance created', 'Turn between lines', 'Shot', 'Press trigger', 'Receive between lines'],
    'Winger': ['1v1 dribble', 'Cross', 'Cut inside', 'Back-post run', 'Defensive track', 'Press'],
    'Striker': ['Shot', 'Goal', 'Off-ball run', 'Hold-up play', 'Press', 'Layoff pass']
}

outcomes = ['Successful', 'Neutral', 'Unsuccessful']

# -------------------- STATE -------------------- #
if "players_on_field" not in st.session_state:
    st.session_state.players_on_field = []
if "substitutes" not in st.session_state:
    st.session_state.substitutes = []
if "stats" not in st.session_state:
    st.session_state.stats = []
if "match_started" not in st.session_state:
    st.session_state.match_started = False
if "start_time" not in st.session_state:
    st.session_state.start_time = 0
if "elapsed_time" not in st.session_state:
    st.session_state.elapsed_time = 0

# -------------------- ROSTER SETUP -------------------- #
st.sidebar.subheader("Starting 11")
num_players = st.sidebar.number_input("Number of players on field", min_value=1, max_value=11, value=11)
players_on_field = []
for i in range(num_players):
    name = st.sidebar.text_input(f"Player {i+1} Name", key=f"player_{i}")
    pos = st.sidebar.selectbox(f"Position {i+1}", positions, key=f"pos_{i}")
    if name:
        players_on_field.append({'name': name, 'position': pos})

st.session_state.players_on_field = players_on_field

st.sidebar.subheader("Substitutes")
num_subs = st.sidebar.number_input("Number of subs", min_value=0, max_value=12, value=3)
subs = []
for i in range(num_subs):
    name = st.sidebar.text_input(f"Substitute {i+1} Name", key=f"sub_{i}")
    pos = st.sidebar.selectbox(f"Sub Position {i+1}", positions, key=f"sub_pos_{i}")
    if name:
        subs.append({'name': name, 'position': pos})
st.session_state.substitutes = subs

# -------------------- TIMER -------------------- #
st.sidebar.subheader("Match Timer")
col1, col2, col3 = st.sidebar.columns(3)
if col1.button("Start"):
    if not st.session_state.match_started:
        st.session_state.start_time = time.time() - st.session_state.elapsed_time
        st.session_state.match_started = True
if col2.button("Pause"):
    if st.session_state.match_started:
        st.session_state.elapsed_time = time.time() - st.session_state.start_time
        st.session_state.match_started = False
if col3.button("Reset"):
    st.session_state.elapsed_time = 0
    st.session_state.start_time = 0
    st.session_state.match_started = False

# Stopwatch display
if st.session_state.match_started:
    current_time = time.time() - st.session_state.start_time
else:
    current_time = st.session_state.elapsed_time

minutes = int(current_time // 60)
seconds = int(current_time % 60)
st.sidebar.write(f"Time: {minutes:02d}:{seconds:02d}")

# -------------------- FORMATION SCHEMATIC -------------------- #
st.subheader("Formation (Simplified)")
for p in st.session_state.players_on_field:
    st.write(f"{p['name']} - {p['position']} ({role_groups[p['position']]})")

# -------------------- ACTION LOGGING -------------------- #
st.subheader("Log Actions")

for p in st.session_state.players_on_field:
    role = role_groups[p['position']]
    st.markdown(f"**{p['name']} ({role})**")
    actions = actions_per_role[role]
    col = st.columns(min(len(actions), 4))
    for i, act in enumerate(actions):
        for outcome in outcomes:
            button_key = f"{p['name']}_{act}_{outcome}_{i}"
            color = {"Successful":"#4CAF50","Neutral":"#FFC107","Unsuccessful":"#F44336"}[outcome]
            if col[i % len(col)].button(f"{act}\n{outcome}", key=button_key):
                st.session_state.stats.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "player": p['name'],
                    "role": role,
                    "action": act,
                    "outcome": outcome,
                    "elapsed_min": minutes,
                    "elapsed_sec": seconds
                })
                st.success(f"{p['name']} → {act} ({outcome}) logged!")

# -------------------- DOWNLOAD CSV -------------------- #
st.subheader("Download Match Stats")
if st.session_state.stats:
    df = pd.DataFrame(st.session_state.stats)
    st.download_button("Download CSV", df.to_csv(index=False), "match_stats.csv")
