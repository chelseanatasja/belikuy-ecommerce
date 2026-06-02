import streamlit as st
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from utils import get_api, post_api, delete_api, require_role, hide_streamlit_ui
from html_bridge import render_original_html
from unified_sidebar import inject_admin_sidebar, handle_admin_global_action

st.set_page_config(page_title="BeliKuy - Manajemen Ekspedisi", layout="wide", initial_sidebar_state="collapsed")
hide_streamlit_ui()
require_role("admin")

import mysql.connector

def get_db_connection():
    return mysql.connector.connect(host="127.0.0.1", user="root", password="", database="belikuy")

conn = get_db_connection()
cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT * FROM shipment_companies ORDER BY id DESC")
companies = cursor.fetchall()
conn.close()

HTML_BASE = r"D:\belikuy\belikuy_ui_templates"
with open(os.path.join(HTML_BASE, "super_admin_shipment_management/code.html"), encoding='utf-8') as f:
    html = f.read()

# Build Cards
cards = ""
for c in companies:
    is_active = (c.get('status', 'active') == 'active')
    status_dot = '<span class="w-2 h-2 rounded-full bg-emerald-400"></span>' if is_active else '<span class="w-2 h-2 rounded-full bg-gray-400"></span>'
    status_text = 'Aktif' if is_active else 'Nonaktif'
    toggle_icon = 'toggle_on' if is_active else 'toggle_off'
    
    cards += f'''
    <article class="bg-surface-container-lowest rounded-xl p-lg shadow-[0_8px_30px_rgb(255,182,193,0.05)] flex flex-col relative group">
        <div class="flex justify-between items-start mb-6">
            <div class="w-16 h-16 rounded-xl bg-primary-container text-primary flex items-center justify-center overflow-hidden font-h3 font-bold text-2xl">
                {c.get("company_name", "E")[0].upper()}
            </div>
            <button onclick="stNavigate({{action:'toggle_shipment', sid:{c.get('id')}, cstatus:'{c.get('status', 'active')}'}})" class="p-2 rounded-full text-outline hover:text-primary transition-colors" title="Toggle Status">
                <span class="material-symbols-outlined text-[28px]">{toggle_icon}</span>
            </button>
        </div>
        <h3 class="font-h3 text-h3 text-on-surface mb-1">{c.get("company_name","")}</h3>
        <p class="font-body-sm text-body-sm text-on-surface-variant mb-6 flex items-center gap-1">
            {status_dot} {status_text}
        </p>
        <div class="space-y-4 flex-1">
            <div class="bg-surface rounded-lg p-4">
                <p class="font-label-caps text-label-caps text-on-surface-variant mb-2">Layanan Tersedia</p>
                <div class="flex flex-wrap gap-2">
                    <span class="px-3 py-1 bg-primary-container/30 text-on-primary-container font-body-sm text-[12px] rounded-full">{c.get("service_type","")}</span>
                </div>
            </div>
        </div>
        <div class="mt-6 flex gap-2">
            <button onclick="stNavigate({{action:'delete_shipment', sid:{c.get('id')}}})" class="flex-1 bg-error-container text-on-error-container font-label-caps text-[12px] py-2 rounded-full hover:bg-error hover:text-on-error transition-colors">Hapus</button>
        </div>
    </article>
    '''

if not cards:
    cards = '<div class="col-span-1 md:col-span-2 lg:col-span-3 text-center py-12 text-on-surface-variant">Belum ada ekspedisi terdaftar.</div>'

html = re.sub(r'(<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-lg">)(.*?)(</main>)', rf'\1{cards}</div>\3', html, flags=re.DOTALL)

