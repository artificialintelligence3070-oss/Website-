import os
import random
import string
import smtplib
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, redirect, url_for, session

app = Flask(__name__)

# ─── PRODUCTION SECURITY PROTECTION LAYER ───────────────────────────
# Pulls critical secret strings dynamically from environment memory layers on Render
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET_KEY', 'explorer_pay_enterprise_secure_gateway_node_2026')

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_EMAIL = os.environ.get('SMTP_EMAIL_USER', 'artificialintelligence3070@gmail.com')
SMTP_PASSWORD = os.environ.get('SMTP_EMAIL_PASSWORD', 'ftoa gqzk vzas ivzs')
# ───────────────────────────────────────────────────────────────────

# -------------------------------------------------------------------------
# GLOBAL PRODUCTION DATA STORAGE LAYERS (IN-MEMORY STORAGE ENGINE)
# -------------------------------------------------------------------------
MERCHANTS_DB = {}
PAYMENTS_DB = {}
WITHDRAWALS_DB = []
LINKS_DB = []
OTP_RESET_CACHE = {}
EMAIL_UPDATE_CACHE = {}

# Pre-seeded clean professional dashboard account for immediate system verification
MERCHANTS_DB["shayan_explorer"] = {
    "email": "artificialintelligence3070@gmail.com",
    "password": "admin",
    "upi_vpa": "Subhraroy324@okicici",
    "api_key": "pk_live_shayan_7a9f82d1c3b4e",
    "secret_key": "sk_live_shayan_1a2b3c4d5e6f7g",
    "balance": 14250.00,
    "total_earnings": 25800.00,
    "total_withdrawals": 11550.00
}

LINKS_DB.append({"id": "link-api599", "merchant_username": "shayan_explorer", "title": "Truecaller Premium API Endpoint Access", "amount": 599.00, "clicks": 34})
LINKS_DB.append({"id": "link-scrp799", "merchant_username": "shayan_explorer", "title": "Enterprise Cloud Scraper Core License", "amount": 799.00, "clicks": 19})

# -------------------------------------------------------------------------
# SYSTEM MAILING HELPER ROUTINES
# -------------------------------------------------------------------------
def dispatch_secure_verification_email(target_email, verification_otp):
    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = f"ExplorerPay Secure Network Verification OTP: {verification_otp}"
        message["From"] = SMTP_EMAIL
        message["To"] = target_email

        html_body = f"""
        <html>
        <body style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f8fafc; padding: 40px; margin: 0;">
            <div style="max-width: 500px; margin: 0 auto; background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #e2e8f0;">
                <div style="background: linear-gradient(135deg, #4f46e5 0%, #2563eb 100%); padding: 30px; text-align: center; color: #ffffff;">
                    <h2 style="margin: 0; font-size: 24px; font-weight: 800;">ExplorerPay Security</h2>
                </div>
                <div style="padding: 30px; color: #334155;">
                    <p style="font-size: 15px; line-height: 1.5; color: #64748b; margin-top: 0;">A credential adjustment sequence was initiated on your payment platform console node. Use the secure operational OTP code below to verify ownership:</p>
                    <div style="background: #f1f5f9; padding: 16px; text-align: center; border-radius: 12px; margin: 24px 0; border: 1px solid #e2e8f0;">
                        <span style="font-family: 'Courier New', Courier, monospace; font-size: 32px; font-weight: 900; tracking-spacing: 6px; color: #1e1b4b;">{verification_otp}</span>
                    </div>
                    <p style="font-size: 12px; line-height: 1.5; color: #94a3b8; margin-bottom: 0;">If you did not execute this request, change your authentication keys immediately. This code token expires shortly.</p>
                </div>
            </div>
        </body>
        </html>
        """
        message.attach(MIMEText(html_body, "html"))
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, target_email, message.as_string())
        return True
    except Exception as e:
        print(f"[CRITICAL SECURITY EXCEPTION]: Mail dispatch loop crashed -> {str(e)}")
        return False

def dispatch_sale_notification_email(seller_email, txn_id, item_desc, amount):
    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = f"🔥 Success! Instant Sale Alert Received: ₹{amount}"
        message["From"] = SMTP_EMAIL
        message["To"] = seller_email

        html_body = f"""
        <html>
        <body style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #0f172a; padding: 30px; margin: 0;">
            <div style="max-width: 480px; margin: 0 auto; background: #1e293b; border-radius: 24px; overflow: hidden; border: 1px solid #334155; text-align: center; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.3);">
                <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 40px 20px; color: #ffffff;">
                    <div style="font-size: 50px; margin-bottom: 10px;">💰</div>
                    <h1 style="margin: 0; font-size: 28px; font-weight: 800;">SALE COMPLETED</h1>
                    <p style="margin: 5px 0 0 0; font-size: 14px; color: #a7f3d0; opacity: 0.9;">Inbound Infrastructure Credit Confirmed</p>
                </div>
                <div style="padding: 30px; color: #f8fafc; text-align: left;">
                    <div style="text-align: center; margin-bottom: 25px;">
                        <span style="font-size: 14px; color: #94a3b8; display: block; text-transform: uppercase; font-weight: 700; letter-spacing: 1px;">Amount Received</span>
                        <span style="font-size: 42px; font-weight: 900; color: #10b981;">₹{amount:.2f}</span>
                    </div>
                    <div style="border-top: 1px dashed #334155; padding-top: 20px; font-size: 13px; color: #cbd5e1; line-height: 2;">
                        <div style="margin-bottom: 8px;"><strong style="color: #94a3b8;">Payment Reference:</strong> <span style="font-family: monospace; font-size: 14px; background: #0f172a; padding: 2px 6px; border-radius: 6px;">#{txn_id}</span></div>
                        <div style="margin-bottom: 8px;"><strong style="color: #94a3b8;">Allocation Node:</strong> {item_desc}</div>
                        <div><strong style="color: #94a3b8;">Settlement Target:</strong> Core Bank Ledger Active</div>
                    </div>
                </div>
                <div style="background: #0f172a; padding: 15px; color: #64748b; font-size: 11px; border-top: 1px solid #334155;">
                    ExplorerPay Multi-Tenant Automated Network Routing • 2026
                </div>
            </div>
        </body>
        </html>
        """
        message.attach(MIMEText(html_body, "html"))
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, seller_email, message.as_string())
        return True
    except Exception as e:
        print(f"[NOTIFICATION CRASH]: Failed to fire sale email card -> {str(e)}")
        return False

