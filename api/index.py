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
from datetime import datetime
import random
import tempfile
import re
import requests
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


def _upload_blob(data: bytes, dest_path: str, content_type: str = 'image/png') -> str:
    """Upload bytes to Vercel Blob via the official REST API.

    Uses PUT https://blob.vercel-storage.com/<pathname>
    Returns the public URL of the uploaded blob.
    """
    token = os.environ.get('BLOB_READ_WRITE_TOKEN', '')
    if not token:
        raise RuntimeError('BLOB_READ_WRITE_TOKEN is not set')

    url = 'https://blob.vercel-storage.com/' + dest_path
    headers = {
        'Authorization': f'Bearer {token}',
        'x-api-version': '7',
        'x-content-type': content_type,
        'x-add-random-suffix': 'false',
    }

    resp = requests.put(url, headers=headers, data=data)
    if not resp.ok:
        raise RuntimeError(f"blob upload failed ({resp.status_code}): {resp.text}")
    result = resp.json()
    return result.get('url', '')


def _build_certificate_html(cert_id: str, badge_image_src: str, share_url: str) -> str:
    """Build a beautiful, self-contained certificate HTML page with social sharing."""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Participation Badge — LCC Holi Color Donation Drive</title>
  <meta name="description" content="I participated in the LCC Holi Color Donation Drive! Turning Holi-colored clothes into meaningful donations. #HoliForGood #LCCDrive #LeafClothingCompany">
  <meta property="og:title" content="🎨 I participated in the LCC Holi Color Donation Drive!" />
  <meta property="og:description" content="Turning discarded Holi-colored clothes into meaningful donations. Join the movement and spread the colors of kindness! 🌈 #HoliForGood #LCCDrive #LeafClothingCompany" />
  <meta property="og:image" content="{badge_image_src}" />
  <meta property="og:image:width" content="1080" />
  <meta property="og:image:height" content="1080" />
  <meta property="og:image:type" content="image/png" />
  <meta property="og:url" content="{share_url}" />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="Leaf Clothing Company — Holi Drive" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="🎨 I participated in the LCC Holi Color Donation Drive!" />
  <meta name="twitter:description" content="Turning Holi-colored clothes into meaningful donations. Join the movement! #HoliForGood #LCCDrive #LeafClothingCompany" />
  <meta name="twitter:image" content="{badge_image_src}" />
  <meta name="twitter:image:alt" content="LCC Holi Color Donation Drive Participation Badge" />
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&family=Nunito:wght@400;700;800&display=swap" rel="stylesheet">
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: 'Outfit', 'Nunito', system-ui, -apple-system, sans-serif;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, #fff0f5 0%, #fff8e1 30%, #e8f5e9 60%, #e3f2fd 100%);
      padding: 20px;
      position: relative;
      overflow-x: hidden;
    }}
    body::before {{
      content: '';
      position: fixed;
      top: -60px; left: -60px;
      width: 220px; height: 220px;
      background: radial-gradient(circle, rgba(233,30,99,0.15) 0%, transparent 70%);
      border-radius: 50%;
      z-index: 0;
    }}
    body::after {{
      content: '';
      position: fixed;
      bottom: -80px; right: -80px;
      width: 280px; height: 280px;
      background: radial-gradient(circle, rgba(255,152,0,0.12) 0%, transparent 70%);
      border-radius: 50%;
      z-index: 0;
    }}
    .card {{
      position: relative;
      z-index: 1;
      background: rgba(255,255,255,0.85);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid rgba(255,255,255,0.6);
      border-radius: 24px;
      max-width: 560px;
      width: 100%;
      padding: 40px 32px 36px;
      text-align: center;
      box-shadow:
        0 8px 32px rgba(233,30,99,0.08),
        0 2px 8px rgba(0,0,0,0.04);
      animation: fadeUp 0.6s ease-out;
    }}
    @keyframes fadeUp {{
      from {{ opacity: 0; transform: translateY(24px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
    .emoji-header {{ font-size: 32px; margin-bottom: 8px; }}
    h1 {{
      font-family: 'Outfit', sans-serif;
      font-weight: 800;
      font-size: 1.6rem;
      background: linear-gradient(135deg, #e91e63, #ff6f00);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      margin-bottom: 4px;
    }}
    .subtitle {{
      color: #777;
      font-size: 0.92rem;
      margin-bottom: 24px;
      font-weight: 400;
    }}
    .badge-img {{
      width: 100%;
      max-width: 420px;
      border-radius: 14px;
      box-shadow: 0 6px 24px rgba(233,30,99,0.12), 0 2px 8px rgba(0,0,0,0.06);
      margin-bottom: 28px;
      transition: transform 0.3s ease;
    }}
    .badge-img:hover {{ transform: scale(1.02); }}

    .share-label {{
      font-weight: 700;
      font-size: 0.95rem;
      color: #444;
      margin-bottom: 14px;
      letter-spacing: 0.02em;
    }}
    .share-row {{
      display: flex;
      justify-content: center;
      gap: 12px;
      flex-wrap: wrap;
      margin-bottom: 20px;
    }}
    .share-btn {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 48px; height: 48px;
      border-radius: 14px;
      border: none;
      cursor: pointer;
      transition: all 0.25s ease;
      color: #fff;
      font-size: 0;
    }}
    .share-btn:hover {{ transform: translateY(-3px); box-shadow: 0 6px 18px rgba(0,0,0,0.15); }}
    .share-btn:active {{ transform: translateY(-1px); }}
    .share-btn svg {{ width: 22px; height: 22px; }}
    .btn-whatsapp {{ background: #25D366; }}
    .btn-whatsapp:hover {{ background: #1ebe57; }}
    .btn-twitter {{ background: #1a1a1a; }}
    .btn-twitter:hover {{ background: #333; }}
    .btn-facebook {{ background: #1877F2; }}
    .btn-facebook:hover {{ background: #0d65d9; }}
    .btn-linkedin {{ background: #0A66C2; }}
    .btn-linkedin:hover {{ background: #004e9a; }}
    .btn-instagram {{ background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888); }}
    .btn-instagram:hover {{ opacity: 0.9; }}

    .copy-row {{
      display: flex;
      align-items: center;
      gap: 8px;
      background: #f8f0f4;
      border-radius: 12px;
      padding: 10px 14px;
      margin-bottom: 22px;
    }}
    .copy-url {{
      flex: 1;
      font-size: 0.82rem;
      color: #888;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      text-align: left;
      user-select: all;
    }}
    .copy-btn {{
      background: linear-gradient(135deg, #e91e63, #ff6f00);
      color: #fff;
      border: none;
      border-radius: 8px;
      padding: 8px 16px;
      font-size: 0.82rem;
      font-weight: 600;
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.2s ease;
    }}
    .copy-btn:hover {{ opacity: 0.9; transform: scale(1.03); }}

    .cta-link {{
      display: inline-block;
      margin-top: 4px;
      font-size: 0.88rem;
      color: #e91e63;
      text-decoration: none;
      font-weight: 600;
      transition: color 0.2s;
    }}
    .cta-link:hover {{ color: #c2185b; text-decoration: underline; }}

    .branding {{
      margin-top: 18px;
      font-size: 0.75rem;
      color: #bbb;
    }}
    .toast {{
      position: fixed;
      bottom: 24px;
      left: 50%;
      transform: translateX(-50%) translateY(80px);
      background: #333;
      color: #fff;
      padding: 12px 24px;
      border-radius: 10px;
      font-size: 0.88rem;
      opacity: 0;
      transition: all 0.35s ease;
      z-index: 999;
      pointer-events: none;
    }}
    .toast.show {{
      opacity: 1;
      transform: translateX(-50%) translateY(0);
    }}

    @media (max-width: 480px) {{
      .card {{ padding: 28px 18px 28px; }}
      h1 {{ font-size: 1.3rem; }}
      .share-btn {{ width: 42px; height: 42px; border-radius: 12px; }}
      .share-btn svg {{ width: 20px; height: 20px; }}
    }}
  </style>
</head>
<body>
  <div class="card">
    <div class="emoji-header">🎨✨</div>
    <h1>Thank You for Participating!</h1>
    <p class="subtitle">You're part of the Holi Color Donation Drive by Leaf Clothing Company</p>

    <img src="{badge_image_src}" alt="Participation Badge" class="badge-img" />

    <p class="share-label">Share Your Badge</p>
    <div class="share-row">
      <button class="share-btn btn-whatsapp" onclick="shareWhatsApp()" title="Share on WhatsApp">
        <svg viewBox="0 0 24 24"><path fill="currentColor" d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
      </button>
      <button class="share-btn btn-twitter" onclick="shareTwitter()" title="Share on X (Twitter)">
        <svg viewBox="0 0 24 24"><path fill="currentColor" d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
      </button>
      <button class="share-btn btn-facebook" onclick="shareFacebook()" title="Share on Facebook">
        <svg viewBox="0 0 24 24"><path fill="currentColor" d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
      </button>
      <button class="share-btn btn-linkedin" onclick="shareLinkedIn()" title="Share on LinkedIn">
        <svg viewBox="0 0 24 24"><path fill="currentColor" d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
      </button>
      <button class="share-btn btn-instagram" onclick="shareInstagram()" title="Share on Instagram">
        <svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg>
      </button>
    </div>

    <div class="copy-row">
      <span class="copy-url" id="share-url">{share_url}</span>
      <button class="copy-btn" onclick="copyLink()">Copy Link</button>
    </div>

    <a href="/" class="cta-link">🌈 Get your own badge →</a>

    <p class="branding">Leaf Clothing Company · #HoliForGood</p>
  </div>

  <div class="toast" id="toast"></div>

  <script>
    var shareUrl = "{share_url}";
    var caption = "I just participated in the LCC Holi Color Donation Drive!\\nTurning discarded Holi-colored clothes into meaningful donations.\\nJoin the movement and spread the colors of kindness.\\n\\n#HoliForGood #LCCDrive #LeafClothingCompany";

    function showToast(msg) {{
      var t = document.getElementById('toast');
      t.textContent = msg;
      t.classList.add('show');
      setTimeout(function() {{ t.classList.remove('show'); }}, 2500);
    }}

    function copyLink() {{
      var text = caption + "\\n\\n" + shareUrl;
      navigator.clipboard.writeText(text).then(function() {{
        showToast('Link & caption copied!');
      }}).catch(function() {{
        var ta = document.createElement('textarea');
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        showToast('Link & caption copied!');
      }});
    }}

    function shareWhatsApp() {{
      window.open('https://wa.me/?text=' + encodeURIComponent(caption + "\\n\\n" + shareUrl), '_blank');
    }}
    function shareTwitter() {{
      window.open('https://twitter.com/intent/tweet?text=' + encodeURIComponent(caption + "\\n\\n" + shareUrl), '_blank');
    }}
    function shareFacebook() {{
      window.open('https://www.facebook.com/sharer/sharer.php?u=' + encodeURIComponent(shareUrl), '_blank');
    }}
    function shareLinkedIn() {{
      window.open('https://www.linkedin.com/sharing/share-offsite/?url=' + encodeURIComponent(shareUrl), '_blank');
    }}
    function shareInstagram() {{
      // Download badge for user, then open Instagram
      var a = document.createElement('a');
      a.href = "{badge_image_src}";
      a.download = 'LCC_Holi_Badge.png';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      showToast('Badge downloaded! Open Instagram to share.');
      setTimeout(function() {{ window.open('https://instagram.com', '_blank'); }}, 1500);
    }}
  </script>
</body>
</html>"""


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


def _get_origin(request: Request) -> str:
    """Resolve the site origin from env vars or the incoming request."""
    site_origin = os.environ.get('SITE_ORIGIN') or os.environ.get('VERCEL_URL')
    if site_origin:
        if site_origin.startswith('http://') or site_origin.startswith('https://'):
            return site_origin.rstrip('/')
        return f"https://{site_origin}"
    return str(request.base_url).rstrip('/')


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
@app.get("/certificates/{cert_id}")
async def certificate_page(cert_id: str, request: Request):
    """Serve a certificate HTML page with social sharing buttons."""
    origin = _get_origin(request)
    share_url = f"{origin}/api/certificate/{cert_id}"

    # --- Try to serve from static file on disk ---
    cert_index_path = os.path.join(STORAGE_DIR, 'certificate', cert_id, 'index.html')
    if os.path.exists(cert_index_path):
        with open(cert_index_path, 'r', encoding='utf-8') as f:
            return HTMLResponse(f.read())

    # --- Try in-memory store ---
    badge_bytes = CERT_STORE.get(cert_id)
    if badge_bytes:
        og_image = f"{origin}/api/certificate/{cert_id}/image"
        html = _build_certificate_html(cert_id, og_image, share_url)
        return HTMLResponse(html)

    # --- Try blob storage (known URL pattern) ---
    token = os.environ.get('BLOB_READ_WRITE_TOKEN', '')
    if token:
        # Try to build the blob image URL and check if it exists
        blob_base = os.environ.get('BLOB_BASE_URL', '')
        if not blob_base:
            m = re.match(r'vercel_blob_[rw]+_([A-Za-z0-9]+)_', token)
            if m:
                store_id = m.group(1).lower()
                blob_base = f"https://{store_id}.public.blob.vercel-storage.com"

        if blob_base:
            blob_image_url = f"{blob_base}/certificates/{cert_id}.png"
            try:
                check = requests.head(blob_image_url, timeout=3)
                if check.status_code == 200:
                    html = _build_certificate_html(cert_id, blob_image_url, share_url)
                    return HTMLResponse(html)
            except Exception:
                pass

    return HTMLResponse('<h1>Certificate not found</h1>', status_code=404)


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
        today = datetime.now().strftime('%B %d, %Y')
        badge_bytes = generate_badge(name, date=today)
        badge_base64 = base64.b64encode(badge_bytes).decode("utf-8")

        # Create a numeric certificate id and save badge + static certificate page
        def make_numeric_id():
            for _ in range(10):
                candidate = str(random.randint(100000, 9999999))
                img_path = os.path.join(STORAGE_DIR, 'certificates', f"{candidate}.png")
                if not os.path.exists(img_path):
                    return candidate
            return str(int(time.time()))

        cert_id = make_numeric_id()
        origin = _get_origin(request)
        share_url = f"{origin}/api/certificate/{cert_id}"

        # --- Blob upload path (preferred when token is available) ---
        blob_token = os.environ.get('BLOB_READ_WRITE_TOKEN', '')
        if blob_token:
            try:
                blob_image_url = _upload_blob(
                    badge_bytes,
                    f"certificates/{cert_id}.png",
                    'image/png'
                )

                # Build certificate HTML with blob image URL
                cert_html = _build_certificate_html(cert_id, blob_image_url, share_url)

                # Upload the HTML page to blob too
                _upload_blob(
                    cert_html.encode('utf-8'),
                    f"certificate/{cert_id}.html",
                    'text/html'
                )

                # Also store in memory as fallback for the /api/certificate route
                CERT_STORE[cert_id] = badge_bytes

            except Exception as blob_err:
                print(f"Blob upload failed, falling back to local: {blob_err}")
                # Fall through to local storage
                blob_token = ''

        # --- Local filesystem fallback ---
        if not blob_token:
            try:
                certs_dir = os.path.join(STORAGE_DIR, 'certificates')
                cert_page_dir = os.path.join(STORAGE_DIR, 'certificate', cert_id)
                os.makedirs(certs_dir, exist_ok=True)
                os.makedirs(cert_page_dir, exist_ok=True)

                img_path = os.path.join(certs_dir, f"{cert_id}.png")
                with open(img_path, 'wb') as f:
                    f.write(badge_bytes)

                og_image = f"{origin}/api/certificate/{cert_id}/image"
                cert_html = _build_certificate_html(cert_id, og_image, share_url)

                cert_index_path = os.path.join(cert_page_dir, 'index.html')
                with open(cert_index_path, 'w', encoding='utf-8') as f:
                    f.write(cert_html)

            except OSError:
                CERT_STORE[cert_id] = badge_bytes

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
