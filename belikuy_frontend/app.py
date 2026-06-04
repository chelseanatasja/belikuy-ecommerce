import streamlit as st
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import post_api, hide_streamlit_ui
from html_bridge import render_original_html

st.set_page_config(
    page_title="BeliKuy - Login & Register",
    layout="wide",
    initial_sidebar_state="collapsed",
)
hide_streamlit_ui()

# ── Session state ──
if "user" not in st.session_state:
    st.session_state["user"] = None

# Auto-redirect
if st.session_state.get("user"):
    role = st.session_state["user"]["role"]
    if role == "admin":
        st.switch_page("pages/13_Admin_Dashboard.py")
    elif role == "seller":
        st.switch_page("pages/9_Seller_Dashboard.py")
    elif role == "supplier":
        st.switch_page("pages/24_Supplier_Dashboard.py")
    elif role == "fintech":
        st.switch_page("pages/25_Fintech_Dashboard.py")
    elif role == "delivery":
        st.switch_page("pages/26_Delivery_Dashboard.py")
    else:
        st.switch_page("pages/1_Storefront.py")

HTML_BASE = (
    r"D:\Tugas Kuliah\Semester 4\Workshop RPL\belikuy-ecommerce\belikuy_ui_templates"
)

with open(
    os.path.join(HTML_BASE, "login_register_page/code.html"), encoding="utf-8"
) as f:
    html = f.read()

# Error handling alerts from previous actions
alert_js = ""


if "_login_error" in st.session_state:
    st.error(f"❌ {st.session_state.pop('_login_error')}")
elif "_reg_error" in st.session_state:
    st.error(f"❌ {st.session_state.pop('_reg_error')}")
elif "_reg_success" in st.session_state:
    st.success("✅ Akun berhasil dibuat! Silakan login.")
    st.session_state.pop("_reg_success")

js_head = f"""<script>
function doLogin() {{
    var emailEl = document.getElementById('bk-email');
    var passEl  = document.getElementById('bk-pass');
    if (!emailEl || !passEl) return;
    var email = emailEl.value.trim();
    var pass  = passEl.value;
    if (!email) {{ alert('Email wajib diisi!'); emailEl.focus(); return; }}
    if (!pass)  {{ alert('Password wajib diisi!'); passEl.focus(); return; }}
    stNavigate({{ action: 'do_login', email: email, password: pass }});
}}

function doRegister() {{
    var uname = document.getElementById('reg-username');
    var email = document.getElementById('reg-email');
    var pass  = document.getElementById('reg-password');
    var role  = document.getElementById('reg-role');
    if (!uname || !email || !pass) return;
    var u = uname.value.trim(), e = email.value.trim(),
        p = pass.value, r = role ? role.value : 'customer';
    if (!u) {{ alert('Username wajib diisi!'); uname.focus(); return; }}
    if (!e) {{ alert('Email wajib diisi!'); email.focus(); return; }}
    if (!p) {{ alert('Password wajib diisi!'); pass.focus(); return; }}
    stNavigate({{ action: 'do_register', username: u, email: e, password: p, role: r }});
}}

function showRegister() {{
    var ls = document.getElementById('bk-login-section');
    var rs = document.getElementById('bk-register-section');
    if (ls) ls.style.display = 'none';
    if (rs) rs.style.display = 'block';
}}

function showLogin() {{
    var ls = document.getElementById('bk-login-section');
    var rs = document.getElementById('bk-register-section');
    if (ls) ls.style.display = 'block';
    if (rs) rs.style.display = 'none';
}}

{alert_js}
</script>
"""
html = html.replace("</head>", js_head + "\n</head>", 1)

# Modify inputs to add IDs
html = html.replace(
    'placeholder="Email" type="email"',
    'id="bk-email" placeholder="Email" type="email"',
    1,
)
html = html.replace(
    'placeholder="Kata Sandi" type="password"',
    'id="bk-pass" placeholder="Kata Sandi" type="password"',
    1,
)
html = re.sub(
    r'(<button[^>]*type="button"[^>]*>)\s*MASUK SEKARANG',
    r"\1\n                        MASUK SEKARANG",
    html,
    count=1,
)
# Just insert onclick right before type="button" for the login button
html = html.replace(
    '<form class="space-y-md">',
    '<div class="space-y-md" onkeypress="if(event.key === \'Enter\') doLogin();">',
)
html = html.replace(
    'type="button">\n                        MASUK SEKARANG',
    'type="button" onclick="doLogin(); return false;">\n                        MASUK SEKARANG',
)
html = html.replace(
    'href="#">Daftar di sini</a>',
    'href="#" onclick="showRegister(); return false;">Daftar di sini</a>',
    1,
)
html = html.replace("</form>", "</div>", 1)

