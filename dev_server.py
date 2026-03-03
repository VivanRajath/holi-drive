"""
Local development server for the LCC Holi Color Donation Drive.
Serves frontend static files and the badge generation API.
"""

import os
import sys
import json
import base64
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler

# make sure environment variables from .env are loaded
from dotenv import load_dotenv
# attempt to load environment variables from .env and then example
load_dotenv()
load_dotenv('.env.example', override=False)

# add api directory to path so we can import participate module; badge_generator lives at project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))
from badge_generator import generate_badge
from api.index import send_badge_email


class DevHandler(SimpleHTTPRequestHandler):
    """Development server handler that serves both static files and the API."""

    def __init__(self, *args, **kwargs):
        # Serve files from 'public' directory
        super().__init__(*args, directory='public', **kwargs)

    def do_POST(self):
        if self.path == '/api/participate':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)

            try:
                data = json.loads(body)
                name = data.get('name', '').strip()
                email = data.get('email', '').strip()

                if not name or not email:
                    self._send_json(400, {'error': 'Name and email are required.'})
                    return

                # Generate badge
                today = datetime.now().strftime('%B %d, %Y')
                badge_bytes = generate_badge(name, date=today)
                badge_base64 = base64.b64encode(badge_bytes).decode('utf-8')

                # try to send email (non-blocking for response)
                email_sent = False
                try:
                    email_sent = send_badge_email(email, name, badge_bytes)
                except Exception as e:
                    print('Email send error (dev_server):', e)

                # Create certificate id and save files (mirrors api/index.py behavior)
                def make_numeric_id():
                    for _ in range(10):
                        import random, time
                        candidate = str(random.randint(100000, 9999999))
                        img_path = os.path.join('public', 'certificates', f"{candidate}.png")
                        if not os.path.exists(img_path):
                            return candidate
                    return str(int(time.time()))

                cert_id = make_numeric_id()
                certs_dir = os.path.join('public', 'certificates')
                cert_page_dir = os.path.join('public', 'certificate', cert_id)
                os.makedirs(certs_dir, exist_ok=True)
                os.makedirs(cert_page_dir, exist_ok=True)

                # save image file
                img_path = os.path.join(certs_dir, f"{cert_id}.png")
                with open(img_path, 'wb') as f:
                    f.write(badge_bytes)

                # build origin from Host header if available
                host = self.headers.get('Host') or f'localhost:{os.environ.get("PORT", "8000")} '
                origin = f'http://{host}'.strip()
                og_image = f"{origin}/certificates/{cert_id}.png"
                share_url = f"{origin}/certificate/{cert_id}"

                # simple static page with og tags
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
    <img src=\"/certificates/{cert_id}.png\" alt=\"Participation Badge\" style=\"max-width:100%; height:auto; border-radius:8px; box-shadow:0 6px 20px rgba(0,0,0,0.08); margin-top:18px;\" />
    <p style=\"color:#888; margin-top:20px; font-size:14px;\">Share this link: {share_url}</p>
  </div>
</body>
</html>"""

                cert_index_path = os.path.join(cert_page_dir, 'index.html')
                with open(cert_index_path, 'w', encoding='utf-8') as f:
                    f.write(cert_html)

                self._send_json(200, {
                    'success': True,
                    'badge': badge_base64,
                    'email_sent': email_sent,
                    'message': f'Badge generated for {name}!',
                    'certificate_id': cert_id,
                    'share_url': share_url
                })

            except Exception as e:
                self._send_json(500, {'error': str(e)})
        else:
            self._send_json(404, {'error': 'Not found'})

    def _send_json(self, status_code, data):
        response = json.dumps(data).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(response))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


def main():
    port = int(os.environ.get('PORT', 8000))
    server = HTTPServer(('0.0.0.0', port), DevHandler)
    print(f'\n  LCC Holi Color Donation Drive - Dev Server')
    print(f'  http://localhost:{port}\n')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n  Server stopped.')
        server.server_close()


if __name__ == '__main__':
    main()