# -------------------------------------------------------------------------
# CENTRAL SYSTEM TEMPLATE STORAGE ARRAYS
# -------------------------------------------------------------------------
CORE_MASTER_AUTH_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ExplorerPay Gateway Engine</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=400;500;600;700;800&display=swap');
        body { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #f8fafc; }
    </style>
</head>
<body class="min-h-screen flex items-center justify-center p-4 bg-gradient-to-tr from-slate-50 via-slate-100 to-blue-50/30">
    <div class="bg-white max-w-md w-full rounded-3xl shadow-2xl border border-slate-200/60 overflow-hidden p-8 space-y-6 relative">
        <div class="text-center space-y-2">
            <div class="inline-block bg-gradient-to-br from-indigo-600 to-blue-600 text-white p-3 rounded-2xl shadow-xl shadow-indigo-200 mb-1">
                <i class="fa-solid fa-shield-halved text-2xl"></i>
            </div>
            <h2 class="text-2xl font-black bg-gradient-to-r from-indigo-600 via-blue-600 to-indigo-700 bg-clip-text text-transparent tracking-tight">ExplorerPay Enterprise</h2>
            <p class="text-xs text-slate-400 font-medium">Production Infrastructure Node Management Gateway Portal</p>
        </div>
        
        {% if error %}
        <div class="bg-rose-50 border border-rose-100 rounded-xl p-3 text-center flex items-center gap-2 justify-center">
            <i class="fa-solid fa-circle-exclamation text-rose-500 text-sm"></i>
            <p class="text-xs text-rose-800 font-bold">{{ error }}</p>
        </div>
        {% endif %}
        
        {% if success %}
        <div class="bg-emerald-50 border border-emerald-100 rounded-xl p-3 text-center flex items-center gap-2 justify-center">
            <i class="fa-solid fa-circle-check text-emerald-500 text-sm"></i>
            <p class="text-xs text-emerald-800 font-bold">{{ success }}</p>
        </div>
        {% endif %}

        {{ inner_content|safe }}
    </div>
</body>
</html>
"""

LOGIN_VIEW_HTML = """
<form action="/login" method="POST" class="space-y-4">
    <div>
        <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Account Username String</label>
        <div class="relative">
            <span class="absolute inset-y-0 left-0 flex items-center pl-3.5 text-slate-400 text-sm"><i class="fa-solid fa-user-gear"></i></span>
            <input type="text" name="username" required placeholder="Enter username string" class="w-full bg-slate-50 border border-slate-200 rounded-xl pl-10 pr-4 py-3 text-sm focus:outline-none focus:border-indigo-500 transition font-medium text-slate-700">
        </div>
    </div>
    <div>
        <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Access Passphrase</label>
        <div class="relative">
            <span class="absolute inset-y-0 left-0 flex items-center pl-3.5 text-slate-400 text-sm"><i class="fa-solid fa-lock"></i></span>
            <input type="password" name="password" required placeholder="••••••••" class="w-full bg-slate-50 border border-slate-200 rounded-xl pl-10 pr-4 py-3 text-sm focus:outline-none focus:border-indigo-500 transition font-medium text-slate-700">
        </div>
    </div>
    <div class="flex justify-end pt-0.5">
        <a href="/forgot-password" class="text-xs font-bold text-indigo-600 hover:text-indigo-700 transition hover:underline">Forgot Gateway Passphrase?</a>
    </div>
    <button type="submit" class="w-full bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700 text-white font-bold py-3.5 rounded-xl shadow-lg shadow-indigo-200 text-xs transition uppercase tracking-wider">Authorize Terminal</button>
</form>
<div class="text-center border-t border-slate-100 pt-4">
    <p class="text-xs text-slate-400 font-medium">Need payment distribution arrays? <a href="/register" class="text-indigo-600 font-bold hover:underline">Provision Core Node</a></p>
</div>
"""

REGISTER_VIEW_HTML = """
<form action="/register" method="POST" class="space-y-3.5">
    <div>
        <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">System Account Username</label>
        <input type="text" name="username" required placeholder="e.g., global_dev" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500 text-slate-700 font-medium">
    </div>
    <div>
        <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Active Communication Email</label>
        <input type="email" name="email" required placeholder="e.g., developer@domain.com" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500 text-slate-700 font-medium">
    </div>
    <div>
        <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Settlement Address (UPI VPA)</label>
        <input type="text" name="upi_vpa" required placeholder="e.g., realname@okaxis" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500 text-slate-700 font-medium">
    </div>
    <div>
        <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Secure Password Complex String</label>
        <input type="password" name="password" required placeholder="••••••••" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500 text-slate-700 font-medium">
    </div>
    <button type="submit" class="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-bold py-3.5 rounded-xl shadow-lg shadow-emerald-100 text-xs transition uppercase tracking-wider">Initialize Routing Profiles</button>
</form>
<div class="text-center border-t border-slate-100 pt-4">
    <p class="text-xs text-slate-400 font-medium">Existing authorized gateway? <a href="/login" class="text-indigo-600 font-bold hover:underline">Verify Identity</a></p>
</div>
"""

FORGOT_STEP1_HTML = """
<form action="/forgot-password" method="POST" class="space-y-4">
    <div class="text-center pb-2">
        <p class="text-xs text-slate-400 leading-relaxed">Input your verified system registration email address string. Our communication layers will issue a dynamic 6-digit access OTP payload.</p>
    </div>
    <div>
        <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Registered System Email</label>
        <div class="relative">
            <span class="absolute inset-y-0 left-0 flex items-center pl-3.5 text-slate-400 text-sm"><i class="fa-solid fa-envelope"></i></span>
            <input type="email" name="email" required placeholder="developer@domain.com" class="w-full bg-slate-50 border border-slate-200 rounded-xl pl-10 pr-4 py-3 text-sm focus:outline-none focus:border-indigo-500 text-slate-700 font-medium">
        </div>
    </div>
    <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3.5 rounded-xl shadow-lg shadow-indigo-100 text-xs transition uppercase tracking-wider">Dispatch Verification Array</button>
</form>
<div class="text-center border-t border-slate-100 pt-4">
    <a href="/login" class="text-xs font-bold text-slate-400 hover:text-slate-600 transition"><i class="fa-solid fa-arrow-left-long"></i> Back to login gate</a>
</div>
"""

FORGOT_STEP2_OTP_HTML = """
<form action="/forgot-password/verify-otp" method="POST" class="space-y-4">
    <div class="text-center pb-2">
        <p class="text-xs text-emerald-600 font-semibold leading-relaxed bg-emerald-50 border border-emerald-100 rounded-xl p-2"><i class="fa-solid fa-paper-plane animate-bounce"></i> Security array sent successfully to target destination mail strings.</p>
    </div>
    <input type="hidden" name="email" value="{{ target_email }}">
    <div>
        <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1 text-center">Enter 6-Digit Secure Verification Token</label>
        <input type="text" name="otp" required maxlength="6" placeholder="000000" class="w-full bg-slate-50 border-2 border-slate-200 rounded-2xl py-3 text-center tracking-[12px] text-xl font-mono focus:outline-none focus:border-indigo-500 font-black text-slate-800">
    </div>
    <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3.5 rounded-xl text-xs transition uppercase tracking-wider">Verify Escrow Block</button>
</form>
"""

FORGOT_STEP3_RESET_HTML = """
<form action="/forgot-password/commit-reset" method="POST" class="space-y-4">
    <div class="text-center pb-2">
        <p class="text-xs text-slate-400 leading-relaxed">Identity block validation cleared successfully. Establish your brand new access passphrase string below.</p>
    </div>
    <input type="hidden" name="email" value="{{ target_email }}">
    <input type="hidden" name="token" value="{{ verified_token }}">
    <div>
        <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Define New Access Passphrase</label>
        <input type="password" name="new_password" required placeholder="Minimum 6 complex characters" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-indigo-500 text-slate-700">
    </div>
    <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3.5 rounded-xl text-xs transition uppercase tracking-wider">Apply Security Update</button>
</form>
"""

EMAIL_VERIFY_PAGE_HTML = """
<form action="/profile/verify-email-otp" method="POST" class="space-y-4">
    <div class="text-center pb-2">
        <p class="text-xs text-indigo-600 font-semibold leading-relaxed bg-indigo-50 border border-indigo-100 rounded-xl p-3">An email update sequence is pending. Input the 6-digit verification code dispatched to: <br><strong class="text-slate-800">{{ pending_email }}</strong></p>
    </div>
    <div>
        <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1 text-center">Security Email OTP Code</label>
        <input type="text" name="otp" required maxlength="6" placeholder="000000" class="w-full bg-slate-50 border-2 border-slate-200 rounded-2xl py-3 text-center tracking-[12px] text-xl font-mono focus:outline-none focus:border-indigo-500 font-black text-slate-800">
    </div>
    <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3.5 rounded-xl text-xs transition uppercase tracking-wider">Confirm New Email Target</button>
</form>
"""

BASE_DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ExplorerPay - Enterprise Control Board</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=400;500;600;700;800&display=swap');
        body { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #f8fafc; }
    </style>
</head>
<body class="text-slate-800 pb-24 md:pb-0">

    <nav class="bg-white border-b border-slate-200 px-4 py-4 flex justify-between items-center md:px-8 sticky top-0 z-50 shadow-sm">
        <div class="flex items-center space-x-2.5">
            <div class="bg-gradient-to-br from-indigo-600 to-blue-600 text-white p-2.5 rounded-xl shadow-md">
                <i class="fa-solid fa-layer-group text-lg"></i>
            </div>
            <span class="text-xl font-black tracking-tight bg-gradient-to-r from-indigo-600 to-blue-600 bg-clip-text text-transparent">ExplorerPay</span>
        </div>
        <div class="flex items-center space-x-4">
            <span class="bg-indigo-50 border border-indigo-100 text-indigo-700 text-[10px] font-black px-3 py-1.5 rounded-full tracking-wider uppercase hidden sm:inline-block">● Production Infrastructure Online</span>
            <a href="/logout" class="bg-slate-50 hover:bg-rose-50 border border-slate-200 text-slate-400 hover:text-rose-600 transition p-2.5 rounded-xl text-sm" title="Terminate Active Session"><i class="fa-solid fa-power-off"></i></a>
        </div>
    </nav>

    <div class="max-w-7xl mx-auto px-4 py-6 md:py-8 grid grid-cols-1 md:grid-cols-4 gap-6">
        
        <aside class="col-span-1 space-y-4 h-fit">
            
            <div class="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm space-y-3">
                <button onclick="document.getElementById('profile-drawer-accordion').classList.toggle('hidden')" class="w-full flex items-center justify-between p-1 bg-slate-50 hover:bg-slate-100 rounded-xl transition text-left group">
                    <div class="flex items-center space-x-3">
                        <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-blue-600 text-white font-black text-sm flex items-center justify-center shadow-md group-hover:scale-105 transition duration-200">
                            {{ username[0].upper() if username else 'E' }}
                        </div>
                        <div>
                            <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider leading-none">Terminal Profile</p>
                            <p class="text-xs font-black text-slate-700 mt-1">{{ username }}</p>
                        </div>
                    </div>
                    <i class="fa-solid fa-chevron-down text-xs text-slate-400 pr-2 group-hover:text-indigo-600 transition"></i>
                </button>
                
                <div id="profile-drawer-accordion" class="hidden border-t border-slate-100 pt-3 space-y-3 animate-in slide-in-from-top duration-200">
                    <div class="bg-slate-50/70 rounded-xl p-2.5 border border-slate-100 font-medium space-y-2">
                        <div>
                            <span class="text-[9px] uppercase font-bold text-slate-400 tracking-wider block">Linked Mail Node</span>
                            <span class="text-xs text-slate-700 break-all block">{{ account.email }}</span>
                        </div>
                        <div>
                            <span class="text-[9px] uppercase font-bold text-slate-400 tracking-wider block">Settlement Address</span>
                            <span class="text-xs text-slate-600 font-mono block">{{ account.upi_vpa }}</span>
                        </div>
                        <div>
                            <span class="text-[9px] uppercase font-bold text-slate-400 tracking-wider block">Security Password</span>
                            <span class="text-xs text-slate-400 block">•••••••• <span class="text-[9px] text-indigo-500 font-bold ml-1">(Masked)</span></span>
                        </div>
                    </div>
                    
                    <form action="/profile/update" method="POST" class="space-y-2.5">
                        <div>
                            <label class="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-0.5">Edit Settlement UPI</label>
                            <input type="text" name="upi_vpa" value="{{ account.upi_vpa }}" required class="w-full bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs text-slate-700 focus:outline-none focus:border-indigo-500 font-medium">
                        </div>
                        <div>
                            <label class="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-0.5">Edit Notification Mail</label>
                            <input type="email" name="email" value="{{ account.email }}" required class="w-full bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs text-slate-700 focus:outline-none focus:border-indigo-500 font-medium">
                        </div>
                        <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-[10px] py-2 rounded-lg transition uppercase tracking-wider shadow-sm">Commit Changes</button>
                    </form>
                </div>
            </div>

            <div class="hidden md:block space-y-1.5">
                <a href="/" class="flex items-center space-x-3 px-4 py-3.5 rounded-xl transition font-bold {% if active_tab == 'overview' %}text-indigo-700 bg-indigo-50/80{% else %}text-slate-600 hover:text-indigo-600 hover:bg-slate-50{% endif %}">
                    <i class="fa-solid fa-chart-line text-lg w-5"></i> <span>Overview Network Matrix</span>
                </a>
                <a href="/links" class="flex items-center space-x-3 px-4 py-3.5 rounded-xl transition font-bold {% if active_tab == 'links' %}text-indigo-700 bg-indigo-50/80{% else %}text-slate-600 hover:text-indigo-600 hover:bg-slate-50{% endif %}">
                    <i class="fa-solid fa-link text-lg w-5"></i> <span>Hosted Payment Links</span>
                </a>
                <button onclick="document.getElementById('withdraw-modal').classList.remove('hidden')" class="w-full flex items-center space-x-3 px-4 py-3.5 rounded-xl transition text-slate-600 hover:text-indigo-600 hover:bg-slate-50 font-bold text-left">
                    <i class="fa-solid fa-money-bill-transfer text-lg w-5"></i> <span>Request Settlements</span>
                </button>
            </div>
        </aside>

        <main class="col-span-1 md:col-span-3 space-y-6">
            {{ main_content|safe }}
        </main>
    </div>

    <nav class="fixed bottom-0 left-0 right-0 bg-white/90 backdrop-blur-md border-t border-slate-200/80 shadow-2xl flex justify-around py-3 z-50 md:hidden">
        <a href="/" class="flex flex-col items-center space-y-0.5 {% if active_tab == 'overview' %}text-indigo-600{% else %}text-slate-400{% endif %}">
            <i class="fa-solid fa-chart-line text-lg"></i><span class="text-[10px] font-bold">Overview</span>
        </a>
        <a href="/links" class="flex flex-col items-center space-y-0.5 {% if active_tab == 'links' %}text-indigo-600{% else %}text-slate-400{% endif %}">
            <i class="fa-solid fa-link text-lg"></i><span class="text-[10px] font-bold">Links</span>
        </a>
        <button onclick="document.getElementById('withdraw-modal').classList.remove('hidden')" class="flex flex-col items-center space-y-0.5 text-slate-400 hover:text-indigo-600">
            <i class="fa-solid fa-money-bill-transfer text-lg"></i><span class="text-[10px] font-bold">Payout</span>
        </button>
    </nav>

    <div id="withdraw-modal" class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm hidden flex items-center justify-center p-4 z-50 animate-in fade-in duration-150">
        <div class="bg-white rounded-2xl max-w-sm w-full p-6 shadow-2xl border border-slate-100 space-y-4">
            <div>
                <h3 class="font-bold text-slate-900 text-lg">Request Real-time Bank Settlement</h3>
                <p class="text-xs text-slate-400 mt-0.5">Route collected balance assets safely into standard checking layers.</p>
            </div>
            <form action="/withdraw/submit" method="POST" class="space-y-3">
                <div>
                    <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Settlement Network Routing Rails</label>
                    <select name="method" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-indigo-500 font-medium">
                        <option value="Direct UPI Settlement">Instant Core UPI Route</option>
                        <option value="Net Banking (IMPS)">IMPS Automated Settlement</option>
                    </select>
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Target Receiver Destination String</label>
                    <input type="text" name="destination" required placeholder="e.g., name@upi or Account, IFSC" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-indigo-500 text-slate-700">
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Amount to Clear (INR)</label>
                    <input type="number" step="0.01" name="amount" required placeholder="0.00" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-indigo-500 font-semibold text-slate-800">
                </div>
                <div class="flex space-x-2 pt-2">
                    <button type="button" onclick="document.getElementById('withdraw-modal').classList.add('hidden')" class="flex-1 bg-slate-100 text-slate-600 text-xs font-bold py-3 rounded-xl transition hover:bg-slate-200">Cancel</button>
                    <button type="submit" class="flex-1 bg-indigo-600 text-white text-xs font-bold py-3 rounded-xl shadow-lg shadow-indigo-100 transition hover:bg-indigo-700">Confirm Clearance</button>
                </div>
            </form>
        </div>
    </div>

</body>
</html>
"""

OVERVIEW_PAGE_HTML = """
<div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
    <div class="bg-gradient-to-br from-indigo-600 via-indigo-700 to-blue-700 text-white rounded-2xl p-5 shadow-xl relative overflow-hidden">
        <p class="text-indigo-200 text-xs font-bold uppercase tracking-wider">Withdrawable Balance Pool</p>
        <h3 class="text-3xl font-black mt-1">₹{{ "%.2f"|format(account.balance) }}</h3>
        <p class="text-[11px] text-indigo-100/80 mt-3 flex items-center gap-1"><i class="fa-solid fa-circle-check text-emerald-400"></i> Active Core Nodes</p>
    </div>
    <div class="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-sm flex justify-between items-start">
        <div class="space-y-1">
            <p class="text-slate-400 text-xs font-bold uppercase tracking-wider">Gross Revenue Processed</p>
            <h3 class="text-2xl font-black text-slate-800">₹{{ "%.2f"|format(account.total_earnings) }}</h3>
            <span class="inline-block text-[10px] text-emerald-700 bg-emerald-50 border border-emerald-100 px-2 py-0.5 rounded-full font-bold mt-1">100% Success Rate</span>
        </div>
        <div class="bg-emerald-50 text-emerald-600 p-2.5 rounded-xl text-sm"><i class="fa-solid fa-chart-bar"></i></div>
    </div>
    <div class="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-sm flex justify-between items-start">
        <div class="space-y-1">
            <p class="text-slate-400 text-xs font-bold uppercase tracking-wider">Settled External Volume</p>
            <h3 class="text-2xl font-black text-slate-800">₹{{ "%.2f"|format(account.total_withdrawals) }}</h3>
            <span class="inline-block text-[10px] text-blue-700 bg-blue-50 border border-blue-100 px-2 py-0.5 rounded-full font-bold mt-1">Dispatched Wires</span>
        </div>
        <div class="bg-blue-50 text-blue-600 p-2.5 rounded-xl text-sm"><i class="fa-solid fa-building-columns"></i></div>
    </div>
</div>

<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <div class="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-sm space-y-4">
        <div>
            <h4 class="font-bold text-slate-800 text-base">Quick Hosted Link Provisioner</h4>
            <p class="text-xs text-slate-400 mt-0.5">Generate standalone hosted e-commerce invoice destinations.</p>
        </div>
        <form action="/links/create" method="POST" class="space-y-3">
            <div>
                <label class="block text-xs font-bold text-slate-500 mb-1">Invoice Item Cost Amount (INR) *</label>
                <input type="number" step="0.01" name="amount" required placeholder="0.00" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500 font-semibold text-slate-700">
            </div>
            <div>
                <label class="block text-xs font-bold text-slate-500 mb-1">Item Title / Intent Statement Description</label>
                <input type="text" name="title" placeholder="e.g., WhatsApp Business Lookup Module" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500 text-slate-600">
            </div>
            <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3.5 rounded-xl shadow-lg text-xs transition uppercase tracking-wider">Initialize Link Token</button>
        </form>
    </div>

    <div class="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-sm flex flex-col justify-between space-y-4">
        <div class="space-y-1">
            <h4 class="font-bold text-slate-800 text-base">Secure Gateway Storefront Integration Headers</h4>
            <p class="text-xs text-slate-400">Pass these private verification parameters through custom checkouts or remote script files.</p>
        </div>
        <div class="space-y-3">
            <div>
                <span class="text-[10px] uppercase font-bold text-slate-400 tracking-wider block mb-0.5">X-Gateway-API-Key</span>
                <code class="block bg-slate-900 text-emerald-400 text-xs p-3 rounded-xl font-mono overflow-x-auto select-all shadow-inner border border-slate-800">{{ account.api_key }}</code>
            </div>
            <div>
                <span class="text-[10px] uppercase font-bold text-slate-400 tracking-wider block mb-0.5">Webhook Core Encryption Secret Key</span>
                <code class="block bg-slate-900 text-blue-400 text-xs p-3 rounded-xl font-mono overflow-x-auto select-all shadow-inner border border-slate-800">{{ account.secret_key }}</code>
            </div>
        </div>
    </div>
</div>

<div class="bg-white border border-slate-200/80 rounded-2xl shadow-sm overflow-hidden">
    <div class="px-5 py-4 border-b border-slate-200 flex justify-between items-center bg-slate-50/50">
        <h4 class="font-bold text-slate-800 text-sm flex items-center gap-2"><i class="fa-solid fa-list-check text-indigo-500"></i> Local Transaction Pipeline Activity Logs</h4>
        <span class="bg-emerald-100 border border-emerald-200 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">Real-time Node</span>
    </div>
    <div class="divide-y divide-slate-100 overflow-x-auto">
        {% if not txns %}
        <div class="p-8 text-center text-slate-400 text-sm font-medium">
            <i class="fa-solid fa-database text-2xl block mb-2 text-slate-300"></i> No transactions logged on this runtime network.
        </div>
        {% endif %}
        {% for id, p in txns.items() %}
        <div class="p-4 flex items-center justify-between hover:bg-slate-50/40 transition min-w-[550px]">
            <div class="flex items-center space-x-3.5">
                <div class="w-10 h-10 rounded-xl font-bold flex items-center justify-center text-sm {% if p.status == 'Success' %}bg-emerald-50 text-emerald-600 border border-emerald-100{% else %}bg-amber-50 text-amber-600 border border-amber-100 animate-pulse{% endif %}">
                    {% if p.status == 'Success' %}<i class="fa-solid fa-check"></i>{% else %}<i class="fa-solid fa-spinner animate-spin"></i>{% endif %}
                </div>
                <div>
                    <p class="font-bold text-sm text-slate-700 leading-none">{{ p.desc }}</p>
                    <div class="flex items-center space-x-2 text-xs text-slate-400 mt-2 font-medium">
                        <span class="font-mono bg-slate-100 px-1.5 py-0.5 rounded text-slate-500 text-[10px]">#{{ id }}</span>
                        {% if p.utr %}
                        <span class="font-mono bg-indigo-50 px-1.5 py-0.5 rounded text-indigo-600 text-[10px]">Bank UTR: {{ p.utr }}</span>
                        {% endif %}
                        <span>•</span>
                        <span>{{ p.date }}</span>
                    </div>
                </div>
            </div>
            <div class="text-right space-y-1">
                <p class="font-black text-sm text-slate-800">₹{{ "%.2f"|format(p.amount) }}</p>
                <span class="inline-block text-[10px] font-bold px-2 py-0.5 rounded-full {% if p.status == 'Success' %}bg-emerald-100 text-emerald-800{% else %}bg-amber-100 text-amber-800{% endif %}">
                    {{ p.status }}
                </span>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
"""

LINKS_PAGE_HTML = """
<div class="space-y-4">
    <div class="flex justify-between items-center">
        <div>
            <h2 class="text-xl font-bold text-slate-800">Operational Payment Links</h2>
            <p class="text-xs text-slate-400">Distribute infrastructure endpoints directly to downstream clients.</p>
        </div>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {% for link in links %}
        <div class="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-sm flex flex-col justify-between space-y-4">
            <div class="space-y-1">
                <div class="flex justify-between items-center">
                    <span class="text-[10px] font-mono bg-slate-100 text-slate-500 px-2 py-0.5 rounded">ID: {{ link.id }}</span>
                    <span class="text-xs text-slate-400 font-bold"><i class="fa-solid fa-eye"></i> {{ link.clicks }} Hits</span>
                </div>
                <h4 class="font-bold text-slate-700 text-base pt-1">{{ link.title }}</h4>
                <h3 class="text-2xl font-black text-indigo-600">₹{{ "%.2f"|format(link.amount) }}</h3>
            </div>
            <div class="flex space-x-2 pt-2 border-t border-slate-100">
                <a href="/pay/{{ link.id }}" target="_blank" class="flex-1 bg-slate-50 hover:bg-indigo-50 border border-slate-200 text-slate-600 hover:text-indigo-700 font-bold py-2.5 rounded-xl text-xs text-center transition flex items-center justify-center gap-1.5">
                    <i class="fa-solid fa-arrow-up-right-from-square"></i> Open Gateway
                </a>
                <button onclick="navigator.clipboard.writeText(window.location.origin + '/pay/{{ link.id }}'); alert('Hosted URL string copied to systemic storage clipboard.')" class="bg-indigo-50 hover:bg-indigo-100 border border-indigo-100 text-indigo-600 p-2.5 rounded-xl text-xs transition">
                    <i class="fa-solid fa-copy text-sm"></i>
                </button>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
"""

CHECKOUT_GATEWAY_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Secure Central Checkout Portal</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=400;500;600;700;800&display=swap');
        body { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #f1f5f9; overflow-x: hidden; }
        
        /* Razorpay-style High-Speed Coin Animation Mechanics */
        .coin-drop-track {
            position: absolute; top: -60px; left: 50%; transform: translateX(-50%);
            font-size: 40px; z-index: 50; display: none;
        }
        @keyframes animRazorpayCoinDrop {
            0% { top: -60px; transform: translateX(-50%) scale(1); opacity: 1; filter: drop-shadow(0 0 10px rgba(245,158,11,0.6)); }
            80% { top: 65%; transform: translateX(-50%) scale(0.9); opacity: 1; }
            100% { top: 70%; transform: translateX(-50%) scale(0); opacity: 0; }
        }
        .trigger-coin-drop {
            display: block; animation: animRazorpayCoinDrop 0.5s cubic-bezier(0.25, 1, 0.5, 1) forwards;
        }
        
        /* Explosion Boom Ripple Ring */
        .boom-ripple {
            position: absolute; top: 70%; left: 50%; transform: translate(-50%, -50%) scale(0);
            width: 10px; height: 10px; border: 4px solid #10b981; border-radius: 50%;
            z-index: 49; opacity: 0; display: none;
        }
        @keyframes animBoomRipple {
            0% { transform: translate(-50%, -50%) scale(0); opacity: 1; }
            50% { opacity: 0.8; }
            100% { transform: translate(-50%, -50%) scale(22); opacity: 0; border-width: 1px; }
        }
        .trigger-boom { display: block; animation: animBoomRipple 0.6s ease-out forwards; }
    </style>
</head>
<body class="min-h-screen flex flex-col items-center justify-center p-4 bg-gradient-to-tr from-slate-100 to-slate-200 relative">

    <div class="bg-white max-w-sm w-full rounded-3xl shadow-2xl border border-slate-200/80 overflow-hidden relative">
        
        <div id="coin-element" class="coin-drop-track">🪙</div>
        <div id="boom-element" class="boom-ripple"></div>
        
        <div class="bg-gradient-to-br from-indigo-600 via-indigo-700 to-blue-700 text-white p-6 text-center space-y-1 relative">
            <span class="text-[10px] uppercase font-black tracking-widest text-indigo-200 bg-white/10 px-3 py-1 rounded-full backdrop-blur-sm">Escrow Protected Route Node</span>
            <h2 class="text-3xl font-black pt-1.5">₹{{ "%.2f"|format(amount) }}</h2>
            <p class="text-xs text-indigo-100/90 font-medium tracking-tight">{{ desc }}</p>
        </div>

        <div id="checkout-view-port" class="p-6 text-center space-y-5">
            
            <div id="view-state-pending" class="space-y-5">
                <div class="bg-slate-50 border-2 border-dashed border-slate-200 rounded-2xl p-4 flex flex-col items-center relative">
                    <img id="qr-canvas-element" src="https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={{ upi_string }}" alt="UPI QR Asset" class="w-48 h-48 rounded-xl shadow-sm bg-white p-2 border border-slate-100">
                    <p class="text-[10px] text-slate-400 mt-3 font-mono">Gateway Transaction Signature Ref: <span class="text-slate-700 font-bold block text-xs mt-0.5 font-sans">#{{ txn_id }}</span></p>
                </div>

                <div class="sm:hidden">
                    <a href="{{ raw_upi_string }}" class="w-full bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700 text-white text-sm font-bold py-3 px-4 rounded-xl shadow-lg flex items-center justify-center gap-2 transition">
                        <i class="fa-solid fa-bolt"></i> Invoke Local UPI Application
                    </a>
                </div>

                <div id="polling-status-alert-badge" class="flex items-center justify-center space-x-2 text-amber-600 font-bold text-[11px] bg-amber-50/80 py-2.5 rounded-xl border border-amber-100 animate-pulse">
                    <i class="fa-solid fa-spinner animate-spin text-sm"></i>
                    <span>Awaiting Core Account Settlement Verification...</span>
                </div>

                <div class="bg-slate-50 border border-slate-200 rounded-2xl p-4 text-left space-y-2">
                    <span class="text-[11px] font-bold text-slate-600 uppercase tracking-wider block"><i class="fa-solid fa-receipt text-indigo-500"></i> Paste Payment UTR Reference String</span>
                    <p class="text-[11px] text-slate-400 leading-tight">Provide the 12-digit systemic bank UTR confirmation token array below to initialize instant manual verification loops.</p>
                    <div class="flex gap-2 mt-1">
                        <input type="text" id="manual-utr-input" placeholder="Enter 12-Digit UTR Number" class="w-full bg-white border border-slate-200 rounded-xl px-3 py-2 text-xs font-mono focus:outline-none focus:border-indigo-500 text-slate-700">
                        <button onclick="submitManualUtrPayment()" class="bg-indigo-600 hover:bg-indigo-700 text-white font-bold px-4 py-2 rounded-xl text-xs transition shadow-md">Verify</button>
                    </div>
                </div>

                <button id="action-download-qr-btn" class="w-full bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 font-bold py-2.5 rounded-xl text-xs transition flex items-center justify-center gap-1.5 shadow-sm">
                    <i class="fa-solid fa-cloud-arrow-down text-sm text-indigo-600"></i> Save QR Image Asset to Gallery
                </button>
            </div>

            <div id="view-state-success" class="hidden py-6 space-y-5">
                <div class="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center text-3xl mx-auto shadow-xl shadow-emerald-50">
                    <i class="fa-solid fa-circle-check"></i>
                </div>
                <div>
                    <h3 class="text-xl font-black text-slate-800">Transaction Confirmed!</h3>
                    <p class="text-xs text-slate-400 mt-0.5">Asset volumes cleared safely to target merchant arrays.</p>
                </div>
                <div class="bg-slate-50 border border-slate-200 rounded-xl p-3.5 text-left font-mono text-[11px] text-slate-500 space-y-1">
                    <div><span class="font-sans font-bold text-slate-600">Tracking Reference Signature:</span> #{{ txn_id }}</div>
                    <div><span class="font-sans font-bold text-slate-600">Final Volume Clear:</span> ₹{{ amount }}</div>
                    <div id="success-utr-row" class="hidden"><span class="font-sans font-bold text-slate-600">Bank Committed UTR:</span> <span id="success-utr-label"></span></div>
                </div>

                <div id="merchant-redirect-container" class="pt-2">
                    <button onclick="executeClientWebsiteReturn()" class="w-full bg-gradient-to-r from-indigo-600 to-blue-600 text-white text-xs font-bold py-3 px-4 rounded-xl shadow-md transition hover:scale-[1.02] flex items-center justify-center gap-2">
                        <i class="fa-solid fa-arrow-left-long"></i> Return back to Website
                    </button>
                </div>
            </div>

        </div>
    </div>

    <script>
        const txnId = "{{ txn_id }}";
        const targetAmount = "{{ amount }}";
        let clientRedirectOriginUrl = null;

        document.getElementById('action-download-qr-btn').addEventListener('click', async () => {
            try {
                const img = document.getElementById('qr-canvas-element');
                const response = await fetch(img.src);
                const blob = await response.blob();
                const fileUrl = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.download = `ExplorerPay-QR-${txnId}.png`;
                link.href = fileUrl;
                link.click();
                URL.revokeObjectURL(fileUrl);
            } catch (err) { alert('Download mapping array exception.'); }
        });

        function triggerRazorpayCoinExplosion(finalUtr, returnUrl) {
            const coin = document.getElementById('coin-element');
            const boom = document.getElementById('boom-element');
            clientRedirectOriginUrl = returnUrl;
            
            coin.classList.add('trigger-coin-drop');
            
            setTimeout(() => {
                boom.classList.add('trigger-boom');
                setTimeout(() => {
                    document.getElementById('view-state-pending').classList.add('hidden');
                    document.getElementById('view-state-success').classList.remove('hidden');
                    if (finalUtr) {
                        document.getElementById('success-utr-row').classList.remove('hidden');
                        document.getElementById('success-utr-label').innerText = finalUtr;
                    }
                }, 150);
            }, 450);
        }

        function pollGatewayDatabaseState() {
            fetch(`/api/status/${txnId}`)
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'Success') {
                        clearInterval(pollingIntervalWorker);
                        triggerRazorpayCoinExplosion(data.utr, data.redirect_url);
                    }
                })
                .catch(err => console.error("Error monitoring matrix status metrics:", err));
        }
        const pollingIntervalWorker = setInterval(pollGatewayDatabaseState, 2000);

        function submitManualUtrPayment() {
            const utrValue = document.getElementById('manual-utr-input').value.trim();
            if (utrValue.length < 6) {
                alert('Please provide a valid structured verification UTR string array.');
                return;
            }
            
            fetch('/api/webhook/payment-verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ payment_id: txnId, amount: targetAmount, utr: utrValue })
            })
            .then(res => res.json())
            .then(data => { 
                if(data.status === "Success") {
                    clearInterval(pollingIntervalWorker);
                    triggerRazorpayCoinExplosion(utrValue, data.redirect_url);
                } else {
                    alert('Verification infrastructure returned mismatch: ' + data.message);
                }
            })
            .catch(err => alert('Communication with centralized endpoint structure timed out.'));
        }

        // Action trigger to map user safely backward to source system node
        function executeClientWebsiteReturn() {
            if (clientRedirectOriginUrl && clientRedirectOriginUrl !== "null" && clientRedirectOriginUrl !== "") {
                window.location.href = clientRedirectOriginUrl;
            } else {
                alert("Transaction finished. You can now close this payment window tab securely.");
            }
        }
    </script>

