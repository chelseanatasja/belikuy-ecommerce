import streamlit as st
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from utils import get_api, post_api, delete_api, require_role, hide_streamlit_ui
from html_bridge import render_original_html
from unified_sidebar import inject_admin_sidebar, handle_admin_global_action

st.set_page_config(page_title="BeliKuy - Manajemen Supplier", layout="wide", initial_sidebar_state="collapsed")
hide_streamlit_ui()
require_role("admin")

import mysql.connector

def get_db_connection():
    return mysql.connector.connect(host="127.0.0.1", user="root", password="", database="belikuy")

conn = get_db_connection()
cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT * FROM supply_companies ORDER BY id DESC")
suppliers = cursor.fetchall()
conn.close()

HTML_BASE = r"D:\belikuy\belikuy_ui_templates"
with open(os.path.join(HTML_BASE, "super_admin_supplier_management/code.html"), encoding='utf-8') as f:
    html = f.read()

# Remove filter button and change search placeholder
html = html.replace('placeholder="Cari nama supplier, kategori, atau kontak..."', 'placeholder="Cari nama supplier..."')
html = re.sub(r'<button class="bg-surface-container-lowest text-on-surface font-label-caps text-label-caps px-lg py-md rounded-xl flex items-center gap-sm shadow-sm hover:bg-surface-container-low transition-colors">\s*<span class="material-symbols-outlined">filter_list</span>\s*Filter\s*</button>', '', html, flags=re.DOTALL)

# Build Cards
cards = ""
for s in suppliers:
    is_active = (s.get('status', 'active') == 'active')
    status_badge = '<span class="bg-primary-container text-on-primary-container font-label-caps text-[10px] px-2 py-1 rounded-full tracking-wider">Aktif</span>' if is_active else '<span class="bg-surface-variant text-on-surface-variant font-label-caps text-[10px] px-2 py-1 rounded-full tracking-wider">Nonaktif</span>'
    toggle_icon = 'toggle_on' if is_active else 'toggle_off'
    
    cards += f'''
    <article class="bg-surface-container-lowest rounded-xl p-lg shadow-[0_8px_30px_rgb(255,182,193,0.1)] hover:shadow-[0_12px_40px_rgb(255,182,193,0.15)] transition-shadow duration-300 flex flex-col group border border-transparent hover:border-primary-fixed-dim">
        <div class="flex justify-between items-start mb-md">
            <div class="flex items-center gap-md">
                <div class="w-14 h-14 rounded-full overflow-hidden bg-primary-container text-primary border-2 border-surface-container-lowest shadow-sm flex items-center justify-center font-h3 font-bold text-xl">
                    {s.get("supply_company_name", "S")[0].upper()}
                </div>
                <div>
                    <h3 class="font-h3 text-[18px] text-on-surface leading-tight mb-xs">{s.get("supply_company_name","")}</h3>
                    <div class="flex gap-xs">
                        {status_badge}
                    </div>
                </div>
            </div>
            <div class="flex gap-2">
                <button onclick="stNavigate({{action:'toggle_supplier', sid:{s.get('id')}, cstatus:'{s.get('status', 'active')}'}})" class="text-outline hover:text-primary p-2 rounded-full transition-colors" title="Toggle Status">
                    <span class="material-symbols-outlined">{toggle_icon}</span>
                </button>
                <button onclick="stNavigate({{action:'delete_supplier', sid:{s.get('id')}}})" class="text-error hover:bg-error-container p-2 rounded-full transition-colors" title="Hapus">
                    <span class="material-symbols-outlined">delete</span>
                </button>
            </div>
        </div>
        <div class="mb-lg">
            <p class="font-body-sm text-body-sm text-on-surface-variant line-clamp-2">Penyuplai terverifikasi BeliKuy.</p>
        </div>
        <div class="mt-auto flex flex-col gap-sm pt-md border-t border-surface-variant/50">
            <div class="flex items-center gap-sm text-on-surface-variant font-body-sm text-body-sm">
                <span class="material-symbols-outlined text-[18px]">phone</span>
                <span>{s.get("contact_number","")}</span>
            </div>
            <div class="flex items-center gap-sm text-on-surface-variant font-body-sm text-body-sm">
                <span class="material-symbols-outlined text-[18px]">location_on</span>
                <span>{s.get("address","")}</span>
            </div>
        </div>
    </article>
    '''

if not cards:
    cards = '<div class="col-span-1 md:col-span-2 lg:col-span-3 text-center py-12 text-on-surface-variant">Belum ada supplier terdaftar.</div>'

html = re.sub(r'(<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-lg pb-xl">)(.*?)(</div>\s*</div>\s*</main>)', rf'\1{cards}\3', html, flags=re.DOTALL)

