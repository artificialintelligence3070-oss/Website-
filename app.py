import os
import json
import secrets
import requests
import math
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
from datetime import datetime
from dateutil import parser
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = secrets.token_hex(24)

TARGET_API_BASE = "https://ft-osint-api.duckdns.org/api"
UPSTREAM_DEFAULT_KEY = "vernex-6a9dc4fdd5923c40b0aba27bf1e39e3f"

YOUR_UPI_ID = "your-upi-id@ybl"
BASE_PRICE_PER_DAY = 10 

# --- CLOUD DATABASE SYSTEM (MONGODB ATLAS) ---
# Replace this string with your real MongoDB Atlas connection URI
MONGO_URI = "YOUR_MONGODB_CONNECTION_STRING"

try:
    client = MongoClient(MONGO_URI)
    db = client["gateway_db"]
    keys_col = db["keys"]
    logs_col = db["logs"]
    users_col = db["users"]
    payments_col = db["payments"]
    
    # Initialize master key if collection is empty
    if keys_col.count_documents({"key": "SHAYAN-MASTER"}) == 0:
        keys_col.insert_one({
            "name": "Master Enterprise Dev",
            "key": "SHAYAN-MASTER",
            "expire_date": "2026-12-31T23:59",
            "limit": 1000,
            "used": 0,
            "status": "Active",
            "tools": ["all"]
        })
except Exception as e:
    print(f"MongoDB Connection Failure: {str(e)}")

SUPPORTED_TOOLS = [
    "adv", "paytm", "imei", "calltracer", "upi", "ifsc", 
    "number", "pincode", "ip", "challan", "ff", "bgmi", 
    "snap", "email", "vehicle", "git", "insta", "tg", 
    "tgidinfo", "numleak", "pan", "adharfamily", "aadhar"
]