</body>
</html>
"""

# -------------------------------------------------------------------------
# CORE EXECUTIVE APPLICATION ENGINE - ROUTING ENDPOINTS
# -------------------------------------------------------------------------
@app.route('/')
def route_merchant_dashboard():
    # DIRECT REGISTRATION LANDING SYSTEM OPTIMIZATION
    if 'username' not in session:
        return redirect(url_for('route_registration_portal'))
        
    merchant = MERCHANTS_DB.get(session['username'])
    merchant_txns = {k: v for k, v in PAYMENTS_DB.items() if v['merchant_username'] == session['username']}
    
    rendered_inner_matrix = render_template_string(OVERVIEW_PAGE_HTML, account=merchant, txns=merchant_txns, username=session['username'])
    return render_template_string(
        BASE_DASHBOARD_HTML, 
        account=merchant,
        username=session['username'], 
        active_tab="overview", 
        main_content=rendered_inner_matrix
    )

@app.route('/links')
def route_links_manager():
    if 'username' not in session:
        return redirect(url_for('route_registration_portal'))
        
    merchant = MERCHANTS_DB.get(session['username'])
    merchant_links = [l for l in LINKS_DB if l['merchant_username'] == session['username']]
    rendered_inner_links = render_template_string(LINKS_PAGE_HTML, links=merchant_links)
    return render_template_string(
        BASE_DASHBOARD_HTML, 
        account=merchant,
        username=session['username'], 
        active_tab="links", 
        main_content=rendered_inner_links
    )

@app.route('/links/create', methods=['POST'])
def handle_link_generation():
    if 'username' not in session:
        return redirect(url_for('route_registration_portal'))
        
    title = request.form.get('title') or "E-Commerce Gateway Processing Invoice Instance"
    amount = float(request.form.get('amount', 0.00))
    link_id = "link-" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
    
    LINKS_DB.append({
        "id": link_id, 
        "merchant_username": session['username'], 
        "title": title, 
        "amount": amount, 
        "clicks": 0
    })
    return redirect(url_for('route_links_manager'))

@app.route('/profile/update', methods=['POST'])
def handle_profile_modification():
    if 'username' not in session:
        return redirect(url_for('route_registration_portal'))
        
    merchant = MERCHANTS_DB.get(session['username'])
    new_upi = request.form.get('upi_vpa').strip()
    new_email = request.form.get('email').strip()
    
    merchant['upi_vpa'] = new_upi
    
    if merchant['email'] != new_email:
        generated_otp = "".join(random.choices(string.digits, k=6))
        EMAIL_UPDATE_CACHE[session['username']] = {
            "pending_email": new_email,
            "otp": generated_otp
        }
        if dispatch_secure_verification_email(new_email, generated_otp):
            return render_template_string(CORE_MASTER_AUTH_LAYOUT, inner_content=EMAIL_VERIFY_PAGE_HTML, pending_email=new_email)
        else:
            return "Critical Error: Mailing infrastructure failed to dispatch update authorization code token.", 500
            
    return redirect(url_for('route_merchant_dashboard'))

@app.route('/profile/verify-email-otp', methods=['POST'])
def verify_profile_email_otp():
    if 'username' not in session:
        return redirect(url_for('route_registration_portal'))
        
    input_otp = request.form.get('otp').strip()
    cache = EMAIL_UPDATE_CACHE.get(session['username'])
    
    if cache and cache['otp'] == input_otp:
        MERCHANTS_DB[session['username']]['email'] = cache['pending_email']
        EMAIL_UPDATE_CACHE.pop(session['username'], None)
        return redirect(url_for('route_merchant_dashboard'))
        
    return render_template_string(CORE_MASTER_AUTH_LAYOUT, inner_content=EMAIL_VERIFY_PAGE_HTML, pending_email=cache['pending_email'] if cache else "", error="Cryptographic mismatch: Verification OTP invalid.")

# --- AUTH INFRASTRUCTURE & DISPATCH CONTROL ENDPOINTS ---
@app.route('/login', methods=['GET', 'POST'])
def route_login_portal():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = MERCHANTS_DB.get(username)
        if user and user['password'] == password:
            session['username'] = username
            return redirect(url_for('route_merchant_dashboard'))
        return render_template_string(CORE_MASTER_AUTH_LAYOUT, inner_content=LOGIN_VIEW_HTML, error="Invalid node credential arrays.")
    return render_template_string(CORE_MASTER_AUTH_LAYOUT, inner_content=LOGIN_VIEW_HTML)

@app.route('/register', methods=['GET', 'POST'])
def route_registration_portal():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        email = request.form.get('email').strip()
        upi_vpa = request.form.get('upi_vpa').strip()
        password = request.form.get('password')
        
        if username in MERCHANTS_DB:
            return render_template_string(CORE_MASTER_AUTH_LAYOUT, inner_content=REGISTER_VIEW_HTML, error="Node Collision: Username identity already deployed.")
            
        for existing_user in MERCHANTS_DB.values():
            if existing_user.get('email') == email:
                return render_template_string(CORE_MASTER_AUTH_LAYOUT, inner_content=REGISTER_VIEW_HTML, error="Node Collision: Email destination matches active arrays.")

        api_key = "pk_live_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))
        secret_key = "sk_live_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=24))
        
        MERCHANTS_DB[username] = {
            "email": email,
            "password": password,
            "upi_vpa": upi_vpa,
            "api_key": api_key,
            "secret_key": secret_key,
            "balance": 0.00,
            "total_earnings": 0.00,
            "total_withdrawals": 0.00
        }
        session['username'] = username
        return redirect(url_for('route_merchant_dashboard'))
    return render_template_string(CORE_MASTER_AUTH_LAYOUT, inner_content=REGISTER_VIEW_HTML)

# --- FORGOT ACCESS PASSPHRASE SMTP OTP COMPLEX LOOPS ---
@app.route('/forgot-password', methods=['GET', 'POST'])
def route_forgot_password_start():
    if request.method == 'POST':
        email = request.form.get('email').strip()
        target_username = None
        for k, v in MERCHANTS_DB.items():
            if v.get('email') == email:
                target_username = k
                break
                
        if not target_username:
            return render_template_string(CORE_MASTER_AUTH_LAYOUT, inner_content=FORGOT_STEP1_HTML, error="Identity mapping failure: Email array not found.")
            
        generated_otp = "".join(random.choices(string.digits, k=6))
        OTP_RESET_CACHE[email] = {
            "otp": generated_otp,
            "username": target_username,
            "verified": False
        }
        
        if dispatch_secure_verification_email(email, generated_otp):
            return render_template_string(CORE_MASTER_AUTH_LAYOUT, inner_content=FORGOT_STEP2_OTP_HTML, target_email=email)
        else:
            return render_template_string(CORE_MASTER_AUTH_LAYOUT, inner_content=FORGOT_STEP1_HTML, error="SMTP protocol loop deployment crashed.")
            
    return render_template_string(CORE_MASTER_AUTH_LAYOUT, inner_content=FORGOT_STEP1_HTML)

@app.route('/forgot-password/verify-otp', methods=['POST'])
def handle_forgot_password_otp_verification():
    email = request.form.get('email')
    input_otp = request.form.get('otp').strip()
    
    cache_record = OTP_RESET_CACHE.get(email)
    if cache_record and cache_record["otp"] == input_otp:
        security_handshake_token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        cache_record["verified"] = True
        cache_record["token"] = security_handshake_token
        
        return render_template_string(CORE_MASTER_AUTH_LAYOUT, inner_content=FORGOT_STEP3_RESET_HTML, target_email=email, verified_token=security_handshake_token)
        
    return render_template_string(CORE_MASTER_AUTH_LAYOUT, inner_content=FORGOT_STEP2_OTP_HTML, target_email=email, error="Cryptographic mismatch: Verification OTP code invalid.")

@app.route('/forgot-password/commit-reset', methods=['POST'])
def handle_forgot_password_commit():
    email = request.form.get('email')
    token = request.form.get('token')
    new_password = request.form.get('new_password')
    
    cache_record = OTP_RESET_CACHE.get(email)
    if cache_record and cache_record["verified"] and cache_record.get("token") == token:
        target_username = cache_record["username"]
        MERCHANTS_DB[target_username]["password"] = new_password
        OTP_RESET_CACHE.pop(email, None)
        return render_template_string(CORE_MASTER_AUTH_LAYOUT, inner_content=LOGIN_VIEW_HTML, success="Passphrase arrays modified successfully. Access unlocked.")
        
    return render_template_string(CORE_MASTER_AUTH_LAYOUT, inner_content=LOGIN_VIEW_HTML, error="Authorization expired or session sequence invalidated.")

@app.route('/logout')
def handle_session_termination():
    session.pop('username', None)
    return redirect(url_for('route_login_portal'))

# --- EXTERNAL PLUG-AND-PLAY SDK / REUSABLE E-COMMERCE CHARGE API ---
@app.route('/api/v1/charge/create', methods=['POST'])
def handle_external_api_charge_requests():
    client_api_key = request.headers.get('X-Gateway-API-Key')
    payload = request.get_json(silent=True) or {}
    
    amount = float(payload.get('amount', 0.00))
    desc = payload.get('description') or "Remote API Integrated Checkout Frame"
    redirect_url = payload.get('redirect_url') or ""  # Capture the third-party return destination parameters
    
    merchant_owner = next((k for k, v in MERCHANTS_DB.items() if v['api_key'] == client_api_key), None)
    if not merchant_owner:
        return jsonify({"error": "Unauthorized API credentials token mapping failed."}), 401
        
    merchant = MERCHANTS_DB[merchant_owner]
    txn_id = "TXN" + ''.join(random.choices(string.digits, k=5))
    
    PAYMENTS_DB[txn_id] = {
        "merchant_username": merchant_owner,
        "amount": amount,
        "status": "Pending",
        "date": datetime.utcnow().strftime('%Y-%m-%d'),
        "desc": desc,
        "utr": None,
        "redirect_url": redirect_url
    }
    
    raw_upi_string = f"upi://pay?pa={merchant['upi_vpa']}&pn=ExplorerPay&tr={txn_id}&tn={txn_id}&am={amount}&cu=INR"
    encoded_upi_string = urllib.parse.quote_plus(raw_upi_string)
    hosted_checkout_url = url_for('route_custom_external_payment_frame', txn_id=txn_id, _external=True)
    
    return jsonify({
        "transaction_id": txn_id,
        "checkout_url": hosted_checkout_url,
        "raw_upi_string": raw_upi_string,
        "encoded_qr_string": encoded_upi_string
    }), 201

@app.route('/pay/checkout-frame/<txn_id>')
def route_custom_external_payment_frame(txn_id):
    txn = PAYMENTS_DB.get(txn_id)
    if not txn:
        return "Transaction frame reference token mapping not found.", 404
        
    merchant = MERCHANTS_DB.get(txn['merchant_username'])
    raw_upi_string = f"upi://pay?pa={merchant['upi_vpa']}&pn=ExplorerPay&tr={txn_id}&tn={txn_id}&am={txn['amount']}&cu=INR"
    encoded_upi_string = urllib.parse.quote_plus(raw_upi_string)
    
    return render_template_string(
        CHECKOUT_GATEWAY_HTML, 
        amount=txn['amount'], 
        desc=txn['desc'], 
        txn_id=txn_id, 
        upi_string=encoded_upi_string, 
        raw_upi_string=raw_upi_string
    )

# --- REUSABLE HOOK ROUTERS AND DYNAMIC TRANSACTION CHANNELS ---
@app.route('/pay/<link_id>')
def route_checkout_gateway(link_id):
    link = next((l for l in LINKS_DB if l["id"] == link_id), None)
    if not link:
        return "Central dynamic address map failed.", 404
        
    link["clicks"] += 1
    merchant = MERCHANTS_DB.get(link['merchant_username'])
    txn_id = "TXN" + ''.join(random.choices(string.digits, k=5))
    
    PAYMENTS_DB[txn_id] = {
        "merchant_username": link['merchant_username'],
        "amount": link["amount"],
        "status": "Pending",
        "date": datetime.utcnow().strftime('%Y-%m-%d'),
        "desc": link["title"],
        "utr": None,
        "redirect_url": ""
    }
    
    raw_upi_string = f"upi://pay?pa={merchant['upi_vpa']}&pn=ExplorerPay&tr={txn_id}&tn={txn_id}&am={link['amount']}&cu=INR"
    encoded_upi_string = urllib.parse.quote_plus(raw_upi_string)
    
    return render_template_string(
        CHECKOUT_GATEWAY_HTML, 
        amount=link['amount'], 
        desc=link['title'], 
        txn_id=txn_id, 
        upi_string=encoded_upi_string, 
        raw_upi_string=raw_upi_string
    )

@app.route('/api/status/<txn_id>')
def check_transaction_status(txn_id):
    txn = PAYMENTS_DB.get(txn_id)
    if txn:
        return jsonify({"status": txn["status"], "utr": txn.get("utr"), "redirect_url": txn.get("redirect_url")})
    return jsonify({"status": "Not Found"}), 404

@app.route('/api/webhook/payment-verify', methods=['POST'])
def handle_automated_bank_verification_webhook():
    payload = request.get_json(silent=True) or {}
    payment_id = payload.get('payment_id')
    received_amount = float(payload.get('amount', 0.00))
    utr_string = payload.get('utr','').strip()
    
    txn = PAYMENTS_DB.get(payment_id)
    if txn and txn["status"] == "Pending":
        txn["status"] = "Success"
        txn["utr"] = utr_string
        
        merchant = MERCHANTS_DB.get(txn['merchant_username'])
        if merchant:
            merchant["balance"] += txn["amount"]
            merchant["total_earnings"] += txn["amount"]
            
            # Fire animated notification card to vendor inbox 
            dispatch_sale_notification_email(merchant["email"], payment_id, txn["desc"], txn["amount"])
        
        return jsonify({"status": "Success", "message": "Transaction verified successfully.", "redirect_url": txn.get("redirect_url")}), 200
            
    return jsonify({"status": "Ignored", "message": "Validation lifecycle failed."}), 400

@app.route('/withdraw/submit', methods=['POST'])
def handle_withdrawal_payout_execution():
    if 'username' not in session:
        return "Unauthorized execution attempt.", 403
        
    merchant = MERCHANTS_DB.get(session['username'])
    amount = float(request.form.get('amount', 0.00))
    method = request.form.get('method')
    destination = request.form.get('destination')
    
    if 0 < amount <= merchant["balance"]:
        merchant["balance"] -= amount
        merchant["total_withdrawals"] += amount
        
        withdrawal_id = "WID" + ''.join(random.choices(string.digits, k=4))
        WITHDRAWALS_DB.append({
            "id": withdrawal_id,
            "merchant_username": session['username'],
            "amount": amount,
            "method": method,
            "destination": destination,
            "date": datetime.utcnow().strftime('%Y-%m-%d'),
            "status": "Settled"
        })
        return redirect(url_for('route_merchant_dashboard'))
        
    return "Error: Withdrawal declined due to insufficient ledger pool assets.", 400

if __name__ == '__main__':
    production_port = int(os.environ.get("PORT", 9666))
    app.run(host='0.0.0.0', port=production_port)
