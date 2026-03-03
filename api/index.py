"""
API endpoint for the LCC Holi Color Donation Drive.
Handles participation form submissions, generates badges, and sends emails.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse, Response

# badge_generator moved to project root; import directly
from badge_generator import generate_badge
import base64
import os
import smtplib
import time
import random
import subprocess
import tempfile
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# load environment variables from .env file if available
from dotenv import load_dotenv
# load primary environment file, then example as fallback
load_dotenv()  # loads .env if present
load_dotenv('.env.example', override=False)

app = FastAPI()

# In-memory fallback store for environments with read-only filesystem (e.g., serverless)
CERT_STORE = {}


def _upload_blob(local_path: str, dest_path: str, access: str = 'public') -> str:
    """Invoke the Node helper to upload a file to Vercel Blob and return its URL."""
    script = os.path.join(os.path.dirname(__file__), '..', 'upload_blob.js')
    # ensure script is executable
    result = subprocess.run(['node', script, local_path, dest_path, access], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"blob upload failed: {result.stderr}")
    return result.stdout.strip()

# determine where to write badge files; by default use /tmp (Vercel ephemeral storage)
# allow overriding via STORAGE_DIR env var
STORAGE_DIR = os.environ.get('STORAGE_DIR', '/tmp')
# during local dev we may prefer writing into public so static preview works
if STORAGE_DIR == '/tmp':
    try:
        if os.path.isdir('public') and os.access('public', os.W_OK):
            STORAGE_DIR = 'public'
    except Exception:
        pass

# ensure directories exist when using local storage
if STORAGE_DIR.startswith('/') or STORAGE_DIR == 'public':
    os.makedirs(os.path.join(STORAGE_DIR, 'certificates'), exist_ok=True)
    os.makedirs(os.path.join(STORAGE_DIR, 'certificate'), exist_ok=True)


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


@app.get("/api/certificate/{cert_id}")
async def certificate_page(cert_id: str, request: Request):
    """Serve a certificate HTML page. Use on-disk files if present, otherwise
    serve a generated page that references the API image endpoint (in-memory)."""
    # Try to serve static file if it exists (the earlier flow writes to public)
    # check storage directory first
    cert_index_path = os.path.join(STORAGE_DIR, 'certificate', cert_id, 'index.html')
    if os.path.exists(cert_index_path):
        with open(cert_index_path, 'r', encoding='utf-8') as f:
            return HTMLResponse(f.read())

    # Fallback: look up in-memory store
    badge_bytes = CERT_STORE.get(cert_id)
    origin = str(request.base_url).rstrip('/')
    share_url = f"{origin}/api/certificate/{cert_id}"

    if badge_bytes:
        og_image = f"{origin}/api/certificate/{cert_id}/image"
        html = f"""<!doctype html>
<html lang=\"en\"> 
<head>
  <meta charset=\"utf-8\"> 
  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"> 
  <title>Participation Badge - Leaf Clothing Company</title>
  <meta name=\"description\" content=\"I participated in the LCC Holi Color Donation Drive!\"> 
  <meta property=\"og:title\" content=\"I participated in the LCC Holi Color Donation Drive!\" />
  <meta property=\"og:description\" content=\"Join the movement — turning Holi-colored clothes into donations.\" />
  <meta property=\"og:image\" content=\"{og_image}\" />
  <meta property=\"twitter:card\" content=\"summary_large_image\" />
</head>
<body style=\"font-family: system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; margin:0; display:flex; align-items:center; justify-content:center; min-height:100vh; background:#fff8fb;\">
  <div style=\"text-align:center; max-width:760px; padding:28px;\">
    <h1 style=\"color:#e91e63; margin-bottom:6px;\">Thank you for participating!</h1>
    <p style=\"color:#555; margin-top:0;\">Share your participation — the badge is below.</p>
    <img src=\"/api/certificate/{cert_id}/image\" alt=\"Participation Badge\" style=\"max-width:100%; height:auto; border-radius:8px; box-shadow:0 6px 20px rgba(0,0,0,0.08); margin-top:18px;\" />
    <p style=\"color:#888; margin-top:20px; font-size:14px;\">Share this link: {share_url}</p>
  </div>
</body>
</html>"""
        return HTMLResponse(html)

    return HTMLResponse('<h1>Not found</h1>', status_code=404)


@app.get("/api/certificate/{cert_id}/image")
async def certificate_image(cert_id: str):
    """Return the PNG bytes for a certificate, using on-disk file if present,
    otherwise the in-memory store."""
    img_path = os.path.join(STORAGE_DIR, 'certificates', f"{cert_id}.png")
    if os.path.exists(img_path):
        with open(img_path, 'rb') as f:
            data = f.read()
        return Response(content=data, media_type='image/png')

    badge_bytes = CERT_STORE.get(cert_id)
    if badge_bytes:
        return Response(content=badge_bytes, media_type='image/png')

    return Response(content=b'Not found', status_code=404)

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

        # Create a numeric certificate id and save badge + static certificate page
        def make_numeric_id():
            for _ in range(10):
                candidate = str(random.randint(100000, 9999999))
                img_path = os.path.join('public', 'certificates', f"{candidate}.png")
                if not os.path.exists(img_path):
                    return candidate
            return str(int(time.time()))

        cert_id = make_numeric_id()

        # Try to save files under public/ (works in local dev). If filesystem
        # is read-only (serverless), fall back to the in-memory CERT_STORE
        site_origin = os.environ.get('SITE_ORIGIN') or os.environ.get('VERCEL_URL')
        # if USE_BLOB is set we'll upload to Vercel Blob instead of local storage
        if os.environ.get('USE_BLOB'):
            # write badge to temp file and call Node helper
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tf:
                tf.write(badge_bytes)
                badge_path = tf.name
            try:
                blob_image_url = _upload_blob(badge_path, f"certificates/{cert_id}.png", 'public')
            finally:
                try:
                    os.remove(badge_path)
                except Exception:
                    pass

            # certificate page html referring to blob_image_url
            og_image = blob_image_url
            html = f"""<!doctype html>
