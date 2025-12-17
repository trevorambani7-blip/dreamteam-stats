import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import time
import hashlib
from datetime import datetime, timedelta
from collections import defaultdict
from fpdf import FPDF
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
from io import BytesIO
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# -------------------- CONFIGURATION -------------------- #
SESSION_TIMEOUT = 3600  # 1 hour session timeout
TEAM_FILE = "team_data.json"
MATCH_DATA_DIR = "match_data"
BACKUP_DIR = "backups"

# Create necessary directories
for directory in [MATCH_DATA_DIR, BACKUP_DIR]:
    os.makedirs(directory, exist_ok=True)

# -------------------- SECURITY -------------------- #
def get_hashed_password():
    """Get password from environment variable or use default (for demo)"""
    import os
    from dotenv import load_dotenv
    load_dotenv()
    password = os.getenv("APP_PASSWORD", "1234567")
    return hashlib.sha256(password.encode()).hexdigest()

HASHED_PASSWORD = get_hashed_password()

def check_session_timeout():
    """Check if session has timed out"""
    if 'login_time' in st.session_state:
        elapsed = time.time() - st.session_state.login_time
        if elapsed > SESSION_TIMEOUT:
            st.session_state.logged_in = False
            st.session_state.login_time = None
            st.error("Session expired. Please login again.")
            st.rerun()
    return True

