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
# Hashed password for security (in production, load from secrets)
HASHED_PASSWORD = hashlib.sha256("1234567".encode()).hexdigest()

def login():
    st.title("DreamTeam Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        hashed_input = hashlib.sha256(password.encode()).hexdigest()
        if username == "dreamteam" and hashed_input == HASHED_PASSWORD:
            st.session_state.logged_in = True
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
            return None
    return None

def save_team(team_data):
    try:
        with open(TEAM_FILE, "w") as f:
            json.dump(team_data, f)
    except Exception as e:
        st.error(f"Error saving team file: {e}")

def team_sheet():
    st.subheader("Team Sheet Setup")
    existing_team = load_team()
    if existing_team:
        st.info("Loaded existing team sheet.")
    
    num_players = st.number_input("Number of players", min_value=1, max_value=30, value=11)
    team_data = {"coach": "", "assistant": "", "players": []}
    if existing_team:
        team_data = existing_team
    
    team_data["coach"] = st.text_input("Coach Name", value=team_data.get("coach", ""))
    team_data["assistant"] = st.text_input("Assistant Coach Name", value=team_data.get("assistant", ""))
    
    positions = ['GK','CB','RCB','LCB','RB','LB','WB','RWB','LWB','DM','CDM','CM','AM','CAM','RM','LM','WM','RW','LW','ST','CF','SS','WF']
    
    team_data["players"] = []  # Reset to avoid appending duplicates on reruns
    used_jerseys = set()
    for i in range(num_players):
        st.markdown(f"### Player {i+1}")
        if existing_team and i < len(existing_team.get("players", [])):
            player = existing_team["players"][i]
        else:
            player = {"name": "", "jersey": "", "position": positions[i] if i < len(positions) else "CM"}
        
        name = st.text_input("Name", value=player["name"], key=f"name_{i}")
        jersey = st.text_input("Jersey Number", value=player.get("jersey",""), key=f"jersey_{i}")
        pos = st.selectbox("Position", options=positions, index=positions.index(player.get("position","CM")), key=f"pos_{i}")
        
        if jersey in used_jerseys:
            st.error(f"Jersey {jersey} is already used. Please choose a unique number.")
        else:
            used_jerseys.add(jersey)
        
        team_data["players"].append({"name": name, "jersey": jersey, "position": pos})
    
    # Validation
    jerseys = [p['jersey'] for p in team_data['players'] if p['jersey']]
    if len(jerseys) != len(set(jerseys)):
        st.error("Duplicate jersey numbers detected—cannot save until fixed.")
        return team_data  # Return without saving
    
    names = [p['name'] for p in team_data['players']]
    if any(not name.strip() for name in names):
        st.warning("Some players have empty names—please fill them in.")
    
    if st.button("Save Team Sheet"):
        save_team(team_data)
        st.success("Team sheet saved!")
    
    # PDF export
    if st.button("Export Team Sheet PDF"):
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "DreamTeam Squad", ln=True, align="C")
            pdf.ln(10)
            pdf.set_font("Arial", "", 12)
            pdf.cell(0, 8, f"Coach: {team_data['coach']}", ln=True)
            pdf.cell(0, 8, f"Assistant Coach: {team_data['assistant']}", ln=True)
            pdf.ln(5)
            pdf.cell(50, 8, "Jersey", 1)
            pdf.cell(80, 8, "Player Name", 1)
            pdf.cell(50, 8, "Position", 1, ln=True)
            for p in team_data["players"]:
                pdf.cell(50, 8, str(p["jersey"]), 1)
                pdf.cell(80, 8, p["name"], 1)
                pdf.cell(50, 8, p["position"], 1, ln=True)
            pdf_file = "team_sheet.pdf"
            pdf.output(pdf_file)
            with open(pdf_file, "rb") as f:
                st.download_button("Download PDF", f, file_name="team_sheet.pdf")
        except Exception as e:
            st.error(f"Error generating PDF: {e}")
    
    return team_data

