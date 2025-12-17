import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from fpdf import FPDF
import hashlib
from collections import defaultdict
import plotly.express as px
import plotly.graph_objects as go

# -------------------- CONFIGURATION -------------------- #
st.set_page_config(page_title="Takti Stats Tracker", layout="wide", initial_sidebar_state="expanded")

# Custom CSS
def load_css():
    css = """
    <style>
    .main {background-color: #f0f2f6;}
    .stButton>button {width: 100%; border-radius: 5px; height: 3em;}
    .success-btn {background-color: #28a745; color: white;}
    .warning-btn {background-color: #ffc107; color: black;}
    .timer-display {
        font-size: 4em;
        font-weight: bold;
        text-align: center;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
    }
    .timer-running {background-color: #d4edda; color: #155724;}
    .timer-paused {background-color: #fff3cd; color: #856404;}
    .stat-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    .player-card {
        background-color: #ffffff;
        border-left: 4px solid #007bff;
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

load_css()

# -------------------- DATA FILES -------------------- #
TEAM_FILE = "team_data.json"
MATCHES_DIR = "matches"
HASHED_PASSWORD = hashlib.sha256("1234567".encode()).hexdigest()

# Create matches directory if it doesn't exist
if not os.path.exists(MATCHES_DIR):
    os.makedirs(MATCHES_DIR)

# -------------------- UTILITY FUNCTIONS -------------------- #
def load_team():
    """Load team data with error handling"""
    if os.path.exists(TEAM_FILE):
        try:
            with open(TEAM_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading team file: {e}")
            return {"coach": "", "assistant": "", "players": []}
    return {"coach": "", "assistant": "", "players": []}

def save_team(team_data):
    """Save team data with error handling"""
    try:
        with open(TEAM_FILE, "w") as f:
            json.dump(team_data, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving team file: {e}")
        return False

def save_match_data(match_data):
    """Save match data to a timestamped file"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{MATCHES_DIR}/match_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(match_data, f, indent=2)
        return filename
    except Exception as e:
        st.error(f"Error saving match: {e}")
        return None

def load_all_matches():
    """Load all saved matches"""
    matches = []
    if os.path.exists(MATCHES_DIR):
        for filename in sorted(os.listdir(MATCHES_DIR), reverse=True):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(MATCHES_DIR, filename), "r") as f:
                        match_data = json.load(f)
                        match_data["filename"] = filename
                        matches.append(match_data)
                except Exception as e:
                    st.warning(f"Error loading {filename}: {e}")
    return matches

