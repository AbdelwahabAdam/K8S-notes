import socket
import threading
import time
import psycopg2

from flask import Flask, jsonify, send_file

TCP_HOST = "0.0.0.0"
TCP_PORT = 5000

WEB_PORT = 8080

DB_CONFIG = {
    "host": "postgres",
    "database": "mydb",
    "user": "postgres",
    "password": "postgres",
    "port": 5432
}

message_buffer = []
buffer_lock = threading.Lock()

# -------------------------
# PostgreSQL
# -------------------------

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS slave_messages (
    id SERIAL PRIMARY KEY,
    message TEXT NOT NULL,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

# -------------------------
# TCP SERVER
# -------------------------

def handle_client(client, addr):

    print(f"Connected: {addr}")

    try:
        while True:
            data = client.recv(4096)

            if not data:
                break

            msg = data.decode()

            print(msg)

            with buffer_lock:
                message_buffer.append(msg)

    except Exception as e:
        print(e)

    finally:
        client.close()


def tcp_server():

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server.bind((TCP_HOST, TCP_PORT))
    server.listen()

    print(f"TCP Listening on {TCP_PORT}")

    while True:
        client, addr = server.accept()

        threading.Thread(
            target=handle_client,
            args=(client, addr),
            daemon=True
        ).start()

# -------------------------
# DB WRITER
# -------------------------

def db_writer():

    while True:

        time.sleep(10)

        with buffer_lock:

            if not message_buffer:
                continue

            batch = message_buffer.copy()
            message_buffer.clear()

        db = psycopg2.connect(**DB_CONFIG)
        cur = db.cursor()

        for msg in batch:
            cur.execute(
                "INSERT INTO slave_messages (message) VALUES (%s)",
                (msg,)
            )

        db.commit()

        cur.close()
        db.close()

        print(f"Saved {len(batch)} messages")


# -------------------------
# WEB
# -------------------------

app = Flask(__name__)

@app.route("/")
def home():
    return send_file("index.html")


@app.route("/api/messages")
def messages():

    db = psycopg2.connect(**DB_CONFIG)
    cur = db.cursor()

    cur.execute("""
        SELECT id,
               message,
               received_at
        FROM slave_messages
        ORDER BY id DESC
        LIMIT 1000
    """)

    rows = cur.fetchall()

    cur.close()
    db.close()

    return jsonify([
        {
            "id": r[0],
            "message": r[1],
            "received_at": str(r[2])
        }
        for r in rows
    ])


# -------------------------
# START
# -------------------------

threading.Thread(
    target=tcp_server,
    daemon=True
).start()

threading.Thread(
    target=db_writer,
    daemon=True
).start()

app.run(
    host="0.0.0.0",
    port=WEB_PORT
)