# -------------------- FORMATION & LINEUP -------------------- #
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
            "Centre-Back": ["Tackles attempted", "Tackles won", "Clearances"],  # Defenders
            "Full-Back": ["Tackles attempted", "Tackles won", "Clearances"],  # Defenders
            "Defensive Midfielder": ["Passes attempted", "Passes completed", "Shots"],  # Midfielders
            "Central Midfielder": ["Passes attempted", "Passes completed", "Shots"],
            "Attacking Midfielder": ["Passes attempted", "Passes completed", "Shots"],
            "Winger": ["Shots", "Shots on target", "Goals"],  # Forwards
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
            "Winger": ["Shots", "Shots on target", "Goals", "Big chances missed", "Touches in box", "Successful presses (final third)", "Offsides"],  # Forwards
            "Striker": ["Shots", "Shots on target", "Goals", "Big chances missed", "Touches in box", "Successful presses (final third)", "Offsides"]
        },
        "Pro": {
            "All": ["Actions per 90", "Success rate by zone", "Press resistance actions", "Ball losses under pressure", "Contribution to goal sequences"],
            "Goalkeeper": ["Shots on target faced", "Saves", "Goals conceded", "PSxG / xG prevented", "Cross claim success", "Distribution leading to shot", "Sweeper actions"],
            "Centre-Back": ["Defensive actions per 90", "Line-breaking passes", "Progressive carries", "Recovery runs", "Errors leading to goal"],
            "Full-Back": ["Progressive runs", "Crosses into danger area", "Assists", "Defensive recoveries", "Pressing success rate"],
            "Defensive Midfielder": ["Progressive passes", "Progressive carries", "Passes under pressure", "Key passes", "Expected assists (xA)", "Tempo-control actions"],  # Midfielders
            "Central Midfielder": ["Progressive passes", "Progressive carries", "Passes under pressure", "Key passes", "Expected assists (xA)", "Tempo-control actions"],
            "Attacking Midfielder": ["Progressive passes", "Progressive carries", "Passes under pressure", "Key passes", "Expected assists (xA)", "Tempo-control actions"],
            "Winger": ["Shots by zone", "Expected goals (xG)", "Non-penalty goals", "Shot conversion rate", "Pressing intensity", "Off-ball runs leading to shots"],  # Forwards
            "Striker": ["Shots by zone", "Expected goals (xG)", "Non-penalty goals", "Shot conversion rate", "Pressing intensity", "Off-ball runs leading to shots"]
        }
    }

def lineup_selection(team_data):
    st.subheader("Select Formation and Lineup")
    formation_name = st.selectbox("Choose Formation", options=list(formations.keys()))
    slots = formations[formation_name]
    
    players_by_pos = {}
    for p in team_data["players"]:
        pos = p["position"]
        if pos not in players_by_pos:
            players_by_pos[pos] = []
        players_by_pos[pos].append(p["name"])
    
    lineup = {}
    selected_players = set()
    for i, role in enumerate(slots):
        available = players_by_pos.get(role, [])
        if not available:
            st.warning(f"No players available for {role}. Assign in team sheet.")
        selected_player = st.selectbox(f"{role} - Slot {i+1}", options=available, key=f"slot_{i}")
        if selected_player:
            lineup[role] = selected_player
            if selected_player in selected_players:
                st.warning(f"Duplicate selection: {selected_player} assigned to multiple roles.")
            selected_players.add(selected_player)
    
    # Subs selection
    st.subheader("Select Substitutes (up to 15)")
    all_players = [p["name"] for p in team_data["players"] if p["name"] not in selected_players]
    subs = []
    for j in range(15):
        sub = st.selectbox(f"Sub {j+1}", options=[""] + all_players, key=f"sub_{j}")
        if sub:
            subs.append(sub)
            all_players.remove(sub)  # Prevent duplicates
    
    st.write("### Selected Formation:", formation_name)
    st.write("### Starting Lineup:")
    
    lineup_data = []
    for role, player in lineup.items():
        jersey = next((p["jersey"] for p in team_data["players"] if p["name"] == player), "")
        lineup_data.append({"Position": role, "Name": player, "Jersey": jersey})
    
    st.table(pd.DataFrame(lineup_data))
    
    st.write("### Substitutes:")
    subs_data = [{"Position": "Sub", "Name": sub, "Jersey": next((p["jersey"] for p in team_data["players"] if p["name"] == sub), "")} for sub in subs]
    st.table(pd.DataFrame(subs_data))
    
    # Export Lineup PDF
    if st.button("Export Lineup PDF"):
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "DreamTeam Lineup", ln=True, align="C")
            pdf.ln(10)
            pdf.set_font("Arial", "", 12)
            pdf.cell(0, 8, f"Coach: {team_data['coach']}", ln=True)
            pdf.cell(0, 8, f"Assistant Coach: {team_data['assistant']}", ln=True)
            pdf.ln(5)
            pdf.cell(50, 8, "Position", 1)
            pdf.cell(80, 8, "Player Name", 1)
            pdf.cell(50, 8, "Jersey", 1, ln=True)
            for item in lineup_data:
                pdf.cell(50, 8, item["Position"], 1)
                pdf.cell(80, 8, item["Name"], 1)
                pdf.cell(50, 8, str(item["Jersey"]), 1, ln=True)
            pdf.ln(10)
            pdf.cell(0, 8, "Substitutes:", ln=True)
            for item in subs_data:
                pdf.cell(50, 8, item["Position"], 1)
                pdf.cell(80, 8, item["Name"], 1)
                pdf.cell(50, 8, str(item["Jersey"]), 1, ln=True)
            pdf_file = "lineup.pdf"
            pdf.output(pdf_file)
            with open(pdf_file, "rb") as f:
                st.download_button("Download Lineup PDF", f, file_name="lineup.pdf")
        except Exception as e:
            st.error(f"Error generating PDF: {e}")
    
    return formation_name, lineup, subs

