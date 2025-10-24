import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/calendar']
CLIENT_SECRETS_FILE = os.getenv("GOOGLE_CLIENT_SECRETS")
TOKEN_FILE = os.getenv("TOKEN_FILE")

# Check that environment variables are set
if not CLIENT_SECRETS_FILE or not TOKEN_FILE:
    raise Exception(
        "Environment variables GOOGLE_CLIENT_SECRETS or TOKEN_FILE not set."
    )

app = FastAPI(
    title="Google Calendar API Service",
    description="FastAPI service to create Google Calendar events",
    version="1.0.0"
)

# ✅ Event request body
class Event(BaseModel):
    summary: str
    location: str
    description: str
    start: str  # ISO 8601 format: "2025-10-25T19:00:00"
    end: str
    attendees: list[str]

# Function to get Google Calendar service
def get_calendar_service():
    if not os.path.exists(TOKEN_FILE):
        raise HTTPException(
            status_code=500,
            detail="Token file not found. Generate token.json locally first."
        )

    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    service = build('calendar', 'v3', credentials=creds)
    return service

# 1️⃣ HTML Home Page
@app.get("/", response_class=HTMLResponse)
def home_page():
    return """
    <html>
        <head>
            <title>Google Calendar API</title>
        </head>
        <body style="font-family: Arial, sans-serif; text-align: center; margin-top: 50px;">
            <h1>🎉 Welcome to the Google Calendar FastAPI Service! 🎉</h1>
            <p>Create and manage your calendar events easily.</p>
            <p>Go to <a href='/docs'>Swagger UI</a> to test the API.</p>
            <p>Go to <a href='/redoc'>ReDoc</a> for alternative API docs.</p>
        </body>
    </html>
    """

# 2️⃣ Create event endpoint
@app.post("/create-event")
def create_event(event: Event):
    service = get_calendar_service()
    
    event_body = {
        "summary": event.summary,
        "location": event.location,
        "description": event.description,
        "start": {"dateTime": event.start, "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": event.end, "timeZone": "Asia/Kolkata"},
        "attendees": [{"email": email} for email in event.attendees],
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": 24 * 60},
                {"method": "popup", "minutes": 30}
            ]
        }
    }

    created_event = service.events().insert(
        calendarId='primary',
        body=event_body,
        sendUpdates='all'
    ).execute()

    return {
        "message": "✅ Event created successfully!",
        "event_link": created_event.get('htmlLink')
    }
