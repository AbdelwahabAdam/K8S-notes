import os
import time
import requests
import threading
import json
from flask import Flask, jsonify, request, render_template
from datetime import datetime

app = Flask(__name__)

# Configuration
SLAVE_PORT = int(os.getenv("SLAVE_PORT", 5001))
MASTER_URL = os.getenv("MASTER_URL", "http://master-service:5000")

# Store messages
messages = []
message_lock = threading.Lock()

class SlaveNode:
    def __init__(self):
        self.running = True
        self.master_available = False
        
    def send_bong(self):
        """Send BONG to master"""
        try:
            response = requests.post(
                f"{MASTER_URL}/receive",
                json={
                    "from": "Slave",
                    "message": "BONG",
                    "timestamp": datetime.now().isoformat()
                },
                timeout=2
            )
            if response.status_code == 200:
                self.master_available = True
                return True
        except requests.exceptions.RequestException:
            self.master_available = False
            print("⚠️ Master is not responding")
        return False

    def receive_bing(self, data):
        """Receive BING from master"""
        with message_lock:
            messages.append({
                "from": "Master",
                "message": data.get("message", "BING"),
                "timestamp": data.get("timestamp", datetime.now().isoformat())
            })
        print(f"📨 Received BING from Master")
        return True

    def run(self):
        """Main loop to send BONG every 2 seconds"""
        print("🚀 Slave Node Started")
        print(f"📍 Slave running on port {SLAVE_PORT}")
        print(f"📍 Master URL: {MASTER_URL}")
        print("=" * 50)
        
        while self.running:
            success = self.send_bong()
            if success:
                with message_lock:
                    messages.append({
                        "from": "Slave",
                        "message": "BONG",
                        "timestamp": datetime.now().isoformat()
                    })
                print(f"📤 Sent BONG to Master")
            time.sleep(2)

# Initialize slave node
slave = SlaveNode()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/messages')
def get_messages():
    with message_lock:
        return jsonify(messages[-50:])

@app.route('/api/status')
def get_status():
    return jsonify({
        "node_type": "Slave",
        "master_available": slave.master_available,
        "total_messages": len(messages),
        "port": SLAVE_PORT
    })

@app.route('/receive', methods=['POST'])
def receive_from_master():
    data = request.json
    if data and data.get('message') == 'BING':
        slave.receive_bing(data)
        return jsonify({"status": "received"}), 200
    return jsonify({"status": "invalid"}), 400

if __name__ == "__main__":
    # Start slave loop in background
    thread = threading.Thread(target=slave.run, daemon=True)
    thread.start()
    app.run(host='0.0.0.0', port=SLAVE_PORT, debug=False)