import traceback
import sys

# Ensure the project root is on the import path so that ``backend`` can be imported
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# Import the FastAPI app to ensure it initializes without errors
try:
    from backend.main import app
except Exception as e:
    print("Failed to import backend.main:")
    traceback.print_exc()
    sys.exit(1)

# Import DB session and models
from backend.persistence import SessionLocal, User, Event, Theme, CheckIn, VoteToken, Vote, init_db
from backend.database import db_instance
from backend.merkle import merkle_root
from backend.anchor import ANCHOR_FILE
import json
import time

# Ensure tables exist
init_db()

# Helper to print step results

def step(name, fn):
    try:
        result = fn()
        print(f"[OK] {name}")
        return result
    except Exception as e:
        print(f"[FAIL] {name}")
        traceback.print_exc()
        sys.exit(1)

# 1. Create a user (login)

def create_user():
    import secrets
    token = secrets.token_urlsafe(16)
    cpf = "12345678900"
    # Register user via db_instance
    db_instance.register_user(token, cpf)
    return token

user_token = step("Create user", create_user)

# 2. Create an event

def create_event():
    now = time.time()
    event_id = db_instance.create_event(
        name="Test Event",
        description="Integration test event",
        latitude=-23.5505,
        longitude=-46.6333,
        radius=1000.0,
        start_time=now - 60,
        end_time=now + 3600,
    )
    return event_id

event_id = step("Create event", create_event)

# 3. Register a check‑in

def register_checkin():
    leaf, root = db_instance.create_checkin(
        token=user_token,
        event_id=event_id,
        latitude=-23.5505,
        longitude=-46.6333,
        timestamp=None,
        photo_hash=None,
    )
    return leaf, root

checkin_leaf, checkin_root = step("Register check‑in", register_checkin)

# 4. Create a voting theme

def create_theme():
    theme_id = db_instance.create_theme(
        question="Best color?",
        options=["Red", "Green", "Blue"],
        open_time=time.time() - 10,
        close_time=time.time() + 3600,
    )
    return theme_id

theme_id = step("Create voting theme", create_theme)

# 5. Issue a vote token

def issue_vote_token():
    vt = db_instance.issue_vote_token(user_token, theme_id)
    return vt

vote_token = step("Issue vote token", issue_vote_token)

# 6. Cast a vote

def cast_vote():
    leaf, root = db_instance.cast_vote(vote_token, "Red")
    return leaf, root

vote_leaf, vote_root = step("Cast vote", cast_vote)

# 7. Verify Merkle roots are anchored

def verify_anchors():
    if not ANCHOR_FILE.exists():
        raise RuntimeError("Anchor file not found")
    data = json.loads(ANCHOR_FILE.read_text())
    # Look for entries for our event and theme (support both 'key' and 'type' fields)
    event_entry = next((e for e in data if e.get('key') == f"checkin:{event_id}" or e.get('type') == f"checkin:{event_id}"), None)
    theme_entry = next((e for e in data if e.get('key') == f"vote:{theme_id}" or e.get('type') == f"vote:{theme_id}"), None)
    if not event_entry or not theme_entry:
        raise RuntimeError("Missing Merkle roots in anchor log")
    return True

step("Verify Merkle anchors", verify_anchors)

# 8. Start cron job scheduler (should not raise)

def start_cron():
    from backend.cron_job import schedule_sync
    # Use a dummy Database instance (db_instance) and a short interval
    schedule_sync(db_instance, interval_minutes=1)
    return True

step("Start cron job", start_cron)

print("Integração completa com sucesso")
