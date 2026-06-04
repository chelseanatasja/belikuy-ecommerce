import streamlit as st
import sys, os, re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from utils import (
    get_api,
    post_api,
    put_api,
    delete_api,
    require_login,
    hide_streamlit_ui,
)
from html_bridge import render_original_html
from unified_navbar import inject_navbar, handle_global_action

st.set_page_config(
    page_title="BeliKuy - Manajemen Alamat",
    layout="wide",
    initial_sidebar_state="collapsed",
)
hide_streamlit_ui()
require_login()

user = st.session_state["user"]

addresses, _ = get_api(f"addresses/{user['id']}")
if not addresses:
    addresses = []

HTML_BASE = (
    r"D:\Tugas Kuliah\Semester 4\Workshop RPL\belikuy-ecommerce\belikuy_ui_templates"
)
with open(
    os.path.join(HTML_BASE, "address_management/code.html"), encoding="utf-8"
) as f:
    html = f.read()

addr_cards = ""
for a in addresses:
    is_def = a.get("is_default", 0)

    if is_def:
        addr_cards += f"""
        <div class="bg-surface-container-lowest rounded-xl p-lg shadow-[0_8px_30px_rgba(255,182,193,0.15)] relative overflow-hidden group border border-transparent hover:border-primary-fixed transition-colors">
            <div class="absolute top-0 right-0 bg-primary-container text-on-primary-container font-label-caps text-label-caps px-4 py-2 rounded-bl-xl shadow-sm z-10">
                Alamat Utama
            </div>
            <div class="flex items-start gap-4 mb-4">
                <div class="w-12 h-12 rounded-full bg-primary-fixed flex items-center justify-center text-on-primary-fixed-variant shrink-0">
                    <span class="material-symbols-outlined text-2xl" data-icon="home">home</span>
                </div>
                <div>
                    <h3 class="font-h3 text-h3 text-on-background">Alamat</h3>
                    <p class="font-body-md text-body-md text-on-surface-variant font-medium mt-1">{user.get("name","")}</p>
                </div>
            </div>
            <div class="pl-16 space-y-2 mb-6">
                <p class="font-body-sm text-body-sm text-on-surface-variant leading-relaxed">{a.get("address","")}, {a.get("city","")} {a.get("postal_code","")}</p>
            </div>
            <div class="flex items-center gap-3 pl-16 border-t border-surface-variant pt-4 mt-auto">
                <button onclick="stNavigate({{action:'delete_address', aid:{a['id']}}})" class="font-label-caps text-label-caps text-on-surface-variant hover:text-error transition-colors px-4 py-2 bg-surface rounded-full">
                    Hapus
                </button>
            </div>
        </div>
        """
    else:
        addr_cards += f"""
        <div class="bg-surface-container-lowest rounded-xl p-lg shadow-[0_4px_20px_rgba(0,0,0,0.03)] relative overflow-hidden border border-surface-variant hover:border-primary-fixed transition-colors">
            <div class="flex items-start gap-4 mb-4">
                <div class="w-12 h-12 rounded-full bg-surface-container flex items-center justify-center text-on-surface-variant shrink-0">
                    <span class="material-symbols-outlined text-2xl" data-icon="location_on">location_on</span>
                </div>
                <div>
                    <h3 class="font-h3 text-h3 text-on-background">Alamat Lain</h3>
                    <p class="font-body-md text-body-md text-on-surface-variant font-medium mt-1">{user.get("name","")}</p>
                </div>
            </div>
            <div class="pl-16 space-y-2 mb-6">
                <p class="font-body-sm text-body-sm text-on-surface-variant leading-relaxed">{a.get("address","")}, {a.get("city","")} {a.get("postal_code","")}</p>
            </div>
            <div class="flex flex-wrap items-center gap-3 pl-16 border-t border-surface-variant pt-4 mt-auto">
                <button onclick="stNavigate({{action:'delete_address', aid:{a['id']}}})" class="font-label-caps text-label-caps text-on-surface-variant hover:text-error transition-colors px-4 py-2 bg-surface rounded-full">
                    Hapus
                </button>
                <div class="flex-grow"></div>
                <button onclick="stNavigate({{action:'set_default', aid:{a['id']}}})" class="font-label-caps text-label-caps text-primary-container bg-on-primary-container px-4 py-2 rounded-full hover:bg-surface-tint transition-colors">
                    Set Utama
                </button>
            </div>
        </div>
        """

