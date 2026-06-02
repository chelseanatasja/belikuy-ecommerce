import streamlit as st
import sys, os, re
import mysql.connector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from utils import hide_streamlit_ui, require_role
from html_bridge import render_original_html
from unified_sidebar import inject_admin_sidebar, handle_admin_global_action

st.set_page_config(page_title="BeliKuy - Manajemen Pembayaran", layout="wide", initial_sidebar_state="collapsed")
hide_streamlit_ui()
require_role("admin")

# --- Database Connection ---
def get_db_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="",
        database="belikuy"
    )

# --- Fetch Data ---
def fetch_payment_methods():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM payment_methods ORDER BY id DESC")
    methods = cursor.fetchall()
    conn.close()
    return methods

def add_payment_method(name, type_val):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO payment_methods (institution_name, institution_type, status) VALUES (%s, %s, 'active')", (name, type_val))
    conn.commit()
    conn.close()

def delete_payment_method(pid):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM payment_methods WHERE id = %s", (pid,))
    conn.commit()
    conn.close()

def toggle_payment_method(pid, current_status):
    new_status = 'inactive' if current_status == 'active' else 'active'
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE payment_methods SET status = %s WHERE id = %s", (new_status, pid))
    conn.commit()
    conn.close()

# --- Build HTML ---
methods = fetch_payment_methods()
tailwind_config_str = """
tailwind.config = {
    theme: {
        extend: {
            colors: {
                "primary": "#874e58",
                "primary-container": "#ffb6c1",
                "on-primary-container": "#7b444e",
                "surface-container-lowest": "#ffffff",
                "surface-variant": "#e1e3e4",
                "on-surface-variant": "#514345",
                "on-background": "#191c1d",
                "outline": "#847375",
                "surface-container": "#edeeef",
                "primary-fixed-dim": "#fcb3be",
                "error": "#ba1a1a",
                "error-container": "#ffdad6"
            }
        }
    }
}
"""

cards_html = ""
for m in methods:
    is_active = (m['status'] == 'active')
    status_badge = '<span class="bg-primary-container text-on-primary-container text-xs px-3 py-1 rounded-full font-bold">Aktif</span>' if is_active else '<span class="bg-surface-variant text-on-surface-variant text-xs px-3 py-1 rounded-full font-bold">Non-Aktif</span>'
    
    icon_map = {
        'Bank': 'account_balance',
        'Fintech': 'account_balance_wallet',
        'Virtual Account': 'credit_card'
    }
    icon = icon_map.get(m['institution_type'], 'payments')
    
    cards_html += f'''
    <article class="bg-surface-container-lowest rounded-xl p-6 shadow-sm flex items-center justify-between group border border-transparent hover:border-primary-fixed-dim transition-all">
        <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-full bg-primary-container/30 text-primary flex items-center justify-center">
                <span class="material-symbols-outlined">{icon}</span>
            </div>
            <div>
                <h3 class="text-lg font-bold text-on-background">{m['institution_name']}</h3>
                <div class="flex items-center gap-2 mt-1">
                    <span class="text-sm text-on-surface-variant font-medium">{m['institution_type']}</span>
                    {status_badge}
                </div>
            </div>
        </div>
        <div class="flex items-center gap-2">
            <button onclick="stNavigate({{action:'toggle_status', pid:{m['id']}, cstatus:'{m['status']}'}})" class="p-2 rounded-full text-outline hover:text-primary hover:bg-primary-container/20 transition-colors" title="Toggle Status">
                <span class="material-symbols-outlined">{'toggle_on' if is_active else 'toggle_off'}</span>
            </button>
            <button onclick="stNavigate({{action:'delete_method', pid:{m['id']}}})" class="p-2 rounded-full text-error hover:bg-error-container transition-colors" title="Hapus">
                <span class="material-symbols-outlined">delete</span>
            </button>
        </div>
    </article>
    '''

if not cards_html:
    cards_html = '<div class="text-center py-12 text-on-surface-variant w-full">Belum ada metode pembayaran yang dikonfigurasi.</div>'

