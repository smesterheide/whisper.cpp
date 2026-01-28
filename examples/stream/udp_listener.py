#!/usr/bin/env python3
"""
Simple UDP listener for testing whisper-stream UDP output.
Receives SRT format packets and displays them in a readable format.

Usage: python3 udp_listener.py [port]
Default port: 5555
"""
import socket
import sys
from datetime import datetime

UDP_IP = "0.0.0.0"
UDP_PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5555

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print(f"UDP listener started on {UDP_IP}:{UDP_PORT}")
print("Waiting for SRT packets...\n")

try:
    while True:
        data, addr = sock.recvfrom(4096)
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        try:
            srt_text = data.decode('utf-8')
            print(f"[{timestamp}] Received from {addr}:")
            print("---")
            print(srt_text, end='')
            print("---")
        except Exception as e:
            print(f"[{timestamp}] Error parsing: {e}")
            print(f"  Raw data: {data}")
            print()
except KeyboardInterrupt:
    print("\nShutting down...")
    sock.close()