# -------------------- FORMATIONS & ACTIONS -------------------- #
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
            "All": ["Pass", "Dribble", "Tackle", "Shot"],
            "Goalkeeper": ["Save", "Catch", "Punch"],
            "Centre-Back": ["Clearance", "Header", "Block"],
            "Full-Back": ["Cross", "Overlap"],
            "Defensive Midfielder": ["Interception", "Recovery"],
            "Central Midfielder": ["Key Pass", "Long Ball"],
            "Attacking Midfielder": ["Through Ball", "Assist"],
            "Winger": ["Cross", "Cut Inside", "1v1"],
            "Striker": ["Shot", "Header", "Hold Up"]
        },
        "Intermediate": {
            "All": ["Pass", "Dribble", "Tackle", "Shot", "Foul", "Yellow Card", "Red Card"],
            "Goalkeeper": ["Save", "Catch", "Punch", "Long Kick", "Distribution"],
            "Centre-Back": ["Clearance", "Interception", "Aerial Duel", "Tackle"],
            "Full-Back": ["Cross", "Overlap", "Tackle", "Recovery Run"],
            "Defensive Midfielder": ["Interception", "Tackle", "Forward Pass", "Ball Recovery"],
            "Central Midfielder": ["Key Pass", "Long Ball", "Dribble", "Shot"],
            "Attacking Midfielder": ["Through Ball", "Assist", "Shot", "Dribble"],
            "Winger": ["Cross", "Shot", "Dribble", "Pressing"],
            "Striker": ["Shot", "Header", "Hold Up", "Pressing", "Assist"]
        },
        "Semi-Pro": {
            "All": ["Pass", "Progressive Pass", "Dribble", "Tackle", "Shot", "Foul", "Card"],
            "Goalkeeper": ["Save", "Claim Cross", "Sweeper Action", "Distribution", "Long Pass"],
            "Centre-Back": ["Progressive Pass", "Aerial Duel", "Tackle", "Block", "Clearance"],
            "Full-Back": ["Cross", "Progressive Run", "Tackle", "Overlap", "Recovery"],
            "Defensive Midfielder": ["Ball Recovery", "Tackle", "Progressive Pass", "Interception"],
            "Central Midfielder": ["Key Pass", "Progressive Pass", "Dribble", "Shot", "Assist"],
            "Attacking Midfielder": ["Chance Created", "Shot", "Assist", "Dribble", "Key Pass"],
            "Winger": ["Shot", "Dribble", "Cross", "Pressing", "Touch in Box"],
            "Striker": ["Shot", "Touch in Box", "Pressing", "Assist", "Offside"]
        },
        "Pro": {
            "All": ["Pass", "Progressive Action", "Dribble", "Tackle", "Shot", "Pressing"],
            "Goalkeeper": ["Save", "xG Prevented", "Sweeper Action", "Progressive Distribution"],
            "Centre-Back": ["Line Breaking Pass", "Progressive Carry", "Defensive Action", "Aerial Duel"],
            "Full-Back": ["Progressive Run", "Cross into Danger", "Defensive Recovery", "Assist"],
            "Defensive Midfielder": ["Progressive Pass", "Progressive Carry", "Pass Under Pressure", "Ball Recovery"],
            "Central Midfielder": ["Progressive Pass", "Key Pass", "xA Action", "Dribble", "Shot"],
            "Attacking Midfielder": ["Chance Created", "xA Action", "Progressive Action", "Shot"],
            "Winger": ["Shot", "xG Action", "Dribble", "Pressing", "Off-ball Run"],
            "Striker": ["Shot", "xG Action", "Pressing", "Touch in Box", "Assist"]
        }
    }

# -------------------- LOGIN -------------------- #
def login():
    st.title("⚽ Takti Stats Tracker")
    st.markdown("### Professional Football Statistics Management")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("---")
        username = st.text_input("Username", placeholder="Enter username")
        password = st.text_input("Password", type="password", placeholder="Enter password")
        
        if st.button("🔐 Login", use_container_width=True):
            hashed_input = hashlib.sha256(password.encode()).hexdigest()
            if username == "dreamteam" and hashed_input == HASHED_PASSWORD:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("❌ Invalid credentials")
        
        st.markdown("---")
        st.info("💡 Default credentials: dreamteam / 1234567")

