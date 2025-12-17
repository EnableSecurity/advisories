package main

import (
	"context"
	"flag"
	"log/slog"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/emiago/sipgo"
	"github.com/emiago/sipgo/sip"
)

func main() {
	addr := flag.String("addr", "127.0.0.1:5060", "Listen address")
	transport := flag.String("transport", "udp", "Transport (udp, tcp, tls)")
	debug := flag.Bool("debug", false, "Enable SIP debug logging")
	flag.Parse()

	if *debug {
		sip.SIPDebug = true
	}

	log := slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{
		Level: slog.LevelInfo,
	}))

	log.Info("Starting vulnerable sipgo server", 
		"addr", *addr, 
		"transport", *transport,
		"version", "vulnerable to ES2025-02")

	// Create User Agent
	ua, err := sipgo.NewUA(
		sipgo.WithUserAgent("VulnerableSipGo/1.0"),
	)
	if err != nil {
		log.Error("Failed to create user agent", "error", err)
		os.Exit(1)
	}
	defer ua.Close()

	// Create Server
	srv, err := sipgo.NewServer(ua)
	if err != nil {
		log.Error("Failed to create server", "error", err)
		os.Exit(1)
	}

	// Handle REGISTER requests (most common trigger)
	srv.OnRegister(func(req *sip.Request, tx sip.ServerTransaction) {
		log.Info("Received REGISTER request", "from", req.From(), "to", req.To())
		
		// VULNERABLE CODE: This will crash if To header is missing
		// The NewResponseFromRequest function calls res.To().Params["tag"] 
		// without checking if res.To() returns nil
		res := sip.NewResponseFromRequest(req, 200, "OK", nil)
		
		if err := tx.Respond(res); err != nil {
			log.Error("Failed to send response", "error", err)
		}
		
		log.Info("Sent 200 OK response")
	})

	// Handle INVITE requests (also vulnerable)
	srv.OnInvite(func(req *sip.Request, tx sip.ServerTransaction) {
		log.Info("Received INVITE request", "from", req.From(), "to", req.To())
		
		// VULNERABLE CODE: Also crashes on missing To header
		res := sip.NewResponseFromRequest(req, 200, "OK", nil)
		
		if err := tx.Respond(res); err != nil {
			log.Error("Failed to send response", "error", err)
		}
		
		log.Info("Sent 200 OK response")
	})

	// Handle OPTIONS requests (also vulnerable)
	srv.OnOptions(func(req *sip.Request, tx sip.ServerTransaction) {
		log.Info("Received OPTIONS request", "from", req.From(), "to", req.To())
		
		// VULNERABLE CODE: Also crashes on missing To header
		res := sip.NewResponseFromRequest(req, 200, "OK", nil)
		
		if err := tx.Respond(res); err != nil {
			log.Error("Failed to send response", "error", err)
		}
		
		log.Info("Sent 200 OK response")
	})

	// Note: OnRegister, OnInvite, OnOptions handlers above will catch most requests
	// Any other SIP methods will still be vulnerable if they trigger NewResponseFromRequest

	// Setup graceful shutdown
	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer cancel()

	log.Info("Server starting...", "listening", *addr)
	
	// Start server in goroutine
	go func() {
		if err := srv.ListenAndServe(ctx, *transport, *addr); err != nil {
			log.Error("Server error", "error", err)
			cancel()
		}
	}()

	// Wait for shutdown signal
	<-ctx.Done()
	log.Info("Shutting down server...")
	
	// Give server time to clean up
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer shutdownCancel()
	
	<-shutdownCtx.Done()
	log.Info("Server stopped")
}