# -------------------- CUSTOM CSS -------------------- #
def load_custom_css():
    """Load enhanced CSS with better styling"""
    custom_css = """
    <style>
    /* Main styles */
    .main {
        padding: 1rem;
    }
    
    /* Header styles */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background-color: #f0f2f6;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 5px 5px 0 0;
    }
    
    /* Card styling */
    .card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    /* Timer styling */
    .timer-container {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        color: white;
        margin: 20px 0;
    }
    
    .timer-display {
        font-size: 4rem;
        font-weight: bold;
        font-family: monospace;
        margin: 10px 0;
    }
    
    .period-display {
        font-size: 1.5rem;
        opacity: 0.9;
    }
    
    /* Button styling */
    .stButton button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
    
    /* Player card */
    .player-card {
        background: #f8f9fa;
        border-left: 4px solid #667eea;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    
    /* Success/Error messages */
    .stSuccess {
        border-radius: 10px;
        padding: 15px;
    }
    
    .stError {
        border-radius: 10px;
        padding: 15px;
    }
    
    /* Formation visualization */
    .formation-grid {
        display: grid;
        gap: 10px;
        padding: 20px;
        background: #f0f2f6;
        border-radius: 10px;
        margin: 20px 0;
    }
    
    /* Action button styling */
    .action-button {
        margin: 5px 0;
        width: 100%;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .timer-display {
            font-size: 3rem;
        }
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

# -------------------- INITIALIZATION -------------------- #
def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        'logged_in': False,
        'login_time': None,
        'team_data': {'coach': '', 'assistant': '', 'players': []},
        'lineup': {},
        'substitutes': [],
        'match_ready': False,
        'match_level': 'Beginner',
        'game_duration': 90,
        'halftime_duration': 15,
        'match_started': False,
        'match_paused': False,
        'elapsed_time': 0,
        'start_time': None,
        'stats': [],
        'first_half_stats': [],
        'second_half_stats': [],
        'formation': '4-4-2',
        'current_half': 1,
        'selected_player': 'All Players',
        'action_history': [],
        'match_notes': '',
        'opponent_team': '',
        'match_location': '',
        'weather_conditions': 'Sunny',
        'undo_stack': [],
        'redo_stack': [],
        'cached_actions': get_actions_per_level()
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# -------------------- ENHANCED LOGIN -------------------- #
def login_page():
    """Enhanced login page with better UX"""
    st.title("⚽ Takti Stats Tracker")
    st.markdown("---")
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login_form", clear_on_submit=True):
                st.subheader("Login")
                
                username = st.text_input("👤 Username", placeholder="Enter your username")
                password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    login_btn = st.form_submit_button("🚀 Login", use_container_width=True)
                with col_b:
                    demo_btn = st.form_submit_button("🎮 Demo Mode", use_container_width=True)
                
                if login_btn:
                    if username.strip() and password.strip():
                        hashed_input = hashlib.sha256(password.encode()).hexdigest()
                        if username == "dreamteam" and hashed_input == HASHED_PASSWORD:
                            st.session_state.logged_in = True
                            st.session_state.login_time = time.time()
                            st.success("✅ Login successful! Redirecting...")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ Invalid username or password")
                    else:
                        st.warning("⚠️ Please enter both username and password")
                
                if demo_btn:
                    st.session_state.logged_in = True
                    st.session_state.login_time = time.time()
                    st.session_state.demo_mode = True
                    st.success("🎮 Entering demo mode...")
                    time.sleep(0.5)
                    st.rerun()
            
            st.markdown("---")
            st.caption("Default credentials: username: `dreamteam`, password: `1234567`")
            st.caption("⚠️ For production use, set APP_PASSWORD in .env file")

# -------------------- ENHANCED TEAM SHEET -------------------- #
def validate_team_data(team_data: Dict) -> Tuple[bool, List[str]]:
    """Validate team data with comprehensive checks"""
    errors = []
    
    # Check required fields
    if not team_data.get('coach', '').strip():
        errors.append("Coach name is required")
    
    # Check players
    players = team_data.get('players', [])
    if len(players) < 11:
        errors.append(f"Need at least 11 players (currently {len(players)})")
    
    # Check for duplicate jerseys
    jerseys = []
    for i, player in enumerate(players):
        if not player.get('name', '').strip():
            errors.append(f"Player {i+1}: Name is required")
        
        jersey = player.get('jersey', '').strip()
        if jersey:
            if jersey in jerseys:
                errors.append(f"Jersey #{jersey} is duplicated")
            jerseys.append(jersey)
    
    return len(errors) == 0, errors

def save_team_backup(team_data: Dict):
    """Create backup of team data"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"team_backup_{timestamp}.json")
    try:
        with open(backup_file, 'w') as f:
            json.dump(team_data, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Backup failed: {e}")
        return False

def team_sheet_page():
    """Enhanced team sheet management"""
    st.header("👥 Team Sheet Management")
    
    # Initialize
    if 'team_data' not in st.session_state:
        st.session_state.team_data = load_team_data()
    
    team_data = st.session_state.team_data.copy()
    
    # Main form
    with st.form("team_sheet_form"):
        # Coach information
        col1, col2 = st.columns(2)
        with col1:
            team_data['coach'] = st.text_input(
                "Head Coach",
                value=team_data.get('coach', ''),
                help="Enter the name of the head coach"
            )
        with col2:
            team_data['assistant'] = st.text_input(
                "Assistant Coach",
                value=team_data.get('assistant', ''),
                help="Enter the name of the assistant coach"
            )
        
        st.markdown("---")
        
        # Squad size selection
        st.subheader("Squad Configuration")
        current_size = len(team_data.get('players', []))
        squad_size = st.slider(
            "Squad Size",
            min_value=11,
            max_value=30,
            value=max(18, current_size),
            help="Select total number of players in the squad"
        )
        
        # Positions with emojis for better visualization
        positions = {
            'GK': '🧤 Goalkeeper',
            'CB': '🛡️ Centre-Back',
            'RCB': '🛡️ Right Centre-Back',
            'LCB': '🛡️ Left Centre-Back',
            'RB': '🏃 Right-Back',
            'LB': '🏃 Left-Back',
            'WB': '🏃 Wing-Back',
            'RWB': '🏃 Right Wing-Back',
            'LWB': '🏃 Left Wing-Back',
            'DM': '🛡️ Defensive Midfielder',
            'CDM': '🛡️ Central Defensive Midfielder',
            'CM': '⚙️ Central Midfielder',
            'AM': '🎯 Attacking Midfielder',
            'CAM': '🎯 Central Attacking Midfielder',
            'RM': '🚀 Right Midfielder',
            'LM': '🚀 Left Midfielder',
            'WM': '🚀 Winger',
            'RW': '🚀 Right Winger',
            'LW': '🚀 Left Winger',
            'ST': '⚽ Striker',
            'CF': '⚽ Centre Forward',
            'SS': '⚽ Second Striker',
            'WF': '⚽ Wide Forward'
        }
        
        # Player entries
        st.subheader("Player Roster")
        team_data['players'] = []
        used_jerseys = set()
        
        for i in range(squad_size):
            with st.expander(f"Player {i+1}", expanded=(i < 5)):
                col1, col2, col3 = st.columns([3, 1, 2])
                
                with col1:
                    name = st.text_input(
                        "Full Name",
                        value=team_data.get('players', [{}])[i].get('name', '') if i < len(team_data.get('players', [])) else '',
                        key=f"name_{i}",
                        placeholder="Enter player's full name"
                    )
                
                with col2:
                    jersey = st.text_input(
                        "Jersey #",
                        value=team_data.get('players', [{}])[i].get('jersey', '') if i < len(team_data.get('players', [])) else '',
                        key=f"jersey_{i}",
                        placeholder="#",
                        max_chars=3
                    )
                    
                    if jersey and jersey in used_jerseys:
                        st.error(f"#{jersey} already used")
                    elif jersey:
                        used_jerseys.add(jersey)
                
                with col3:
                    pos_options = list(positions.keys())
                    default_pos = team_data.get('players', [{}])[i].get('position', 'CM') if i < len(team_data.get('players', [])) else 'CM'
                    default_idx = pos_options.index(default_pos) if default_pos in pos_options else 0
                    
                    pos = st.selectbox(
                        "Position",
                        options=pos_options,
                        format_func=lambda x: positions[x],
                        index=default_idx,
                        key=f"pos_{i}"
                    )
                
                # Additional player info
                col4, col5 = st.columns(2)
                with col4:
                    age = st.number_input(
                        "Age",
                        min_value=6,
                        max_value=50,
                        value=team_data.get('players', [{}])[i].get('age', 16) if i < len(team_data.get('players', [])) else 16,
                        key=f"age_{i}"
                    )
                
                with col5:
                    foot = st.selectbox(
                        "Preferred Foot",
                        options=["Right", "Left", "Both"],
                        index=["Right", "Left", "Both"].index(
                            team_data.get('players', [{}])[i].get('foot', 'Right') if i < len(team_data.get('players', [])) else 'Right'
                        ),
                        key=f"foot_{i}"
                    )
                
                if name.strip():
                    player_data = {
                        'name': name.strip(),
                        'jersey': jersey.strip(),
                        'position': pos,
                        'age': age,
                        'foot': foot,
                        'id': f"p_{i}_{hashlib.md5(name.strip().encode()).hexdigest()[:8]}"
                    }
                    team_data['players'].append(player_data)
        
        # Form submission
        col1, col2, col3 = st.columns(3)
        with col1:
            save_btn = st.form_submit_button("💾 Save Team Sheet", use_container_width=True)
        with col2:
            reset_btn = st.form_submit_button("🔄 Reset to Default", use_container_width=True)
        with col3:
            load_btn = st.form_submit_button("📂 Load from Backup", use_container_width=True)
    
    # Button actions
    if save_btn:
        is_valid, errors = validate_team_data(team_data)
        if not is_valid:
            for error in errors:
                st.error(error)
        else:
            # Create backup before saving
            if save_team_backup(team_data):
                save_team_data(team_data)
                st.session_state.team_data = team_data
                st.success("✅ Team sheet saved successfully!")
                st.balloons()
    
    elif reset_btn:
        st.session_state.team_data = {'coach': '', 'assistant': '', 'players': []}
        st.rerun()
    
    elif load_btn:
        load_backup_interface()
    
    # Display summary
    if team_data.get('players'):
        display_team_summary(team_data)
    
    return team_data

def display_team_summary(team_data: Dict):
    """Display team summary with visualization"""
    st.markdown("---")
    st.subheader("📊 Team Summary")
    
    players_df = pd.DataFrame(team_data['players'])
    
    if not players_df.empty:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Players", len(players_df))
        with col2:
            avg_age = players_df['age'].mean() if 'age' in players_df.columns else 'N/A'
            st.metric("Average Age", f"{avg_age:.1f}" if isinstance(avg_age, (int, float)) else avg_age)
        with col3:
            right_footed = sum(1 for p in team_data['players'] if p.get('foot') == 'Right')
            st.metric("Right Footed", right_footed)
        with col4:
            positions_count = len(set(p['position'] for p in team_data['players']))
            st.metric("Positions", positions_count)
        
        # Position distribution chart
        if 'position' in players_df.columns:
            fig = px.pie(
                players_df,
                names='position',
                title='Position Distribution',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_layout(showlegend=True, height=300)
            st.plotly_chart(fig, use_container_width=True)

# -------------------- ENHANCED FORMATIONS -------------------- #
def get_formations_with_visuals() -> Dict:
    """Get formations with visual representations"""
    formations = {
        "4-4-2": {
            "positions": ["GK", "LB", "CB", "CB", "RB", "LM", "CM", "CM", "RM", "ST", "ST"],
            "description": "Balanced formation with two strikers",
            "emoji": "⚖️"
        },
        "4-3-3": {
            "positions": ["GK", "LB", "CB", "CB", "RB", "CM", "CM", "CM", "LW", "ST", "RW"],
            "description": "Attacking formation with wingers",
            "emoji": "⚡"
        },
        "4-2-3-1": {
            "positions": ["GK", "LB", "CB", "CB", "RB", "CDM", "CDM", "CAM", "LW", "ST", "RW"],
            "description": "Modern formation with attacking midfield",
            "emoji": "🎯"
        },
        "3-5-2": {
            "positions": ["GK", "CB", "CB", "CB", "LM", "CM", "CM", "RM", "CAM", "ST", "ST"],
            "description": "Midfield dominance with three centre-backs",
            "emoji": "🛡️"
        },
        "4-5-1": {
            "positions": ["GK", "LB", "CB", "CB", "RB", "LM", "CM", "CM", "CM", "RM", "ST"],
            "description": "Defensive formation packing midfield",
            "emoji": "🔒"
        },
        "3-4-3": {
            "positions": ["GK", "CB", "CB", "CB", "LM", "CM", "CM", "RM", "LW", "ST", "RW"],
            "description": "Very attacking with three forwards",
            "emoji": "🔥"
        }
    }
    return formations

def visualize_formation(formation_name: str, lineup: Dict):
    """Create visual formation diagram"""
    formation = get_formations_with_visuals()[formation_name]
    positions = formation["positions"]
    
    # Create a football pitch visualization
    fig = go.Figure()
    
    # Add pitch background
    fig.add_shape(type="rect", x0=0, y0=0, x1=100, y1=100, 
                  line=dict(color="green", width=2), fillcolor="lightgreen")
    
    # Position mapping to coordinates
    position_coords = {
        "GK": (50, 10),
        "CB": [(35, 30), (65, 30)],
        "LCB": (30, 30),
        "RCB": (70, 30),
        "LB": (20, 40),
        "RB": (80, 40),
        "LWB": (15, 50),
        "RWB": (85, 50),
        "DM": [(40, 50), (60, 50)],
        "CDM": [(45, 45), (55, 45)],
        "CM": [(40, 60), (60, 60)],
        "LM": (20, 70),
        "RM": (80, 70),
        "CAM": (50, 70),
        "LW": (20, 85),
        "RW": (80, 85),
        "ST": (50, 85),
        "CF": (50, 80),
        "SS": (50, 75)
    }
    
    # Plot players
    player_x = []
    player_y = []
    player_names = []
    
    for pos in positions:
        if pos in lineup and lineup[pos] != "—":
            if pos in position_coords:
                coords = position_coords[pos]
                if isinstance(coords[0], (list, tuple)) and isinstance(coords[0][0], (int, float)):
                    # Multiple positions
                    for coord in coords:
                        player_x.append(coord[0])
                        player_y.append(coord[1])
                        player_names.append(lineup[pos])
                else:
                    player_x.append(coords[0])
                    player_y.append(coords[1])
                    player_names.append(lineup[pos])
    
    fig.add_trace(go.Scatter(
        x=player_x, y=player_y,
        mode='markers+text',
        marker=dict(size=20, color='blue'),
        text=player_names,
        textposition="top center"
    ))
    
    fig.update_layout(
        title=f"{formation_name} Formation",
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        height=400,
        showlegend=False
    )
    
    return fig

# -------------------- ENHANCED LINEUP SELECTION -------------------- #
def lineup_selection_page():
    """Enhanced lineup selection with visualization"""
    st.header("🎯 Lineup Selection")
    
    if 'team_data' not in st.session_state or not st.session_state.team_data.get('players'):
        st.warning("⚠️ Please complete Team Sheet first.")
        return {}
    
    team_data = st.session_state.team_data
    formations = get_formations_with_visuals()
    
    # Formation selection with preview
    col1, col2 = st.columns([2, 1])
    with col1:
        formation_options = {f"{v['emoji']} {k}": k for k, v in formations.items()}
        selected_form = st.selectbox(
            "Select Formation",
            options=list(formation_options.keys()),
            help="Choose your tactical formation"
        )
        formation_name = formation_options[selected_form]
        st.session_state.formation = formation_name
    
    with col2:
        st.metric("Formation", formation_name)
        st.caption(formations[formation_name]["description"])
    
    # Visual formation preview
    with st.expander("📐 Formation Preview", expanded=True):
        fig = visualize_formation(formation_name, {})
        st.plotly_chart(fig, use_container_width=True)
    
    # Starting lineup selection
    st.subheader("🏁 Starting XI")
    slots = formations[formation_name]["positions"]
    
    # Group players by position
    players_by_pos = defaultdict(list)
    for player in team_data['players']:
        pos = player['position']
        players_by_pos[pos].append((player['name'], player['jersey']))
    
    # Starting lineup selection
    lineup = {}
    used_players = set()
    
    cols = st.columns(3)
    col_idx = 0
    
    for i, role in enumerate(slots):
        col = cols[col_idx]
        with col:
            # Find suitable players
            suitable_players = []
            for player in team_data['players']:
                if player['name'] not in used_players:
                    if player['position'] == role or role in player['position']:
                        suitable_players.append(f"{player['name']} (#{player['jersey']})")
            
            if not suitable_players:
                suitable_players = [f"{p['name']} (#{p['jersey']})" 
                                   for p in team_data['players'] 
                                   if p['name'] not in used_players]
            
            # Add "—" option
            options = ["—"] + suitable_players
            
            # Get current selection
            current_val = lineup.get(role, "—")
            if current_val != "—":
                current_display = f"{current_val} (#{next(p['jersey'] for p in team_data['players'] if p['name'] == current_val)})"
                if current_display not in options:
                    options.insert(0, current_display)
            
            # Selectbox
            selected = st.selectbox(
                f"{role}",
                options=options,
                key=f"start_{i}",
                help=f"Select player for {role} position"
            )
            
            if selected != "—":
                player_name = selected.split(" (")[0]
                if player_name in used_players:
                    st.error(f"⚠️ {player_name} already selected!")
                else:
                    used_players.add(player_name)
                    lineup[role] = player_name
        
        col_idx = (col_idx + 1) % 3
    
    # Substitutes
    st.subheader("🔄 Substitutes")
    remaining_players = [p for p in team_data['players'] if p['name'] not in used_players]
    
    if 'substitutes' not in st.session_state:
        st.session_state.substitutes = []
    
    num_subs = st.slider("Number of Substitutes", 0, 15, min(7, len(remaining_players)))
    
    subs = []
    for i in range(num_subs):
        sub_options = ["—"] + [f"{p['name']} (#{p['jersey']})" for p in remaining_players if f"{p['name']} (#{p['jersey']})" not in subs]
        
        selected_sub = st.selectbox(
            f"Substitute {i+1}",
            options=sub_options,
            key=f"sub_{i}"
        )
        
        if selected_sub != "—":
            player_name = selected_sub.split(" (")[0]
            subs.append(player_name)
            st.session_state.substitutes = subs
    
    # Display lineup summary
    st.markdown("---")
    st.subheader("📋 Lineup Summary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Starting XI**")
        for role, player in lineup.items():
            if player != "—":
                jersey = next((p['jersey'] for p in team_data['players'] if p['name'] == player), "—")
                st.write(f"• {role}: {player} (#{jersey})")
    
    with col2:
        st.write("**Substitutes**")
        for sub in st.session_state.substitutes:
            if sub != "—":
                jersey = next((p['jersey'] for p in team_data['players'] if p['name'] == sub), "—")
                st.write(f"• {sub} (#{jersey})")
    
    # Export options
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💾 Save Lineup", use_container_width=True):
            st.session_state.lineup = lineup
            st.success("Lineup saved!")
    
    with col2:
        if st.button("📄 Export PDF", use_container_width=True):
            pdf_path = export_lineup_to_pdf(lineup, st.session_state.substitutes)
            with open(pdf_path, "rb") as f:
                st.download_button(
                    "Download PDF",
                    f,
                    file_name=pdf_path,
                    mime="application/pdf"
                )
    
    with col3:
        if st.button("🖨️ Print View", use_container_width=True):
            show_print_view(lineup, st.session_state.substitutes)
    
    st.session_state.lineup = lineup
    return lineup

def export_lineup_to_pdf(lineup: Dict, substitutes: List[str]) -> str:
    """Export lineup to PDF"""
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", "B", 24)
    pdf.cell(0, 20, "Match Lineup Sheet", ln=True, align="C")
    pdf.ln(10)
    
    # Team info
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Coach: {st.session_state.team_data.get('coach', 'N/A')}", ln=True)
    pdf.cell(0, 10, f"Assistant: {st.session_state.team_data.get('assistant', 'N/A')}", ln=True)
    pdf.cell(0, 10, f"Formation: {st.session_state.get('formation', 'N/A')}", ln=True)
    pdf.cell(0, 10, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.ln(10)
    
    # Starting XI
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Starting XI", ln=True)
    pdf.set_font("Arial", "", 12)
    
    pdf.cell(40, 10, "Position", 1)
    pdf.cell(100, 10, "Player", 1)
    pdf.cell(40, 10, "Jersey #", 1, ln=True)
    
    for position, player in lineup.items():
        if player != "—":
            jersey = next((p['jersey'] for p in st.session_state.team_data['players'] if p['name'] == player), "—")
            pdf.cell(40, 10, position, 1)
            pdf.cell(100, 10, player, 1)
            pdf.cell(40, 10, str(jersey), 1, ln=True)
    
    pdf.ln(10)
    
    # Substitutes
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Substitutes", ln=True)
    pdf.set_font("Arial", "", 12)
    
    pdf.cell(40, 10, "Position", 1)
    pdf.cell(100, 10, "Player", 1)
    pdf.cell(40, 10, "Jersey #", 1, ln=True)
    
    for sub in substitutes:
        if sub != "—":
            jersey = next((p['jersey'] for p in st.session_state.team_data['players'] if p['name'] == sub), "—")
            pdf.cell(40, 10, "SUB", 1)
            pdf.cell(100, 10, sub, 1)
            pdf.cell(40, 10, str(jersey), 1, ln=True)
    
    # Save file
    filename = f"lineup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(filename)
    return filename

def show_print_view(lineup: Dict, substitutes: List[str]):
    """Display printable lineup view"""
    with st.expander("🖨️ Printable Lineup", expanded=True):
        st.markdown("""
        <style>
        @media print {
            .no-print { display: none; }
            body { font-size: 12pt; }
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.header("Match Lineup Sheet")
        st.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        st.write(f"**Coach:** {st.session_state.team_data.get('coach', 'N/A')}")
        st.write(f"**Formation:** {st.session_state.get('formation', 'N/A')}")
        
        st.subheader("Starting XI")
        start_df = pd.DataFrame([
            {
                "Position": pos,
                "Player": player,
                "Jersey": next((p['jersey'] for p in st.session_state.team_data['players'] if p['name'] == player), "—")
            }
            for pos, player in lineup.items() if player != "—"
        ])
        st.table(start_df)
        
        st.subheader("Substitutes")
        sub_df = pd.DataFrame([
            {
                "Position": "SUB",
                "Player": sub,
                "Jersey": next((p['jersey'] for p in st.session_state.team_data['players'] if p['name'] == sub), "—")
            }
            for sub in substitutes if sub != "—"
        ])
        st.table(sub_df)
        
        st.button("🖨️ Print this Page", on_click=lambda: st.write('<script>window.print()</script>', unsafe_allow_html=True))

# -------------------- ENHANCED MATCH SETTINGS -------------------- #
def match_settings_page():
    """Enhanced match settings with more options"""
    st.header("⚙️ Match Settings")
    
    if 'team_data' not in st.session_state:
        st.warning("⚠️ Please complete Team Sheet first.")
        return
    
    if 'lineup' not in st.session_state or not st.session_state.lineup:
        st.warning("⚠️ Please select lineup first.")
        return
    
    # Match details
    with st.form("match_settings_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Match Information")
            st.session_state.match_date = st.date_input("Match Date", datetime.now())
            st.session_state.match_time = st.time_input("Match Time", datetime.now().time())
            st.session_state.match_location = st.text_input("Venue", placeholder="Stadium name")
            st.session_state.opponent_team = st.text_input("Opponent Team", placeholder="Opponent team name")
        
        with col2:
            st.subheader("Match Conditions")
            st.session_state.game_duration = st.number_input(
                "Match Duration (minutes)",
                min_value=40,
                max_value=120,
                value=90,
                help="Total match duration including stoppage time"
            )
            st.session_state.halftime_duration = st.number_input(
                "Halftime Duration (minutes)",
                min_value=5,
                max_value=30,
                value=15
            )
            st.session_state.match_level = st.selectbox(
                "Tracking Level",
                options=["Beginner", "Intermediate", "Semi-Pro", "Pro"],
                index=0,
                help="Select the level of detail for statistics tracking"
            )
            st.session_state.weather_conditions = st.selectbox(
                "Weather Conditions",
                options=["Sunny", "Cloudy", "Rainy", "Windy", "Snow", "Artificial Light"],
                index=0
            )
        
        # Additional match info
        st.subheader("Additional Information")
        col3, col4 = st.columns(2)
        with col3:
            st.session_state.referee = st.text_input("Referee", placeholder="Referee name")
            st.session_state.competition = st.text_input("Competition", placeholder="Tournament/League name")
        
        with col4:
            st.session_state.match_notes = st.text_area(
                "Match Notes",
                placeholder="Additional notes about the match...",
                height=100
            )
        
        # Actions preview
        st.subheader("📊 Available Actions Preview")
        actions_dict = get_actions_per_level()[st.session_state.match_level]
        
        for group, actions in actions_dict.items():
            with st.expander(f"{group} Actions"):
                cols = st.columns(3)
                for idx, action in enumerate(actions):
                    col = cols[idx % 3]
                    col.info(f"• {action}")
        
        # Submit button
        if st.form_submit_button("🚀 Proceed to Live Match", use_container_width=True, type="primary"):
            if validate_match_settings():
                st.session_state.match_ready = True
                st.session_state.match_id = f"match_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                st.success("✅ Match settings saved! Proceeding to Live Match...")
                st.balloons()
                time.sleep(1)
                st.rerun()

def validate_match_settings() -> bool:
    """Validate match settings"""
    errors = []
    
    if not st.session_state.get('opponent_team', '').strip():
        errors.append("Opponent team name is required")
    
    if st.session_state.get('game_duration', 0) < 40:
        errors.append("Match duration must be at least 40 minutes")
    
    if len(st.session_state.get('lineup', {})) < 7:
        errors.append("Need at least 7 players in lineup")
    
    if errors:
        for error in errors:
            st.error(error)
        return False
    
    return True

# -------------------- ENHANCED LIVE MATCH TIMER -------------------- #
class MatchTimer:
    """Enhanced match timer with multiple periods"""
    
    def __init__(self):
        self.ph = st.empty()
        self.status_ph = st.empty()
        
    def display(self):
        """Display the timer with status"""
        if st.session_state.match_started and not st.session_state.match_paused:
            current_time = time.time()
            elapsed = current_time - st.session_state.start_time
            st.session_state.elapsed_time = elapsed
            
            # Check for half time
            if elapsed > (st.session_state.game_duration * 60 / 2) and st.session_state.current_half == 1:
                st.session_state.current_half = 1.5  # Half time
                self._handle_half_time()
            elif elapsed > (st.session_state.game_duration * 60 / 2 + st.session_state.halftime_duration * 60) and st.session_state.current_half == 1.5:
                st.session_state.current_half = 2
                self._handle_second_half_start()
        
        mins, secs = self._get_display_time()
        period = self._get_period_display()
        
        # Determine color
        color = self._get_timer_color(mins, secs)
        
        # Display timer
        self.ph.markdown(f"""
        <div class="timer-container">
            <div class="period-display">{period}</div>
            <div class="timer-display" style="color: {color}">{mins:02d}:{secs:02d}</div>
        </div>
        """, unsafe_allow_html=True)
        
        return mins, secs
    
    def _get_display_time(self) -> Tuple[int, int]:
        """Get formatted time"""
        elapsed = st.session_state.elapsed_time
        
        if st.session_state.current_half == 2:
            # Second half time
            halftime_point = (st.session_state.game_duration * 60 / 2) + (st.session_state.halftime_duration * 60)
            second_half_elapsed = elapsed - halftime_point
            if second_half_elapsed < 0:
                second_half_elapsed = 0
            mins = int(second_half_elapsed // 60)
            secs = int(second_half_elapsed % 60)
        else:
            mins = int(elapsed // 60)
            secs = int(elapsed % 60)
        
        return mins, secs
    
    def _get_period_display(self) -> str:
        """Get period display string"""
        if st.session_state.current_half == 1:
            return "1st Half"
        elif st.session_state.current_half == 1.5:
            return "Half Time"
        elif st.session_state.current_half == 2:
            return "2nd Half"
        else:
            return "Match Ended"
    
    def _get_timer_color(self, mins: int, secs: int) -> str:
        """Get timer color based on match state"""
        if not st.session_state.match_started:
            return "#FFA500"  # Orange for paused
        elif st.session_state.match_paused:
            return "#FFA500"  # Orange for paused
        elif st.session_state.current_half == 1.5:
            return "#9370DB"  # Purple for half time
        elif mins >= st.session_state.game_duration:
            return "#FF4444"  # Red for overtime
        else:
            return "#44FF44"  # Green for running
    
    def _handle_half_time(self):
        """Handle half time transition"""
        # Save first half stats
        if st.session_state.stats:
            st.session_state.first_half_stats = st.session_state.stats.copy()
            st.session_state.stats = []
        
        # Update status
        self.status_ph.info("⏸️ Half time! Stats saved for first half.")
    
    def _handle_second_half_start(self):
        """Handle second half start"""
        self.status_ph.success("▶️ Second half started!")
    
    def control_panel(self):
        """Display timer control panel"""
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if not st.session_state.match_started:
                if st.button("▶️ Start Match", use_container_width=True, type="primary"):
                    if not st.session_state.match_started:
                        st.session_state.start_time = time.time() - st.session_state.elapsed_time
                        st.session_state.match_started = True
                        st.session_state.match_paused = False
                        st.rerun()
            elif st.session_state.match_paused:
                if st.button("▶️ Resume", use_container_width=True, type="primary"):
                    st.session_state.start_time = time.time() - st.session_state.elapsed_time
                    st.session_state.match_paused = False
                    st.rerun()
            else:
                if st.button("⏸️ Pause", use_container_width=True):
                    st.session_state.elapsed_time = time.time() - st.session_state.start_time
                    st.session_state.match_paused = True
                    st.rerun()
        
        with col2:
            if st.button("⏹️ End Half", use_container_width=True):
                if st.session_state.current_half == 1:
                    st.session_state.current_half = 1.5
                    self._handle_half_time()
                elif st.session_state.current_half == 2:
                    st.session_state.current_half = 3  # Match ended
                    self._handle_match_end()
                st.rerun()
        
        with col3:
            if st.button("➕ Add Time", use_container_width=True):
                st.session_state.elapsed_time += 60  # Add 1 minute
                if st.session_state.match_started and not st.session_state.match_paused:
                    st.session_state.start_time = time.time() - st.session_state.elapsed_time
                st.rerun()
        
        with col4:
            if st.button("➖ Remove Time", use_container_width=True):
                st.session_state.elapsed_time = max(0, st.session_state.elapsed_time - 60)
                if st.session_state.match_started and not st.session_state.match_paused:
                    st.session_state.start_time = time.time() - st.session_state.elapsed_time
                st.rerun()
        
        with col5:
            if st.button("🔄 Reset", use_container_width=True):
                self._reset_timer()
                st.rerun()
    
    def _reset_timer(self):
        """Reset timer to initial state"""
        st.session_state.elapsed_time = 0
        st.session_state.start_time = None
        st.session_state.match_started = False
        st.session_state.match_paused = False
        st.session_state.current_half = 1
        st.session_state.stats = []
        st.session_state.first_half_stats = []
        st.session_state.second_half_stats = []
    
    def _handle_match_end(self):
        """Handle match end"""
        # Save second half stats
        if st.session_state.stats:
            st.session_state.second_half_stats = st.session_state.stats.copy()
        
        # Save full match data
        save_match_data()
        
        st.success("🏁 Match ended! Full stats saved.")

# -------------------- ENHANCED ACTION LOGGING -------------------- #
def action_logging_page():
    """Enhanced action logging interface"""
    st.header("📝 Action Logging")
    
    if not st.session_state.get('match_ready', False):
        st.info("Please complete match settings first.")
        return
    
    # Quick stats overview
    if st.session_state.stats:
        display_quick_stats()
    
    # Player selection
    col1, col2 = st.columns([2, 1])
    with col1:
        player_options = ["All Players"] + list(st.session_state.lineup.values())
        st.session_state.selected_player = st.selectbox(
            "Select Player",
            options=player_options,
            index=0
        )
    
    with col2:
        # Undo/Redo functionality
        col_undo, col_redo = st.columns(2)
        with col_undo:
            if st.button("↶ Undo", disabled=not st.session_state.undo_stack):
                undo_last_action()
        with col_redo:
            if st.button("↷ Redo", disabled=not st.session_state.redo_stack):
                redo_action()
    
    # Get current time
    timer = MatchTimer()
    mins, secs = timer.display()
    
    # Action logging interface
    if st.session_state.selected_player == "All Players":
        # Show all players in expanders
        for position, player in st.session_state.lineup.items():
            if player != "—":
                with st.expander(f"**{player}** ({position})", expanded=True):
                    display_player_actions(player, position, mins, secs)
    else:
        # Show single player actions
        player = st.session_state.selected_player
        position = [k for k, v in st.session_state.lineup.items() if v == player][0]
        display_player_actions(player, position, mins, secs, expanded=True)
    
    # Live stats display
    if st.session_state.stats:
        display_live_stats()

def display_player_actions(player: str, position: str, mins: int, secs: int, expanded: bool = False):
    """Display action buttons for a specific player"""
    # Get actions for player's role
    level = st.session_state.match_level
    actions_dict = get_actions_per_level()[level]
    role_group = role_groups.get(position, "Central Midfielder")
    
    # Combine all actions and role-specific actions
    all_actions = actions_dict.get("All", [])
    role_actions = actions_dict.get(role_group, [])
    available_actions = list(set(all_actions + role_actions))
    
    # Display action buttons in columns
    cols_per_row = 3
    cols = st.columns(cols_per_row)
    
    outcomes = ["✅ Successful", "❌ Unsuccessful", "⚪ Neutral"]
    
    for idx, action in enumerate(available_actions):
        col = cols[idx % cols_per_row]
        with col:
            # Create a unique key
            action_key = f"{player}_{action}_{idx}_{mins}_{secs}"
            
            # Use columns within button for better layout
            if st.button(
                f"{action}",
                key=f"btn_{action_key}",
                use_container_width=True
            ):
                # Show outcome selector
                outcome = st.selectbox(
                    "Select Outcome",
                    options=outcomes,
                    key=f"outcome_{action_key}",
                    label_visibility="collapsed"
                )
                
                if outcome:
                    log_action(player, position, action, outcome, mins, secs)
                    st.success(f"✅ Logged: {player} - {action}")
                    st.rerun()

def log_action(player: str, position: str, action: str, outcome: str, mins: int, secs: int):
    """Log an action with undo support"""
    # Save current state for undo
    if len(st.session_state.stats) > 0:
        st.session_state.undo_stack.append(st.session_state.stats.copy())
    
    # Clear redo stack
    st.session_state.redo_stack.clear()
    
    # Add new action
    action_record = {
        "player": player,
        "position": position,
        "action": action,
        "outcome": outcome.replace("✅ ", "").replace("❌ ", "").replace("⚪ ", ""),
        "time": f"{mins:02d}:{secs:02d}",
        "timestamp": datetime.now().isoformat(),
        "half": "1H" if st.session_state.current_half == 1 else "2H"
    }
    
    st.session_state.stats.append(action_record)

def undo_last_action():
    """Undo the last action"""
    if st.session_state.undo_stack:
        # Move current state to redo stack
        st.session_state.redo_stack.append(st.session_state.stats.copy())
        # Restore previous state
        st.session_state.stats = st.session_state.undo_stack.pop()
        st.rerun()

def redo_action():
    """Redo the last undone action"""
    if st.session_state.redo_stack:
        # Save current state to undo stack
        st.session_state.undo_stack.append(st.session_state.stats.copy())
        # Restore redone state
        st.session_state.stats = st.session_state.redo_stack.pop()
        st.rerun()

def display_quick_stats():
    """Display quick stats overview"""
    st.subheader("📊 Live Stats Summary")
    
    df = pd.DataFrame(st.session_state.stats)
    
    if not df.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_actions = len(df)
            st.metric("Total Actions", total_actions)
        
        with col2:
            successful = len(df[df['outcome'] == 'Successful'])
            success_rate = (successful / total_actions * 100) if total_actions > 0 else 0
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        with col3:
            unique_players = df['player'].nunique()
            st.metric("Active Players", unique_players)
        
        with col4:
            actions_per_min = total_actions / (st.session_state.elapsed_time / 60) if st.session_state.elapsed_time > 0 else 0
            st.metric("Actions/Min", f"{actions_per_min:.1f}")

def display_live_stats():
    """Display live statistics table"""
    df = pd.DataFrame(st.session_state.stats)
    
    # Summary by player
    st.subheader("Player Statistics")
    player_summary = df.groupby(['player', 'action', 'outcome']).size().unstack(fill_value=0)
    st.dataframe(player_summary, use_container_width=True)
    
    # Recent actions
    st.subheader("Recent Actions")
    recent_df = df.tail(10).copy()
    recent_df['index'] = range(len(recent_df) - 1, -1, -1)
    st.dataframe(
        recent_df[['time', 'player', 'action', 'outcome']].sort_values('time', ascending=False),
        use_container_width=True,
        hide_index=True
    )

# -------------------- ENHANCED ANALYTICS -------------------- #
def analytics_page():
    """Enhanced analytics dashboard"""
    st.header("📈 Match Analytics")
    
    # Check for data
    has_live_data = len(st.session_state.stats) > 0
    has_saved_data = len(os.listdir(MATCH_DATA_DIR)) > 0
    
    if not has_live_data and not has_saved_data:
        st.info("No match data available yet. Start a match to see analytics.")
        return
    
    # Data selection
    tab1, tab2, tab3 = st.tabs(["📊 Live Match", "📁 Historical", "📋 Player Reports"])
    
    with tab1:
        if has_live_data:
            display_live_analytics()
        else:
            st.info("No live match data available.")
    
    with tab2:
        if has_saved_data:
            display_historical_analytics()
        else:
            st.info("No historical match data available.")
    
    with tab3:
        display_player_reports()

def display_live_analytics():
    """Display analytics for live match"""
    df = pd.DataFrame(st.session_state.stats)
    
    if df.empty:
        st.info("No live match data available.")
        return
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_actions = len(df)
        st.metric("Total Actions", total_actions)
    
    with col2:
        successful = len(df[df['outcome'] == 'Successful'])
        success_rate = (successful / total_actions * 100) if total_actions > 0 else 0
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    with col3:
        players = df['player'].nunique()
        st.metric("Players Involved", players)
    
    with col4:
        avg_actions = total_actions / players if players > 0 else 0
        st.metric("Avg Actions/Player", f"{avg_actions:.1f}")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Actions by player
        fig = px.bar(
            df['player'].value_counts().reset_index(),
            x='player',
            y='count',
            title='Actions by Player',
            color='player'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Outcome distribution
        outcome_counts = df['outcome'].value_counts()
        fig = px.pie(
            values=outcome_counts.values,
            names=outcome_counts.index,
            title='Outcome Distribution',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Action timeline
    st.subheader("Action Timeline")
    
    # Convert time to minutes for plotting
    df['time_min'] = df['time'].apply(lambda x: int(x.split(':')[0]) + int(x.split(':')[1])/60)
    
    timeline_df = df.groupby('time_min').size().reset_index()
    timeline_df.columns = ['Time (min)', 'Actions']
    
    fig = px.line(
        timeline_df,
        x='Time (min)',
        y='Actions',
        title='Actions Over Time'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed statistics
    st.subheader("Detailed Statistics")
    
    # Player performance matrix
    player_matrix = df.groupby(['player', 'action']).size().unstack(fill_value=0)
    st.dataframe(player_matrix, use_container_width=True)

def display_historical_analytics():
    """Display analytics for historical matches"""
    # Load all match files
    match_files = [f for f in os.listdir(MATCH_DATA_DIR) if f.endswith('.json')]
    
    if not match_files:
        st.info("No historical match data available.")
        return
    
    # Match selection
    selected_match = st.selectbox(
        "Select Match",
        options=match_files,
        format_func=lambda x: x.replace('.json', '').replace('match_', '').replace('_', ' ')
    )
    
    # Load selected match
    match_path = os.path.join(MATCH_DATA_DIR, selected_match)
    with open(match_path, 'r') as f:
        match_data = json.load(f)
    
    # Display match info
    st.subheader(f"Match: {match_data.get('timestamp', 'Unknown Date')}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Coach:** {match_data.get('coach', 'N/A')}")
        st.write(f"**Formation:** {match_data.get('formation', 'N/A')}")
    with col2:
        st.write(f"**Level:** {match_data.get('level', 'N/A')}")
        st.write(f"**Duration:** {match_data.get('duration', 'N/A')} min")
    
    # Load stats
    stats_df = pd.DataFrame(match_data.get('stats', []))
    
    if not stats_df.empty:
        # Similar analytics as live match
        display_match_analytics(stats_df, match_data)
    else:
        st.info("No statistics available for this match.")

def display_match_analytics(df: pd.DataFrame, match_data: Dict):
    """Display analytics for a specific match"""
    # Key metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_actions = len(df)
        st.metric("Total Actions", total_actions)
    
    with col2:
        successful = len(df[df['outcome'] == 'Successful'])
        success_rate = (successful / total_actions * 100) if total_actions > 0 else 0
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    with col3:
        players = df['player'].nunique()
        st.metric("Players", players)
    
    # Performance by half
    if 'half' in df.columns:
        st.subheader("Performance by Half")
        half_stats = df.groupby('half').agg({
            'player': 'count',
            'outcome': lambda x: (x == 'Successful').mean() * 100
        }).round(1)
        half_stats.columns = ['Total Actions', 'Success Rate %']
        st.dataframe(half_stats)
    
    # Export options
    st.subheader("Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        csv = df.to_csv(index=False)
        st.download_button(
            "📥 Download CSV",
            csv,
            file_name=f"match_stats_{match_data.get('timestamp', 'data')}.csv",
            mime="text/csv"
        )
    
    with col2:
        json_str = json.dumps(match_data, indent=2)
        st.download_button(
            "📥 Download JSON",
            json_str,
            file_name=f"match_data_{match_data.get('timestamp', 'data')}.json",
            mime="application/json"
        )

def display_player_reports():
    """Generate individual player reports"""
    # Load all match data
    all_stats = []
    match_files = [f for f in os.listdir(MATCH_DATA_DIR) if f.endswith('.json')]
    
    for match_file in match_files:
        match_path = os.path.join(MATCH_DATA_DIR, match_file)
        with open(match_path, 'r') as f:
            match_data = json.load(f)
            for stat in match_data.get('stats', []):
                stat['match_date'] = match_data.get('timestamp', 'Unknown')
                all_stats.append(stat)
    
    if not all_stats:
        st.info("No player data available.")
        return
    
    all_df = pd.DataFrame(all_stats)
    
    # Player selection
    players = sorted(all_df['player'].unique())
    selected_player = st.selectbox("Select Player", options=players)
    
    # Filter data for selected player
    player_df = all_df[all_df['player'] == selected_player].copy()
    
    if player_df.empty:
        st.info(f"No data available for {selected_player}.")
        return
    
    # Player profile
    st.subheader(f"Player Report: {selected_player}")
    
    # Calculate player stats
    total_matches = player_df['match_date'].nunique()
    total_actions = len(player_df)
    successful_actions = len(player_df[player_df['outcome'] == 'Successful'])
    success_rate = (successful_actions / total_actions * 100) if total_actions > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Matches Played", total_matches)
    with col2:
        st.metric("Total Actions", total_actions)
    with col3:
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    # Action breakdown
    st.subheader("Action Breakdown")
    
    # Most common actions
    common_actions = player_df['action'].value_counts().head(10)
    fig = px.bar(
        x=common_actions.index,
        y=common_actions.values,
        title="Most Common Actions",
        labels={'x': 'Action', 'y': 'Count'}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Performance trend
    if 'match_date' in player_df.columns:
        st.subheader("Performance Trend")
        
        # Group by match date
        player_df['date'] = pd.to_datetime(player_df['match_date'])
        trend_df = player_df.groupby('date').agg({
            'action': 'count',
            'outcome': lambda x: (x == 'Successful').mean() * 100
        }).round(1)
        trend_df.columns = ['Actions', 'Success Rate %']
        trend_df = trend_df.sort_index()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=trend_df.index,
            y=trend_df['Actions'],
            name='Actions',
            line=dict(color='blue')
        ))
        fig.add_trace(go.Scatter(
            x=trend_df.index,
            y=trend_df['Success Rate %'],
            name='Success Rate %',
            yaxis='y2',
            line=dict(color='green', dash='dash')
        ))
        
        fig.update_layout(
            title='Performance Over Time',
            yaxis=dict(title='Actions'),
            yaxis2=dict(title='Success Rate %', overlaying='y', side='right')
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed statistics table
    st.subheader("Detailed Statistics")
    detailed_stats = player_df.groupby(['action', 'outcome']).size().unstack(fill_value=0)
    st.dataframe(detailed_stats, use_container_width=True)

# -------------------- DATA MANAGEMENT -------------------- #
def load_team_data() -> Dict:
    """Load team data from file"""
    if os.path.exists(TEAM_FILE):
        try:
            with open(TEAM_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading team file: {e}")
            return {"coach": "", "assistant": "", "players": []}
    return {"coach": "", "assistant": "", "players": []}

def save_team_data(team_data: Dict):
    """Save team data to file"""
    try:
        with open(TEAM_FILE, 'w') as f:
            json.dump(team_data, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving team file: {e}")
        return False

def save_match_data():
    """Save match data to JSON file"""
    try:
        match_data = {
            "timestamp": datetime.now().isoformat(),
            "coach": st.session_state.team_data.get('coach', ''),
            "assistant": st.session_state.team_data.get('assistant', ''),
            "formation": st.session_state.get('formation', '4-4-2'),
            "level": st.session_state.match_level,
            "duration": st.session_state.game_duration,
            "lineup": st.session_state.lineup,
            "substitutes": st.session_state.get('substitutes', []),
            "opponent": st.session_state.get('opponent_team', ''),
            "location": st.session_state.get('match_location', ''),
            "weather": st.session_state.get('weather_conditions', ''),
            "notes": st.session_state.get('match_notes', ''),
            "stats": st.session_state.stats + st.session_state.first_half_stats + st.session_state.second_half_stats
        }
        
        filename = f"match_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(MATCH_DATA_DIR, filename)
        
        with open(filepath, 'w') as f:
            json.dump(match_data, f, indent=2)
        
        st.success(f"Match data saved to {filename}")
        return filename
    except Exception as e:
        st.error(f"Error saving match data: {e}")
        return None

def load_backup_interface():
    """Interface for loading from backup"""
    backup_files = [f for f in os.listdir(BACKUP_DIR) if f.startswith('team_backup_')]
    
    if backup_files:
        selected_backup = st.selectbox(
            "Select Backup File",
            options=backup_files,
            format_func=lambda x: x.replace('team_backup_', '').replace('.json', '')
        )
        
        if st.button("Load Backup"):
            backup_path = os.path.join(BACKUP_DIR, selected_backup)
            with open(backup_path, 'r') as f:
                team_data = json.load(f)
            st.session_state.team_data = team_data
            st.success("Backup loaded successfully!")
            st.rerun()
    else:
        st.info("No backup files available.")

# -------------------- HELPER FUNCTIONS -------------------- #
def get_actions_per_level() -> Dict:
    """Return actions per tracking level (unchanged from original)"""
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

role_groups = {
    'GK': 'Goalkeeper',
    'CB': 'Centre-Back',
    'RCB': 'Centre-Back',
    'LCB': 'Centre-Back',
    'RB': 'Full-Back',
    'LB': 'Full-Back',
    'WB': 'Full-Back',
    'RWB': 'Full-Back',
    'LWB': 'Full-Back',
    'DM': 'Defensive Midfielder',
    'CDM': 'Defensive Midfielder',
    'CM': 'Central Midfielder',
    'AM': 'Attacking Midfielder',
    'CAM': 'Attacking Midfielder',
    'RM': 'Winger',
    'LM': 'Winger',
    'WM': 'Winger',
    'RW': 'Winger',
    'LW': 'Winger',
    'ST': 'Striker',
    'CF': 'Striker',
    'SS': 'Striker',
    'WF': 'Striker'
}

# -------------------- MAIN APP -------------------- #
def main():
    """Main application entry point"""
    # Page configuration
    st.set_page_config(
        page_title="Takti Stats Tracker",
        page_icon="⚽",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Load CSS
    load_custom_css()
    
    # Initialize session state
    initialize_session_state()
    
    # Check session timeout
    if st.session_state.logged_in:
        check_session_timeout()
    
    # Main app logic
    if not st.session_state.logged_in:
        login_page()
    else:
        # Sidebar
        with st.sidebar:
            st.title("⚽ Takti Stats")
            st.markdown("---")
            
            # User info
            st.write(f"👤 Logged in as: **dreamteam**")
            
            # Navigation
            st.subheader("Navigation")
            
            # Create tabs in sidebar for better navigation
            page = st.radio(
                "Go to:",
                ["👥 Team Sheet", "🎯 Lineup", "⚙️ Match Settings", "📝 Live Match", "📈 Analytics", "⚙️ Settings"],
                label_visibility="collapsed"
            )
            
            st.markdown("---")
            
            # Match info if in progress
            if st.session_state.match_started:
                st.info("📊 Match in Progress")
                mins = int(st.session_state.elapsed_time // 60)
                secs = int(st.session_state.elapsed_time % 60)
                st.write(f"⏱️ {mins:02d}:{secs:02d}")
                st.write(f"📊 {len(st.session_state.stats)} actions logged")
            
            # Logout button
            if st.button("🚪 Logout", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
            
            st.markdown("---")
            st.caption(f"v1.2.0 | © {datetime.now().year} Takti Stats")
        
        # Main content area
        if page == "👥 Team Sheet":
            team_sheet_page()
        
        elif page == "🎯 Lineup":
            lineup_selection_page()
        
        elif page == "⚙️ Match Settings":
            match_settings_page()
        
        elif page == "📝 Live Match":
            if not st.session_state.get('match_ready', False):
                st.warning("⚠️ Please complete Match Settings first.")
                st.info("Go to Match Settings tab and click 'Proceed to Live Match'")
            else:
                # Timer
                timer = MatchTimer()
                timer.control_panel()
                mins, secs = timer.display()
                
                # Action logging
                action_logging_page()
                
                # Export options
                if st.session_state.stats:
                    st.markdown("---")
                    st.subheader("💾 Export Options")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("💾 Save Match Data", use_container_width=True):
                            filename = save_match_data()
                            if filename:
                                st.success(f"Match saved: {filename}")
                    
                    with col2:
                        df = pd.DataFrame(st.session_state.stats)
                        csv = df.to_csv(index=False)
                        st.download_button(
                            "📥 Download CSV",
                            csv,
                            file_name="live_match_stats.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    
                    with col3:
                        if st.button("🏁 End Match", use_container_width=True, type="primary"):
                            timer._handle_match_end()
                            st.success("Match ended. Data saved.")
                            st.rerun()
        
        elif page == "📈 Analytics":
            analytics_page()
        
        elif page == "⚙️ Settings":
            settings_page()

def settings_page():
    """Application settings page"""
    st.header("⚙️ Application Settings")
    
    tab1, tab2, tab3 = st.tabs(["General", "Data Management", "About"])
    
    with tab1:
        st.subheader("General Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            auto_save = st.checkbox("Enable Auto-save", value=True)
            backup_interval = st.selectbox(
                "Backup Interval",
                options=["5 minutes", "15 minutes", "30 minutes", "1 hour"],
                index=1
            )
        
        with col2:
            default_level = st.selectbox(
                "Default Tracking Level",
                options=["Beginner", "Intermediate", "Semi-Pro", "Pro"],
                index=0
            )
            default_duration = st.number_input(
                "Default Match Duration (min)",
                min_value=40,
                max_value=120,
                value=90
            )
        
        if st.button("💾 Save Settings", use_container_width=True):
            st.success("Settings saved!")
    
    with tab2:
        st.subheader("Data Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Team Data**")
            if os.path.exists(TEAM_FILE):
                file_size = os.path.getsize(TEAM_FILE)
                st.write(f"File size: {file_size / 1024:.1f} KB")
                
                if st.button("🗑️ Clear Team Data", use_container_width=True):
                    if os.path.exists(TEAM_FILE):
                        os.remove(TEAM_FILE)
                    st.session_state.team_data = {"coach": "", "assistant": "", "players": []}
                    st.success("Team data cleared!")
                    st.rerun()
            else:
                st.info("No team data file found.")
        
        with col2:
            st.write("**Match Data**")
            match_files = [f for f in os.listdir(MATCH_DATA_DIR) if f.endswith('.json')]
            st.write(f"Matches stored: {len(match_files)}")
            
            if match_files:
                if st.button("🗑️ Clear All Match Data", use_container_width=True):
                    for file in match_files:
                        os.remove(os.path.join(MATCH_DATA_DIR, file))
                    st.success("All match data cleared!")
                    st.rerun()
        
        st.subheader("Import/Export")
        
        col3, col4 = st.columns(2)
        
        with col3:
            uploaded_file = st.file_uploader("Import Team Data", type=['json'])
            if uploaded_file is not None:
                try:
                    team_data = json.load(uploaded_file)
                    save_team_data(team_data)
                    st.session_state.team_data = team_data
                    st.success("Team data imported successfully!")
                except Exception as e:
                    st.error(f"Import failed: {e}")
        
        with col4:
            if os.path.exists(TEAM_FILE):
                with open(TEAM_FILE, 'r') as f:
                    team_json = f.read()
                
                st.download_button(
                    "📤 Export Team Data",
                    team_json,
                    file_name="team_data_export.json",
                    mime="application/json",
                    use_container_width=True
                )
    
    with tab3:
        st.subheader("About Takti Stats Tracker")
        
        st.write("""
        ### ⚽ Takti Stats Tracker v1.2.0
        
        A comprehensive soccer statistics tracking application designed for youth and amateur teams.
        
        **Features:**
        - 👥 Team roster management
        - 🎯 Formation and lineup selection
        - 📝 Real-time match statistics tracking
        - 📊 Advanced analytics and reporting
        - 💾 Data export and backup
        
        **Tracking Levels:**
        1. **Beginner**: Basic actions for young players
        2. **Intermediate**: More detailed statistics
        3. **Semi-Pro**: Advanced metrics
        4. **Pro**: Professional-level analytics
        
        **System Requirements:**
        - Python 3.8+
        - Streamlit
        - Modern web browser
        
        **License:**
        © 2024 Takti Stats. All rights reserved.
        
        For support or feature requests, please contact the development team.
        """)
        
        st.info("🔒 **Security Note**: Change default password in production deployment.")

# -------------------- APPLICATION START -------------------- #
if __name__ == "__main__":
    main()
