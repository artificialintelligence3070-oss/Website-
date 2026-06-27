import os
import json
import secrets
import requests
from datetime import datetime
from dateutil import parser
from flask import Flask, request, jsonify, render_template_string
import telebot

app = Flask(__name__)

# --- CONFIGURATIONS ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "8842248531:AAFLjUKst9mYf2IJgP2j4sSK4p_B5tymkik")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8505747325"))  # आपकी Telegram User ID
TARGET_API_BASE = "https://ft-osint-api.duckdns.org/api"
UPSTREAM_DEFAULT_KEY = "vernex-6a9dc4fdd5923c40b0aba27bf1e39e3f"

# Vercel KV REST API Credentials (इसे Environment Variables से लिया जाएगा)
KV_URL = os.getenv("KV_REST_API_URL")
KV_TOKEN = os.getenv("KV_REST_API_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

SUPPORTED_TOOLS = [
    "adv", "paytm", "imei", "calltracer", "upi", "ifsc", 
    "number", "pincode", "ip", "challan", "ff", "bgmi", 
    "snap", "email", "vehicle", "git", "insta", "tg", 
    "tgidinfo", "numleak", "pan", "adharfamily", "aadhar"
]

# --- VERCEL KV (REDIS) HELPER FUNCTIONS ---
def query_kv(command, *args):
    """Vercel KV Rest API के जरिए Redis से कम्युनिकेट करने का फंक्शन"""
    if not KV_URL or not KV_TOKEN:
        # लोकल फॉलबैक (अगर क्लाउड कनेक्टेड न हो)
        return None
    headers = {"Authorization": f"Bearer {KV_TOKEN}"}
    url = f"{KV_URL}/{command}/" + "/".join(map(str, args))
    try:
        res = requests.get(url, headers=headers)
        return res.json().get("result")
    except Exception:
        return None

def load_db():
    """KV Redis से डेटाबेस लोड करना"""
    db_str = query_kv("get", "gateway_db")
    if db_str:
        return json.loads(db_str)
    
    # डिफॉल्ट स्ट्रक्चर अगर KV खाली है
    default_db = {
        "keys": {
            "SHAYAN-MASTER": {
                "name": "Master Enterprise Dev",
                "key": "SHAYAN-MASTER",
                "expire_date": "2026-12-31T23:59",
                "limit": 1000,
                "used": 0,
                "status": "Active",
                "tools": ["all"]
            }
        },
        "logs": []
    }
    save_db(default_db)
    return default_db

def save_db(data):
    """KV Redis में परमानेंटली डेटा सेव करना"""
    if not KV_URL or not KV_TOKEN:
        return
    headers = {"Authorization": f"Bearer {KV_TOKEN}"}
    url = f"{KV_URL}/set/gateway_db"
    try:
        requests.post(url, headers=headers, data=json.dumps(data))
    except Exception as e:
        print(f"Error saving to Vercel KV: {e}")

def check_key_validity(db, api_key, tool_name):
    if api_key not in db["keys"]:
        return False, "KEY_NOT_FOUND"
    key_data = db["keys"][api_key]
    if key_data.get("status", "Active") == "Suspended":
        return False, "This API access footprint has been explicitly suspended."
    try:
        expire_dt = parser.parse(key_data["expire_date"])
        if datetime.now() > expire_dt:
            return False, f"API Key expired automatically on {key_data['expire_date']}."
    except Exception:
        return False, "System runtime token configuration parse exception."
    if int(key_data["used"]) >= int(key_data["limit"]):
        return False, f"Allocated quota threshold limit reached ({key_data['limit']})."
    allowed_tools = key_data.get("tools", [])
    if "all" not in allowed_tools and tool_name not in allowed_tools:
        return False, f"Access denied for router parameter: '{tool_name}'."
    return True, key_data

# --- TELEGRAM BOT WEBHOOK & LOGIC HANDLING ---
@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    """Vercel पर टेलीग्राम बोट की रिक्वेस्ट हैंडल करने के लिए Webhook रूट"""
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'Invalid Trigger', 400

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome = (
        "🤖 *SHAYAN_EXPLORER Cloud Gateway*\n\n"
        "🔑 `/query <key> <tool> <value>` - Run API lookup\n"
        "📊 `/status <key>` - Check token usage\n"
    )
    if message.from_user.id == ADMIN_ID:
        welcome += (
            "\n👑 *Admin Tools:*\n"
            "➕ `/genkey <name> <limit>` - Provision Key\n"
            "❌ `/delkey <key>` - Wipe Token"
        )
    bot.reply_to(message, welcome, parse_mode="Markdown")

@bot.message_handler(commands=['status'])
def key_status(message):
    args = message.text.split()
    if len(args) < 2: return bot.reply_to(message, "⚠️ Usage: `/status <key>`")
    db = load_db()
    key_id = args[1]
    if key_id not in db["keys"]: return bot.reply_to(message, "❌ Key not found.")
    k = db["keys"][key_id]
    bot.reply_to(message, f"👤 *Name:* {k['name']}\n📊 *Usage:* {k['used']}/{k['limit']}\n⚡ *Status:* {k['status']}", parse_mode="Markdown")

@bot.message_handler(commands=['query'])
def run_query(message):
    args = message.text.split()
    if len(args) < 4: return bot.reply_to(message, "⚠️ Usage: `/query <key> <tool> <value>`")
    user_key, tool, value = args[1], args[2].lower(), " ".join(args[3:])
    
    if tool not in SUPPORTED_TOOLS: return bot.reply_to(message, "❌ Invalid tool.")
    db = load_db()
    is_valid, result = check_key_validity(db, user_key, tool)
    if not is_valid: return bot.reply_to(message, f"🚫 {result}")

    param_key = 'num'
    if tool in ['email']: param_key = 'email'
    elif tool in ['vehicle']: param_key = 'vehicle'
    elif tool in ['pan']: param_key = 'pan'

    try:
        res = requests.get(f"{TARGET_API_BASE}/{tool}", params={'key': UPSTREAM_DEFAULT_KEY, param_key: value}, timeout=10)
        if res.status_code == 200:
            db["keys"][user_key]["used"] += 1
            save_db(db)
            bot.reply_to(message, f"✅ *Result:*\n```json\n{json.dumps(res.json(), indent=2)}\n```", parse_mode="Markdown")
        else:
            bot.reply_to(message, f"❌ Failed (HTTP {res.status_code})")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['genkey'])
