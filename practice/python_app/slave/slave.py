import socket
import time
from datetime import datetime
import os


MASTER_IP = "master"  # Master VM IP
MASTER_PORT = 5000

SLAVE_NAME = os.getenv("SLAVE_NAME", "Slave1")


while True:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((MASTER_IP, MASTER_PORT))

        print("Connected to master")

        while True:
            msg = f"{SLAVE_NAME}: Hello, {datetime.now():%Y-%m-%d %H:%M:%S}"

            sock.sendall(msg.encode())

            print(msg)

            time.sleep(5)

    except Exception as e:
        print("Disconnected:", e)
        time.sleep(5)