if not addresses:
    addr_cards = '<div class="col-span-1 lg:col-span-2 text-center py-10 text-on-surface-variant">Belum ada alamat tersimpan. Silakan tambah alamat.</div>'

html = re.sub(
    r'(<div class="grid grid-cols-1 lg:grid-cols-2 gap-lg">)(.*?)(</main>)',
    rf"\1{addr_cards}</div>\3",
    html,
    flags=re.DOTALL,
)

# Add Modal functionality
js_head = """<script>
function toggleModal() {
    const modal = document.getElementById('addressModal');
    if (modal.classList.contains('hidden')) {
        modal.classList.remove('hidden');
    } else {
        modal.classList.add('hidden');
    }
}
function saveAddress() {
    const addr = document.getElementById('new_addr').value;
    const city = document.getElementById('new_city').value;
    const isMain = document.getElementById('setMain').checked;
    stNavigate({action: 'add_address', addr: addr, city: city, postal: '00000', is_default: isMain});
}
</script>"""
html = html.replace("</head>", js_head + "</head>")
html = html.replace('href="#"', 'href="#" onclick="event.preventDefault();"')

# Modify the button to open modal
# Modify the button to open modal
html = re.sub(
    r'(<button class="inline-flex items-center gap-2 bg-gradient-to-r from-primary-container[^>]*?)(>)',
    r'\1 onclick="toggleModal()"\2',
    html,
)

# Modify modal HTML structure slightly for IDs
modal_html = html[html.find("<!-- Overlay Modal") :]
new_modal_html = re.sub(
    r'<div class="fixed inset-0[^>]*?>',
    lambda m: m.group(0)
    .replace('class="', 'id="addressModal" class="')
    .replace("items-center", "items-start pt-32"),
    modal_html,
    count=1,
)
new_modal_html = new_modal_html.replace('id="setMain"', 'id="setMain"')
# Replace close button action
new_modal_html = re.sub(
    r'(<button class="absolute top-6 right-6[^>]*?)(>)',
    r'\1 onclick="toggleModal()" type="button"\2',
    new_modal_html,
)
# Replace cancel button action
new_modal_html = re.sub(
    r'(<button class="px-6 py-3 rounded-full font-label-caps text-label-caps text-on-surface-variant[^>]*?)(>)',
    r'\1 onclick="toggleModal()" type="button"\2',
    new_modal_html,
)
# Replace save button action
new_modal_html = re.sub(
    r'(<button class="[^"]*bg-primary text-on-primary[^"]*")( type="button">|>)',
    r'\1 onclick="saveAddress()" type="button">',
    new_modal_html,
)

# Set input IDs
new_modal_html = new_modal_html.replace(
    'placeholder="Cth: Rumah, Kantor"', 'placeholder="Cth: Rumah, Kantor" id="new_city"'
)
new_modal_html = new_modal_html.replace(
    'placeholder="Nama jalan, gedung, no. rumah"',
    'placeholder="Nama jalan, gedung, no. rumah" id="new_addr"',
)

html = html[: html.find("<!-- Overlay Modal")] + new_modal_html

# ── Inject Unified Navbar ───────────────────────────────────────────────────
cart_len = len(st.session_state.get("cart", []))
html = inject_navbar(html, cart_len)

action_data = render_original_html("belikuy_v2_address", html, height=1000)

if action_data:
    act = action_data.get("action")
    current_user = st.session_state.get("user")
    if handle_global_action(st, act, action_data, current_user):
        pass
    elif act == "go_home":
        st.switch_page("pages/1_Storefront.py")
    elif act == "add_address":
        addr = action_data.get("addr", "")
        city = action_data.get("city", "")
        postal = action_data.get("postal", "")
        is_def = action_data.get("is_default", False)
        if addr and city:
            post_api(
                f"addresses",
                {
                    "user_id": user["id"],
                    "address": addr,
                    "city": city,
                    "postal_code": postal,
                    "is_default": is_def,
                },
            )
            st.rerun()
        else:
            st.error("Alamat dan kota harus diisi")
    elif act == "set_default":
        aid = action_data.get("aid")
        if aid:
            put_api(f"addresses/{aid}/default", {"user_id": user["id"]})
        st.rerun()
    elif act == "delete_address":
        aid = action_data.get("aid")
        if aid:
            delete_api(f"addresses/{aid}")
        st.rerun()