# Add Modal
modal_html = f'''
<div id="addModal" class="fixed inset-0 bg-inverse-surface/40 backdrop-blur-sm z-[100] hidden flex items-start pt-32 justify-center p-4">
    <div class="bg-surface-container-lowest rounded-xl w-full max-w-md p-xl shadow-[0_20px_50px_rgba(255,182,193,0.3)] relative transform transition-transform">
        <button onclick="toggleModal()" type="button" class="absolute top-6 right-6 text-on-surface-variant hover:text-error transition-colors p-2 rounded-full hover:bg-surface-container">
            <span class="material-symbols-outlined">close</span>
        </button>
        <h2 class="font-h2 text-h2 text-on-background mb-6">Tambah Kurir Baru</h2>
        <div class="mb-4">
            <label class="font-label-caps text-label-caps text-on-surface-variant ml-2 block mb-2">Nama Ekspedisi</label>
            <input id="s_name" type="text" class="w-full bg-surface-bright border-none rounded-lg py-3 px-4 focus:ring-2 focus:ring-primary-container" placeholder="Contoh: JNE"/>
        </div>
        <div class="mb-6">
            <label class="font-label-caps text-label-caps text-on-surface-variant ml-2 block mb-2">Tipe Layanan</label>
            <input id="s_type" type="text" class="w-full bg-surface-bright border-none rounded-lg py-3 px-4 focus:ring-2 focus:ring-primary-container" placeholder="Contoh: Reguler"/>
        </div>
        <div class="flex justify-end gap-4">
            <button type="button" onclick="toggleModal()" class="px-6 py-3 rounded-full font-label-caps text-label-caps text-on-surface-variant hover:bg-surface-container transition-colors">Batal</button>
            <button type="button" onclick="saveShipment()" class="px-8 py-3 rounded-full font-label-caps text-label-caps bg-primary text-on-primary hover:bg-surface-tint shadow-[0_4px_14px_rgba(255,182,193,0.4)] transition-all">Simpan</button>
        </div>
    </div>
</div>
'''
html = html.replace('</body>', modal_html + '</body>')

js_head = """<script>
function stNavigate(params) {
    if(window.Streamlit) {
        window.Streamlit.setComponentValue(params);
    }
}
function toggleModal() {
    const modal = document.getElementById('addModal');
    if (modal.classList.contains('hidden')) {
        modal.classList.remove('hidden');
    } else {
        modal.classList.add('hidden');
    }
}
function saveShipment() {
    const name = document.getElementById('s_name').value;
    const type = document.getElementById('s_type').value;
    if(!name || !type) { alert("Semua field wajib diisi!"); return; }
    stNavigate({action: 'add_shipment', name: name, stype: type});
}

document.addEventListener('DOMContentLoaded', function() {
    // Add shipment button
    document.querySelectorAll('button').forEach(btn => {
        if (btn.textContent.toLowerCase().includes('tambah kurir')) {
            btn.onclick = toggleModal;
        }
    });
});
</script>"""
html = html.replace("</head>", js_head + "</head>")
html = html.replace('href="#"', 'href="#" onclick="event.preventDefault();"')

html = inject_admin_sidebar(html, "16_Manajemen_Ekspedisi")

action_data = render_original_html("belikuy_v2_admin_shipment", html, height=1200)

if action_data:
    act = action_data.get('action')
    if handle_admin_global_action(st, act):
        pass
    elif act == "add_shipment":
        name = action_data.get("name", "")
        stype = action_data.get("stype", "")
        if name and stype:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO shipment_companies (company_name, service_type) VALUES (%s, %s)", (name, stype))
            conn.commit()
            conn.close()
        st.rerun()
    elif act == "delete_shipment":
        sid = action_data.get("sid")
        if sid:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM shipment_companies WHERE id = %s", (sid,))
            conn.commit()
            conn.close()
        st.rerun()
    elif act == "toggle_shipment":
        sid = action_data.get("sid")
        cstatus = action_data.get("cstatus")
        if sid:
            new_status = 'inactive' if cstatus == 'active' else 'active'
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE shipment_companies SET status = %s WHERE id = %s", (new_status, sid))
            conn.commit()
            conn.close()
        st.rerun()
