import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from fastapi.middleware.cors import CORSMiddleware  # ✅ Added for teammates

app = FastAPI(
    title="Google Calendar API FastAPI",
    description="Create calendar events directly from Swagger UI and send invites to attendees.",
    version="1.2.0"
)

# --------------------------------------------------
# ✅ Enable CORS (so your teammates can connect)
# --------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can later restrict this to specific domains if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# ✅ Environment variables & file setup (Render Safe)
# --------------------------------------------------

TOKEN_PATH = "token.json"
CLIENT_SECRET_PATH = "client_secrets.json"

# --- Handle token.json (Google credentials) ---
if not os.path.exists(TOKEN_PATH):
    token_content = os.environ.get("TOKEN_FILE_CONTENT")
    if token_content:
        try:
            with open(TOKEN_PATH, "w") as f:
                f.write(token_content)
            print("✅ token.json created from environment variable.")
        except Exception as e:
            raise Exception(f"Failed to write token.json: {e}")
    else:
        raise Exception("TOKEN_FILE_CONTENT environment variable not set.")

# --- Handle client_secrets.json ---
if not os.path.exists(CLIENT_SECRET_PATH):
    client_secret_content = os.environ.get("GOOGLE_CLIENT_SECRETS_CONTENT") or os.environ.get("GOOGLE_CLIENT_SECRETS")
    if client_secret_content:
        try:
            with open(CLIENT_SECRET_PATH, "w") as f:
                f.write(client_secret_content)
            print("✅ client_secrets.json created from environment variable.")
        except Exception as e:
            raise Exception(f"Failed to write client_secrets.json: {e}")
    else:
        raise Exception("GOOGLE_CLIENT_SECRETS_CONTENT environment variable not set.")

# --------------------------------------------------
# ✅ Google Calendar API Setup
# --------------------------------------------------
SCOPES = ['https://www.googleapis.com/auth/calendar']
creds = None

if os.path.exists(TOKEN_PATH):
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, SCOPES)
        creds = flow.run_local_server(port=0)
    with open(TOKEN_PATH, 'w') as token:
        token.write(creds.to_json())

service = build('calendar', 'v3', credentials=creds)

# --------------------------------------------------
# ✅ Pydantic Model
# --------------------------------------------------
class Event(BaseModel):
    summary: str
    description: str = None
    start: dict
    end: dict
    attendees: list[dict] = []

# --------------------------------------------------
# ✅ Routes
# --------------------------------------------------
@app.get("/", include_in_schema=False)
async def root_redirect():
    """Redirect root to Swagger UI"""
    return RedirectResponse(url="/docs")


@app.post("/create-event")
async def create_event(event: Event):
    """Create a new Google Calendar event and send invites"""
    try:
        calendar_id = 'primary'
        created_event = service.events().insert(
            calendarId=calendar_id,
            body=event.dict(),
            sendUpdates='all'
        ).execute()
        return {"status": "success", "event": created_event}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
