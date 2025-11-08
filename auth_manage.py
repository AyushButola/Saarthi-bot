import requests, json, os, time, jwt, logging
from datetime import datetime

# ===============================================
# 🔗 Backend Endpoints (based on your Django setup)
# ===============================================
BASE_URL = "https://saarthi-backend-xv47.onrender.com/api/users"
REGISTER_URL = f"{BASE_URL}/auth/register/"
LOGIN_URL = f"{BASE_URL}/auth/login/"
REFRESH_URL = f"{BASE_URL}/auth/refresh/"
SESSIONS_FILE = "sessions.json"

# ===============================================
# 🔐 Session Persistence
# ===============================================
if os.path.exists(SESSIONS_FILE):
    with open(SESSIONS_FILE, "r") as f:
        sessions = json.load(f)
else:
    sessions = {}

def save_sessions():
    with open(SESSIONS_FILE, "w") as f:
        json.dump(sessions, f, indent=2)

# ===============================================
# 🧍‍♂️ Register a New User
# ===============================================
def register_user(**kwargs):
    """
    Register a new Saarthi user using keyword arguments.
    Expected fields: email, username, password, first_name, last_name, etc.
    """
    payload = kwargs  # directly use the passed dict
    try:
        resp = requests.post(REGISTER_URL, json=payload, timeout=10)
        if resp.status_code == 201:
            return True, "🎉 Registration successful! You can now /login"
        elif resp.status_code == 400:
            return False, f"⚠️ Registration failed: {resp.json()}"
        else:
            return False, f"❌ Unexpected error: {resp.text}"
    except Exception as e:
        logging.error(f"Registration error: {e}")
        return False, "Server connection failed ❌"


# ===============================================
# 🔑 Login (Obtain Tokens)
# ===============================================
def login_user(telegram_id: str, username: str, password: str):
    """
    Authenticate user and save access/refresh tokens.
    """
    try:
        resp = requests.post(LOGIN_URL, json={"username": username, "password": password}, timeout=10)
        if resp.status_code == 200:
            tokens = resp.json()
            sessions[str(telegram_id)] = {
                "access": tokens.get("access"),
                "refresh": tokens.get("refresh"),
                "login_time": datetime.now().isoformat()
            }
            save_sessions()
            return True, "✅ Login successful!"
        elif resp.status_code == 401:
            return False, "❌ Invalid credentials"
        else:
            return False, f"⚠️ Login failed: {resp.text}"
    except Exception as e:
        logging.error(f"Login error: {e}")
        return False, "Server connection error ❌"

# ===============================================
# ♻️ Refresh Access Token
# ===============================================
def refresh_access_token(telegram_id: str):
    user = sessions.get(str(telegram_id))
    if not user or "refresh" not in user:
        return False, "No refresh token found"
    try:
        resp = requests.post(REFRESH_URL, json={"refresh": user["refresh"]}, timeout=10)
        if resp.status_code == 200:
            new_access = resp.json().get("access")
            user["access"] = new_access
            sessions[str(telegram_id)] = user
            save_sessions()
            return True, new_access
        else:
            return False, f"Refresh failed: {resp.text}"
    except Exception as e:
        logging.error(f"Token refresh error: {e}")
        return False, "Error refreshing token"

# ===============================================
# 🧮 Token Expiry Check
# ===============================================
def is_token_expired(token: str) -> bool:
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded.get("exp", 0) < time.time()
    except Exception:
        return True

# ===============================================
# 🚪 Logout
# ===============================================
def logout_user(telegram_id: str):
    if str(telegram_id) in sessions:
        del sessions[str(telegram_id)]
        save_sessions()
        return True
    return False

# ===============================================
# 🧾 Get Auth Header (auto-refresh if expired)
# ===============================================
def get_auth_header(telegram_id: str):
    user = sessions.get(str(telegram_id))
    if not user:
        return None
    access_token = user.get("access")
    if is_token_expired(access_token):
        ok, result = refresh_access_token(telegram_id)
        if not ok:
            return None
        access_token = result
    return {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
