import os
import time
import requests
import threading
import json
from flask import Flask, jsonify, request, render_template
from datetime import datetime

app = Flask(__name__)

# Configuration
MASTER_PORT = int(os.getenv("MASTER_PORT", 5000))
SLAVE_URL = os.getenv("SLAVE_URL", "http://slave-service:5001")

# Store messages
messages = []
message_lock = threading.Lock()

class MasterNode:
    def __init__(self):
        self.running = True
        self.slave_available = False
        
    def send_bing(self):
        """Send BING to slave"""
        try:
            response = requests.post(
                f"{SLAVE_URL}/receive",
                json={
                    "from": "Master",
                    "message": "BING",
                    "timestamp": datetime.now().isoformat()
                },
                timeout=2
            )
            if response.status_code == 200:
                self.slave_available = True
                return True
        except requests.exceptions.RequestException:
            self.slave_available = False
            print("⚠️ Slave is not responding")
        return False

    def receive_bong(self, data):
        """Receive BONG from slave"""
        with message_lock:
            messages.append({
                "from": "Slave",
                "message": data.get("message", "BONG"),
                "timestamp": data.get("timestamp", datetime.now().isoformat())
            })
        print(f"📨 Received BONG from Slave")
        return True

    def run(self):
        """Main loop to send BING every 2 seconds"""
        print("🚀 Master Node Started")
        print(f"📍 Master running on port {MASTER_PORT}")
        print(f"📍 Slave URL: {SLAVE_URL}")
        print("=" * 50)
        
        while self.running:
            success = self.send_bing()
            if success:
                with message_lock:
                    messages.append({
                        "from": "Master",
                        "message": "BING",
                        "timestamp": datetime.now().isoformat()
                    })
                print(f"📤 Sent BING to Slave")
            time.sleep(2)

# Initialize master node
master = MasterNode()

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
        "node_type": "Master",
        "slave_available": master.slave_available,
        "total_messages": len(messages),
        "port": MASTER_PORT
    })

@app.route('/receive', methods=['POST'])
def receive_from_slave():
    data = request.json
    if data and data.get('message') == 'BONG':
        master.receive_bong(data)
        return jsonify({"status": "received"}), 200
    return jsonify({"status": "invalid"}), 400

if __name__ == "__main__":
    # Start master loop in background
    thread = threading.Thread(target=master.run, daemon=True)
    thread.start()
    app.run(host='0.0.0.0', port=MASTER_PORT, debug=False)