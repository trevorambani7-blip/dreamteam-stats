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
    for i in range(num_players):
        st.markdown(f"### Player {i+1}")
        if existing_team and i < len(existing_team.get("players", [])):
            player = existing_team["players"][i]
        else:
            player = {"name": "", "jersey": "", "position": positions[i] if i < len(positions) else "CM"}
        
        name = st.text_input("Name", value=player["name"], key=f"name_{i}")
        jersey = st.text_input("Jersey Number", value=player.get("jersey",""), key=f"jersey_{i}")
        pos = st.selectbox("Position", options=positions, index=positions.index(player.get("position","CM")), key=f"pos_{i}")
        
        team_data["players"].append({"name": name, "jersey": jersey, "position": pos})
    
    # Validation
    jerseys = [p['jersey'] for p in team_data['players'] if p['jersey']]
    if len(jerseys) != len(set(jerseys)):
        st.warning("Duplicate jersey numbers detected—please fix for uniqueness.")
    
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
    "4-5-1": ["GK","LB","CB","CB","RB","LM","CM","CM","CM","RM","ST"],  # Added more formations
    "3-4-3": ["GK","CB","CB","CB","LM","CM","CM","RM","LW","ST","RW"],
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

role_groups = {
    'GK':'Goalkeeper','CB':'Centre-Back','RCB':'Centre-Back','LCB':'Centre-Back',
    'RB':'Full-Back','LB':'Full-Back','WB':'Full-Back','RWB':'Full-Back','LWB':'Full-Back',
    'DM':'Defensive Midfielder','CDM':'Defensive Midfielder',
    'CM':'Central Midfielder','AM':'Attacking Midfielder','CAM':'Attacking Midfielder',
    'RM':'Winger','LM':'Winger','WM':'Winger','RW':'Winger','LW':'Winger',
    'ST':'Striker','CF':'Striker','SS':'Striker','WF':'Striker'
}

def lineup_selection(team_data):
    st.subheader("Select Formation and Lineup")
    formation_name = st.selectbox("Choose Formation", options=list(formations.keys()))
    slots = formations[formation_name]
    players_available = [p["name"] for p in team_data["players"] if p["name"]]
    
    lineup = {}
    selected_players = set()
    for i, role in enumerate(slots):
        selected_player = st.selectbox(f"{role} - Slot {i+1}", options=players_available, key=f"slot_{i}")
        lineup[role] = selected_player
        if selected_player in selected_players:
            st.warning(f"Duplicate selection: {selected_player} assigned to multiple roles.")
        selected_players.add(selected_player)
    
    st.write("### Selected Formation:", formation_name)
    st.write("### Lineup:")
    st.table([{role: player} for role, player in lineup.items()])
    
    return formation_name, lineup

# -------------------- STOPWATCH & ACTION LOGGING -------------------- #
def stopwatch_and_actions(lineup):
    st.subheader("Match Timer & Action Logging")
    if "match_started" not in st.session_state:
        st.session_state.match_started = False
        st.session_state.start_time = 0
        st.session_state.elapsed_time = 0
    if "stats" not in st.session_state:
        st.session_state.stats = []
    
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
    
    # Display timer
    current_time = time.time() - st.session_state.start_time if st.session_state.match_started else st.session_state.elapsed_time
    minutes = int(current_time // 60)
    seconds = int(current_time % 60)
    st.write(f"**Time:** {minutes:02d}:{seconds:02d}")
    
    # Halftime mode
    halftime = st.checkbox("Halftime Mode (45 min halves)")
    if halftime:
        half_duration = 45 * 60
        if current_time > half_duration:
            st.info("Halftime reached—pause and reset for second half if needed.")
    
    # Action logging buttons
    outcomes = ['Successful', 'Neutral', 'Unsuccessful']
    for role, player in lineup.items():  # Note: lineup is {role: player}, so iterate correctly
        st.markdown(f"**{player} ({role})**")
        grouped_role = role_groups.get(role, 'Central Midfielder')  # Fix: Use grouping
        actions = actions_per_role.get(grouped_role, [])
        cols = st.columns(min(len(actions), 4))
        for i, act in enumerate(actions):
            for outcome in outcomes:
                button_key = f"{player}_{act}_{outcome}_{i}"
                # Note: Colors not directly supported in st.button; could use custom CSS if needed
                if cols[i % len(cols)].button(f"{act}\n{outcome}", key=button_key):
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
        # Display summary in UI
        summary = df.groupby('player').agg(
            total_actions=('action', 'count'),
            successful=('outcome', lambda x: (x == 'Successful').sum()),
            neutral=('outcome', lambda x: (x == 'Neutral').sum()),
            unsuccessful=('outcome', lambda x: (x == 'Unsuccessful').sum())
        ).reset_index()
        st.subheader("Stats Summary")
        st.table(summary)
        
        # Concat for download
        csv_data = pd.concat([df, pd.DataFrame(), summary]).to_csv(index=False)  # Add empty row separator
        st.download_button("Download Match Stats CSV", csv_data, "match_stats.csv")

# -------------------- APP ENTRY -------------------- #
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login()
else:
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.pop('stats', None)  # Optional: Clear stats on logout
        st.rerun()
    
    team_data = team_sheet()
    formation_name, lineup = lineup_selection(team_data)
    stopwatch_and_actions(lineup)

