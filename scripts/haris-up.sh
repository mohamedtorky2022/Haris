#!/bin/zsh
# Start Haris on this Mac: the server, a Cloudflare quick tunnel, no sleep, and point
# Meta's WhatsApp webhook at the tunnel's new address. Run from anywhere:
#   ~/Desktop/Haseen/scripts/haris-up.sh
# Secrets are read from .env and never printed.
set -u
ROOT="${0:A:h:h}"
cd "$ROOT" || exit 1
pkill -f "uvicorn app.main:app" 2>/dev/null
pkill -f "cloudflared tunnel --no-autoupdate --url http://localhost:8000" 2>/dev/null
sleep 1
(cd backend && nohup ../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --env-file ../.env > /tmp/haris-server.log 2>&1 &)
nohup ./tools/cloudflared tunnel --no-autoupdate --url http://localhost:8000 > /tmp/haris-tunnel.log 2>&1 &
pgrep -x caffeinate >/dev/null || nohup caffeinate -dimsu -t 864000 >/dev/null 2>&1 &
URL=""
for i in {1..30}; do
  URL=$(grep -oE "https://[a-z0-9-]+\.trycloudflare\.com" /tmp/haris-tunnel.log | head -1)
  [[ -n "$URL" ]] && break
  sleep 1
done
[[ -z "$URL" ]] && { echo "The tunnel did not start; see /tmp/haris-tunnel.log"; exit 1; }
for i in {1..20}; do curl -s -m 5 -o /dev/null "$URL/api/health" && break; sleep 2; done
.venv/bin/python - "$URL" <<'PY'
import json, sys, urllib.error, urllib.parse, urllib.request
env = {}
for line in open(".env"):
    if "=" in line and not line.startswith("#"):
        k, v = line.rstrip("\n").split("=", 1)
        env[k] = v.strip().strip('"')
app = env.get("WHATSAPP_APP_ID", "2177505529820595")
token = f"{app}|{env['WHATSAPP_APP_SECRET']}"
data = urllib.parse.urlencode({"object": "whatsapp_business_account", "callback_url": sys.argv[1] + "/webhook/whatsapp",
                               "fields": "messages", "verify_token": env["WHATSAPP_VERIFY_TOKEN"], "include_values": "true"}).encode()
req = urllib.request.Request(f"https://graph.facebook.com/v26.0/{app}/subscriptions", data=data, method="POST",
                             headers={"Authorization": "Bearer " + token})
try:
    ok = json.load(urllib.request.urlopen(req, timeout=30)).get("success")
except urllib.error.HTTPError as e:
    ok = False
    print("Meta refused the webhook:", json.loads(e.read().decode()).get("error", {}).get("message"))
print("WhatsApp webhook updated" if ok else "WhatsApp webhook NOT updated")
PY
echo "Haris is up: $URL"
echo "Dashboard:   $URL/reports.html"
