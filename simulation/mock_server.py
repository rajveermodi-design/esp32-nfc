#!/usr/bin/env python3
"""
Local Mock Server for NFC Security Dashboard
Serves index.html and provides mock /api/logs and /api/reboot endpoints.
Run on macOS to test frontend UI functionality without an ESP32.
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
import random
import time

PORT = 8080
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../firmware/esp32_nfc_system/data"))

# In-memory mock database of card scans
scan_history = [
    {
        "timestamp": 1050,
        "family": "MIFARE Classic 1K",
        "uid": "A4:3B:11:0C",
        "atqa": "0x0004",
        "sak": "0x08",
        "read_time_us": 28400,
        "status": "AUTH_SUCCESS"
    },
    {
        "timestamp": 3420,
        "family": "NTAG213",
        "uid": "04:88:2E:5A:91:0F:80",
        "atqa": "0x0044",
        "sak": "0x00",
        "read_time_us": 2410,
        "status": "UID_READ_ONLY"
    }
]

class MockDashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            with open(os.path.join(DATA_DIR, "index.html"), "rb") as f:
                self.wfile.write(f.read())
                
        elif self.path == "/api/logs":
            # Simulate real-time scans by occasionally injecting a new tag
            if random.random() < 0.25:
                scan_history.append({
                    "timestamp": int(time.time() * 1000) % 100000,
                    "family": random.choice(["MIFARE Classic 1K", "NTAG215", "MIFARE Ultralight"]),
                    "uid": ":".join([f"{random.randint(0, 255):02X}" for _ in range(4 if random.random() > 0.5 else 7)]),
                    "atqa": "0x0004" if random.random() > 0.5 else "0x0044",
                    "sak": "0x08" if random.random() > 0.5 else "0x00",
                    "read_time_us": random.randint(22000, 36000),
                    "status": random.choice(["AUTH_SUCCESS", "AUTH_SUCCESS", "AUTH_FAILED"])
                })
            
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(scan_history).encode("utf-8"))
            
        elif self.path == "/api/export":
            # Generate downloadable CSV
            self.send_response(200)
            self.send_header("Content-type", "text/csv")
            self.send_header("Content-Disposition", "attachment; filename=nfc_scans.csv")
            self.end_headers()
            csv_data = "Timestamp,Family,UID,ATQA,SAK,ReadTimeUs,Status\n"
            for item in scan_history:
                csv_data += f"{item['timestamp']},{item['family']},{item['uid']},{item['atqa']},{item['sak']},{item['read_time_us']},{item['status']}\n"
            self.wfile.write(csv_data.encode("utf-8"))
        else:
            self.send_error(404, "Endpoint not found")

    def do_POST(self):
        if self.path == "/api/reboot":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Mock Reboot Completed. Flash records preserved.")
        else:
            self.send_error(404)

if __name__ == "__main__":
    print(f"Mock server starting on http://localhost:{PORT}")
    print(f"Serving UI from: {DATA_DIR}")
    server = HTTPServer(("localhost", PORT), MockDashboardHandler)
    server.serve_forever()
