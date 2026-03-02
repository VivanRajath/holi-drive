"""
API endpoint for the LCC Holi Color Donation Drive.
Handles participation form submissions, generates badges, and sends emails.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# badge_generator moved to project root; import directly
from badge_generator import generate_badge
import base64
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# load environment variables from .env file if available
from dotenv import load_dotenv
# load primary environment file, then example as fallback
load_dotenv()  # loads .env if present
load_dotenv('.env.example', override=False)

app = FastAPI()


def send_badge_email(recipient_email: str, recipient_name: str, badge_bytes: bytes):
    """Send the participation badge to the user via email."""
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_email = os.environ.get("SMTP_EMAIL", "")
    smtp_password = os.environ.get("SMTP_PASSWORD", "")

    if not smtp_email or not smtp_password:
        print("SMTP credentials not configured. Skipping email.")
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = smtp_email
        msg["To"] = recipient_email
        msg["Subject"] = "Your Holi Drive Participation Badge - LCC"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #fff5f8; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; padding: 30px; box-shadow: 0 2px 12px rgba(0,0,0,0.1);">
                <h1 style="color: #e91e8c; text-align: center;">🎨 Thank You, {recipient_name}! 🎨</h1>
                <p style="color: #555; font-size: 16px; line-height: 1.6;">
                    Thank you for joining the <strong>LCC Holi Color Donation Drive</strong>!
                </p>
                <p style="color: #555; font-size: 16px; line-height: 1.6;">
                    The clothes you have donated will be washed and steamed before being
                    given away to those who need them most. Your contribution truly
                    makes a difference.
                </p>
                <p style="color: #555; font-size: 16px; line-height: 1.6;">
                    Your personalized participation badge is attached to this email.
                    Feel free to share it on social media and inspire others to join the movement!
                </p>
                <p style="color: #888; font-size: 14px; text-align: center; margin-top: 30px;">
                    #HoliForGood #LCCDrive #LeafClothingCompany
                </p>
                <p style="color: #aaa; font-size: 12px; text-align: center;">
                    — Leaf Clothing Company
                </p>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(html_body, "html"))

        # Attach badge
        badge_attachment = MIMEImage(badge_bytes, _subtype="png")
        badge_attachment.add_header(
            "Content-Disposition", "attachment",
            filename="LCC_Holi_Badge.png"
        )
        msg.attach(badge_attachment)

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_email, smtp_password)
            server.sendmail(smtp_email, recipient_email, msg.as_string())

        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False


# This file is invoked by Vercel at /api/participate; the runtime
# automatically maps incoming requests to the root of the file.  Only
# relative routes ("/" rather than "/api/participate") should be used.
#
# A simple GET handler allows the service to be checked in the browser.
@app.get("/")
@app.get("/api/participate")
async def root():
    return {"status": "alive"}

@app.post("/")
@app.post("/api/participate")
async def participate(request: Request):
    """Handle participation form submission."""
    try:
        data = await request.json()

        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        phone = data.get("phone", "").strip()
        city = data.get("city", "").strip()

        # Validate
        if not name or not email:
            return JSONResponse(
                status_code=400,
                content={"error": "Name and email are required."}
            )

        # Generate badge
        badge_bytes = generate_badge(name)
        badge_base64 = base64.b64encode(badge_bytes).decode("utf-8")

        # Send email (non-blocking — don't fail the request if email fails)
        email_sent = send_badge_email(email, name, badge_bytes)

        return JSONResponse(content={
            "success": True,
            "badge": badge_base64,
            "email_sent": email_sent,
            "message": f"Badge generated for {name}!"
        })

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Something went wrong: {str(e)}"}
        )
