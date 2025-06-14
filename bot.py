import os
import json
import random
import asyncio
from datetime import datetime, timedelta
from telethon import TelegramClient, events
from telethon.errors import RPCError

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [6249999953]  # Add your Telegram user ID(s) here

DATA_FILE = "data.json"

client = TelegramClient("sessions/bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Load data or create new
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
else:
    data = {"start": True, "ads": [], "groups": [], "admins": ADMIN_IDS}

# Save data after any update
def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# Get uptime
start_time = datetime.now()

def get_uptime():
    delta = datetime.now() - start_time
    return str(delta).split('.')[0]  # Remove microseconds

# Handler for new messages
@client.on(events.NewMessage)
async def handler(event):
    try:
        sender = None
        try:
            sender = await event.get_sender()
        except Exception as e:
            print(f"[!] Failed to get sender: {e}")

        if event.is_private:
            sender_id = event.sender_id
            message = event.raw_text.strip()

            # Help
            if message.lower() in ["/help", "!help"]:
                await event.reply("📢 AdBot Commands:\n!start / !stop / !uptime / !status / !test / !preview\n!addgroup <id>\n!setfreq <min>\n!setmode random/order")

            # Start ads
            elif message.startswith("!start") and sender_id in data["admins"]:
                data["start"] = True
                save_data()
                await event.reply("✅ Ad sending started.")

            # Stop ads
            elif message.startswith("!stop") and sender_id in data["admins"]:
                data["start"] = False
                save_data()
                await event.reply("⛔ Ad sending stopped.")

            # Uptime
            elif message.startswith("!uptime"):
                await event.reply(f"⏱ Bot has been running for: `{get_uptime()}`")

            # Status
            elif message.startswith("!status"):
                await event.reply(f"📊 Mode: {data.get('mode', 'order')}\nGroups: {len(data['groups'])}\nGlobal Frequency: {data.get('global_freq', 60)} min")

            # Test
            elif message.startswith("!test") and data.get("ads"):
                ad = data["ads"][-1]
                await event.reply("📢 Previewing latest ad:")
                await client.send_message(sender_id, ad)

            # Add group (manual)
            elif message.startswith("!addgroup") and sender_id in data["admins"]:
                try:
                    group_id = int(message.split()[1])
                    if group_id not in data["groups"]:
                        data["groups"].append(group_id)
                        save_data()
                        await event.reply(f"✅ Group `{group_id}` added.")
                    else:
                        await event.reply("⚠️ Group already added.")
                except Exception:
                    await event.reply("❌ Invalid command. Use `!addgroup <group_id>`")

    except Exception as e:
        print(f"[!!] Exception in handler: {e}")

# Background task: send ads
async def ad_sender():
    while True:
        if data["start"] and data.get("ads") and data.get("groups"):
            ad_index = random.randint(0, len(data["ads"]) - 1) if data.get("mode") == "random" else 0
            ad = data["ads"][ad_index]
            for group in data["groups"]:
                try:
                    await client.send_message(group, ad)
                    print(f"✅ Sent ad to {group}")
                    await asyncio.sleep(data.get("global_freq", 60) * 60)  # Frequency in minutes
                except RPCError as e:
                    print(f"⚠️ Failed to send to {group}: {e}")
        else:
            await asyncio.sleep(30)

# Run everything
async def main():
    print("🤖 Bot started.")
    await client.start()
    client.loop.create_task(ad_sender())
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("👋 Bot stopped.")
