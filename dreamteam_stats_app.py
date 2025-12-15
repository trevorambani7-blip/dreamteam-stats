import streamlit as st
from collections import defaultdict
import pandas as pd
import time

st.set_page_config(page_title="DreamTeam Stats Tracker", layout="wide")

# ------------------ PREDEFINED DATA ------------------ #
positions = ['GK','CB','RCB','LCB','RB','LB','WB','RWB','LWB','DM','CDM','CM','AM','CAM','RM','LM','WM','RW','LW','ST','CF','SS','WF']
role_groups = {
    'GK':'Goalkeeper','CB':'Centre-Back','RCB':'Centre-Back','LCB':'Centre-Back',
    'RB':'Full-Back','LB':'Full-Back','WB':'Full-Back','RWB':'Full-Back','LWB':'Full-Back',
    'DM':'Defensive Midfielder','CDM':'Defensive Midfielder',
    'CM':'Central Midfielder',
    'AM':'Attacking Midfielder','CAM':'Attacking Midfielder',
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

# ------------------ APP STATE ------------------ #
if "stats" not in st.session_state:
    st.session_state.stats = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
if "players_on_field" not in st.session_state:
    st.session_state.players_on_field = []
if "player_minutes" not in st.session_state:
    st.session_state.player_minutes = defaultdict(int)
if "match_started" not in st.session_state:
    st.session_state.match_started = False
if "start_time" not in st.session_state:
    st.session_state.start_time = 0

# ------------------ MATCH TIMER ------------------ #
def start_match():
    st.session_state.match_started = True
    st.session_state.start_time = time.time()

def pause_match():
    st.session_state.match_started = False
    elapsed = int(time.time() - st.session_state.start_time)
    for p in st.session_state.players_on_field:
        st.session_state.player_minutes[p] += elapsed

def reset_match():
    st.session_state.match_started = False
    st.session_state.start_time = 0
    st.session_state.player_minutes = defaultdict(int)
    st.session_state.stats = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

st.title("⚽ DreamTeam Stats Tracker")

# ------------------ PLAYER SELECTION ------------------ #
st.sidebar.header("Team Setup")

num_players = st.sidebar.number_input("Number of players on field", min_value=1, max_value=11, value=11)

st.sidebar.subheader("Select players on field")
players_on_field = []
for i in range(num_players):
    name = st.sidebar.text_input(f"Player {i+1} name", key=f"player_{i}")
    pos = st.sidebar.selectbox(f"Position {i+1}", positions, key=f"pos_{i}")
    if name:
        players_on_field.append((name, pos))

st.session_state.players_on_field = [p[0] for p in players_on_field]

# ------------------ TIMER UI ------------------ #
st.sidebar.subheader("Match Timer")
col1, col2, col3 = st.sidebar.columns(3)
if col1.button("Start"):
    start_match()
if col2.button("Pause"):
    pause_match()
if col3.button("Reset"):
    reset_match()

# Show elapsed time
if st.session_state.match_started:
    elapsed = int(time.time() - st.session_state.start_time)
else:
    elapsed = 0
st.sidebar.write(f"Elapsed: {elapsed + sum(st.session_state.player_minutes.values())} sec")

# ------------------ LOG ACTIONS ------------------ #
st.header("Tap Player Actions")

for name, pos in players_on_field:
    role = role_groups[pos]
    st.subheader(f"{name} ({role})")
    actions = actions_per_role[role]
    col = st.columns(len(actions))
    for i, act in enumerate(actions):
        if col[i % len(col)].button(f"{act}"):
            st.session_state.stats[name][act]["Successful"] += 1  # default to Successful for tap
            st.success(f"{name} → {act} logged!")

# ------------------ DOWNLOAD CSV ------------------ #
st.header("Match Summary / Download")

rows = []
for p, acts in st.session_state.stats.items():
    for act, outcomes_dict in acts.items():
        total = sum(outcomes_dict.values())
        for outcome, count in outcomes_dict.items():
            rows.append([p, act, outcome, count, round(count/total*100,1)])

df = pd.DataFrame(rows, columns=["Player","Action","Outcome","Count","Percent"])

st.dataframe(df)

st.download_button("Download CSV", df.to_csv(index=False), "match_stats.csv")

