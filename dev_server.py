"""
Local development server for the LCC Holi Color Donation Drive.
Serves frontend static files and the badge generation API.
"""

import os
import sys
import json
import base64
from http.server import HTTPServer, SimpleHTTPRequestHandler

# make sure environment variables from .env are loaded
from dotenv import load_dotenv
# attempt to load environment variables from .env and then example
load_dotenv()
load_dotenv('.env.example', override=False)

# add api directory to path so we can import participate module; badge_generator lives at project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))
from badge_generator import generate_badge
from api.participate import send_badge_email


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
                badge_bytes = generate_badge(name)
                badge_base64 = base64.b64encode(badge_bytes).decode('utf-8')

                # try to send email (non-blocking for response)
                email_sent = False
                try:
                    email_sent = send_badge_email(email, name, badge_bytes)
                except Exception as e:
                    print('Email send error (dev_server):', e)

                self._send_json(200, {
                    'success': True,
                    'badge': badge_base64,
                    'email_sent': email_sent,
                    'message': f'Badge generated for {name}!'
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
    print(f'\n  🎨 LCC Holi Color Donation Drive - Dev Server')
    print(f'  ➡️  http://localhost:{port}\n')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n  Server stopped.')
        server.server_close()


if __name__ == '__main__':
    main()
