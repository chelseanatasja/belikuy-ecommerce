import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from utils import get_api, put_api, post_api, require_role, hide_streamlit_ui, format_rupiah, get_image_base64
from html_bridge import render_original_html
from unified_sidebar import inject_seller_sidebar, handle_seller_global_action

st.set_page_config(page_title="BeliKuy - Pengaturan Toko", layout="wide", initial_sidebar_state="collapsed")
hide_streamlit_ui()
require_role("seller")

user = st.session_state['user']
company = user.get('company', {}); company_id = company.get('company_id') if company else None

# Fetch company info fresh from DB
company_info, _ = get_api(f"companies/{company_id}") if company_id else ({}, None)
if not company_info: company_info = {}

company_name   = company_info.get('company_name', '') or ''
company_addr   = company_info.get('address', '') or ''
company_rating = float(company_info.get('rating') or 0)
user_email     = user.get('email', '') or ''
user_username  = user.get('username', '') or ''


settings_html = f'''<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Pengaturan Toko - BeliKuy</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&family=Inter:wght@400;600&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
<script id="tailwind-config">
tailwind.config = {{
    darkMode: "class",
    theme: {{
        extend: {{
            colors: {{
                "primary": "#874e58", "primary-container": "#ffb6c1", "on-primary": "#ffffff",
                "on-primary-container": "#7b444e", "secondary": "#715572", "secondary-container": "#f8d5f7",
                "surface": "#f8f9fa", "surface-bright": "#f8f9fa", "surface-container-lowest": "#ffffff",
                "surface-container-low": "#f3f4f5", "surface-container": "#edeeef",
                "surface-container-high": "#e7e8e9", "surface-variant": "#e1e3e4",
                "on-background": "#191c1d", "on-surface": "#191c1d", "on-surface-variant": "#514345",
                "outline": "#847375", "outline-variant": "#d6c2c3", "background": "#f8f9fa",
                "error": "#ba1a1a", "error-container": "#ffdad6", "primary-fixed": "#ffd9de",
                "tertiary-fixed": "#f7ddda",
            }},
            fontFamily: {{ "sans": ["Plus Jakarta Sans", "Inter", "sans-serif"] }}
        }}
    }}
}}
</script>
<style>
.material-symbols-outlined {{ font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; }}
input, textarea, select {{ font-family: "Inter", sans-serif; }}
</style>
</head>
<body class="bg-background text-on-background font-sans min-h-screen flex">

<!-- Main Content -->
<main class="flex-1 md:ml-64 p-6 md:p-10 min-h-screen">
    <header class="mb-8">
        <h1 class="text-3xl font-bold text-on-background">Pengaturan Toko</h1>
        <p class="text-on-surface-variant mt-1">Kelola informasi toko dan akun kamu</p>
    </header>

    <!-- Info cards at top -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div class="bg-surface-container-lowest rounded-xl p-4 shadow-sm text-center">
            <span class="material-symbols-outlined text-primary text-3xl" style="font-variation-settings: 'FILL' 1;">storefront</span>
            <p class="text-xs text-on-surface-variant mt-1">Nama Toko</p>
            <p class="font-semibold text-on-surface text-sm mt-1 truncate">{company_name}</p>
        </div>
        <div class="bg-surface-container-lowest rounded-xl p-4 shadow-sm text-center">
            <span class="material-symbols-outlined text-yellow-500 text-3xl" style="font-variation-settings: 'FILL' 1;">star</span>
            <p class="text-xs text-on-surface-variant mt-1">Rating Toko</p>
            <p class="font-semibold text-on-surface text-sm mt-1">{company_rating:.1f} / 5.0</p>
        </div>
        <div class="bg-surface-container-lowest rounded-xl p-4 shadow-sm text-center">
            <span class="material-symbols-outlined text-secondary text-3xl" style="font-variation-settings: 'FILL' 1;">person</span>
            <p class="text-xs text-on-surface-variant mt-1">Username</p>
            <p class="font-semibold text-on-surface text-sm mt-1 truncate">{user_username}</p>
        </div>
        <div class="bg-surface-container-lowest rounded-xl p-4 shadow-sm text-center">
            <span class="material-symbols-outlined text-primary text-3xl" style="font-variation-settings: 'FILL' 1;">mail</span>
            <p class="text-xs text-on-surface-variant mt-1">Email</p>
            <p class="font-semibold text-on-surface text-sm mt-1 truncate">{user_email}</p>
        </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Edit Info Toko -->
        <section class="bg-surface-container-lowest rounded-2xl p-6 shadow-sm">
            <div class="flex items-center gap-3 mb-6">
                <div class="w-10 h-10 rounded-full bg-primary-container flex items-center justify-center">
                    <span class="material-symbols-outlined text-primary" style="font-variation-settings: 'FILL' 1;">storefront</span>
                </div>
                <div>
                    <h2 class="font-bold text-on-background text-lg">Informasi Toko</h2>
                    <p class="text-xs text-on-surface-variant">Update nama dan alamat toko</p>
                </div>
            </div>
            <div class="space-y-4">
                <div>
                    <label class="block text-xs font-semibold text-on-surface-variant uppercase tracking-wider mb-2">Nama Toko</label>
                    <input id="s_company_name" type="text" value="{company_name}"
                        class="w-full bg-surface-container-low border border-outline-variant rounded-xl py-3 px-4 focus:ring-2 focus:ring-primary-container outline-none text-on-surface"/>
                </div>
                <div>
                    <label class="block text-xs font-semibold text-on-surface-variant uppercase tracking-wider mb-2">Alamat Toko</label>
                    <textarea id="s_address" rows="3"
                        class="w-full bg-surface-container-low border border-outline-variant rounded-xl py-3 px-4 focus:ring-2 focus:ring-primary-container outline-none resize-none text-on-surface"
                        placeholder="Alamat lengkap toko...">{company_addr}</textarea>
                </div>
                <button onclick="saveToko()"
                    class="w-full py-3 rounded-xl bg-primary text-on-primary font-semibold hover:opacity-90 transition-all shadow-[0_4px_14px_rgba(135,78,88,0.3)]">
                    Simpan Perubahan
                </button>
            </div>
        </section>

        <!-- Informasi Akun (read-only) -->
        <section class="bg-surface-container-lowest rounded-2xl p-6 shadow-sm">
            <div class="flex items-center gap-3 mb-6">
                <div class="w-10 h-10 rounded-full bg-secondary-container flex items-center justify-center">
                    <span class="material-symbols-outlined text-secondary" style="font-variation-settings: 'FILL' 1;">manage_accounts</span>
                </div>
                <div>
                    <h2 class="font-bold text-on-background text-lg">Informasi Akun</h2>
                    <p class="text-xs text-on-surface-variant">Data akun seller kamu</p>
                </div>
            </div>
            <div class="space-y-4">
                <div class="bg-surface-container-low rounded-xl p-4">
                    <p class="text-xs text-on-surface-variant mb-1">Username</p>
                    <p class="font-semibold text-on-surface">{user_username}</p>
                </div>
                <div class="bg-surface-container-low rounded-xl p-4">
                    <p class="text-xs text-on-surface-variant mb-1">Email</p>
                    <p class="font-semibold text-on-surface">{user_email}</p>
                </div>
                <div class="bg-surface-container-low rounded-xl p-4">
                    <p class="text-xs text-on-surface-variant mb-1">Role</p>
                    <span class="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-primary-container text-on-primary-container text-sm font-semibold">
                        <span class="material-symbols-outlined text-[14px]" style="font-variation-settings: 'FILL' 1;">verified</span> Seller
                    </span>
                </div>
                <div class="bg-surface-container-low rounded-xl p-4">
                    <p class="text-xs text-on-surface-variant mb-1">Rating Toko</p>
                    <div class="flex items-center gap-2">
                        <span class="material-symbols-outlined text-yellow-500 text-[20px]" style="font-variation-settings: 'FILL' 1;">star</span>
                        <p class="font-semibold text-on-surface">{company_rating:.1f} / 5.0</p>
                    </div>
                </div>
            </div>
        </section>

        <!-- Danger Zone -->
        <section class="bg-surface-container-lowest rounded-2xl p-6 shadow-sm lg:col-span-2 border border-error-container">
            <div class="flex items-center gap-3 mb-4">
                <div class="w-10 h-10 rounded-full bg-error-container flex items-center justify-center">
                    <span class="material-symbols-outlined text-error" style="font-variation-settings: 'FILL' 1;">warning</span>
                </div>
                <div>
                    <h2 class="font-bold text-error text-lg">Danger Zone</h2>
                    <p class="text-xs text-on-surface-variant">Aksi berikut tidak dapat diurungkan</p>
                </div>
            </div>
            <div class="flex flex-col sm:flex-row gap-4">
                <button onclick="stNavigate({{action:'logout'}})"
                    class="flex items-center gap-2 px-6 py-3 rounded-xl border border-error text-error hover:bg-error-container transition-colors font-semibold">
                    <span class="material-symbols-outlined">logout</span> Keluar dari Akun
                </button>
            </div>
        </section>
    </div>
</main>

<div id="toast" class="fixed bottom-6 right-6 z-50 hidden">
    <div class="bg-on-background text-surface px-5 py-3 rounded-xl shadow-xl flex items-center gap-3 text-sm font-semibold">
        <span class="material-symbols-outlined text-green-400" style="font-variation-settings: 'FILL' 1;">check_circle</span>
        <span id="toast_msg">Tersimpan!</span>
    </div>
</div>

</body></html>'''

