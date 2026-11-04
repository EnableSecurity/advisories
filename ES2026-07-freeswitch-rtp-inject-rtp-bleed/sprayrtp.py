import argparse
import socket
import struct
import time

parser = argparse.ArgumentParser()
parser.add_argument("target")
parser.add_argument("start_port", type=int)
parser.add_argument("end_port", type=int)
parser.add_argument("--seconds", type=float, default=10.0)
args = parser.parse_args()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 41000))
sequence = {port: 0 for port in range(args.start_port, args.end_port + 1)}

sent = 0
deadline = time.monotonic() + args.seconds
while time.monotonic() < deadline:
    for port in sequence:
        seq = sequence[port]
        packet = struct.pack("!BBHII", 0x80, 0, seq, seq * 160, 0x51515151)
        packet += b"\x11" * 160
        sock.sendto(packet, (args.target, port))
        sequence[port] = (seq + 1) & 0xffff
        sent += 1
print(f"sent={sent}")