page_html = f'''<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Manajemen Pembayaran - Admin BeliKuy</title>
<script src="https://cdn.tailwindcss.com?plugins=container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&family=Inter:wght@400;600&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
<script>
{tailwind_config_str}
</script>
<style>
body {{ font-family: "Plus Jakarta Sans", "Inter", sans-serif; background: #f8f9fa; }}
.material-symbols-outlined {{ font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24; font-size: 20px; }}
</style>
</head>
<body class="min-h-screen bg-gray-50 flex">

<main class="flex-1 md:ml-64 p-8 overflow-y-auto">
    <div class="max-w-4xl mx-auto">
        <header class="flex justify-between items-center mb-8">
            <div>
                <h1 class="text-3xl font-bold text-gray-900 mb-2">Manajemen Pembayaran</h1>
                <p class="text-gray-500">Atur metode pembayaran dan dompet digital yang aktif di BeliKuy.</p>
            </div>
            <button onclick="toggleModal()" class="bg-primary text-white px-6 py-2 rounded-full font-semibold hover:bg-[#6c3e46] transition-colors flex items-center gap-2">
                <span class="material-symbols-outlined" style="font-size: 18px;">add</span>
                Tambah Metode
            </button>
        </header>

        <!-- Search Bar -->
        <div class="mb-6 relative">
            <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <span class="material-symbols-outlined text-outline">search</span>
            </div>
            <input type="text" id="searchBox" class="w-full bg-white text-on-surface pl-12 pr-4 py-3 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-container" placeholder="Cari nama bank atau institusi...">
        </div>

        <div class="flex flex-col gap-4">
            {cards_html}
        </div>
    </div>
</main>

<!-- Modal Tambah -->
<div id="addModal" class="fixed inset-0 bg-black/40 backdrop-blur-sm z-[100] hidden flex items-start pt-32 justify-center p-4">
    <div class="bg-white rounded-2xl w-full max-w-md p-6 shadow-2xl relative">
        <button onclick="toggleModal()" class="absolute top-4 right-4 text-gray-400 hover:text-gray-700">
            <span class="material-symbols-outlined">close</span>
        </button>
        <h2 class="text-xl font-bold mb-6">Tambah Metode Pembayaran</h2>
        
        <div class="mb-4">
            <label class="block text-sm font-semibold text-gray-700 mb-2">Nama Institusi</label>
            <input type="text" id="m_name" class="w-full border border-gray-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-container" placeholder="Contoh: OVO, Bank Mandiri">
        </div>
        
        <div class="mb-6">
            <label class="block text-sm font-semibold text-gray-700 mb-2">Tipe Pembayaran</label>
            <select id="m_type" class="w-full border border-gray-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-container bg-white">
                <option value="Bank">Transfer Bank</option>
                <option value="Fintech">Dompet Digital (Fintech)</option>
                <option value="Virtual Account">Virtual Account</option>
            </select>
        </div>
        
        <div class="flex justify-end gap-3">
            <button onclick="toggleModal()" class="px-5 py-2 rounded-full font-semibold text-gray-600 hover:bg-gray-100">Batal</button>
            <button onclick="saveMethod()" class="px-5 py-2 rounded-full font-semibold bg-primary text-white hover:bg-[#6c3e46] shadow-md">Simpan</button>
        </div>
    </div>
</div>

<script>
function stNavigate(params) {{
    if(window.Streamlit) {{
        window.Streamlit.setComponentValue(params);
    }}
}}

function toggleModal() {{
    const modal = document.getElementById('addModal');
    modal.classList.toggle('hidden');
}}

function saveMethod() {{
    const name = document.getElementById('m_name').value;
    const type = document.getElementById('m_type').value;
    if(!name) {{ alert("Nama wajib diisi!"); return; }}
    stNavigate({{action: 'add_method', name: name, mtype: type}});
}}

// Search functionality
document.addEventListener('DOMContentLoaded', function() {{
    const searchBox = document.getElementById('searchBox');
    if(searchBox) {{
        searchBox.addEventListener('input', function(e) {{
            const query = e.target.value.toLowerCase();
            document.querySelectorAll('article').forEach(card => {{
                const text = card.innerText.toLowerCase();
                card.style.display = text.includes(query) ? 'flex' : 'none';
            }});
        }});
    }}
}});
</script>
</body>
</html>
'''

# Inject the unified sidebar
page_html = inject_admin_sidebar(page_html, "21_Manajemen_Pembayaran")

# Render
action_data = render_original_html("belikuy_v2_admin_payments", page_html, height=1000)

if action_data:
    act = action_data.get('action')
    if handle_admin_global_action(st, act):
        pass
    elif act == "add_method":
        add_payment_method(action_data.get("name"), action_data.get("mtype"))
        st.rerun()
    elif act == "delete_method":
        delete_payment_method(action_data.get("pid"))
        st.rerun()
    elif act == "toggle_status":
        toggle_payment_method(action_data.get("pid"), action_data.get("cstatus"))
        st.rerun()
