import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

app = FastAPI(
    title="Google Calendar API FastAPI",
    description="Create calendar events directly from Swagger UI and send invites to attendees.",
    version="1.0.0"
)

# --------------------------
# Environment variables handling
# --------------------------
TOKEN_PATH = "token.json"
CLIENT_SECRET_PATH = "client_secret.json"

if not os.path.exists(TOKEN_PATH):
    token_content = os.environ.get("TOKEN_FILE_CONTENT")
    if token_content:
        with open(TOKEN_PATH, "w") as f:
            f.write(token_content)
    else:
        raise Exception("TOKEN_FILE_CONTENT environment variable not set.")

if not os.path.exists(CLIENT_SECRET_PATH):
    client_secret_content = os.environ.get("GOOGLE_CLIENT_SECRETS")
    if client_secret_content:
        with open(CLIENT_SECRET_PATH, "w") as f:
            f.write(client_secret_content)
    else:
        raise Exception("GOOGLE_CLIENT_SECRETS environment variable not set.")

# --------------------------
# Google Calendar setup
# --------------------------
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

# --------------------------
# Models
# --------------------------
class Event(BaseModel):
    summary: str
    description: str = None
    start: dict
    end: dict
    attendees: list[dict] = []

# --------------------------
# Routes
# --------------------------
@app.get("/", include_in_schema=False)
async def swagger_redirect():
    # Redirect root to Swagger UI
    return RedirectResponse(url="/docs")

@app.post("/create-event")
async def create_event(event: Event):
    try:
        calendar_id = 'primary'
        created_event = service.events().insert(
            calendarId=calendar_id,
            body=event.dict(),
            sendUpdates='all'  # This sends email notifications to attendees
        ).execute()
        return {"status": "success", "event": created_event}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
