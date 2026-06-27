import os
import json
import secrets
import requests
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
from datetime import datetime
from dateutil import parser

app = Flask(__name__)
app.secret_key = secrets.token_hex(24) # सेशन्स को सुरक्षित रखने के लिए सीक्रेट की

TARGET_API_BASE = "https://ft-osint-api.duckdns.org/api"
UPSTREAM_DEFAULT_KEY = "vernex-6a9dc4fdd5923c40b0aba27bf1e39e3f"

# --- कॉन्फिगरेशन (यहाँ अपनी डिटेल्स सेट करें) ---
YOUR_UPI_ID = "your-upi-id@ybl"
BASE_PRICE_PER_DAY = 10  # ₹10 प्रति दिन के हिसाब से कैलकुलेशन

DB_FILE = "keys_db.json"

def load_db():
    if not os.path.exists(DB_FILE):
        default_db = {
            "users": {},        # {"username": "password"}
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
            "logs": [],
            "payments": []      # UTR और पेंडिंग पेमेंट्स रिकॉर्ड करने के लिए
        }
        with open(DB_FILE, 'w') as f:
            json.dump(default_db, f, indent=4)
        return default_db
    try:
        with open(DB_FILE, 'r') as f:
            db = json.load(f)
            if "users" not in db: db["users"] = {}
            if "payments" not in db: db["payments"] = []
            return db
    except Exception:
        return {"users": {}, "keys": {}, "logs": [], "payments": []}

