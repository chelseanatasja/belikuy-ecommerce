"""
BeliKuy - Shared utilities for all Streamlit pages
"""
import streamlit as st
import requests
import os

API_URL = "http://localhost:3000/api"
HTML_BASE = r"D:\belikuy\belikuy_ui_templates"

# ── HTTP API Helpers ──────────────────────────────────────────────────────────

def get_api(endpoint, params=None):
    try:
        r = requests.get(f"{API_URL}/{endpoint}", params=params, timeout=8)
        if r.status_code == 200:
            return r.json(), None
        return None, r.json().get('error', 'Error')
    except Exception as e:
        return None, str(e)

def post_api(endpoint, data):
    try:
        r = requests.post(f"{API_URL}/{endpoint}", json=data, timeout=8)
        return r.json(), r.status_code
    except Exception as e:
        return {"error": str(e)}, 500

def put_api(endpoint, data):
    try:
        r = requests.put(f"{API_URL}/{endpoint}", json=data, timeout=8)
        return r.json(), r.status_code
    except Exception as e:
        return {"error": str(e)}, 500

def delete_api(endpoint, data=None):
    try:
        r = requests.delete(f"{API_URL}/{endpoint}", json=data, timeout=8)
        return r.json(), r.status_code
    except Exception as e:
        return {"error": str(e)}, 500

# ── Auth / Session Helpers ────────────────────────────────────────────────────

def check_session():
    return bool(st.session_state.get('user'))

def require_login():
    if not check_session():
        if st.session_state.get('_redirect_to_login'):
            st.session_state.pop('_redirect_to_login')
            st.switch_page("app.py")
        else:
            from html_bridge import render_original_html
            empty_html = "<html><head></head><body style='background:transparent; display:flex; justify-content:center; align-items:center; height:100vh; font-family:sans-serif; color:#666;'>Sedang memulihkan sesi...</body></html>"
            render_original_html("global_auto_login_handler", empty_html, height=200)
            st.stop()

def require_role(role):
    require_login()
    if st.session_state['user'].get('role', '') != role:
        st.error(f"🚫 Akses ditolak. Halaman ini hanya untuk {role}.")
        st.stop()

# ── HTML Template Helpers ─────────────────────────────────────────────────────

def load_html(relative_path: str) -> str:
    """Baca file HTML original dari folder UI design."""
    full_path = os.path.join(HTML_BASE, relative_path)
    with open(full_path, encoding='utf-8') as f:
        return f.read()

def inject_bridge(html: str, extra_js: str = "") -> str:
    """
    Injeksikan Streamlit JS bridge ke HTML original.
    stNavigate(params_dict) → update URL params → Streamlit handles the action.
    """
    bridge = f"""
<script>
// ── BeliKuy Streamlit Bridge v2 ──────────────────────────────────────────────
function stNavigate(params) {{
    try {{
        const url = new URL(window.parent.location.href);
        // Clear previous action params
        const keysToDelete = [];
        url.searchParams.forEach((v, k) => keysToDelete.push(k));
        keysToDelete.forEach(k => url.searchParams.delete(k));
        // Set new params
        Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
        window.parent.location.href = url.toString();
    }} catch(e) {{
        // fallback: direct location
        const qs = Object.entries(params).map(([k,v]) => k+'='+encodeURIComponent(v)).join('&');
        window.parent.location.search = '?' + qs;
    }}
}}

{extra_js}
// ─────────────────────────────────────────────────────────────────────────────
</script>
<style>
/* Global standardize for page titles to ensure consistency */
h1 {{
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 28px !important;
    font-weight: 700 !important;
    line-height: 1.2 !important;
    letter-spacing: -0.02em !important;
    color: #191c1d !important;
    margin-bottom: 8px !important;
}}
</style>
"""
    if '</body>' in html:
        return html.replace('</body>', bridge + '\n</body>', 1)
    return html + bridge


def get_html_template(filename):
    """Alias untuk load_html."""
    return load_html(filename)

# ── Streamlit UI Helpers ──────────────────────────────────────────────────────

def hide_streamlit_ui():
    """Sembunyikan semua chrome Streamlit (header, footer, sidebar)."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    .block-container {padding: 0 !important; max-width: 100% !important; margin: 0 !important;}
    [data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"], [data-testid="stHeader"] {display: none !important;}
    section[data-testid="stSidebar"] {display: none !important;}
    
    /* Allow Streamlit to scroll with iframe content */
    body { overflow-x: hidden !important; overflow-y: auto !important; }
    .stApp { overflow: visible !important; background: transparent !important; }
    iframe {
        width: 100% !important;
        border: none !important;
        display: block !important;
    }
    </style>
    """, unsafe_allow_html=True)


def format_rupiah(amount):
    if amount is None: return "Rp 0"
    try:
        return f"Rp {int(float(amount)):,}".replace(',', '.')
    except:
        return f"Rp {amount}"

def get_current_user():
    return st.session_state.get('user')

def get_company_id():
    user = get_current_user()
    if user and user.get('company'):
        return user['company'].get('company_id')
    return None

def get_image_base64(image_path):
    """Membaca file gambar lokal dan mengubahnya menjadi base64 data URI untuk HTML."""
    if not image_path:
        return ""
    if image_path.startswith("http"):
        return image_path
        
    try:
        import base64
        import os
        
        # Ensure path uses correct separators
        clean_path = image_path.replace("\\", "/")
        
        # Try to resolve path relative to belikuy_frontend
        base_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_dir, clean_path)
        
        if os.path.exists(full_path):
            with open(full_path, "rb") as img_file:
                encoded = base64.b64encode(img_file.read()).decode('utf-8')
                
            ext = os.path.splitext(full_path)[1].lower()
            mime = "image/png" if ext == ".png" else "image/jpeg"
            return f"data:{mime};base64,{encoded}"
        return ""
    except Exception as e:
        print("Error loading image:", e)
        return ""
