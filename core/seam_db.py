import os
import datetime
from dotenv import load_dotenv
import streamlit as st

# Cache client object to avoid recreating it on every successful database call
supabase_client = None

def _get_secret(key: str) -> str:
    """Reads a secret from st.secrets (Streamlit Cloud) or falls back to environment variables."""
    try:
        val = st.secrets.get(key)
        if val:
            return str(val).strip()
    except Exception:
        pass
    return os.getenv(key, "")

def get_supabase_client():
    global supabase_client
    if supabase_client is not None:
        return supabase_client
        
    # Reload environment variables to see if credentials were provided locally
    if os.path.exists("env.txt"):
        load_dotenv("env.txt", override=True)
    else:
        load_dotenv(override=True)
        
    url = _get_secret("SUPABASE_URL")
    key = _get_secret("SUPABASE_KEY") or _get_secret("SUPABASE_ANON_KEY")
    
    if url and key and url.strip() and key.strip():
        try:
            from supabase import create_client
            supabase_client = create_client(url.strip(), key.strip())
            print("Seam DB: Connected to Supabase successfully.")
            return supabase_client
        except Exception as e:
            print(f"Seam DB: Failed to connect to Supabase: {e}. Falling back to In-Memory.")
            return None
    return None

def ensure_in_memory_chats():
    """Initializes in-memory chats in session state if not present."""
    if "in_memory_chats" not in st.session_state:
        st.session_state.in_memory_chats = {}

def get_in_memory_sessions():
    """Returns sessions stored in session_state, sorted by last message time."""
    ensure_in_memory_chats()
    sessions = []
    for sess_id, msgs in st.session_state.in_memory_chats.items():
        if msgs:
            last_time = msgs[-1].get("created_at", datetime.datetime.now())
            sessions.append((sess_id, last_time))
    sessions.sort(key=lambda x: x[1], reverse=True)
    return [s[0] for s in sessions]

def save_message(session_id: str, role: str, content: str, signals: list = None):
    """Saves a user or assistant message to Supabase, falling back silently to session_state."""
    ensure_in_memory_chats()
    signals_data = signals if signals else []
    timestamp = datetime.datetime.now().isoformat()
    
    # Save to memory first to ensure we have a fallback record
    if session_id not in st.session_state.in_memory_chats:
        st.session_state.in_memory_chats[session_id] = []
    st.session_state.in_memory_chats[session_id].append({
        "role": role,
        "content": content,
        "signals": signals_data,
        "created_at": timestamp
    })
    
    # Try writing to Supabase
    client = get_supabase_client()
    if client:
        try:
            data = {
                "session_id": session_id,
                "role": role,
                "content": content,
                "signals": signals_data
            }
            client.table("seam_chats").insert(data).execute()
        except Exception as e:
            # Fallback silently, log only to console
            print(f"Seam DB: Supabase write failed: {e}. Message persisted in memory.")

def get_chat_history(session_id: str) -> list:
    """Retrieves chat history for a session, falling back silently to memory on error."""
    ensure_in_memory_chats()
    client = get_supabase_client()
    if client:
        try:
            response = client.table("seam_chats") \
                .select("*") \
                .eq("session_id", session_id) \
                .order("created_at", desc=False) \
                .execute()
            
            history = []
            for row in response.data:
                history.append({
                    "role": row["role"],
                    "content": row["content"],
                    "signals": row.get("signals") or []
                })
            
            # Sync to in-memory cache to ensure consistent UI state
            st.session_state.in_memory_chats[session_id] = [
                {
                    "role": r["role"],
                    "content": r["content"],
                    "signals": r["signals"],
                    "created_at": r.get("created_at", datetime.datetime.now().isoformat())
                } for r in history
            ]
            return history
        except Exception as e:
            print(f"Seam DB: Supabase read history failed: {e}. Reading from memory.")
            
    # In-memory fallback
    return st.session_state.in_memory_chats.get(session_id, [])

def get_sessions() -> list:
    """Retrieves all unique session IDs, falling back silently to memory on error."""
    client = get_supabase_client()
    if client:
        try:
            response = client.table("seam_chats") \
                .select("session_id, created_at") \
                .execute()
            
            # Group sessions and find the latest timestamp for each
            sess_map = {}
            for row in response.data:
                sid = row["session_id"]
                t = row.get("created_at", "")
                if sid not in sess_map or t > sess_map[sid]:
                    sess_map[sid] = t
            
            # Sort sessions by creation time descending
            sorted_sessions = sorted(sess_map.keys(), key=lambda x: sess_map[x], reverse=True)
            return sorted_sessions
        except Exception as e:
            print(f"Seam DB: Supabase fetch sessions failed: {e}. Reading from memory.")
            
    return get_in_memory_sessions()

def clear_session(session_id: str):
    """Deletes a session from memory and Supabase."""
    ensure_in_memory_chats()
    if session_id in st.session_state.in_memory_chats:
        del st.session_state.in_memory_chats[session_id]
        
    client = get_supabase_client()
    if client:
        try:
            client.table("seam_chats") \
                .delete() \
                .eq("session_id", session_id) \
                .execute()
        except Exception as e:
            print(f"Seam DB: Supabase delete failed: {e}. Cleared in memory only.")
