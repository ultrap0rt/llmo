import requests
import time

API_URL = "http://127.0.0.1:8000/chat"
SESSION_ID = "user_123_pause_test"

def send_message(message: str):
    print(f"\n[User]: {message}")
    response = requests.post(API_URL, json={
        "session_id": SESSION_ID,
        "message": message
    })
    
    if response.status_code == 200:
        print(f"[Assistant]: {response.json()['response']}")
    else:
        print(f"[Error]: {response.text}")

print("=== Starting test session ===")
send_message("Hi! I am starting a new project called 'Project X', it's a secret AI system.")

# Wait for background extraction to complete
print("\n... Waiting for background graph extraction to complete ...")
time.sleep(10)

send_message("The main components of Project X are an LLM and a Knowledge Graph.")
print("\n... Waiting for background graph extraction to complete ...")
time.sleep(10)

print("\n... Simulating a long pause (e.g. 1 month) ...")
# A long pause doesn't change anything technically in the code, but the context window has ended
# and no local history is passed except what is fetched from DB.

send_message("Hey! Can you remind me what my secret project is about and what components it has?")

print("\n=== Test completed ===")