# --- HTML TEMPLATES ---
HTML_AUTH = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gateway Access - {{ mode }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>body { background: radial-gradient(circle at top right, #0c071e, #020105); color: #f3f4f6; }</style>
</head>
<body class="min-h-screen flex items-center justify-center p-4">
    <div class="w-full max-w-md bg-white/5 border border-white/10 backdrop-blur-xl p-8 rounded-2xl shadow-xl space-y-6">
        <div class="text-center">
            <h2 class="text-2xl font-black tracking-wider text-purple-400">SHAYAN_EXPLORER</h2>
            <p class="text-xs text-gray-400 mt-1 uppercase tracking-widest">{{ mode }} Portal Access</p>
        </div>
        {% if error %}<div class="p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-xs text-rose-400 text-center">{{ error }}</div>{% endif %}
        <form action="{{ url_for('auth_' + mode.lower()) }}" method="POST" class="space-y-4">
            <div>
                <label class="block text-[10px] uppercase text-gray-400 font-bold mb-1">Username</label>
                <input type="text" name="username" class="w-full bg-black/40 border border-white/10 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-purple-500" required>
            </div>
            <div>
                <label class="block text-[10px] uppercase text-gray-400 font-bold mb-1">Password</label>
                <input type="password" name="password" class="w-full bg-black/40 border border-white/10 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-purple-500" required>
            </div>
            <button type="submit" class="w-full py-3 bg-gradient-to-r from-purple-600 to-indigo-600 rounded-xl text-xs font-bold uppercase tracking-wider text-white shadow-lg shadow-purple-600/20">{{ mode }}</button>
        </form>
        <div class="text-center text-xs">
            {% if mode == 'Login' %}
                <span class="text-gray-400">New operator?</span> <a href="{{ url_for('auth_register') }}" class="text-purple-400 font-bold hover:underline">Register Account</a>
            {% else %}
                <span class="text-gray-400">Already registered?</span> <a href="{{ url_for('auth_login') }}" class="text-purple-400 font-bold hover:underline">Login Securely</a>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

HTML_CUSTOMER_STORE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SHAYAN_EXPLORER | Secure API Store</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>body { background: radial-gradient(circle at top right, #0c071e, #020105); color: #f3f4f6; }</style>
</head>
<body class="min-h-screen antialiased pb-12">
    <header class="border-b border-white/5 py-4 px-6 flex justify-between items-center bg-black/40 backdrop-blur-md sticky top-0 z-40">
        <span class="text-lg font-black tracking-wider text-white">SHAYAN_STORE</span>
        <div class="flex items-center space-x-4">
            <span class="text-xs text-gray-400 font-mono">Operator: <strong class="text-purple-400">{{ session['username'] }}</strong></span>
            <a href="{{ url_for('logout') }}" class="text-xs bg-rose-600/20 text-rose-400 border border-rose-500/20 px-3 py-1.5 rounded-xl hover:bg-rose-600/30 transition">Logout</a>
        </div>
    </header>
    <main class="max-w-xl mx-auto mt-10 p-4">
        <div class="bg-white/5 border border-white/10 rounded-2xl p-6 shadow-xl space-y-6">
            <h2 class="text-sm font-black tracking-wider text-purple-400 uppercase border-b border-white/5 pb-2">Deploy New Token Instance</h2>
            <form action="{{ url_for('generate_invoice') }}" method="POST" class="space-y-4">
                <div>
                    <label class="block text-[10px] uppercase text-gray-400 font-bold mb-1">Target Name Identifier</label>
                    <input type="text" name="name" placeholder="E.g., Production Instance" class="w-full bg-black/40 border border-white/10 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-purple-500" required>
                </div>
                <div>
                    <label class="block text-[10px] uppercase text-gray-400 font-bold mb-1">Expiration Context & Time Limit</label>
                    <input type="datetime-local" id="expire_date" name="expire_date" class="w-full bg-black/40 border border-white/10 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-purple-500" onchange="calculatePrice()" required>
                </div>
                <div>
                    <label class="block text-[10px] uppercase text-gray-400 font-bold mb-2">Scope Authorization Strategy</label>
                    <div class="grid grid-cols-2 gap-2 max-h-32 overflow-y-auto p-1 bg-black/20 rounded-xl border border-white/5">
                        {% for tool in tools %}
                        <div class="flex items-center space-x-2 p-1.5">
                            <input type="checkbox" name="tools" value="{{ tool }}" id="tool-{{ tool }}" class="accent-purple-600" checked>
                            <label for="tool-{{ tool }}" class="text-xs uppercase text-gray-300 font-mono cursor-pointer">{{ tool }}</label>
                        </div>
                        {% endfor %}
                    </div>
                </div>
                <div class="bg-purple-950/20 border border-purple-500/20 rounded-xl p-4 flex justify-between items-center">
                    <div>
                        <span class="text-[10px] uppercase text-purple-300 font-bold block">Estimated Dynamic Cost</span>
                        <span class="text-xs text-gray-400" id="duration_days">0 days remaining</span>
                    </div>
                    <span class="text-2xl font-black text-white font-mono" id="total_price_label">₹0</span>
                </div>
                <button type="submit" class="w-full py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-xl font-bold text-xs uppercase tracking-wider shadow-lg shadow-purple-600/20">Proceed to Checkout</button>
            </form>
        </div>
    </main>
    <script>
        const pricePerDay = {{ base_price }};
        function calculatePrice() {
            const expInput = document.getElementById('expire_date').value;
            if(!expInput) return;
            const expDate = new Date(expInput);
            const now = new Date();
            const diffTime = expDate - now;
            if(diffTime <= 0) {
                document.getElementById('total_price_label').innerText = "₹0";
                document.getElementById('duration_days').innerText = "Invalid Date Selected";
                return;
            }
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            const totalPrice = diffDays * pricePerDay;
            document.getElementById('total_price_label').innerText = "₹" + totalPrice;
            document.getElementById('duration_days').innerText = diffDays + " Day(s) Deployment Configured";
        }
    </script>
</body>
</html>
"""

HTML_INVOICE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Secure Checkout Gateway</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>body { background: radial-gradient(circle at top right, #0c071e, #020105); color: #f3f4f6; }</style>
</head>
<body class="min-h-screen p-4 flex items-center justify-center">
    <div class="w-full max-w-md bg-white/5 border border-white/10 rounded-3xl p-6 shadow-2xl space-y-6 backdrop-blur-md">
        <div class="border border-white/10 bg-black/40 rounded-2xl p-5 space-y-4 relative overflow-hidden font-mono text-xs">
            <div class="absolute top-0 right-0 w-24 h-24 bg-purple-600/10 rounded-full blur-xl"></div>
            <div class="flex justify-between items-center border-b border-white/5 pb-2">
                <div>
                    <h3 class="font-black text-sm text-white">SHAYAN METADATA NETWORKS</h3>
                    <p class="text-[9px] text-gray-400">INVOICE #{{ order_id }}</p>
                </div>
                <span class="text-emerald-400 font-bold bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded text-[9px]">UNPAID</span>
            </div>
            <div class="space-y-1.5 text-gray-300">
                <div class="flex justify-between"><span>Client Identity:</span><span class="text-white">{{ name }}</span></div>
                <div class="flex justify-between"><span>Expiration Target:</span><span class="text-purple-300">{{ expire_date }}</span></div>
                <div class="flex justify-between"><span>Allocated Modules:</span><span class="text-indigo-300">{{ tool_count }} Tools</span></div>
            </div>
            <div class="border-t border-white/5 pt-2 flex justify-between items-center text-sm font-bold">
                <span class="text-gray-400">Total Aggregate Payable:</span>
                <span class="text-white text-lg">₹{{ price }}</span>
            </div>
        </div>
        <div class="text-center space-y-4">
            <p class="text-[11px] text-gray-400 uppercase tracking-widest">Scan QR Code via any UPI App to Pay</p>
            <div class="inline-block p-3 bg-white rounded-2xl shadow-inner">
                <img src="https://chart.googleapis.com/chart?chs=180x180&cht=qr&chl=upi://pay?pa={{ upi_id }}%26am={{ price }}%26tn=API-Token-Order-{{ order_id }}" alt="Payment QR Code" class="w-44 h-44">
            </div>
            <div class="text-xs text-purple-300 font-bold">
                <a href="upi://pay?pa={{ upi_id }}&am={{ price }}&tn=API-Token-Order-{{ order_id }}" class="inline-block px-4 py-2 bg-purple-600/20 hover:bg-purple-600/30 border border-purple-500/20 rounded-xl transition">
                    Open in Mobile UPI Apps
                </a>
            </div>
        </div>
        <form action="{{ url_for('submit_utr') }}" method="POST" class="border-t border-white/5 pt-4 space-y-3">
            <input type="hidden" name="name" value="{{ name }}">
            <input type="hidden" name="expire_date" value="{{ expire_date }}">
            <input type="hidden" name="tools" value='{{ tools_json }}'>
            <input type="hidden" name="price" value="{{ price }}">
            <input type="hidden" name="order_id" value="{{ order_id }}">
            <div>
                <label class="block text-[10px] uppercase text-gray-400 font-bold mb-1">Enter 12-Digit Bank UTR / Transaction Reference Number</label>
                <input type="text" name="utr" placeholder="E.g., 3491XXXXXXXX" minlength="12" maxlength="12" class="w-full bg-black/40 border border-white/10 rounded-xl p-3 text-sm text-center font-mono text-amber-300 tracking-widest focus:outline-none focus:border-amber-500" required>
            </div>
            <button type="submit" class="w-full py-3 bg-gradient-to-r from-emerald-600 to-teal-600 text-white font-bold text-xs uppercase tracking-wider rounded-xl shadow-lg shadow-emerald-600/20">Submit Transaction UTR</button>
        </form>
    </div>
</body>
</html>
"""

# --- AUTHENTICATION ENDPOINTS ---
@app.route('/login', methods=['GET', 'POST'])
def auth_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = users_col.find_one({"username": username, "password": password})
        if user:
            session['username'] = username
            return redirect(url_for('customer_store'))
        return render_template_string(HTML_AUTH, mode="Login", error="Invalid cryptographic credentials.")
    return render_template_string(HTML_AUTH, mode="Login", error=None)

@app.route('/register', methods=['GET', 'POST'])
def auth_register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if users_col.find_one({"username": username}):
            return render_template_string(HTML_AUTH, mode="Register", error="Operator identity already allocated.")
        users_col.insert_one({"username": username, "password": password})
        session['username'] = username
        return redirect(url_for('customer_store'))
    return render_template_string(HTML_AUTH, mode="Register", error=None)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth_login'))

# --- FRONTEND CUSTOMER GATEWAY STORES ---
@app.route('/store')
def customer_store():
    if 'username' not in session: return redirect(url_for('auth_login'))
    return render_template_string(HTML_CUSTOMER_STORE, tools=SUPPORTED_TOOLS, base_price=BASE_PRICE_PER_DAY)

@app.route('/store/invoice', methods=['POST'])
def generate_invoice():
    if 'username' not in session: return redirect(url_for('auth_login'))
    name = request.form.get('name')
    expire_date = request.form.get('expire_date')
    selected_tools = request.form.getlist('tools')
    
    if not expire_date or not selected_tools:
        return "Invalid selection parameters configured.", 400
        
    try:
        exp_dt = parser.parse(expire_date)
        diff = exp_dt - datetime.now()
        days = max(1, math.ceil(diff.total_seconds() / (3600 * 24)))
        calculated_price = days * BASE_PRICE_PER_DAY
    except Exception:
        calculated_price = 100
        
    order_id = secrets.token_hex(4).upper()
    return render_template_string(
        HTML_INVOICE, name=name, expire_date=expire_date,
        tool_count=len(selected_tools), price=calculated_price,
        order_id=order_id, upi_id=YOUR_UPI_ID, tools_json=json.dumps(selected_tools)
    )

@app.route('/store/submit-utr', methods=['POST'])
def submit_utr():
    if 'username' not in session: return redirect(url_for('auth_login'))
    utr = request.form.get('utr')
    name = request.form.get('name')
    expire_date = request.form.get('expire_date')
    tools = json.loads(request.form.get('tools', '[]'))
    price = request.form.get('price')
    order_id = request.form.get('order_id')
    
    payments_col.insert_one({
        "order_id": order_id, "username": session['username'],
        "name": name, "expire_date": expire_date, "tools": tools,
        "price": price, "utr": utr, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Pending Verification"
    })
    
    generated_key = f"SHAYAN-{secrets.token_hex(8).upper()}"
    keys_col.insert_one({
        "name": f"{name} ({session['username']})",
        "key": generated_key,
        "expire_date": expire_date,
        "limit": 500, "used": 0, "status": "Active", "tools": tools
    })
    
    return f"""
    <div style="background:#0c071e; color:#f3f4f6; min-height:100vh; font-family:sans-serif; flex-direction:column; display:flex; align-items:center; justify-content:center; padding:20px; text-align:center;">
        <div style="background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); padding:30px; border-radius:20px; max-width:450px;">
            <h2 style="color:#34d399; margin-bottom:10px;">✔ PAYMENT UTR SUBMITTED</h2>
            <p style="font-size:13px; color:#9ca3af;">Your 12-Digit Reference <strong>{utr}</strong> is being processed.</p>
            <div style="background:rgba(0,0,0,0.3); border:1px solid rgba(147,51,234,0.3); padding:15px; border-radius:12px; margin:20px 0; font-family:monospace; font-size:13px; color:#c084fc;">
                <strong>YOUR ALLOCATED API KEY:</strong><br><span style="font-size:14px; font-weight:bold; display:block; margin-top:5px;">{generated_key}</span>
            </div>
            <a href="/store" style="text-decoration:none; color:#fff; background:#9333ea; padding:10px 20px; border-radius:10px; font-size:12px; font-weight:bold; display:inline-block;">Back to Store</a>
        </div>
    </div>
    """

# --- CORE INTEGRATED GATEWAY ROUTINGS ---
@app.route('/')
def dashboard():
    return "SHAYAN_EXPLORER Gateway Hub"

@app.route('/api/admin/keys', methods=['GET', 'POST'])
def handle_keys():
    if request.method == 'POST':
        data = request.json or {}
        key_id = data.get('key')
        if not key_id: return jsonify({"status": "error", "message": "Key code is mandatory"}), 400
        
        keys_col.update_one(
            {"key": key_id},
            {"$set": {
                "name": data.get('name', 'Client Target Profile'),
                "expire_date": data.get('expire_date', '2026-12-31T23:59'),
                "limit": int(data.get('limit', 100)),
                "used": int(data.get('used', 0)),
                "status": data.get('status', 'Active'),
                "tools": data.get('tools', ['all'])
            }},
            upsert=True
        )
        return jsonify({"status": "success"})
    
    all_keys = list(keys_col.find({}, {"_id": 0}))
    return jsonify(all_keys)

@app.route('/api/<tool>', methods=['GET'])
def proxy_gateway(tool):
    if tool not in SUPPORTED_TOOLS: return jsonify({"status": "error", "message": "Invalid Route."}), 404
    user_key = request.args.get('key')
    if not user_key: return jsonify({"status": "error", "message": "Missing key parameter."}), 401
    
    key_data = keys_col.find_one({"key": user_key})
    if not key_data: return jsonify({"status": "error", "message": "KEY_NOT_FOUND"}), 403
    if key_data.get("status") == "Suspended": return jsonify({"status": "error", "message": "Key Suspended"}), 403
    
    try:
        if datetime.now() > parser.parse(key_data["expire_date"]):
            return jsonify({"status": "error", "message": "Key Expired"}), 403
    except: pass
    
    if int(key_data["used"]) >= int(key_data["limit"]):
        return jsonify({"status": "error", "message": "Quota Limit Reached"}), 403

    upstream_params = dict(request.args)
    upstream_params['key'] = UPSTREAM_DEFAULT_KEY

    try:
        response = requests.get(f"{TARGET_API_BASE}/{tool}", params=upstream_params, timeout=12)
        try: response_data = response.json()
        except: response_data = {"data": response.text}
    except Exception as e: response_data = {"status": "error", "message": str(e)}

    if response.status_code == 200:
        keys_col.update_one({"key": user_key}, {"$inc": {"used": 1}})
        
    return jsonify(response_data), response.status_code

# Vercel requires WSGI application object assignment
handler = app

if __name__ == '__main__':
    app.run(debug=True, port=5000)
