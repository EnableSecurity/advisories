package main

import (
	"bytes"
	"flag"
	"fmt"
	"math/rand"
	"net"
	"strconv"
	"strings"
	"time"
)

const charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

func init() {
	rand.Seed(time.Now().UnixNano())
}

func randstr(length int) string {
	b := make([]byte, length)
	for i := range b {
		b[i] = charset[rand.Intn(len(charset))]
	}
	return string(b)
}

type loop struct {
	host   string
	port   int
	conn   net.Conn
	invite []byte
	cseq   int
}

func (l *loop) start() {
	sdp := "v=0\r\n"
	sdp += "o=- 1598350717 1598350717 IN IP4 192.168.1.112\r\n"
	sdp += "s=-\r\n"
	sdp += "c=IN IP4 192.168.1.112\r\n"
	sdp += "t=0 0\r\n"
	sdp += "m=audio 9999 RTP/AVP 0\r\n"
	sdp += "a=rtpmap:0 PCMU/8000/1\r\n"
	sdp += "a=sendrecv\r\n"

	invite := "INVITE sip:5cb49ced@127.0.0.1:5060 SIP/2.0\r\n"
	invite += "Via: SIP/2.0/UDP 192.168.1.112:44896;rport;branch=z9hG4bK-_BRANCH_\r\n"
	invite += "Max-Forwards: 70\r\n"
	invite += "From: <sip:5cb49ced@127.0.0.1:5060>;tag=2k309f\r\n"
	invite += "To: <sip:5cb49ced@127.0.0.1:5060>\r\n"
	invite += "Call-ID: 2345908ux\r\n"
	invite += "CSeq: _CSEQ_ INVITE\r\n"
	invite += "Contact: <sip:5cb49ced@192.168.1.112:44896;transport=udp>\r\n"
	invite += fmt.Sprintf("Content-Length: %d\r\n", len(sdp))
	invite += "Content-Type: application/sdp\r\n"
	invite += "\r\n"
	invite += sdp

	l.invite = []byte(invite)

	var err error
	l.conn, err = net.DialTimeout("tcp4", fmt.Sprintf("%s:%d", l.host, l.port), 5*time.Second)
	if err != nil {
		fmt.Println(err.Error())
		time.Sleep(10 * time.Millisecond)
		go l.start()
		return
	}

	if l.conn != nil {
		l.run()
	} else {
		time.Sleep(10 * time.Millisecond)
		go l.start()
	}
}

func (l *loop) run() {
	if err := l.conn.SetWriteDeadline(time.Now().Add(10 * time.Millisecond)); err != nil {
		if strings.Contains(err.Error(), "use of closed network connection") {
			l.start()
		}

	}

	var err error
	for {
		l.cseq++
		inv := l.invite
		inv = bytes.ReplaceAll(inv, []byte("_BRANCH_"), []byte(randstr(8)))
		inv = bytes.ReplaceAll(inv, []byte("_CSEQ_"), []byte(strconv.Itoa(l.cseq)))

		if _, err = l.conn.Write(inv); err != nil {
			go l.start()
			return
		}
	}
}

func main() {
	var port = flag.Int("p", 5060, "Port")
	var host = flag.String("h", "127.0.0.1", "Host")
	flag.Parse()

	for i := 0; i < 100; i++ {
		go func() {
			l := loop{
				host: *host,
				port: *port,
			}
			l.start()
		}()
	}
	select {}
}
