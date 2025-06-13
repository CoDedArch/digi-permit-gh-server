# services/sms_service.py

import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_PHONE_NUMBER")


def send_sms_otp(contact: str, otp: str):
    if not all([TWILIO_SID, TWILIO_AUTH, TWILIO_FROM]):
        raise EnvironmentError("Missing Twilio environment variables")

    client = Client(TWILIO_SID, TWILIO_AUTH)

    message_body = (
        f"Digi-Permit OTP: {otp}\n"
        f"This code expires in 5 minutes.\n\n"
        f"Akan: Wo nhyehyɛe kɔd ne {otp}. Ebɛyɛ adwuma mmerɛ 5 pɛ."
    )

    try:
        message = client.messages.create(
            body=message_body,
            from_=TWILIO_FROM,
            to=contact
        )
        print(f"[SMS] OTP sent to {contact}: SID={message.sid}")
    except Exception as e:
        print(f"[SMS ERROR] Failed to send OTP to {contact}: {e}")
        raise
