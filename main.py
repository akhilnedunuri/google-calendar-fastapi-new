import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional
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
    version="2.2.0"
)

# --------------------------------------------------
# ✅ Enable CORS
# --------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# ✅ Google Calendar Setup
# --------------------------------------------------
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Local defaults
LOCAL_TOKEN_PATH = "token.json"
LOCAL_CLIENT_SECRET_PATH = "client_secrets.json"

# On Render: prefer /etc/secrets
CLIENT_SECRET_PATH = (
    "/etc/secrets/client_secrets.json"
    if os.path.exists("/etc/secrets/client_secrets.json")
    else LOCAL_CLIENT_SECRET_PATH
)
TOKEN_PATH = (
    "/etc/secrets/token.json"
    if os.path.exists("/etc/secrets/token.json")
    else LOCAL_TOKEN_PATH
)

print(f"✅ Using CLIENT_SECRET_PATH: {CLIENT_SECRET_PATH}")
print(f"✅ Using TOKEN_PATH: {TOKEN_PATH}")

# --------------------------------------------------
# ✅ Load Google Credentials
# --------------------------------------------------
creds = None

if os.path.exists(TOKEN_PATH):
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

# If creds invalid or missing, refresh or recreate
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        if not os.path.exists(CLIENT_SECRET_PATH):
            raise Exception("client_secrets.json not found in project folder or /etc/secrets/")
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, SCOPES)
        creds = flow.run_local_server(port=0)

    # ✅ Render fix: write refreshed token to /tmp if /etc/secrets/ is read-only
    writable_token_path = TOKEN_PATH
    if TOKEN_PATH.startswith("/etc/secrets"):
        writable_token_path = "/tmp/token.json"

    try:
        with open(writable_token_path, "w") as token_file:
            token_file.write(creds.to_json())
        print(f"✅ Token saved to: {writable_token_path}")
    except OSError as e:
        print(f"⚠️ Could not write token to {writable_token_path}: {e}")

# Build Calendar service
service = build("calendar", "v3", credentials=creds)

# --------------------------------------------------
# ✅ Models
# --------------------------------------------------
class CalendarEvent(BaseModel):
    title: str
    description: Optional[str] = None
    startDateTime: str
    endDateTime: str


class BookingPayload(BaseModel):
    customerEmail: str
    customerFirstName: str
    customerLastName: str
    customerPhone: Optional[str] = None
    tourType: str
    numberOfParticipants: int
    bookingDate: str
    bookingTime: str
    isParticipantAdult: bool
    hasAcceptedTerms: bool
    digitalSignature: Optional[str] = None
    paymentMethod: str
    paymentStatus: str
    tourPrice: float
    calendarEvent: CalendarEvent
    fulfillmentStatus: str
    orderTimestamp: str

# --------------------------------------------------
# ✅ Routes
# --------------------------------------------------
@app.get("/", include_in_schema=False)
async def root_redirect():
    """Redirect root to Swagger UI"""
    return RedirectResponse(url="/docs")


@app.post("/create-booking-event")
async def create_booking_event(booking: BookingPayload):
    """Create a Google Calendar event for tour bookings"""
    try:
        calendar_id = "primary"

        summary = f"{booking.calendarEvent.title} - {booking.tourType}"
        description = f"""
        Booking Confirmation:

        👤 Customer: {booking.customerFirstName} {booking.customerLastName}
        📧 Email: {booking.customerEmail}
        📞 Phone: {booking.customerPhone or 'N/A'}

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
                "timeZone": "Asia/Kolkata",
            },
            "end": {
                "dateTime": booking.calendarEvent.endDateTime,
                "timeZone": "Asia/Kolkata",
            },
            "attendees": [
                {"email": booking.customerEmail},
                {"email": "akhilnedunuri7@gmail.com"},  # your copy
            ],
        }

        created_event = service.events().insert(
            calendarId=calendar_id, body=event_body, sendUpdates="all"
        ).execute()

        return {
            "status": "success",
            "message": "Booking event created successfully and invite sent!",
            "eventLink": created_event.get("htmlLink"),
            "eventId": created_event.get("id"),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
