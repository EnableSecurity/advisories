INVITE {{.RequestURI}} SIP/2.0
Via: SIP/2.0/{{.AddrFamily}} {{.LocalAddr}};rport;branch=z9hG4bK-{{.Branch}}
Max-Forwards: 70
From: {{.FromVal}}
To: {{.ToVal}}
Call-ID: {{.CallID}}
CSeq: {{.CSeq}} INVITE
Contact: {{.ContactVal}}
Content-Length: {{.Body | len}}
X-Bypass-me : yes please
Content-Type: application/sdp

{{.Body -}}