def generate_key(message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 3: return bot.reply_to(message, "⚠️ `/genkey <name> <limit>`")
    name, limit = args[1], int(args[2])
    db = load_db()
    hex_secret = 'SHAYAN-' + secrets.token_hex(6).upper()
    db["keys"][hex_secret] = {
        "name": name, "key": hex_secret, "expire_date": "2026-12-31T23:59",
        "limit": limit, "used": 0, "status": "Active", "tools": ["all"]
    }
    save_db(db)
    bot.reply_to(message, f"✨ *Generated!* \nKey: `{hex_secret}`", parse_mode="Markdown")

@bot.message_handler(commands=['delkey'])
def delete_key(message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 2: return bot.reply_to(message, "⚠️ `/delkey <key>`")
    db = load_db()
    if args[1] in db["keys"]:
        del db["keys"][args[1]]
        save_db(db)
        bot.reply_to(message, "🗑️ Deleted.")

# --- FLASK API ROUTES (HTTP GATEWAY) ---
@app.route('/')
def home():
    return jsonify({"status": "running", "developer": "SHAYAN_EXPLORER"})

@app.route('/api/<tool>', methods=['GET'])
def proxy_gateway(tool):
    if tool not in SUPPORTED_TOOLS:
        return jsonify({"status": "error", "message": "Invalid Route."}), 404
    user_key = request.args.get('key')
    if not user_key:
        return jsonify({"status": "error", "message": "Missing key."}), 401
    
    db = load_db()
    is_valid, result = check_key_validity(db, user_key, tool)
    if not is_valid:
        return jsonify({"status": "error", "message": result}), 403

    upstream_params = dict(request.args)
    upstream_params['key'] = UPSTREAM_DEFAULT_KEY

    try:
        response = requests.get(f"{TARGET_API_BASE}/{tool}", params=upstream_params, timeout=12)
        response_data = response.json()
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    if response.status_code == 200:
        db["keys"][user_key]["used"] += 1
        save_db(db)

    return jsonify(response_data), response.status_code
