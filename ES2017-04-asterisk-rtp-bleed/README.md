# Asterisk vulnerable to RTP Bleed

- Authors: 
	- Klaus-Peter Junghanns <kapejod@gmail.com>
	- Sandro Gauci <sandro@enablesecurity.com>
- Vulnerable version: Asterisk 11.4.0 to 14.6.1 (fix incomplete)
- References: AST-2017-005, CVE-2017-14099
- Advisory URL: <https://github.com/EnableSecurity/advisories/tree/master/ES2017-04-asterisk-rtp-bleed>
- Timeline:
	- First report date: 2011-09-11
	- Fix applied: [2011-09-21](https://issues.asterisk.org/jira/browse/ASTERISK-18587)
	- Issue apparently reintroduced: [2013-03-07](https://github.com/asterisk/asterisk/commit/80b8c2349c427a94a428670f1183bdc693936813)
    - New report date: 2017-05-17
    - Vendor patch provided for testing: 2017-05-23
    - Vendor advisory: 2017-08-31
    - Enable Security advisory: 2017-09-01

## Description

When Asterisk is configured with the `nat=yes` and `strictrtp=yes` (on by default) options, it is vulnerable to an attack which we call RTP Bleed. Further information about the attack can be found at <https://rtpbleed.com>.

## Impact

Abuse of this attack allows malicious users to inject and receive RTP streams of ongoing calls **without** needing to be positioned as man-in-the-middle. As a result, in the case of an RTP stream containing audio media, attackers can inject their own audio and receive audio being proxied through the Asterisk server.

## How to reproduce the issue

The vulnerability can be exploited when a call is taking place and the RTP is being proxied. To exploit this issue, an attacker needs to send RTP packets to the Asterisk server on one of the ports allocated to receive RTP. When the target is vulnerable, the RTP proxy responds back to the attacker with RTP packets relayed from the other party. The payload of the RTP packets can then be decoded into audio.

This issue can be reproduced by making use of [rtpnatscan](https://github.com/kapejod/rtpnatscan) (freely available) or [SIPVicious PRO](https://sipvicious.pro) (will be commercially available).


## Solutions and recommendations

We have the following recommendations:

- It is recommended to apply the fix issued by Asterisk which limits the window of vulnerability to the first few milliseconds. 
- When possible the `nat=yes` option should be avoided.
- To protect against RTP injection the media streams should be encrypted (and authenticated) with SRTP.
- A configuration option for SIP peers should be added that allows to prioritize RTP packets coming from the IP address learned through SIP signalling during the initial probation period.

Note that as for the time of writing, the official Asterisk fix is vulnerable to a race condition. An attacker may continuously _spray_ an Asterisk server with RTP packets. This allows the attacker to send RTP within those first few packets and still exploit this vulnerability.

The official Asterisk fix also does not properly validate very short RTCP packets (e.g. 4 octets, see [rtcpnatscan](https://github.com/kapejod/rtpnatscan) to reproduce the problem) resulting in an out of bounds read disabling SSRC matching.
This makes Asterisk vulnerable to RTCP hijacking of **ongoing** calls. An attacker can extract RTCP sender reports containing the SSRCs of both RTP endpoints.

A patch for this is available at (https://raw.githubusercontent.com/kapejod/rtpnatscan/master/patches/asterisk/too-short-rtcp-bugfix.diff)

## References

- [Kamailio World 2017: Listening By Speaking - Security Attacks On Media Servers And RTP Relays](https://www.youtube.com/watch?v=cAia1owHy68)
- [27C3: Having fun with RTP by Kapejod](https://www.youtube.com/watch?v=cp7VDRC-RcY)


## About Enable Security

[Enable Security](https://www.enablesecurity.com) provides Information Security services, including Penetration Testing, Research and Development, to help protect client networks and applications against online attackers.

## Disclaimer

The information in the advisory is believed to be accurate at the time of publishing based on currently available information. Use of the information constitutes acceptance for use in an AS IS condition. There are no warranties with regard to this information. Neither the author nor the publisher accepts any liability for any direct, indirect, or consequential loss or damage arising from use of, or reliance on, this information.

