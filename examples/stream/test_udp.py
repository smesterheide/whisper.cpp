#!/usr/bin/env python3
"""Test UDP functionality by sending an SRT packet to localhost:5555"""
import socket

UDP_IP = "127.0.0.1"
UDP_PORT = 5555

# SRT format test message
test_message = """999
00:00:01,000 --> 00:00:02,000
This is a test message

"""

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
message = test_message.encode('utf-8')

print(f"Sending UDP packet to {UDP_IP}:{UDP_PORT}")
print("SRT Message:")
print("---")
print(test_message, end='')
print("---")

sock.sendto(message, (UDP_IP, UDP_PORT))
print("\nPacket sent!")
sock.close()