settings_html = inject_seller_sidebar(settings_html, "19_Seller_Settings", company_name)

js_head = f"""<script>
function stNavigate(params) {{
    params._ts = Date.now();
    if(window.Streamlit) {{ window.Streamlit.setComponentValue(params); }}
}}
function showToast(msg) {{
    const t = document.getElementById('toast');
    document.getElementById('toast_msg').textContent = msg;
    t.classList.remove('hidden');
    setTimeout(() => t.classList.add('hidden'), 3000);
}}
function saveToko() {{
    const name = document.getElementById('s_company_name').value.trim();
    const addr = document.getElementById('s_address').value.trim();
    if (!name) {{ alert('Nama toko tidak boleh kosong!'); return; }}
    stNavigate({{action: 'save_toko', name: name, addr: addr}});
}}
</script>"""
settings_html = settings_html.replace("</head>", js_head + "</head>")

action_data = render_original_html("belikuy_v2_settings", settings_html, height=1200)

if action_data:
    act = action_data.get('action')
    if handle_seller_global_action(st, act):
        pass
    elif act == "save_toko":
        name = action_data.get("name", "").strip()
        addr = action_data.get("addr", "")
        if name and company_id:
            resp, code = put_api(f"companies/{company_id}", {"company_name": name, "address": addr})
            if code == 200:
                st.success("✅ Informasi toko berhasil diperbarui!")
                # Update session
                if user.get('company'):
                    st.session_state['user']['company']['company_name'] = name
            else:
                st.error(f"Gagal menyimpan: {resp}")
        st.rerun()
