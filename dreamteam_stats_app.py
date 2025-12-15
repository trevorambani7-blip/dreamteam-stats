
import streamlit as st
from collections import defaultdict
import pandas as pd

st.set_page_config(page_title="DreamTeam Stats", layout="centered")

# ------------------ DATA ------------------ #
positions = ['GK','CB','RB','LB','DM','CM','AM','RW','LW','ST']
role_groups = {
    'GK':'Goalkeeper','CB':'Centre-Back','RB':'Full-Back','LB':'Full-Back',
    'DM':'Defensive Midfielder','CM':'Central Midfielder',
    'AM':'Attacking Midfielder','RW':'Winger','LW':'Winger','ST':'Striker'
}

actions = {
    'Goalkeeper':['Save','Distribution','Sweeper'],
    'Centre-Back':['Tackle','Interception','Clearance'],
    'Full-Back':['Cross','1v1 defend','Overlap'],
    'Defensive Midfielder':['Ball recovery','Forward pass','Press'],
    'Central Midfielder':['Progressive pass','Carry','Press'],
    'Attacking Midfielder':['Key pass','Shot','Turn'],
    'Winger':['Dribble','Cross','Track back'],
    'Striker':['Shot','Goal','Press']
}

outcomes = ['Successful','Neutral','Unsuccessful']

# ------------------ STATE ------------------ #
if "stats" not in st.session_state:
    st.session_state.stats = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

# ------------------ UI ------------------ #
st.title("⚽ DreamTeam Stats Tracker")

player = st.text_input("Player Name")
position = st.selectbox("Position", positions)

role = role_groups[position]
action = st.selectbox("Action", actions[role])
outcome = st.radio("Outcome", outcomes)

if st.button("Log Action"):
    st.session_state.stats[player][action][outcome] += 1
    st.success("Logged!")

if st.button("Download CSV"):
    rows = []
    for p,a in st.session_state.stats.items():
        for act,o in a.items():
            total = sum(o.values())
            for res,c in o.items():
                rows.append([p,act,res,c,round(c/total*100,1)])
    df = pd.DataFrame(rows, columns=["Player","Action","Outcome","Count","Percent"])
    st.download_button("Download CSV", df.to_csv(index=False), "match_stats.csv")
