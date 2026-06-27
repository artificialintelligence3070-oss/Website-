import os
import json
import secrets
import requests
from datetime import datetime
from dateutil import parser
from flask import Flask, request, jsonify
import telebot

app = Flask(__name__)

# --- HARDCODED CREDENTIALS ---
BOT_TOKEN = "8842248531:AAFLjUKst9mYf2IJgP2j4sSK4p_B5tymkik"
ADMIN_ID = 8505747325

TARGET_API_BASE = "https://ft-osint-api.duckdns.org/api"
UPSTREAM_DEFAULT_KEY = "vernex-6a9dc4fdd5923c40b0aba27bf1e39e3f"

KV_URL = os.getenv("KV_REST_API_URL")
KV_TOKEN = os.getenv("KV_REST_API_TOKEN")

# threaded=False is strictly required for Vercel Serverless
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

SUPPORTED_TOOLS = [
    "adv", "paytm", "imei", "calltracer", "upi", "ifsc", 
    "number", "pincode", "ip", "challan", "ff", "bgmi", 
    "snap", "email", "vehicle", "git", "insta", "tg", 
    "tgidinfo", "numleak", "pan", "adharfamily", "aadhar"
]

# --- SAFE MEMORY FALLBACK IF KV IS NOT CONNECTED ---
LOCAL_MEMORY_DB = {
    "keys": {
        "SHAYAN-MASTER": {
            "name": "Master Enterprise Dev",
            "key": "SHAYAN-MASTER",
            "expire_date": "2026-12-31T23:59",
            "limit": 5000,
            "used": 0,
            "status": "Active",
            "tools": ["all"]
        }
    },
    "logs": []
}

# --- DATA MANAGEMENT ---
def load_db():
    if not KV_URL or not KV_TOKEN:
        return LOCAL_MEMORY_DB
    headers = {"Authorization": f"Bearer {KV_TOKEN}"}
    try:
        res = requests.get(f"{KV_URL}/get/gateway_db", headers=headers, timeout=5)
        result = res.json().get("result")
        if result:
            return json.loads(result)
    except Exception as e:
        print(f"KV Load Error: {e}")
    return LOCAL_MEMORY_DB

def save_db(data):
    if not KV_URL or not KV_TOKEN:
        return
    headers = {"Authorization": f"Bearer {KV_TOKEN}"}
    try:
        requests.post(f"{KV_URL}/set/gateway_db", headers=headers, data=json.dumps(data), timeout=5)
    except Exception as e:
        print(f"KV Save Error: {e}")

def check_key_validity(db, api_key, tool_name):
    if api_key not in db["keys"]:
        return False, "KEY_NOT_FOUND"
    key_data = db["keys"][api_key]
    if key_data.get("status", "Active") == "Suspended":
        return False, "This API access has been suspended."
    try:
        expire_dt = parser.parse(key_data["expire_date"])
        if datetime.now() > expire_dt:
            return False, f"API Key expired on {key_data['expire_date']}."
    except Exception:
        return False, "Token parsing error."
    if int(key_data["used"]) >= int(key_data["limit"]):
        return False, f"Quota limit reached ({key_data['limit']})."
    allowed_tools = key_data.get("tools", [])
    if "all" not in allowed_tools and tool_name not in allowed_tools:
        return False, f"Access denied for tool: '{tool_name}'."
    return True, key_data

# --- TELEGRAM WEBHOOK ROUTE ---
@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    if request.headers.get('content-type') == 'application/json':
        try:
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return '', 200
        except Exception as e:
            print(f"Webhook Processing Error: {e}")
            return jsonify({"error": str(e)}), 500
    return 'Invalid Framework Trigger', 400

# --- TELEGRAM BOT COMMAND HANDLERS ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome = (
        "🤖 *SHAYAN_EXPLORER Live Cloud Gateway*\n\n"
        "🔑 `/query <key> <tool> <value>` - Run API lookup\n"
        "📊 `/status <key>` - Check token usage\n"
    )
    if message.from_user.id == ADMIN_ID:
        welcome += (
            "\n👑 *Admin Control Panel:*\n"
            "➕ `/genkey <name> <limit>` - Provision New Key\n"
            "❌ `/delkey <key>` - Delete Key\n"
            "📋 `/stats` - View System Registry Overview"
        )
    bot.reply_to(message, welcome, parse_mode="Markdown")

