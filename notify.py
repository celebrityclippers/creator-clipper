import os
import sys
import json
import urllib.request

def send_discord_status(status_type, message_details):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("⚠️ Warning: DISCORD_WEBHOOK_URL environment variable is missing.")
        return

    color_map = {"SUCCESS": 3066993, "FAILURE": 15158332, "START": 3447003}
    color = color_map.get(status_type.upper(), 8421504)

    payload = {
        "username": "AI Clipper Bot",
        "avatar_url": "https://githubassets.com",
        "embeds": [
            {
                "title": f"🎬 Pipeline Status Alert: {status_type.upper()}",
                "description": message_details,
                "color": color,
                "footer": {
                    "text": "Automated Cloud Workspace Engine"
                }
            }
        ]
    }

    req = urllib.request.Request(
        webhook_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    )

    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 204:
                print("🔔 Discord notification delivered successfully.")
    except Exception as e:
        print(f"❌ Failed to deliver Discord status webhook: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        send_discord_status(sys.argv[1], sys.argv[2])
    else:
        send_discord_status("START", "The automated video clipping engine has been triggered on the cloud.")
