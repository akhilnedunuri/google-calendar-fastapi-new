import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional, List
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# --------------------------------------------------
# ✅ App Configuration
# --------------------------------------------------
app = FastAPI(
    title="Tour Booking Calendar API",
    description="Integrate tour booking confirmations with Google Calendar and send invite emails.",
    version="2.0.0"
)

# --------------------------------------------------
# ✅ Enable CORS (Allow your teammate’s frontend)
# --------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with your frontend domain for production (e.g., "https://your-frontend.com")
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# ✅ Environment variables & Google Auth setup
# --------------------------------------------------
TOKEN_PATH = "token.json"
CLIENT_SECRET_PATH = "client_secrets.json"

# --- Handle token.json ---
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
# ✅ Google Calendar Setup
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
# ✅ Models
# --------------------------------------------------
class CalendarEvent(BaseModel):
    title: str
    description: Optional[str] = None
    startDateTime: str
    endDateTime: str

class BookingPayload(BaseModel):
    # Customer Information
    customerEmail: str
    customerFirstName: str
    customerLastName: str
    customerPhone: Optional[str] = None

    # Booking Details
    tourType: str
    numberOfParticipants: int
    bookingDate: str
    bookingTime: str
    isParticipantAdult: bool

    # Legal Agreement
    hasAcceptedTerms: bool
    digitalSignature: Optional[str] = None

    # Payment Details
    paymentMethod: str
    paymentStatus: str
    tourPrice: float

    # Calendar Integration
    calendarEvent: CalendarEvent

    # System Fields
    fulfillmentStatus: str
    orderTimestamp: str

# --------------------------------------------------
# ✅ Routes
# --------------------------------------------------
@app.get("/", include_in_schema=False)
async def root_redirect():
    """Redirect root to Swagger UI"""
    return RedirectResponse(url="/docs")

# ---- Old Endpoint (Still Works) ----
@app.post("/create-event")
async def create_event(event: dict):
    """Legacy endpoint for manual calendar events"""
    try:
        calendar_id = 'primary'
        created_event = service.events().insert(
            calendarId=calendar_id,
            body=event,
            sendUpdates='all'
        ).execute()
        return {"status": "success", "event": created_event}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---- New Booking Endpoint ----
@app.post("/create-booking-event")
async def create_booking_event(booking: BookingPayload):
    """Create a Google Calendar event for tour bookings"""
    try:
        calendar_id = 'primary'

        summary = f"{booking.calendarEvent.title} - {booking.tourType}"
        description = f"""
        Booking Confirmation:

        👤 Customer: {booking.customerFirstName} {booking.customerLastName}
        📧 Email: {booking.customerEmail}
        📞 Phone: {booking.customerPhone}

        🏝️ Tour Type: {booking.tourType}
        👥 Participants: {booking.numberOfParticipants}
        🧑‍🧑 Adults: {"Yes" if booking.isParticipantAdult else "No"}

        📅 Booking Date: {booking.bookingDate}
        🕒 Time: {booking.bookingTime}

        💳 Payment Method: {booking.paymentMethod}
        💰 Payment Status: {booking.paymentStatus}
        💵 Price: ${booking.tourPrice}

        🚚 Fulfillment Status: {booking.fulfillmentStatus}
        🕓 Order Timestamp: {booking.orderTimestamp}

        ✅ Terms Accepted: {"Yes" if booking.hasAcceptedTerms else "No"}
        ✍️ Signature: {booking.digitalSignature or 'N/A'}
        """.strip()

        event_body = {
            "summary": summary,
            "description": description,
            "start": {
                "dateTime": booking.calendarEvent.startDateTime,
                "timeZone": "Asia/Kolkata"
            },
            "end": {
                "dateTime": booking.calendarEvent.endDateTime,
                "timeZone": "Asia/Kolkata"
            },
            "attendees": [
                {"email": booking.customerEmail},
                {"email": "yourofficialteam@gmail.com"}  # Replace with your team’s email
            ],
        }

        created_event = service.events().insert(
            calendarId=calendar_id,
            body=event_body,
            sendUpdates='all'
        ).execute()

        return {
            "status": "success",
            "message": "Booking event created successfully and invite sent!",
            "eventLink": created_event.get("htmlLink"),
            "eventId": created_event.get("id")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
