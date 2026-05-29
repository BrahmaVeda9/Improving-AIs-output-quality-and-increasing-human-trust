import os
import requests
import datetime
from dotenv import load_dotenv

# Load configuration from env.txt or .env
if os.path.exists("env.txt"):
    load_dotenv("env.txt")
else:
    load_dotenv()

STREAMLIT_APP_URL = os.getenv("STREAMLIT_APP_URL", "http://localhost:8501")

def ping_app():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        response = requests.get(STREAMLIT_APP_URL, timeout=10)
        status_code = response.status_code
        log_message = f"[{timestamp}] Pinged {STREAMLIT_APP_URL} - Status Code: {status_code}\n"
        print(log_message.strip())
        
        # Log to file
        with open("keep_alive.log", "a", encoding="utf-8") as f:
            f.write(log_message)
    except Exception as e:
        log_message = f"[{timestamp}] Failed to ping {STREAMLIT_APP_URL} - Error: {e}\n"
        print(log_message.strip())
        with open("keep_alive.log", "a", encoding="utf-8") as f:
            f.write(log_message)

if __name__ == "__main__":
    ping_app()
