import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from fpdf import FPDF
import time
import hashlib

st.set_page_config(page_title="DreamTeam Stats Tracker", layout="wide")

# -------------------- LOGIN -------------------- #
HASHED_PASSWORD = hashlib.sha256("1234567".encode()).hexdigest()

def login():
    st.title("DreamTeam Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        hashed_input = hashlib.sha256(password.encode()).hexdigest()
        if username == "dreamteam" and hashed_input == HASHED_PASSWORD:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Invalid credentials")

# -------------------- TEAM SHEET -------------------- #
TEAM_FILE = "team_data.json"

def load_team():
    if os.path.exists(TEAM_FILE):
        try:
            with open(TEAM_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading team file: {e}")
            return {"coach": "", "assistant": "", "players": []}
    return {"coach": "", "assistant": "", "players": []}

def save_team(team_data):
    try:
        with open(TEAM_FILE, "w") as f:
            json.dump(team_data, f)
    except Exception as e:
        st.error(f"Error saving team file: {e}")

def team_sheet():
    st.subheader("Team Sheet Setup")
    team_data = load_team()
    st.info("Configure your full squad below. Jersey numbers must be unique.")

    team_data["coach"] = st.text_input("Coach Name", value=team_data.get("coach", ""))
    team_data["assistant"] = st.text_input("Assistant Coach Name", value=team_data.get("assistant", ""))

    num_players = st.number_input("Total Squad Size (incl. subs)", min_value=11, max_value=30, value=18)
    positions = ['GK','CB','RCB','LCB','RB','LB','WB','RWB','LWB','DM','CDM','CM','AM','CAM','RM','LM','WM','RW','LW','ST','CF','SS','WF']

    team_data["players"] = []
    used_jerseys = set()

    for i in range(num_players):
        st.markdown(f"### Player {i+1}")
        col1, col2, col3 = st.columns([3, 2, 2])
        with col1:
            name = st.text_input("Name", key=f"name_{i}")
        with col2:
            jersey = st.text_input("Jersey #", key=f"jersey_{i}")
        with col3:
            pos_index = positions.index(team_data.get("players", [{}])[i]["position"]) if i < len(team_data.get("players", [])) and team_data["players"][i].get("position") in positions else 0
            pos = st.selectbox("Position", options=positions, index=pos_index, key=f"pos_{i}")

        if jersey and jersey in used_jerseys:
            st.error(f"Jersey {jersey} is already assigned!")
        elif jersey:
            used_jerseys.add(jersey)

        if name.strip():
            team_data["players"].append({"name": name, "jersey": jersey, "position": pos})

    if st.button("Save Team Sheet"):
        if len(used_jerseys) != len([p for p in team_data["players"] if p["jersey"]]):
            st.error("Fix duplicate jerseys before saving.")
        else:
            save_team(team_data)
            st.success("Team sheet saved successfully!")

    return team_data

# -------------------- FORMATIONS & LINEUP -------------------- #
formations = {
    "4-4-2": ["GK","LB","CB","CB","RB","LM","CM","CM","RM","ST","ST"],
    "4-3-3": ["GK","LB","CB","CB","RB","CM","CM","CM","LW","ST","RW"],
    "4-2-3-1": ["GK","LB","CB","CB","RB","CDM","CDM","CAM","LW","ST","RW"],
    "3-5-2": ["GK","CB","CB","CB","LM","CM","CM","RM","CAM","ST","ST"],
    "4-5-1": ["GK","LB","CB","CB","RB","LM","CM","CM","CM","RM","ST"],
    "3-4-3": ["GK","CB","CB","CB","LM","CM","CM","RM","LW","ST","RW"],
}

role_groups = {
    'GK':'Goalkeeper','CB':'Centre-Back','RCB':'Centre-Back','LCB':'Centre-Back',
    'RB':'Full-Back','LB':'Full-Back','WB':'Full-Back','RWB':'Full-Back','LWB':'Full-Back',
    'DM':'Defensive Midfielder','CDM':'Defensive Midfielder',
    'CM':'Central Midfielder','AM':'Attacking Midfielder','CAM':'Attacking Midfielder',
    'RM':'Winger','LM':'Winger','WM':'Winger','RW':'Winger','LW':'Winger',
    'ST':'Striker','CF':'Striker','SS':'Striker','WF':'Striker'
}

def get_actions_per_level():
    return {
        "Beginner": {
            "All": ["Minutes played", "Touches", "Successful actions", "Unsuccessful actions", "Goals", "Assists"],
            "Goalkeeper": ["Shots faced", "Saves", "Goals conceded"],
            "Centre-Back": ["Tackles attempted", "Tackles won", "Clearances"],
            "Full-Back": ["Tackles attempted", "Tackles won", "Clearances"],
            "Defensive Midfielder": ["Passes attempted", "Passes completed", "Shots"],
            "Central Midfielder": ["Passes attempted", "Passes completed", "Shots"],
            "Attacking Midfielder": ["Passes attempted", "Passes completed", "Shots"],
            "Winger": ["Shots", "Shots on target", "Goals"],
            "Striker": ["Shots", "Shots on target", "Goals"]
        },
        "Intermediate": {
            "All": ["Minutes played", "Touches", "Passes attempted", "Passes completed", "Ball losses", "Duels attempted", "Duels won"],
            "Goalkeeper": ["Shots on target faced", "Saves", "Goals conceded", "Passes attempted", "Passes completed", "Long kicks attempted", "Long kicks completed"],
            "Centre-Back": ["Tackles attempted", "Tackles won", "Interceptions", "Clearances", "Aerial duels attempted", "Aerial duels won", "Fouls conceded"],
            "Full-Back": ["Tackles attempted", "Tackles won", "Interceptions", "Clearances", "Aerial duels attempted", "Aerial duels won", "Fouls conceded"],
            "Defensive Midfielder": ["Passes completed", "Forward passes", "Ball recoveries", "Interceptions", "Shots", "Assists", "Key passes"],
            "Central Midfielder": ["Passes completed", "Forward passes", "Ball recoveries", "Interceptions", "Shots", "Assists", "Key passes"],
            "Attacking Midfielder": ["Passes completed", "Forward passes", "Ball recoveries", "Interceptions", "Shots", "Assists", "Key passes"],
            "Winger": ["Shots", "Shots on target", "Goals", "Assists", "Dribbles attempted", "Dribbles completed", "Pressing actions"],
            "Striker": ["Shots", "Shots on target", "Goals", "Assists", "Dribbles attempted", "Dribbles completed", "Pressing actions"]
        },
        "Semi-Pro": {
            "All": ["Successful actions", "Unsuccessful actions", "Duels won", "Duels lost", "Ball losses by zone", "Pressing actions", "Successful presses"],
            "Goalkeeper": ["Shots on target faced", "Saves", "Goals conceded", "Crosses faced", "Crosses claimed", "Crosses punched", "Long passes completed", "Errors leading to shot"],
            "Centre-Back": ["Defensive duels attempted", "Defensive duels won", "Aerial duels attempted", "Aerial duels won", "Blocks", "Clearances", "Progressive passes", "Errors leading to shot"],
            "Full-Back": ["Tackles won", "Interceptions", "Overlaps", "Crosses attempted", "Crosses completed", "Touches in final third", "Recovery runs"],
            "Defensive Midfielder": ["Ball recoveries", "Interceptions", "Tackles won", "Passes under pressure", "Forward passes completed", "Fouls conceded"],
            "Central Midfielder": ["Progressive passes", "Key passes", "Chances created", "Dribbles completed", "Shots", "Assists"],
            "Attacking Midfielder": ["Progressive passes", "Key passes", "Chances created", "Dribbles completed", "Shots", "Assists"],
            "Winger": ["Shots", "Shots on target", "Goals", "Big chances missed", "Touches in box", "Successful presses (final third)", "Offsides"],
            "Striker": ["Shots", "Shots on target", "Goals", "Big chances missed", "Touches in box", "Successful presses (final third)", "Offsides"]
        },
        "Pro": {
            "All": ["Actions per 90", "Success rate by zone", "Press resistance actions", "Ball losses under pressure", "Contribution to goal sequences"],
            "Goalkeeper": ["Shots on target faced", "Saves", "Goals conceded", "PSxG / xG prevented", "Cross claim success", "Distribution leading to shot", "Sweeper actions"],
            "Centre-Back": ["Defensive actions per 90", "Line-breaking passes", "Progressive carries", "Recovery runs", "Errors leading to goal"],
            "Full-Back": ["Progressive runs", "Crosses into danger area", "Assists", "Defensive recoveries", "Pressing success rate"],
            "Defensive Midfielder": ["Progressive passes", "Progressive carries", "Passes under pressure", "Key passes", "Expected assists (xA)", "Tempo-control actions"],
            "Central Midfielder": ["Progressive passes", "Progressive carries", "Passes under pressure", "Key passes", "Expected assists (xA)", "Tempo-control actions"],
            "Attacking Midfielder": ["Progressive passes", "Progressive carries", "Passes under pressure", "Key passes", "Expected assists (xA)", "Tempo-control actions"],
            "Winger": ["Shots by zone", "Expected goals (xG)", "Non-penalty goals", "Shot conversion rate", "Pressing intensity", "Off-ball runs leading to shots"],
            "Striker": ["Shots by zone", "Expected goals (xG)", "Non-penalty goals", "Shot conversion rate", "Pressing intensity", "Off-ball runs leading to shots"]
        }
    }

def lineup_selection(team_data):
    st.subheader("Select Formation & Starting Lineup")
    formation = st.selectbox("Formation", options=list(formations.keys()))
    slots = formations[formation]

    players_by_pos = {}
    for p in team_data["players"]:
        pos = p["position"]
        players_by_pos.setdefault(pos, []).append(p["name"])

    lineup = {}
    used_players = set()

    for i, role in enumerate(slots):
        options = players_by_pos.get(role, [])
        if not options:
            st.warning(f"No players assigned to {role} in team sheet.")
            options = [p["name"] for p in team_data["players"]]
        player = st.selectbox(f"{role}", options=options, key=f"start_{i}")
        if player in used_players:
            st.error(f"{player} already selected!")
        else:
            used_players.add(player)
            lineup[role] = player

    st.subheader("Substitutes (up to 15)")
    remaining = [p["name"] for p in team_data["players"] if p["name"] not in used_players]
    subs = []
    for i in range(15):
        sub = st.selectbox(f"Sub {i+1}", options=["—"] + remaining, key=f"sub_{i}")
        if sub != "—" and sub in remaining:
            subs.append(sub)
            remaining.remove(sub)

    # Display lineup table
    st.write("### Starting XI")
    lineup_rows = []
    for role, player in lineup.items():
        jersey = next(p["jersey"] for p in team_data["players"] if p["name"] == player)
        lineup_rows.append({"Position": role, "Name": player, "Jersey": jersey})
    st.table(pd.DataFrame(lineup_rows))

    st.write("### Substitutes")
    sub_rows = [{"Position": "SUB", "Name": s, "Jersey": next(p["jersey"] for p in team_data["players"] if p["name"] == s)} for s in subs]
    st.table(pd.DataFrame(sub_rows or [{"Position": "SUB", "Name": "-", "Jersey": "-"}]))

    if st.button("Export Lineup PDF"):
        # PDF export logic (same as before)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Match Lineup", ln=True, align="C")
        pdf.ln(10)
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 8, f"Coach: {team_data['coach']} | Assistant: {team_data['assistant']}", ln=True)
        pdf.ln(10)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Starting XI", ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.cell(40, 10, "Pos", 1)
        pdf.cell(100, 10, "Player", 1)
        pdf.cell(40, 10, "Jersey", 1, ln=True)
        for row in lineup_rows:
            pdf.cell(40, 10, row["Position"], 1)
            pdf.cell(100, 10, row["Name"], 1)
            pdf.cell(40, 10, row["Jersey"], 1, ln=True)
        pdf.ln(10)
        pdf.cell(0, 8, "Substitutes", ln=True)
        for row in sub_rows:
            pdf.cell(40, 10, row["Position"], 1)
            pdf.cell(100, 10, row["Name"], 1)
            pdf.cell(40, 10, row["Jersey"], 1, ln=True)
        pdf.output("lineup.pdf")
        with open("lineup.pdf", "rb") as f:
            st.download_button("Download Lineup PDF", f, "lineup.pdf")

    return lineup

# -------------------- MAIN APP -------------------- #
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login()
else:
    st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"logged_in": False, "match_ready": False}))

    tab1, tab2, tab3, tab4 = st.tabs(["Team Sheet", "Lineup", "Match Settings", "Live Match"])

    with tab1:
        team_data = team_sheet()
        st.session_state.team_data = team_data  # Save for later tabs

    with tab2:
        if "team_data" not in st.session_state:
            st.warning("Please complete Team Sheet first.")
        else:
            lineup = lineup_selection(st.session_state.team_data)
            st.session_state.lineup = lineup

    with tab3:
        st.header("Match Settings")
        if "team_data" not in st.session_state:
            st.warning("Complete Team Sheet first.")
        elif "lineup" not in st.session_state:
            st.warning("Select lineup first.")
        else:
            level = st.selectbox("Tracking Level", ["Beginner", "Intermediate", "Semi-Pro", "Pro"])
            game_duration = st.number_input("Match Duration (minutes)", min_value=20, value=90)
            halftime_mins = st.number_input("Halftime Duration (minutes)", min_value=0, value=15)

            st.markdown("### Selected Actions Preview (for reference only)")
            preview_actions = get_actions_per_level()[level]
            for group, actions in preview_actions.items():
                st.write(f"**{group}**: {', '.join(actions)}")

            if st.button("🚀 Proceed to Live Match", type="primary", use_container_width=True):
                st.session_state.match_level = level
                st.session_state.game_duration = game_duration
                st.session_state.halftime_duration = halftime_mins
                st.session_state.match_ready = True
                st.success("Match settings locked! Go to 'Live Match' tab to start.")
                st.rerun()

    with tab4:
        if not st.session_state.get("match_ready", False):
            st.info("Please complete all previous tabs and click 'Proceed to Live Match' in Match Settings.")
            st.stop()

        st.header("Live Match - Timer & Action Logging")
        lineup = st.session_state.lineup
        level = st.session_state.match_level
        game_duration = st.session_state.game_duration
        halftime_duration = st.session_state.halftime_duration

        actions_dict = get_actions_per_level()[level]

        # Timer
        if "match_started" not in st.session_state:
            st.session_state.match_started = False
            st.session_state.elapsed_time = 0
            st.session_state.start_time = None

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Start Match", type="primary"):
                if not st.session_state.match_started:
                    st.session_state.start_time = time.time() - st.session_state.elapsed_time
                    st.session_state.match_started = True
        with col2:
            if st.button("Pause"):
                if st.session_state.match_started:
                    st.session_state.elapsed_time = time.time() - st.session_state.start_time
                    st.session_state.match_started = False
        with col3:
            if st.button("Reset"):
                st.session_state.elapsed_time = 0
                st.session_state.start_time = None
                st.session_state.match_started = False
                st.session_state.stats = []

        # Live timer display
        timer_ph = st.empty()
        if st.session_state.match_started:
            while True:
                elapsed = time.time() - st.session_state.start_time
                mins = int(elapsed // 60)
                secs = int(elapsed % 60)
                timer_ph.markdown(f"<h1 style='text-align:center;color:green'>{mins:02d}:{secs:02d}</h1>", unsafe_allow_html=True)
                time.sleep(0.5)
                st.rerun()
        else:
            mins = int(st.session_state.elapsed_time // 60)
            secs = int(st.session_state.elapsed_time % 60)
            timer_ph.markdown(f"<h1 style='text-align:center;color:orange'>{mins:02d}:{secs:02d}</h1>", unsafe_allow_html=True)

        # Action buttons - ONLY for selected level
        if "stats" not in st.session_state:
            st.session_state.stats = []

        outcomes = ["Successful", "Unsuccessful"]  # Simplified for kids/beginners

        st.subheader(f"Action Logging - {level} Level")
        for role, player in lineup.items():
            with st.expander(f"**{player} ({role})**", expanded=True):
                grouped_role = role_groups.get(role, "Central Midfielder")
                actions = actions_dict.get("All", []) + actions_dict.get(grouped_role, [])
                cols = st.columns(3)
                for idx, action in enumerate(actions):
                    col = cols[idx % 3]
                    for outcome in outcomes:
                        if col.button(f"{action}\n{outcome}", key=f"{player}_{action}_{outcome}_{idx}"):
                            st.session_state.stats.append({
                                "player": player,
                                "role": role,
                                "action": action,
                                "outcome": outcome,
                                "time": f"{mins:02d}:{secs:02d}"
                            })
                            st.success(f"{action} - {outcome}")

        # Stats summary & download
        if st.session_state.stats:
            df = pd.DataFrame(st.session_state.stats)
            st.subheader("Live Stats Summary")
            summary = df.groupby(["player", "action", "outcome"]).size().unstack(fill_value=0)
            st.dataframe(summary)

            csv = df.to_csv(index=False)
            st.download_button("Download Full Stats", csv, "match_stats.csv", "text/csv")
