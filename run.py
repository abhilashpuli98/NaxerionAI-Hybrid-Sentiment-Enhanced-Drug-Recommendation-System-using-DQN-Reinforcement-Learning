#!/usr/bin/env python3
"""Flask development server for SEDRS"""

import ssl
import os
import certifi

# Configure SSL for HuggingFace model downloads
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
os.environ['CURL_CA_BUNDLE'] = certifi.where()

from app import create_app

if __name__ == '__main__':
    app = create_app()
    print("[*] Starting SEDRS Development Server...")
    print("[*] Database: instance/sedrs.db")
    print("[*] Server: http://127.0.0.1:5000")
    print("[!] Press CTRL+C to stop")
    app.run(debug=True, host='127.0.0.1', port=5000)