<html lang=\"en\"> 
<head>
  <meta charset=\"utf-8\"> 
  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"> 
  <title>Participation Badge - Leaf Clothing Company</title>
  <meta name=\"description\" content=\"I participated in the LCC Holi Color Donation Drive!\"> 
  <meta property=\"og:title\" content=\"I participated in the LCC Holi Color Donation Drive!\" />
  <meta property=\"og:description\" content=\"Join the movement — turning Holi-colored clothes into donations.\" />
  <meta property=\"og:image\" content=\"{og_image}\" />
  <meta property=\"twitter:card\" content=\"summary_large_image\" />
</head>
<body style=\"font-family: system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; margin:0; display:flex; align-items:center; justify-content:center; min-height:100vh; background:#fff8fb;\">
  <div style=\"text-align:center; max-width:760px; padding:28px;\">
    <h1 style=\"color:#e91e63; margin-bottom:6px;\">Thank you for participating!</h1>
    <p style=\"color:#555; margin-top:0;\">Share your participation — the badge is below.</p>
    <img src=\"{blob_image_url}\" alt=\"Participation Badge\" style=\"max-width:100%; height:auto; border-radius:8px; box-shadow:0 6px 20px rgba(0,0,0,0.08); margin-top:18px;\" />
    <p style=\"color:#888; margin-top:20px; font-size:14px;\">Share this link: {share_url}</p>
  </div>
</body>
</html>"""

            # upload certificate HTML
            with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as tf:
                tf.write(html)
                html_path = tf.name
            try:
                html_url = _upload_blob(html_path, f"certificate/{cert_id}.html", 'public')
            finally:
                try:
                    os.remove(html_path)
                except Exception:
                    pass

            share_url = html_url
        else:
            try:
                # write into chosen storage directory (default /tmp on Vercel)
                certs_dir = os.path.join(STORAGE_DIR, 'certificates')
                cert_page_dir = os.path.join(STORAGE_DIR, 'certificate', cert_id)
                os.makedirs(certs_dir, exist_ok=True)
                os.makedirs(cert_page_dir, exist_ok=True)

                # Save image file
                img_path = os.path.join(certs_dir, f"{cert_id}.png")
                with open(img_path, 'wb') as f:
                    f.write(badge_bytes)

                # Determine absolute origin for social preview images
                if site_origin:
                    if site_origin.startswith('http://') or site_origin.startswith('https://'):
                        origin = site_origin
                    else:
                        origin = f"https://{site_origin}"
                    og_image = f"{origin}/certificate/{cert_id}"
                    share_url = f"{origin}/api/certificate/{cert_id}"
                else:
                    # when STORAGE_DIR is public the static path may work
                    og_image = f"/certificate/{cert_id}"
                    share_url = f"/api/certificate/{cert_id}"

                # Save the certificate HTML to storage
                cert_html = f"""<!doctype html>
<html lang=\"en\"> 
<head>
  <meta charset=\"utf-8\"> 
  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"> 
  <title>Participation Badge - Leaf Clothing Company</title>
  <meta name=\"description\" content=\"I participated in the LCC Holi Color Donation Drive!\"> 
  <meta property=\"og:title\" content=\"I participated in the LCC Holi Color Donation Drive!\" />
  <meta property=\"og:description\" content=\"Join the movement — turning Holi-colored clothes into donations.\" />
  <meta property=\"og:image\" content=\"{og_image}\" />
  <meta property=\"twitter:card\" content=\"summary_large_image\" />
</head>
<body style=\"font-family: system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; margin:0; display:flex; align-items:center; justify-content:center; min-height:100vh; background:#fff8fb;\">
  <div style=\"text-align:center; max-width:760px; padding:28px;\">
    <h1 style=\"color:#e91e63; margin-bottom:6px;\">Thank you for participating!</h1>
    <p style=\"color:#555; margin-top:0;\">Share your participation — the badge is below.</p>
    <img src=\"/api/certificate/{cert_id}/image\" alt=\"Participation Badge\" style=\"max-width:100%; height:auto; border-radius:8px; box-shadow:0 6px 20px rgba(0,0,0,0.08); margin-top:18px;\" />
    <p style=\"color:#888; margin-top:20px; font-size:14px;\">Share this link: {share_url}</p>
  </div>
</body>
</html>"""

                cert_index_path = os.path.join(cert_page_dir, 'index.html')
                with open(cert_index_path, 'w', encoding='utf-8') as f:
                    f.write(cert_html)

            except OSError as oe:
                # Filesystem may be read-only even in STORAGE_DIR; fall back to memory store
                CERT_STORE[cert_id] = badge_bytes
                if site_origin:
                    if site_origin.startswith('http://') or site_origin.startswith('https://'):
                        origin = site_origin
                    else:
                        origin = f"https://{site_origin}"
                else:
                        origin = str(request.base_url).rstrip('/')

                share_url = f"{origin}/api/certificate/{cert_id}"

        # Send email (non-blocking — don't fail the request if email fails)
        email_sent = send_badge_email(email, name, badge_bytes)

        return JSONResponse(content={
            "success": True,
            "badge": badge_base64,
            "email_sent": email_sent,
            "message": f"Badge generated for {name}!",
            "certificate_id": cert_id,
            "share_url": share_url
        })

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Something went wrong: {str(e)}"}
        )
