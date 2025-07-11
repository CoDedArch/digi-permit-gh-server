# services/email_service.py

import os
from postmarker.core import PostmarkClient
from dotenv import load_dotenv

load_dotenv()

POSTMARK_API_TOKEN = os.getenv("POSTMARK_API_TOKEN")
SENDER_EMAIL = os.getenv("POSTMARK_SENDER_EMAIL")  # e.g., verified@yourdomain.com

DIGI_PERMIT_LOGO_URL = "https://your-cdn.com/static/digi-permit-logo.png"  # Replace with actual image URL

if not POSTMARK_API_TOKEN or not SENDER_EMAIL:
    raise ValueError("POSTMARK_API_TOKEN or POSTMARK_SENDER_EMAIL is not set")


async def send_email_otp(email: str, code: str):
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="{DIGI_PERMIT_LOGO_URL}" alt="Digi-Permit Logo" width="80" style="margin-bottom: 10px;" />
            <h2 style="color: #6366F1;">Digi-Permit Verification Code</h2>
        </div>

        <p>Hello / <strong>Agoo</strong>,</p>
        
        <p>
            Your one-time verification code is: <br>
            <span style="font-size: 24px; font-weight: bold; color: #6366F1;">{code}</span>
        </p>

        <p>This code will expire in 5 minutes. If you didn’t request this code, you can safely ignore this email.</p>

        <hr style="margin: 20px 0;">

        <p><strong>Akan Translation:</strong></p>
        <p>
            Wo Digi-Permit dwumadie ho nhyehyɛe kɔd no ne: <br>
            <span style="font-size: 24px; font-weight: bold; color: #6366F1;">{code}</span>
        </p>
        <p>
            Kɔd no bɛyɛ adwuma mmerɛ 5 pɛ. Sɛ woannhyɛ sɛ wɔmfa nhyehyɛe kɔd mma wo a, gye ntɔkwaw na gya email no.
        </p>

        <p style="margin-top: 30px;">– Digi-Permit Team</p>
    </div>
    """

    try:
        client = PostmarkClient(server_token=POSTMARK_API_TOKEN)
        response = client.emails.send(
            From=SENDER_EMAIL,
            To=email,
            Subject="Digi-Permit OTP Code / Nhyehyɛe Kɔd",
            HtmlBody=html_content
        )
        print(f"[EMAIL] Sent OTP {code} to {email}, status: {response['Message']}")
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send OTP to {email}: {e}")
        raise