# -------------------- TEAM SHEET -------------------- #
def team_sheet():
    st.header("📋 Team Sheet Management")
    team_data = load_team()
    
    st.info("Configure your full squad below. Jersey numbers must be unique and numeric.")
    
    col1, col2 = st.columns(2)
    with col1:
        team_data["coach"] = st.text_input("👔 Coach Name", value=team_data.get("coach", ""))
    with col2:
        team_data["assistant"] = st.text_input("👔 Assistant Coach Name", value=team_data.get("assistant", ""))
    
    st.markdown("---")
    num_players = st.number_input("Total Squad Size", min_value=11, max_value=30, value=len(team_data.get("players", [])) or 18)
    
    positions = ['GK','CB','RCB','LCB','RB','LB','WB','RWB','LWB','DM','CDM','CM','AM','CAM','RM','LM','WM','RW','LW','ST','CF','SS','WF']
    
    # Load existing players
    existing_players = team_data.get("players", [])
    new_players = []
    used_jerseys = set()
    used_names = set()
    
    st.subheader("Player Roster")
    
    for i in range(num_players):
        with st.expander(f"Player {i+1}", expanded=(i < 11)):
            col1, col2, col3 = st.columns([3, 1, 2])
            
            # Pre-fill with existing data if available
            existing = existing_players[i] if i < len(existing_players) else {}
            
            with col1:
                name = st.text_input("Name", value=existing.get("name", ""), key=f"name_{i}", placeholder="Player name")
            with col2:
                jersey = st.text_input("Jersey #", value=existing.get("jersey", ""), key=f"jersey_{i}", placeholder="##")
            with col3:
                pos_index = positions.index(existing.get("position", "CM")) if existing.get("position") in positions else positions.index("CM")
                pos = st.selectbox("Position", options=positions, index=pos_index, key=f"pos_{i}")
            
            # Validation
            errors = []
            if name.strip():
                if jersey:
                    if not jersey.isdigit():
                        errors.append("Jersey must be numeric")
                    elif jersey in used_jerseys:
                        errors.append(f"Jersey {jersey} already assigned")
                    else:
                        used_jerseys.add(jersey)
                else:
                    errors.append("Jersey number required")
                
                if name in used_names:
                    errors.append(f"Player name already used")
                else:
                    used_names.add(name)
                
                if errors:
                    st.error(" | ".join(errors))
                else:
                    new_players.append({"name": name, "jersey": jersey, "position": pos})
    
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("💾 Save Team Sheet", use_container_width=True, type="primary"):
            if len(new_players) < 11:
                st.error("❌ You need at least 11 players!")
            elif len(used_jerseys) != len(new_players):
                st.error("❌ Fix duplicate or missing jerseys before saving.")
            else:
                team_data["players"] = new_players
                if save_team(team_data):
                    st.success("✅ Team sheet saved successfully!")
                    st.session_state.team_data = team_data
                    st.rerun()
    
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    with col3:
        if len(new_players) > 0:
            df = pd.DataFrame(new_players)
            csv = df.to_csv(index=False)
            st.download_button("📥 Export CSV", csv, "team_roster.csv", "text/csv", use_container_width=True)
    
    # Display current squad
    if new_players:
        st.markdown("---")
        st.subheader("Current Squad Overview")
        df = pd.DataFrame(new_players)
        st.dataframe(df, use_container_width=True)
        
        # Position distribution
        pos_counts = df['position'].value_counts()
        fig = px.bar(x=pos_counts.index, y=pos_counts.values, 
                     labels={'x': 'Position', 'y': 'Count'},
                     title="Squad Distribution by Position")
        st.plotly_chart(fig, use_container_width=True)
    
    return team_data