# Add Modal
modal_html = f'''
<div id="addModal" class="fixed inset-0 bg-inverse-surface/40 backdrop-blur-sm z-[100] hidden flex items-start pt-32 justify-center p-4">
    <div class="bg-surface-container-lowest rounded-xl w-full max-w-md p-xl shadow-[0_20px_50px_rgba(255,182,193,0.3)] relative transform transition-transform">
        <button onclick="toggleModal()" type="button" class="absolute top-6 right-6 text-on-surface-variant hover:text-error transition-colors p-2 rounded-full hover:bg-surface-container">
            <span class="material-symbols-outlined">close</span>
        </button>
        <h2 class="font-h2 text-h2 text-on-background mb-6">Tambah Supplier Baru</h2>
        <div class="mb-4">
            <label class="font-label-caps text-label-caps text-on-surface-variant ml-2 block mb-2">Nama Supplier</label>
            <input id="s_name" type="text" class="w-full bg-surface-bright border-none rounded-lg py-3 px-4 focus:ring-2 focus:ring-primary-container" placeholder="Nama Supplier"/>
        </div>
        <div class="mb-4">
            <label class="font-label-caps text-label-caps text-on-surface-variant ml-2 block mb-2">Kontak</label>
            <input id="s_contact" type="text" class="w-full bg-surface-bright border-none rounded-lg py-3 px-4 focus:ring-2 focus:ring-primary-container" placeholder="Nomor Telepon/HP"/>
        </div>
        <div class="mb-6">
            <label class="font-label-caps text-label-caps text-on-surface-variant ml-2 block mb-2">Alamat</label>
            <textarea id="s_addr" rows="2" class="w-full bg-surface-bright border-none rounded-lg py-3 px-4 focus:ring-2 focus:ring-primary-container resize-none" placeholder="Alamat lengkap..."></textarea>
        </div>
        <div class="flex justify-end gap-4">
            <button type="button" onclick="toggleModal()" class="px-6 py-3 rounded-full font-label-caps text-label-caps text-on-surface-variant hover:bg-surface-container transition-colors">Batal</button>
            <button type="button" onclick="saveSupplier()" class="px-8 py-3 rounded-full font-label-caps text-label-caps bg-primary text-on-primary hover:bg-surface-tint shadow-[0_4px_14px_rgba(255,182,193,0.4)] transition-all">Simpan</button>
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
function saveSupplier() {
    const name = document.getElementById('s_name').value;
    const contact = document.getElementById('s_contact').value;
    const addr = document.getElementById('s_addr').value;
    if(!name) { alert("Nama supplier wajib diisi!"); return; }
    stNavigate({action: 'add_supplier', name: name, contact: contact, addr: addr});
}

document.addEventListener('DOMContentLoaded', function() {
    // Search Box Filtering
    const searchBox = document.querySelector('input[type="text"]');
    if (searchBox) {
        searchBox.addEventListener('input', function(e) {
            const query = e.target.value.toLowerCase();
            document.querySelectorAll('article').forEach(card => {
                const text = card.innerText.toLowerCase();
                if (text.includes(query)) {
                    card.style.display = '';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }

    // Add supplier and filter buttons
    document.querySelectorAll('button').forEach(btn => {
        if (btn.textContent.toLowerCase().includes('tambah supplier') || btn.textContent.toLowerCase().includes('add new product')) {
            btn.onclick = toggleModal;
        }
    });
});
</script>"""
html = html.replace("</head>", js_head + "</head>")
html = html.replace('href="#"', 'href="#" onclick="event.preventDefault();"')

html = inject_admin_sidebar(html, "17_Manajemen_Supplier")

action_data = render_original_html("belikuy_v2_admin_supplier", html, height=1200)

if action_data:
    act = action_data.get('action')
    if handle_admin_global_action(st, act):
        pass
    elif act == "add_supplier":
        name = action_data.get("name", "")
        contact = action_data.get("contact", "")
        addr = action_data.get("addr", "")
        if name: 
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO supply_companies (supply_company_name, contact_number, address) VALUES (%s, %s, %s)", (name, contact, addr))
            conn.commit()
            conn.close()
        st.rerun()
    elif act == "delete_supplier":
        sid = action_data.get("sid")
        if sid:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM supply_companies WHERE id = %s", (sid,))
            conn.commit()
            conn.close()
        st.rerun()
    elif act == "toggle_supplier":
        sid = action_data.get("sid")
        cstatus = action_data.get("cstatus")
        if sid:
            new_status = 'inactive' if cstatus == 'active' else 'active'
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE supply_companies SET status = %s WHERE id = %s", (new_status, sid))
            conn.commit()
            conn.close()
        st.rerun()
