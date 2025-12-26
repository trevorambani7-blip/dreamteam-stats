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