# -------------------- LINEUP SELECTION -------------------- #
def lineup_selection(team_data):
    st.header("📝 Match Lineup Selection")
    
    if not team_data.get("players"):
        st.warning("⚠️ Please complete Team Sheet first.")
        return None
    
    col1, col2 = st.columns([2, 1])
    with col1:
        formation = st.selectbox("⚽ Formation", options=list(formations.keys()))
    with col2:
        opponent = st.text_input("🆚 Opponent", placeholder="Opposition team")
    
    slots = formations[formation]
    
    # Group players by position
    players_by_pos = defaultdict(list)
    for p in team_data["players"]:
        players_by_pos[p["position"]].append(p)
    
    # All players for fallback
    all_players = [p["name"] for p in team_data["players"]]
    
    st.markdown("---")
    st.subheader("Starting XI")
    
    lineup = {}
    used_players = set()
    
    # Group positions for better UX
    cols = st.columns(3)
    for i, role in enumerate(slots):
        col = cols[i % 3]
        
        # Get players for this position + fallback
        pos_options = [p["name"] for p in players_by_pos.get(role, [])]
        if not pos_options:
            pos_options = all_players.copy()
        
        # Remove already used players
        available = [p for p in pos_options if p not in used_players]
        
        with col:
            player = st.selectbox(
                f"{role}", 
                options=["—"] + available,
                key=f"start_{i}",
                help=f"Select player for {role} position"
            )
            
            if player != "—":
                if player in used_players:
                    st.error(f"❌ {player} already selected!")
                else:
                    used_players.add(player)
                    lineup[role] = player
    
    st.markdown("---")
    st.subheader("Substitutes Bench")
    
    remaining_players = [p for p in all_players if p not in used_players]
    subs = []
    
    cols = st.columns(5)
    for i in range(15):
        col = cols[i % 5]
        with col:
            sub = st.selectbox(
                f"Sub {i+1}", 
                options=["—"] + [p for p in remaining_players if p not in subs],
                key=f"sub_{i}"
            )
            if sub != "—":
                subs.append(sub)
    
    # Lineup summary
    st.markdown("---")
    st.subheader("Lineup Summary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Starting XI**")
        lineup_rows = []
        for role in slots:
            player = lineup.get(role, "—")
            if player != "—":
                player_data = next((p for p in team_data["players"] if p["name"] == player), None)
                jersey = player_data["jersey"] if player_data else "—"
            else:
                jersey = "—"
            lineup_rows.append({"Position": role, "Player": player, "Jersey": jersey})
        
        st.dataframe(pd.DataFrame(lineup_rows), use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("**Substitutes**")
        sub_rows = []
        for s in subs:
            player_data = next((p for p in team_data["players"] if p["name"] == s), None)
            jersey = player_data["jersey"] if player_data else "—"
            sub_rows.append({"Player": s, "Jersey": jersey})
        
        if sub_rows:
            st.dataframe(pd.DataFrame(sub_rows), use_container_width=True, hide_index=True)
        else:
            st.info("No substitutes selected")
    
    # Export options
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Export Lineup PDF", use_container_width=True):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 20)
            pdf.cell(0, 15, "Match Lineup", ln=True, align="C")
            pdf.ln(5)
            
            pdf.set_font("Arial", "", 12)
            pdf.cell(0, 8, f"Coach: {team_data['coach']} | Assistant: {team_data['assistant']}", ln=True)
            if opponent:
                pdf.cell(0, 8, f"Opponent: {opponent}", ln=True)
            pdf.cell(0, 8, f"Formation: {formation}", ln=True)
            pdf.cell(0, 8, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
            pdf.ln(10)
            
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Starting XI", ln=True)
            pdf.set_font("Arial", "B", 10)
            pdf.cell(50, 8, "Position", 1)
            pdf.cell(90, 8, "Player", 1)
            pdf.cell(40, 8, "Jersey", 1, ln=True)
            
            pdf.set_font("Arial", "", 10)
            for row in lineup_rows:
                pdf.cell(50, 8, str(row["Position"]), 1)
                pdf.cell(90, 8, str(row["Player"]), 1)
                pdf.cell(40, 8, str(row["Jersey"]), 1, ln=True)
            
            pdf.ln(10)
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Substitutes", ln=True)
            pdf.set_font("Arial", "", 10)
            
            for row in sub_rows:
                pdf.cell(90, 8, str(row["Player"]), 1)
                pdf.cell(40, 8, str(row["Jersey"]), 1, ln=True)
            
            pdf.output("lineup.pdf")
            with open("lineup.pdf", "rb") as f:
                st.download_button("📥 Download PDF", f, "lineup.pdf", use_container_width=True)
    
    with col2:
        if st.button("💾 Save Lineup", use_container_width=True, type="primary"):
            st.session_state.lineup = lineup
            st.session_state.subs = subs
            st.session_state.formation = formation
            st.session_state.opponent = opponent
            st.success("✅ Lineup saved!")
    
    with col3:
        if lineup:
            lineup_json = json.dumps({"lineup": lineup, "subs": subs, "formation": formation}, indent=2)
            st.download_button("📥 Export JSON", lineup_json, "lineup.json", use_container_width=True)
    
    return lineup, subs, opponent

# -------------------- MATCH SETTINGS -------------------- #
def match_settings():
    st.header("⚙️ Match Configuration")
    
    if "team_data" not in st.session_state:
        st.warning("⚠️ Complete Team Sheet first.")
        return
    
    if "lineup" not in st.session_state:
        st.warning("⚠️ Select lineup first.")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        level = st.selectbox("📊 Tracking Level", ["Beginner", "Intermediate", "Semi-Pro", "Pro"])
    
    with col2:
        game_duration = st.number_input("⏱️ Match Duration (min)", min_value=20, max_value=120, value=90, step=10)
    
    with col3:
        halftime_duration = st.number_input("☕ Halftime Duration (min)", min_value=0, max_value=30, value=15, step=5)
    
    st.markdown("---")
    st.subheader("📋 Actions Preview")
    st.info(f"Review the actions available for tracking at **{level}** level")
    
    actions_dict = get_actions_per_level()[level]
    
    tabs = st.tabs(list(actions_dict.keys()))
    for tab, (group, actions) in zip(tabs, actions_dict.items()):
        with tab:
            st.markdown(f"**{group}**: {', '.join(actions)}")
    
    st.markdown("---")
    
    if st.button("🚀 START MATCH", use_container_width=True, type="primary"):
        st.session_state.match_level = level
        st.session_state.game_duration = game_duration
        st.session_state.halftime_duration = halftime_duration
        st.session_state.match_ready = True
        st.session_state.match_started = False
        st.session_state.elapsed_time = 0
        st.session_state.stats = []
        st.session_state.match_events = []
        st.session_state.substitutions = []
        st.session_state.active_players = set(st.session_state.lineup.values())
        st.session_state.match_score = {"home": 0, "away": 0}
        
        st.success("✅ Match settings locked! Proceeding to Live Match...")
        st.balloons()
        st.rerun()

# -------------------- LIVE MATCH -------------------- #
def live_match():
    if not st.session_state.get("match_ready", False):
        st.info("⚠️ Please complete all setup tabs and click 'START MATCH' in Match Settings.")
        return
    
    st.header("⚽ Live Match Tracking")
    
    # Match info header
    col1, col2, col3 = st.columns([2, 3, 2])
    
    with col1:
        st.metric("Formation", st.session_state.get("formation", "N/A"))
        st.metric("Level", st.session_state.get("match_level", "N/A"))
    
    with col2:
        # Timer display
        mins = int(st.session_state.elapsed_time // 60)
        secs = int(st.session_state.elapsed_time % 60)
        status = "🟢 LIVE" if st.session_state.match_started else "⏸️ PAUSED"
        
        st.markdown(f"""
        <div class='timer-display {"timer-running" if st.session_state.match_started else "timer-paused"}'>
            {status}<br>{mins:02d}:{secs:02d}
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.metric("Opponent", st.session_state.get("opponent", "N/A"))
        
        # Score tracking
        col_a, col_b = st.columns(2)
        with col_a:
            home_score = st.number_input("Us", value=st.session_state.match_score["home"], min_value=0, key="home_score")
            st.session_state.match_score["home"] = home_score
        with col_b:
            away_score = st.number_input("Them", value=st.session_state.match_score["away"], min_value=0, key="away_score")
            st.session_state.match_score["away"] = away_score
    
    # Timer controls
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("▶️ Start", use_container_width=True, type="primary"):
            st.session_state.match_started = True
            st.rerun()
    
    with col2:
        if st.button("⏸️ Pause", use_container_width=True):
            st.session_state.match_started = False
    
    with col3:
        if st.button("🔄 Reset", use_container_width=True):
            if st.session_state.get("stats"):
                st.warning("⚠️ This will clear all match data!")
            else:
                st.session_state.elapsed_time = 0
                st.session_state.match_started = False
                st.session_state.stats = []
                st.session_state.match_events = []
                st.rerun()
    
    with col4:
        if st.button("💾 Save & End", use_container_width=True):
            if st.session_state.get("stats"):
                match_data = {
                    "date": datetime.now().isoformat(),
                    "opponent": st.session_state.get("opponent", "Unknown"),
                    "formation": st.session_state.get("formation"),
                    "level": st.session_state.get("match_level"),
                    "duration": st.session_state.elapsed_time,
                    "score": st.session_state.match_score,
                    "lineup": st.session_state.get("lineup", {}),
                    "subs": st.session_state.get("subs", []),
                    "substitutions": st.session_state.get("substitutions", []),
                    "stats": st.session_state.stats,
                    "events": st.session_state.get("match_events", [])
                }
                filename = save_match_data(match_data)
                if filename:
                    st.success(f"✅ Match saved: {filename}")
                    st.session_state.match_ready = False
            else:
                st.error("No stats to save!")
    
    # Auto-refresh timer when running
    if st.session_state.match_started:
        st.session_state.elapsed_time += 1
        import time
        time.sleep(1)
        st.rerun()
    
    st.markdown("---")
    
    # Substitution management
    with st.expander("🔄 Substitutions", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            active = list(st.session_state.active_players)
            player_off = st.selectbox("Player OFF", active, key="sub_off")
        
        with col2:
            available_subs = [s for s in st.session_state.subs if s not in st.session_state.active_players]
            player_on = st.selectbox("Player ON", available_subs, key="sub_on")
        
        with col3:
            if st.button("Make Substitution", use_container_width=True):
                if player_off and player_on:
                    st.session_state.active_players.remove(player_off)
                    st.session_state.active_players.add(player_on)
                    
                    sub_event = {
                        "time": f"{mins:02d}:{secs:02d}",
                        "type": "substitution",
                        "off": player_off,
                        "on": player_on
                    }
                    st.session_state.substitutions.append(sub_event)
                    st.session_state.match_events.append(sub_event)
                    st.success(f"✅ {player_on} replaces {player_off}")
                    st.rerun()
        
        # Show substitution history
        if st.session_state.substitutions:
            st.markdown("**Substitution History:**")
            for sub in st.session_state.substitutions:
                st.text(f"{sub['time']}: {sub['on']} ➡️ {sub['off']}")
    
    # Quick actions
    st.markdown("---")
    st.subheader("⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("⚽ GOAL", use_container_width=True):
            st.session_state.match_events.append({
                "time": f"{mins:02d}:{secs:02d}",
                "type": "goal",
                "team": "home"
            })
            st.session_state.match_score["home"] += 1
            st.success("⚽ GOAL!")
    
    with col2:
        if st.button("🟨 Yellow Card", use_container_width=True):
            st.session_state.match_events.append({
                "time": f"{mins:02d}:{secs:02d}",
                "type": "yellow_card"
            })
            st.warning("🟨 Yellow Card")
    
    with col3:
        if st.button("🟥 Red Card", use_container_width=True):
            st.session_state.match_events.append({
                "time": f"{mins:02d}:{secs:02d}",
                "type": "red_card"
            })
            st.error("🟥 Red Card")
    
    with col4:
        if st.button("🎯 Penalty", use_container_width=True):
            st.session_state.match_events.append({
                "time": f"{mins:02d}:{secs:02d}",
                "type": "penalty"
            })
            st.info("🎯 Penalty")
    
    # Action logging
    st.markdown("---")
    st.subheader("📊 Player Action Logging")
    
    lineup = st.session_state.lineup
    level = st.session_state.match_level
    actions_dict = get_actions_per_level()[level]
    
    # Filter to show only active players
    active_lineup = {role: player for role, player in lineup.items() 
                     if player in st.session_state.active_players}
    
    # Group by position type
    position_groups = {
        "Goalkeeper": ["GK"],
        "Defence": ["CB", "RCB", "LCB", "RB", "LB", "RWB", "LWB"],
        "Midfield": ["DM", "CDM", "CM", "CAM", "AM", "RM", "LM"],
        "Attack": ["RW", "LW", "ST", "CF"]
    }
    
    tabs = st.tabs(["All Players"] + list(position_groups.keys()))
    
    with tabs[0]:
        for role, player in active_lineup.items():
            log_player_actions(player, role, actions_dict, mins, secs)
    
    for i, (group_name, positions) in enumerate(position_groups.items(), 1):
        with tabs[i]:
            group_players = {r: p for r, p in active_lineup.items() if r in positions}
            if group_players:
                for role, player in group_players.items():
                    log_player_actions(player, role, actions_dict, mins, secs)
            else:
                st.info(f"No active players in {group_name}")
    
    # Live stats display
    if st.session_state.stats:
        st.markdown("---")
        display_live_stats()

def log_player_actions(player, role, actions_dict, mins, secs):
    """Helper function to log actions for a player"""
    with st.expander(f"**{player}** ({role})", expanded=False):
        grouped_role = role_groups.get(role, "Central Midfielder")
        all_actions = list(set(actions_dict.get("All", []) + actions_dict.get(grouped_role, [])))
        
        # Create action buttons in grid
        cols = st.columns(4)
        for idx, action in enumerate(sorted(all_actions)):
            col = cols[idx % 4]
            
            col1, col2 = col.columns(2)
            with col1:
                if col1.button(f"✅ {action}", key=f"{player}_{action}_success_{idx}", use_container_width=True):
                    st.session_state.stats.append({
                        "player": player,
                        "role": role,
                        "action": action,
                        "outcome": "Successful",
                        "time": f"{mins:02d}:{secs:02d}",
                        "timestamp": st.session_state.elapsed_time
                    })
                    st.toast(f"✅ {player}: {action} (Success)")
            
            with col2:
                if col2.button(f"❌ {action}", key=f"{player}_{action}_fail_{idx}", use_container_width=True):
                    st.session_state.stats.append({
                        "player": player,
                        "role": role,
                        "action": action,
                        "outcome": "Unsuccessful",
                        "time": f"{mins:02d}:{secs:02d}",
                        "timestamp": st.session_state.elapsed_time
                    })
                    st.toast(f"❌ {player}: {action} (Failed)")

def display_live_stats():
    """Display live statistics and visualizations"""
    st.subheader("📈 Live Statistics")
    
    df = pd.DataFrame(st.session_state.stats)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_actions = len(df)
        st.metric("Total Actions", total_actions)
    
    with col2:
        success_rate = (df[df['outcome'] == 'Successful'].shape[0] / total_actions * 100) if total_actions > 0 else 0
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    with col3:
        active_players = df['player'].nunique()
        st.metric("Active Players", active_players)
    
    with col4:
        most_actions = df['player'].value_counts().iloc[0] if not df.empty else 0
        st.metric("Most Active", most_actions)
    
    # Detailed stats tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Player Stats", "Action Breakdown", "Timeline", "Export"])
    
    with tab1:
        # Player summary
        player_stats = df.groupby(['player', 'outcome']).size().unstack(fill_value=0)
        if not player_stats.empty:
            player_stats['Total'] = player_stats.sum(axis=1)
            if 'Successful' in player_stats.columns:
                player_stats['Success %'] = (player_stats['Successful'] / player_stats['Total'] * 100).round(1)
            st.dataframe(player_stats.sort_values('Total', ascending=False), use_container_width=True)
            
            # Top performers chart
            fig = px.bar(player_stats.reset_index(), x='player', y='Total',
                        title="Total Actions by Player",
                        color='Total', color_continuous_scale='Blues')
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # Action breakdown
        action_stats = df.groupby(['action', 'outcome']).size().unstack(fill_value=0)
        if not action_stats.empty:
            st.dataframe(action_stats, use_container_width=True)
            
            # Action success rates
            fig = px.bar(action_stats.reset_index(), x='action', 
                        y=['Successful', 'Unsuccessful'],
                        title="Action Success/Failure Breakdown",
                        barmode='group')
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        # Timeline
        st.markdown("**Match Timeline**")
        timeline_df = df[['time', 'player', 'action', 'outcome']].sort_values('time', ascending=False)
        st.dataframe(timeline_df.head(50), use_container_width=True, hide_index=True)
        
        # Actions over time
        df['minute'] = df['timestamp'] // 60
        actions_per_minute = df.groupby('minute').size()
        
        fig = px.line(x=actions_per_minute.index, y=actions_per_minute.values,
                     title="Action Intensity Over Time",
                     labels={'x': 'Minute', 'y': 'Actions'})
        st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        # Export options
        col1, col2 = st.columns(2)
        
        with col1:
            csv = df.to_csv(index=False)
            st.download_button("📥 Download CSV", csv, "match_stats.csv", "text/csv", use_container_width=True)
        
        with col2:
            json_data = df.to_json(orient='records', indent=2)
            st.download_button("📥 Download JSON", json_data, "match_stats.json", use_container_width=True)

# -------------------- MATCH HISTORY -------------------- #
def match_history():
    st.header("📚 Match History")
    
    matches = load_all_matches()
    
    if not matches:
        st.info("No matches recorded yet. Start tracking matches to build your history!")
        return
    
    st.metric("Total Matches", len(matches))
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        opponents = list(set([m.get("opponent", "Unknown") for m in matches]))
        selected_opponent = st.selectbox("Filter by Opponent", ["All"] + opponents)
    
    with col2:
        levels = list(set([m.get("level", "Unknown") for m in matches]))
        selected_level = st.selectbox("Filter by Level", ["All"] + levels)
    
    with col3:
        formations_used = list(set([m.get("formation", "Unknown") for m in matches]))
        selected_formation = st.selectbox("Filter by Formation", ["All"] + formations_used)
    
    # Filter matches
    filtered = matches
    if selected_opponent != "All":
        filtered = [m for m in filtered if m.get("opponent") == selected_opponent]
    if selected_level != "All":
        filtered = [m for m in filtered if m.get("level") == selected_level]
    if selected_formation != "All":
        filtered = [m for m in filtered if m.get("formation") == selected_formation]
    
    st.markdown("---")
    
    # Display matches
    for match in filtered:
        date = datetime.fromisoformat(match["date"]).strftime("%Y-%m-%d %H:%M")
        score = match.get("score", {"home": 0, "away": 0})
        
        with st.expander(f"**{date}** vs {match.get('opponent', 'Unknown')} - {score['home']}:{score['away']}", expanded=False):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Formation", match.get("formation", "N/A"))
            with col2:
                st.metric("Level", match.get("level", "N/A"))
            with col3:
                duration = int(match.get("duration", 0))
                st.metric("Duration", f"{duration//60}:{duration%60:02d}")
            with col4:
                result = "Win" if score["home"] > score["away"] else "Loss" if score["home"] < score["away"] else "Draw"
                st.metric("Result", result)
            
            # Stats summary
            if match.get("stats"):
                df = pd.DataFrame(match["stats"])
                st.subheader("Match Statistics")
                
                player_stats = df.groupby('player').agg({
                    'action': 'count',
                    'outcome': lambda x: (x == 'Successful').sum()
                }).rename(columns={'action': 'Total Actions', 'outcome': 'Successful'})
                player_stats['Success %'] = (player_stats['Successful'] / player_stats['Total Actions'] * 100).round(1)
                
                st.dataframe(player_stats, use_container_width=True)
            
            # Download match data
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"📥 Download JSON", key=f"json_{match['filename']}"):
                    json_str = json.dumps(match, indent=2)
                    st.download_button("Download", json_str, f"{match['filename']}", use_container_width=True)
            
            with col2:
                if match.get("stats"):
                    csv = pd.DataFrame(match["stats"]).to_csv(index=False)
                    st.download_button("📥 Download CSV", csv, f"{match['filename'].replace('.json', '.csv')}", 
                                     "text/csv", use_container_width=True)

# -------------------- MAIN APP -------------------- #
def main():
    # Initialize session state
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    
    if not st.session_state.logged_in:
        login()
        return
    
    # Sidebar
    with st.sidebar:
        st.title("⚽ Takti Stats")
        st.markdown(f"**User:** {st.session_state.get('username', 'User')}")
        st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        st.markdown("---")
        st.markdown("### Quick Stats")
        
        matches = load_all_matches()
        st.metric("Total Matches", len(matches))
        
        if matches:
            wins = sum(1 for m in matches if m.get("score", {}).get("home", 0) > m.get("score", {}).get("away", 0))
            st.metric("Wins", wins)
    
    # Main tabs
    tabs = st.tabs(["📋 Team Sheet", "📝 Lineup", "⚙️ Match Settings", "⚽ Live Match", "📚 History"])
    
    with tabs[0]:
        team_data = team_sheet()
        st.session_state.team_data = team_data
    
    with tabs[1]:
        if "team_data" in st.session_state and st.session_state.team_data.get("players"):
            result = lineup_selection(st.session_state.team_data)
            if result:
                lineup, subs, opponent = result
                st.session_state.lineup = lineup
                st.session_state.subs = subs
                st.session_state.opponent = opponent
        else:
            st.warning("⚠️ Please complete Team Sheet first.")
    
    with tabs[2]:
        match_settings()
    
    with tabs[3]:
        live_match()
    
    with tabs[4]:
        match_history()

if __name__ == "__main__":
    main()