def save_db(data):
    try:
        with open(DB_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving database file: {str(e)}")

SUPPORTED_TOOLS = [
    "adv", "paytm", "imei", "calltracer", "upi", "ifsc", 
    "number", "pincode", "ip", "challan", "ff", "bgmi", 
    "snap", "email", "vehicle", "git", "insta", "tg", 
    "tgidinfo", "numleak", "pan", "adharfamily", "aadhar"
]

# --- UI TEMPLATES ---

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

# --- AUTHENTICATION ROUTES ---

@app.route('/login', methods=['GET', 'POST'])
def auth_login():
    if request.method == 'POST':
        db = load_db()
        username = request.form.get('username')
        password = request.form.get('password')
        if username in db["users"] and db["users"][username] == password:
            session['username'] = username
            return redirect(url_for('customer_store'))
        return render_template_string(HTML_AUTH, mode="Login", error="Invalid cryptographic credentials.")
    return render_template_string(HTML_AUTH, mode="Login", error=None)

@app.route('/register', methods=['GET', 'POST'])
def auth_register():
    if request.method == 'POST':
        db = load_db()
        username = request.form.get('username')
        password = request.form.get('password')
        if username in db["users"]:
            return render_template_string(HTML_AUTH, mode="Register", error="Operator identity already allocated.")
        db["users"][username] = password
        save_db(db)
        session['username'] = username
        return redirect(url_for('customer_store'))
    return render_template_string(HTML_AUTH, mode="Register", error=None)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth_login'))

# --- CUSTOMER STOREFRONT & INVOICE FLOW ---

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
        days = max(1, math.ceil(diff.total_seconds() / (3600 * 24))) if 'math' in globals() else max(1, (diff.days + 1))
        calculated_price = days * BASE_PRICE_PER_DAY
    except Exception:
        calculated_price = 100 # सुरक्षित फॉलबैक प्राइस वैल्यु
        
    order_id = secrets.token_hex(4).upper()
    
    return render_template_string(
        HTML_INVOICE,
        name=name,
        expire_date=expire_date,
        tool_count=len(selected_tools),
        price=calculated_price,
        order_id=order_id,
        upi_id=YOUR_UPI_ID,
        tools_json=json.dumps(selected_tools)
    )

@app.route('/store/submit-utr', methods=['POST'])
def submit_utr():
    if 'username' not in session: return redirect(url_for('auth_login'))
    
    db = load_db()
    utr = request.form.get('utr')
    name = request.form.get('name')
    expire_date = request.form.get('expire_date')
    tools = json.loads(request.form.get('tools', '[]'))
    price = request.form.get('price')
    order_id = request.form.get('order_id')
    
    # पेंडिंग रिक्वेस्ट ऑब्जेक्ट सिंक करें
    payment_record = {
        "order_id": order_id,
        "username": session['username'],
        "name": name,
        "expire_date": expire_date,
        "tools": tools,
        "price": price,
        "utr": utr,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Pending Verification"
    }
    
    db["payments"].append(payment_record)
    
    # ऑटोमेशन सिमुलेशन: UTR सबमिट होते ही टोकन को 'Active' रजिस्ट्री में जोड़ देता है।
    # आप चाहें तो इसे एडमिन द्वारा मैन्युअल अप्रूवल देने के लिए भी रख सकते हैं।
    generated_key = f"SHAYAN-{secrets.token_hex(8).upper()}"
    db["keys"][generated_key] = {
        "name": f"{name} ({session['username']})",
        "key": generated_key,
        "expire_date": expire_date,
        "limit": 500,
        "used": 0,
        "status": "Active",
        "tools": tools
    }
    
    save_db(db)
    
    return f"""
    <div style="background:#0c071e; color:#f3f4f6; min-height:100vh; font-family:sans-serif; flex-direction:column; display:flex; align-items:center; justify-content:center; padding:20px; text-align:center;">
        <div style="background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); padding:30px; border-radius:20px; max-width:450px;">
            <h2 style="color:#34d399; margin-bottom:10px;">✔ PAYMENT UTR SUBMITTED</h2>
            <p style="font-size:13px; color:#9ca3af;">Your 12-Digit Reference <strong>{utr}</strong> is being logs matched in runtime database matrix.</p>
            <div style="background:rgba(0,0,0,0.3); border:1px solid rgba(147,51,234,0.3); padding:15px; border-radius:12px; margin:20px 0; font-family:monospace; font-size:13px; color:#c084fc;">
                <strong>YOUR ALLOCATED API KEY:</strong><br><span style="font-size:14px; font-weight:bold; display:block; margin-top:5px;">{generated_key}</span>
            </div>
            <a href="/store" style="text-decoration:none; color:#fff; background:#9333ea; padding:10px 20px; border-radius:10px; font-size:12px; font-weight:bold; display:inline-block;">Back to Dashboard</a>
        </div>
    </div>
    """

# --- EXISTING CODE PATHS (UNTOUCHED CORE BACKEND) ---

# [ load_db, save_db, check_key_validity, sanitize_payload, handle_keys, proxy_gateway आदि फंक्शन्स पूर्ववत काम करेंगे ]
@app.route('/')
def dashboard():
    return render_template_string(HTML_DASHBOARD)

@app.route('/api/admin/keys', methods=['GET', 'POST'])
def handle_keys():
    db = load_db()
    if request.method == 'POST':
        data = request.json or {}
        key_id = data.get('key')
        if not key_id: return jsonify({"status": "error", "message": "Key code is mandatory"}), 400
        db["keys"][key_id] = {
            "name": data.get('name', 'Client Target Profile'),
            "key": key_id,
            "expire_date": data.get('expire_date', '2026-12-31T23:59'),
            "limit": int(data.get('limit', 100)),
            "used": int(data.get('used', db["keys"].get(key_id, {}).get("used", 0))),
            "status": data.get('status', db["keys"].get(key_id, {}).get("status", "Active")),
            "tools": data.get('tools', ['all'])
        }
        save_db(db)
        return jsonify({"status": "success"})
    return jsonify(list(db["keys"].values()))

@app.route('/api/admin/keys/manual-reset', methods=['POST'])
def manual_reset_key():
    db = load_db()
    data = request.json or {}
    key_id = data.get('key')
    if key_id in db["keys"]:
        db["keys"][key_id]["used"] = 0
        save_db(db)
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Key target profile not found"}), 404

@app.route('/api/admin/keys/status', methods=['POST'])
def change_status():
    db = load_db()
    data = request.json or {}
    key_id = data.get('key')
    new_status = data.get('status')
    if key_id in db["keys"]:
        db["keys"][key_id]["status"] = new_status
        save_db(db)
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Token not found"}), 404

@app.route('/api/admin/keys/delete/<key_id>', methods=['DELETE'])
def drop_key(key_id):
    db = load_db()
    if key_id in db["keys"]:
        del db["keys"][key_id]
        save_db(db)
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 404

@app.route('/api/admin/logs', methods=['GET', 'POST'])
def handle_logs():
    db = load_db()
    if request.method == 'POST':
        db["logs"] = []
        save_db(db)
        return jsonify({"status": "success"})
    return jsonify(db["logs"])

def check_key_validity(db, api_key, tool_name):
    if api_key not in db["keys"]: return False, "KEY_NOT_FOUND"
    key_data = db["keys"][api_key]
    if key_data.get("status", "Active") == "Suspended": return False, "This API access footprint has been explicitly suspended."
    try:
        expire_dt = parser.parse(key_data["expire_date"])
        if datetime.now() > expire_dt: return False, f"API Key expired automatically on {key_data['expire_date']}."
    except Exception: return False, "System runtime token configuration parse exception."
    if int(key_data["used"]) >= int(key_data["limit"]): return False, f"Allocated quota threshold limit reached ({key_data['limit']})."
    allowed_tools = key_data.get("tools", [])
    if "all" not in allowed_tools and tool_name not in allowed_tools: return False, f"Access denied for router parameter: '{tool_name}'."
    return True, key_data

def sanitize_payload(data):
    banned = ["@ftgamer2", "@bornex", "Ultra", "ft-osint", "duckdns", "ft-rahun2m"]
    try:
        if isinstance(data, dict):
            cleaned_dict = {}
            for k, v in data.items():
                if any(b in str(k) for b in banned): continue
                cleaned_dict[k] = sanitize_payload(v)
            return cleaned_dict
        elif isinstance(data, list): return [sanitize_payload(i) for i in data]
        elif isinstance(data, str):
            if "https://t.me/lynx_api" in data: data = data.replace("https://t.me/lynx_api", "https://t.me/shayan_explorer_channel")
            for b in banned: data = data.replace(b, "SHAYAN_EXPLORER")
            return data
    except Exception: return data
    return data

@app.route('/api/<tool>', methods=['GET'])
def proxy_gateway(tool):
    if tool not in SUPPORTED_TOOLS: return jsonify({"status": "error", "developer": "SHAYAN_EXPLORER", "message": "Invalid Route."}), 404
    user_key = request.args.get('key')
    if not user_key: return jsonify({"status": "error", "developer": "SHAYAN_EXPLORER", "message": "Missing key parameters."}), 401
    
    db = load_db()
    is_valid, result = check_key_validity(db, user_key, tool)
    if not is_valid: return jsonify({"status": "error", "developer": "SHAYAN_EXPLORER", "message": result}), 403

    key_data = result
    search_query = "Dynamic Data Request"
    for param in ['num', 'email', 'vehicle', 'username', 'uid', 'id', 'upi', 'ifsc', 'imei', 'ip', 'pin', 'info', 'pan']:
        if request.args.get(param):
            search_query = f"{param}: {request.args.get(param)}"
            break

    upstream_params = dict(request.args)
    upstream_params['key'] = UPSTREAM_DEFAULT_KEY

    try:
        response = requests.get(f"{TARGET_API_BASE}/{tool}", params=upstream_params, timeout=12)
        try: response_data = sanitize_payload(response.json())
        except ValueError: response_data = {"data": sanitize_payload(response.text)}
    except Exception as e: response_data = {"status": "error", "message": f"Link failure: {str(e)}"}

    if response.status_code == 200:
        db["keys"][user_key]["used"] = int(db["keys"][user_key].get("used", 0)) + 1
        
    db["logs"].insert(0, {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "key_name": key_data["name"],
        "key": user_key,
        "tool": tool.upper(),
        "search": search_query,
        "status": "Success" if response.status_code == 200 else "Failed"
    })
    save_db(db)

    if isinstance(response_data, dict):
        response_data["developer"] = "SHAYAN_EXPLORER"
        if "status" not in response_data: response_data["status"] = "SUCCESS"
    return jsonify(response_data), response.status_code

if __name__ == '__main__':
    import math
    app.run(debug=True, port=5000)