# -------------------- MATCH SETTINGS -------------------- #
def match_settings():
    st.subheader("Match Settings")
    level = st.selectbox("Select Level", options=["Beginner", "Intermediate", "Semi-Pro", "Pro"])
    game_duration = st.number_input("Game Duration (minutes)", min_value=1, value=90)
    halftime_duration = st.number_input("Halftime Duration (minutes)", min_value=0, value=15)
    return level, game_duration, halftime_duration

# -------------------- STOPWATCH & ACTION LOGGING -------------------- #
def stopwatch_and_actions(lineup, level, game_duration, halftime_duration):
    actions_per_level = get_actions_per_level()
    actions_per_role = actions_per_level.get(level, actions_per_level["Beginner"])
    
    st.subheader("Match Timer & Action Logging")
    if "match_started" not in st.session_state:
        st.session_state.match_started = False
        st.session_state.start_time = 0
        st.session_state.elapsed_time = 0
        st.session_state.half = 1  # For halftime tracking
    
    col1, col2, col3 = st.columns(3)
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
        st.session_state.half = 1
    
    # Real-time timer update
    timer_placeholder = st.empty()
    stats_placeholder = st.empty()
    while True:
        if st.session_state.match_started:
            current_time = time.time() - st.session_state.start_time
        else:
            current_time = st.session_state.elapsed_time
        
        minutes = int(current_time // 60)
        seconds = int(current_time % 60)
        
        half_duration = game_duration // 2 * 60
        if current_time > half_duration + halftime_duration * 60 and st.session_state.half == 1:
            st.info("Halftime over—starting second half.")
            st.session_state.half = 2
            st.session_state.start_time = time.time() - (current_time - half_duration - halftime_duration * 60)
        
        if current_time > game_duration * 60:
            st.info("Match ended.")
            st.session_state.match_started = False
        
        timer_placeholder.markdown(f"<h1 style='text-align: center; color: red;'>Time: {minutes:02d}:{seconds:02d}</h1>", unsafe_allow_html=True)
        
        if "stats" not in st.session_state:
            st.session_state.stats = []
        
        # Action logging
        with stats_placeholder.container():
            outcomes = ['Successful', 'Neutral', 'Unsuccessful']
            for role, player in lineup.items():
                st.markdown(f"**{player} ({role})**")
                grouped_role = role_groups.get(role, 'Central Midfielder')
                actions = actions_per_role.get("All", []) + actions_per_role.get(grouped_role, [])
                cols = st.columns(min(len(actions), 4))
                for i, act in enumerate(actions):
                    for outcome in outcomes:
                        button_key = f"{player}_{act}_{outcome}_{i}"
                        if cols[i % len(cols)].button(f"{act} ({outcome})", key=button_key):
                            st.session_state.stats.append({
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "player": player,
                                "role": role,
                                "action": act,
                                "outcome": outcome,
                                "elapsed_min": minutes,
                                "elapsed_sec": seconds
                            })
                            st.success(f"{player} → {act} ({outcome}) logged!")
        
        # CSV download with summary
        if st.session_state.stats:
            df = pd.DataFrame(st.session_state.stats)
            summary = df.groupby('player').agg(
                total_actions=('action', 'count'),
                successful=('outcome', lambda x: (x == 'Successful').sum()),
                neutral=('outcome', lambda x: (x == 'Neutral').sum()),
                unsuccessful=('outcome', lambda x: (x == 'Unsuccessful').sum())
            ).reset_index()
            st.subheader("Stats Summary")
            st.table(summary)
            
            csv_data = pd.concat([df, pd.DataFrame(), summary]).to_csv(index=False)
            st.download_button("Download Match Stats CSV", csv_data, "match_stats.csv")
        
        time.sleep(1)  # Update every second
        if not st.session_state.match_started:
            break

# -------------------- APP ENTRY -------------------- #
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login()
else:
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.pop('stats', None)
        st.rerun()
    
    tab1, tab2, tab3, tab4 = st.tabs(["Team Sheet", "Lineup", "Match Settings", "Timer & Logging"])
    
    with tab1:
        team_data = team_sheet()
    
    with tab2:
        if "team_data" in locals():
            formation_name, lineup, subs = lineup_selection(team_data)
        else:
            st.error("Set up team sheet first.")
    
    with tab3:
        level, game_duration, halftime_duration = match_settings()
    
    with tab4:
        if "lineup" in locals() and "level" in locals():
            stopwatch_and_actions(lineup, level, game_duration, halftime_duration)
        else:
            st.error("Complete previous tabs first.")
