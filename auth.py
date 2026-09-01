import hashlib
import os
import time
import streamlit as st

MAX_ATTEMPTS = 5
LOCKOUT_TIME_SECONDS = 900  # 15 Minutes
TIMEOUT_MINUTES = 15

def init_auth_state():
    if "authenticated_user" not in st.session_state:
        st.session_state.authenticated_user = None
    if "failed_attempts" not in st.session_state:
        st.session_state.failed_attempts = 0
    if "lockout_until" not in st.session_state:
        st.session_state.lockout_until = 0
    if "last_activity" not in st.session_state:
        st.session_state.last_activity = time.time()

def check_session_timeout():
    if st.session_state.authenticated_user:
        elapsed_minutes = (time.time() - st.session_state.last_activity) / 60
        if elapsed_minutes > TIMEOUT_MINUTES:
            st.session_state.authenticated_user = None
            st.warning(f"🔒 App locked due to {TIMEOUT_MINUTES} minutes of inactivity.")
            st.rerun()

def update_activity_timer():
    st.session_state.last_activity = time.time()

def check_rate_limit() -> bool:
    if time.time() < st.session_state.lockout_until:
        remaining = int(st.session_state.lockout_until - time.time())
        st.error(f"🔒 Too many failed attempts. Try again in {remaining // 60}m {remaining % 60}s.")
        return False
    return True

def verify_hash(password_plain: str, stored_string: str) -> bool:
    try:
        salt_hex, key_hex = stored_string.split(":")
        salt = bytes.fromhex(salt_hex)
        key = bytes.fromhex(key_hex)
        new_key = hashlib.pbkdf2_hmac("sha256", password_plain.encode("utf-8"), salt, 100000)
        return hashlib.sha256(new_key).digest() == hashlib.sha256(key).digest()
    except Exception:
        return False

def verify_credentials(username: str, password_plain: str) -> bool:
    init_auth_state()
    
    if not check_rate_limit():
        return False

    users = st.secrets.get("auth", {}).get("users", {})
    
    if username in users:
        stored_hash = users[username].get("password_hash", "")
        if stored_hash and verify_hash(password_plain, stored_hash):
            st.session_state.authenticated_user = {
                "username": username,
                "name": users[username].get("name", username),
                "role": users[username].get("role", "user")
            }
            st.session_state.failed_attempts = 0
            st.session_state.last_activity = time.time()
            return True

    # Failed Login Tracking
    st.session_state.failed_attempts += 1
    if st.session_state.failed_attempts >= MAX_ATTEMPTS:
        st.session_state.lockout_until = time.time() + LOCKOUT_TIME_SECONDS
        st.error("🚨 Too many failed login attempts. System locked for 15 minutes.")
    else:
        st.error(f"Invalid credentials. ({MAX_ATTEMPTS - st.session_state.failed_attempts} attempts remaining)")
    
    return False

def render_login_screen():
    st.markdown('<h1 class="responsive-title">🔒 Secure Access Gate</h1>', unsafe_allow_html=True)
    st.caption("Authorized access only.")

    if not check_rate_limit():
        return

    with st.form("login_form"):
        username = st.text_input("Username").strip().lower()
        password = st.text_input("Passcode", type="password")
        submit = st.form_submit_button("Authenticate", use_container_width=True)

        if submit:
            if verify_credentials(username, password):
                st.rerun()

def logout():
    st.session_state.authenticated_user = None
    st.rerun()