@bot.message_handler(commands=['status'])
def key_status(message):
    args = message.text.split()
    if len(args) < 2: 
        return bot.reply_to(message, "⚠️ Usage: `/status <key>`")
    db = load_db()
    key_id = args[1]
    if key_id not in db["keys"]: 
        return bot.reply_to(message, "❌ Key not found in system registry.")
    k = db["keys"][key_id]
    bot.reply_to(message, f"👤 *Client Name:* {k['name']}\n📊 *Usage Consumption:* {k['used']}/{k['limit']}\n⚡ *Status:* {k['status']}", parse_mode="Markdown")

@bot.message_handler(commands=['query'])
def run_query(message):
    args = message.text.split()
    if len(args) < 4: 
        return bot.reply_to(message, "⚠️ Usage: `/query <key> <tool> <value>`")
    user_key, tool, value = args[1], args[2].lower(), " ".join(args[3:])
    
    if tool not in SUPPORTED_TOOLS: 
        return bot.reply_to(message, f"❌ Invalid tool module. Supported:\n`{', '.join(SUPPORTED_TOOLS)}`", parse_mode="Markdown")
    
    db = load_db()
    is_valid, result = check_key_validity(db, user_key, tool)
    if not is_valid: 
        return bot.reply_to(message, f"🚫 {result}")

    # Tool dynamic parameters selector mapping
    param_key = 'num'
    if tool in ['email']: param_key = 'email'
    elif tool in ['vehicle']: param_key = 'vehicle'
    elif tool in ['pan']: param_key = 'pan'
    elif tool in ['ip']: param_key = 'ip'
    elif tool in ['ifsc']: param_key = 'ifsc'

    try:
        res = requests.get(f"{TARGET_API_BASE}/{tool}", params={'key': UPSTREAM_DEFAULT_KEY, param_key: value}, timeout=12)
        if res.status_code == 200:
            db["keys"][user_key]["used"] += 1
            save_db(db)
            
            pretty_json = json.dumps(res.json(), indent=2, ensure_ascii=False)
            if len(pretty_json) > 4000:
                with open("response.json", "w", encoding="utf-8") as f:
                    f.write(pretty_json)
                with open("response.json", "rb") as f:
                    bot.send_document(message.chat.id, f, caption="📦 Big dataset object output payload:")
                os.remove("response.json")
            else:
                bot.reply_to(message, f"✅ *Data Stream Received:*\n```json\n{pretty_json}\n```", parse_mode="Markdown")
        else:
            bot.reply_to(message, f"❌ Request failed on upstream server (HTTP {res.status_code})")
    except Exception as e:
        bot.reply_to(message, f"❌ API Connection Timeout/Error: {str(e)}")

@bot.message_handler(commands=['genkey'])
def generate_key(message):
    if message.from_user.id != ADMIN_ID: 
        return bot.reply_to(message, "🚫 Admin only command.")
    args = message.text.split()
    if len(args) < 3: 
        return bot.reply_to(message, "⚠️ Usage: `/genkey <name> <limit>`")
    name, limit = args[1], int(args[2])
    db = load_db()
    hex_secret = 'SHAYAN-' + secrets.token_hex(6).upper()
    db["keys"][hex_secret] = {
        "name": name, "key": hex_secret, "expire_date": "2026-12-31T23:59",
        "limit": limit, "used": 0, "status": "Active", "tools": ["all"]
    }
    save_db(db)
    bot.reply_to(message, f"✨ *Generated successfully!*\n\n👤 *Client:* {name}\n🔑 *Key:* `{hex_secret}`\n📊 *Limit:* {limit}", parse_mode="Markdown")

@bot.message_handler(commands=['delkey'])
def delete_key(message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 2: 
        return bot.reply_to(message, "⚠️ `/delkey <key>`")
    db = load_db()
    if args[1] in db["keys"]:
        del db["keys"][args[1]]
        save_db(db)
        bot.reply_to(message, "🗑️ Key Wiped.")

@bot.message_handler(commands=['stats'])
def get_stats(message):
    if message.from_user.id != ADMIN_ID: return
    db = load_db()
    bot.reply_to(message, f"📊 *Database Registry Metrics:*\nTotal Active Keys: {len(db['keys'])}")

# --- FLASK ENVIRONMENT ROOT ROUTE ---
@app.route('/')
def home():
    return jsonify({"status": "running", "gateway": "SHAYAN_EXPLORER"})

if __name__ == '__main__':
    app.run(debug=True)
