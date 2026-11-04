# FreeSWITCH: RTP Bleed and RTP Inject through unvalidated source learning

Full advisory: <https://www.enablesecurity.com/advisories/ES2026-07-freeswitch-rtp-inject-rtp-bleed/>

CVE-2026-119293 / [vendor advisory](https://github.com/signalwire/freeswitch/security/advisories/GHSA-cw2f-3w8g-4x9q).

## Before and after mitigation

| Build | RTP source-learning controls | Example Compose run (linux/arm64, 2026-11-04) |
|---|---|---|
| 1.10.12 (`a88d069d6ffb`) | Not available | Attacker-marker echo packets: 19; legitimate-marker echo packets: 0. |
| 1.11.2 (`3f13ad1b1d32`) | Both at default zero values | Attacker-marker echo packets: 20; legitimate-marker echo packets: 0. **Upgrading alone is not a fix.** |
| 1.11.2 (`3f13ad1b1d32`) | Both set before RTP session creation | Attacker-marker echo packets: 0; legitimate-marker echo packets: 30. |

The last row is a **configured mitigation**, not a default fixed release or proof of zero media disclosure. In an earlier linux/amd64 test, two transient outbound packets still reached the attacker before source confirmation; the example Compose run above observed none. Values `rtp_auto_adjustment_wait_for_advertised_ms=3000` and `rtp_packet_not_advertised_reject_threshold=5` are lab settings, not universal production defaults.

## Docker Compose comparison

The self-contained Compose lab builds the exact public FreeSWITCH v1.10.12 and v1.11.2 tags for the host's Docker platform, checks the checked-out commits against the hashes above, and starts one target at a time. `before` uses v1.10.12, `after-default` uses v1.11.2 with both controls at zero, and `after-configured` uses the *same* v1.11.2 image with both controls set before media session creation. The target, attacker, and SIP caller run as separate containers on a dedicated Compose bridge network; **no host ports are published**.

From this directory, with Docker Compose v2 and enough disk/time for two source builds:

```bash
docker compose build before after-default
./run.sh before
./run.sh after-default
./run.sh after-configured
```

Build both exact refs first; the two "after" services share the v1.11.2 image. Each run starts a 30-packet attacker probe, and places a non-ICE plaintext echo call from a separate caller container. The caller waits 400 ms after call setup before sending legitimate PCMU RTP. The same probe runs against all three cases. It prints the attacker and caller summaries and saves JSON plus target/attacker logs to the ignored `results/` directory. It tears down the Compose network and volumes even if a probe fails. Results are *local observations*, not an Internet exposure measurement.

The configured case routes to echo extension `5593`; the other two use unconfigured echo extension `5592`. The included `conf/` sets `inbound-late-negotiation=true` and limits the lab RTP range to `30000-30020`. On `5593`, both channel variables are set before `answer` and RTP session creation. The unconfigured cases do not set these variables. No SIP credentials, private container registries, or FreeSWITCH package tokens are needed.

Expected outcome: attacker media enters the vulnerable echo call; default v1.11.2 still permits attacker source learning; configured v1.11.2 accepts the advertised caller's RTP instead of the attacker's marker. As in the prior lab, a small amount of transient outbound media may still reach the attacker during the learning window. The exact packet totals depend on timing and should not be treated as guaranteed thresholds. Review the target logs if a build, SIP setup, or media check fails.

## Manual sender

`sprayrtp.py` is the bounded-range RTP sender printed in the [full advisory](https://www.enablesecurity.com/advisories/ES2026-07-freeswitch-rtp-inject-rtp-bleed/#how-to-reproduce-the-issue). It is **not** used by the Compose matrix, which uses the bounded `probe.py` caller and attacker pair instead. If testing manually on an isolated network you control, start the sender before the call:

```bash
python3 sprayrtp.py <freeswitch-ip> 30000 30020 --seconds 10
```

The manual script sends from UDP port 41000. It can generate roughly 1 Gbit/s in the isolated lab; do not run it against production or across shared networks. Stop the sender and any captures, hang up the call, and restore temporary configuration after testing.
