#!/bin/bash
set -e

# Start the WARP daemon
warp-svc &
sleep 2

# Register and set proxy mode (no TUN/NET_ADMIN needed)
warp-cli --accept-tos registration new 2>/dev/null || true
warp-cli --accept-tos mode proxy
warp-cli --accept-tos connect

# Wait for WARP to connect (up to 15s)
for i in $(seq 1 15); do
    if warp-cli --accept-tos status 2>/dev/null | grep -q "Connected"; then
        echo "WARP connected!"
        break
    fi
    echo "Waiting for WARP... ($i)"
    sleep 1
done

# Route all traffic through WARP's local SOCKS5 proxy
export ALL_PROXY=socks5h://127.0.0.1:40000
export HTTPS_PROXY=socks5h://127.0.0.1:40000
export HTTP_PROXY=socks5h://127.0.0.1:40000

echo "Starting Flask server..."
exec python server.py