# Add Register HTML Block
REGISTER_HTML = """
<div id="bk-register-section" style="display:none;" class="w-full max-w-md mx-auto space-y-lg">
  <div class="text-center md:text-left space-y-sm">
    <h2 class="font-h2 text-h2 text-on-background">Daftar</h2>
    <p class="font-body-md text-body-md text-on-surface-variant">Bergabung dengan jutaan pembeli &amp; penjual di BeliKuy!</p>
  </div>
  <div class="space-y-md">
    <div class="relative">
      <div class="absolute inset-y-0 left-0 pl-md flex items-center pointer-events-none"><span class="material-symbols-outlined text-outline">person</span></div>
      <input id="reg-username" class="w-full pl-[48px] pr-md py-3 bg-surface-bright border-none rounded-lg font-body-md text-body-md text-on-surface focus:ring-2 focus:ring-primary-container outline-none placeholder:text-outline-variant" placeholder="Username" type="text"/>
    </div>
    <div class="relative">
      <div class="absolute inset-y-0 left-0 pl-md flex items-center pointer-events-none"><span class="material-symbols-outlined text-outline">mail</span></div>
      <input id="reg-email" class="w-full pl-[48px] pr-md py-3 bg-surface-bright border-none rounded-lg font-body-md text-body-md text-on-surface focus:ring-2 focus:ring-primary-container outline-none placeholder:text-outline-variant" placeholder="Email" type="email"/>
    </div>
    <div class="relative">
      <div class="absolute inset-y-0 left-0 pl-md flex items-center pointer-events-none"><span class="material-symbols-outlined text-outline">lock</span></div>
      <input id="reg-password" class="w-full pl-[48px] pr-md py-3 bg-surface-bright border-none rounded-lg font-body-md text-body-md text-on-surface focus:ring-2 focus:ring-primary-container outline-none placeholder:text-outline-variant" placeholder="Kata Sandi" type="password"/>
    </div>
    <div class="relative">
      <div class="absolute inset-y-0 left-0 pl-md flex items-center pointer-events-none"><span class="material-symbols-outlined text-outline">group</span></div>
      <select id="reg-role" class="w-full pl-[48px] pr-md py-3 bg-surface-bright border-none rounded-lg font-body-md text-body-md text-on-surface focus:ring-2 focus:ring-primary-container outline-none cursor-pointer" style="appearance:none;">
        <option value="customer">&#128100; Pembeli (Customer)</option>
        <option value="seller">&#127978; Penjual (Seller)</option>
        <option value="supplier">&#127981; Supplier (B2B)</option>
        <option value="fintech">&#127974; Fintech (Bank)</option>
        <option value="delivery">&#128666; Kurir (Ekspedisi)</option>
      </select>
    </div>
    <button onclick="doRegister()" class="w-full py-4 rounded-full bg-gradient-to-r from-primary-container to-secondary-container text-on-primary-container font-label-caps text-label-caps hover:shadow-[0_8px_20px_rgba(255,182,193,0.4)] hover:-translate-y-0.5 transition-all duration-300" type="button">
      DAFTAR SEKARANG
    </button>
    <div class="text-center font-body-sm text-body-sm pt-md">
      <span class="text-on-surface-variant">Sudah punya akun?</span>
      <a href="#" onclick="showLogin(); return false;" class="text-primary font-medium hover:text-on-primary-container transition-colors ml-1">Masuk di sini</a>
    </div>
  </div>
</div>
<div id="bk-login-section">
"""
html = html.replace(
    '<div class="w-full max-w-md mx-auto space-y-lg">',
    REGISTER_HTML + '<div class="w-full max-w-md mx-auto space-y-lg">',
    1,
)
html = html.replace(
    "</div>\n</div>\n</div>\n</body>",
    "</div>\n</div>\n</div>\n</div>\n</div>\n</body>",
    1,
)

# Remove Social Logins section
html = re.sub(
    r"(<!-- Divider -->.*?<span>Facebook</span>\s*</button>\s*</div>)",
    "",
    html,
    flags=re.IGNORECASE | re.DOTALL,
)

# Render HTML using custom bridge
# This returns the params sent via Streamlit.setComponentValue
action_data = render_original_html("belikuy_v2_login_v2", html)

if action_data:
    if action_data.get("action") == "do_login":
        email = action_data.get("email")
        password = action_data.get("password")
        data, status = post_api("auth/login", {"email": email, "password": password})
        if status == 200:
            st.session_state["user"] = data["user"]
            role = data["user"]["role"]
            if role == "admin":
                st.switch_page("pages/13_Admin_Dashboard.py")
            elif role == "seller":
                st.switch_page("pages/9_Seller_Dashboard.py")
            elif role == "supplier":
                st.switch_page("pages/24_Supplier_Dashboard.py")
            elif role == "fintech":
                st.switch_page("pages/25_Fintech_Dashboard.py")
            elif role == "delivery":
                st.switch_page("pages/26_Delivery_Dashboard.py")
            else:
                st.switch_page("pages/1_Storefront.py")
        else:
            st.error(f"DEBUG: Login failed with status {status}, data: {data}")
            st.session_state["_login_error"] = data.get(
                "error", "Login gagal. Periksa email/password."
            )
            st.rerun()

    elif action_data.get("action") == "do_register":
        username = action_data.get("username")
        email = action_data.get("email")
        password = action_data.get("password")
        role_reg = action_data.get("role")
        data, status = post_api(
            "auth/register",
            {
                "username": username,
                "email": email,
                "password": password,
                "role": role_reg,
            },
        )
        if status == 201:
            st.session_state["_reg_success"] = True
            st.rerun()
        else:
            st.session_state["_reg_error"] = data.get("error", "Registrasi gagal.")
            st.rerun()
