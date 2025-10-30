# 🗓️ Tour Booking Calendar API

Integrate **Tour Booking Confirmations** with **Google Calendar** and automatically send event invites to customers.  
Built using **FastAPI** and **Google Calendar API**, this backend allows seamless connection between your booking system and Google Calendar.

---

## 🚀 Features

✅ Create Google Calendar events for tour bookings  
✅ Automatically send calendar invites to customers  
✅ Supports multiple attendees (emails)  
✅ Secure environment variable setup for Render deployment  
✅ Built-in CORS for frontend integration  
✅ Fully documented Swagger UI at `/docs`

---

## 🧩 Tech Stack

- **Backend Framework:** FastAPI (Python)
- **Google API:** Google Calendar API
- **Hosting:** Render
- **Language:** Python 3.10+
- **Auth:** OAuth2 (Google credentials)
- **Documentation:** Swagger (via FastAPI)

---

## 📁 Project Structure

├── main.py # Core FastAPI application
├── requirements.txt # Python dependencies
├── client_secrets.json # Google OAuth credentials (not committed)
├── token.json # Google OAuth token (not committed)
├── .env # Environment variables for Render (not committed)
└── README.md # Project documentation

⚙️ Environment Variables

In your Render project or local .env file, add:

GOOGLE_CLIENT_SECRETS=client_secrets.json
TOKEN_FILE=token.json


Make sure you upload both client_secrets.json and token.json as secret files in Render.

## 🧠 How It Works

Your teammate (frontend/backend) sends a POST request to your API endpoint (e.g. /send-mail-calendar).

The API automatically:

Sends an email to the customer confirming the booking.

Creates a Google Calendar event with the booking details.

## 📤 Example Request Body
{
  "customerEmail": "customer@example.com",
  "customerFirstName": "John",
  "customerLastName": "Doe",
  "customerPhone": "+91 9876543210",
  "tourType": "Beach Tour",
  "numberOfParticipants": 2,
  "bookingDate": "2025-11-01",
  "bookingTime": "15:00",
  "isParticipantAdult": true,
  "hasAcceptedTerms": true,
  "digitalSignature": "JohnDoeSignature",
  "paymentMethod": "Credit Card",
  "paymentStatus": "Paid",
  "tourPrice": 100.00,
  "calendarEvent": {
    "title": "Beach Tour Booking - John Doe",
    "description": "Booking confirmed for Beach Tour on 2025-11-01",
    "startDateTime": "2025-11-01T15:00:00",
    "endDateTime": "2025-11-01T17:00:00"
  },
  "fulfillmentStatus": "Confirmed",
  "orderTimestamp": "2025-10-28T11:30:00"
}

## 🧪 Example Response
{
  "message": "Email sent and event added to Google Calendar successfully!"
}

## 👨‍💻 How to Run Locally

Clone the repository:

git clone <repo-url>
cd <repo-folder>


Install dependencies:

pip install -r requirements.txt


Run the API:

uvicorn main:app --reload


Open in browser:

http://127.0.0.1:8000/docs

## 📬 Example Use Case

When a customer books a Beach Tour,

They receive a confirmation email with details of the order.

A Google Calendar event is created with their tour date and time.

## 🧑‍🤝‍🧑 Team Usage

Your teammates can connect their booking system or website to this API endpoint by sending a POST request with the correct schema.
   
