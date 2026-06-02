import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils import get_api, require_login, hide_streamlit_ui, format_rupiah, get_current_user
from html_bridge import render_original_html
from unified_sidebar import inject_admin_sidebar, handle_admin_global_action
import requests as _req

st.set_page_config(page_title="BeliKuy Admin - Kelola Penarikan Dana", layout="wide", initial_sidebar_state="collapsed")
hide_streamlit_ui()
require_login()

user = get_current_user()
if user and user.get('role') != 'admin':
    st.error("🚫 Akses ditolak."); st.stop()

withdrawals, _ = get_api("withdrawals")
if not withdrawals: withdrawals = []

# Status filter
status_filter = st.session_state.get('wd_filter', '')

def status_badge(s):
    badges = {
        'pending':   ('<span class="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-yellow-100 text-yellow-700 text-xs font-semibold"><span class="w-2 h-2 rounded-full bg-yellow-400 inline-block"></span>Menunggu</span>'),
        'processed': ('<span class="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-blue-100 text-blue-700 text-xs font-semibold"><span class="w-2 h-2 rounded-full bg-blue-400 inline-block"></span>Diproses</span>'),
        'completed': ('<span class="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-green-100 text-green-700 text-xs font-semibold"><span class="w-2 h-2 rounded-full bg-green-500 inline-block"></span>Selesai</span>'),
        'rejected':  ('<span class="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-red-100 text-red-700 text-xs font-semibold"><span class="w-2 h-2 rounded-full bg-red-500 inline-block"></span>Ditolak</span>'),
    }
    return badges.get(s, badges['pending'])

display = withdrawals if not status_filter else [w for w in withdrawals if w.get('status') == status_filter]

# Counts per status
counts = {s: sum(1 for w in withdrawals if w.get('status') == s) for s in ['pending', 'processed', 'completed', 'rejected']}
total_pending_amount = sum(float(w.get('amount', 0)) for w in withdrawals if w.get('status') == 'pending')

# Build rows
rows = ""
for w in display:
    wid = w.get('id', '')
    st_val = w.get('status', 'pending')
    badge = status_badge(st_val)
    bank_code = (w.get('bank_name', 'BANK') or 'BANK')[:3].upper()

    action_btns = ""
    if st_val == 'pending':
        action_btns = f'''
        <div class="flex gap-2 justify-end">
            <button onclick="stNavigate({{action:'wd_approve',wid:{wid}}})"
                class="px-4 py-2 bg-green-500 hover:bg-green-600 text-white text-xs font-semibold rounded-lg transition-colors flex items-center gap-1">
                <span class="material-symbols-outlined text-[14px]">check_circle</span> Setujui
            </button>
            <button onclick="stNavigate({{action:'wd_reject',wid:{wid}}})"
                class="px-4 py-2 bg-red-100 hover:bg-red-200 text-red-700 text-xs font-semibold rounded-lg transition-colors flex items-center gap-1">
                <span class="material-symbols-outlined text-[14px]">cancel</span> Tolak
            </button>
        </div>'''
    elif st_val == 'processed':
        action_btns = f'''
        <div class="flex gap-2 justify-end">
            <button onclick="stNavigate({{action:'wd_complete',wid:{wid}}})"
                class="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white text-xs font-semibold rounded-lg transition-colors flex items-center gap-1">
                <span class="material-symbols-outlined text-[14px]">payments</span> Tandai Selesai
            </button>
        </div>'''

    rows += f'''
    <tr class="border-b border-gray-100 hover:bg-gray-50 transition-colors">
        <td class="px-6 py-4 text-sm font-semibold text-gray-900">#{wid}</td>
        <td class="px-6 py-4">
            <div class="font-semibold text-gray-900 text-sm">{w.get("company_name","–")}</div>
        </td>
        <td class="px-6 py-4 text-sm font-bold text-gray-900">{format_rupiah(w.get("amount",0))}</td>
        <td class="px-6 py-4">
            <div class="flex items-center gap-2">
                <div class="w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center text-xs font-bold text-gray-700">{bank_code}</div>
                <div>
                    <p class="text-sm font-semibold text-gray-900">{w.get("bank_name","")}</p>
                    <p class="text-xs text-gray-500">{w.get("account_number","")} · {w.get("account_holder","")}</p>
                </div>
            </div>
        </td>
        <td class="px-6 py-4 text-xs text-gray-500">{str(w.get("created_at",""))[:16]}</td>
        <td class="px-6 py-4">{badge}</td>
        <td class="px-6 py-4">{action_btns}</td>
    </tr>'''

if not display:
    rows = '<tr><td colspan="7" class="px-6 py-16 text-center text-gray-400"><div class="text-4xl mb-2">💸</div>Tidak ada permintaan penarikan dana.</td></tr>'

# Filter tabs html
def tab_cls(val):
    return "px-4 py-2 text-sm font-semibold border-b-2 border-primary text-primary" if status_filter == val else "px-4 py-2 text-sm text-gray-500 hover:text-gray-800 transition-colors"

page_html = f'''<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Kelola Penarikan Dana - Admin BeliKuy</title>
<script src="https://cdn.tailwindcss.com?plugins=container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&family=Inter:wght@400;600&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
<script>
tailwind.config = {{
    theme: {{
        extend: {{
            colors: {{
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
            }}
        }}
    }}
}}
</script>
<style>
body {{ font-family: "Plus Jakarta Sans", "Inter", sans-serif; background: #f8f9fa; }}
.material-symbols-outlined {{ font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24; font-size: 20px; }}
</style>
</head>
<body class="min-h-screen bg-gray-50">
<div class="md:ml-64 p-6 md:p-10">
    <!-- Header -->
    <div class="flex items-center gap-4 mb-8">
        <div>
            <h1 class="text-2xl font-bold text-gray-900">Kelola Penarikan Dana Seller</h1>
            <p class="text-sm text-gray-500 mt-0.5">Review dan proses permintaan tarik dana dari semua seller</p>
        </div>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div class="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
            <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Total Permintaan</p>
            <p class="text-3xl font-bold text-gray-900">{len(withdrawals)}</p>
        </div>
        <div class="bg-yellow-50 rounded-2xl p-5 shadow-sm border border-yellow-100">
            <p class="text-xs font-semibold text-yellow-600 uppercase tracking-wider mb-1">Menunggu</p>
            <p class="text-3xl font-bold text-yellow-700">{counts.get("pending",0)}</p>
            <p class="text-xs text-yellow-600 mt-1">{format_rupiah(total_pending_amount)}</p>
        </div>
        <div class="bg-blue-50 rounded-2xl p-5 shadow-sm border border-blue-100">
            <p class="text-xs font-semibold text-blue-600 uppercase tracking-wider mb-1">Diproses</p>
            <p class="text-3xl font-bold text-blue-700">{counts.get("processed",0)}</p>
        </div>
        <div class="bg-green-50 rounded-2xl p-5 shadow-sm border border-green-100">
            <p class="text-xs font-semibold text-green-600 uppercase tracking-wider mb-1">Selesai</p>
            <p class="text-3xl font-bold text-green-700">{counts.get("completed",0)}</p>
        </div>
    </div>

    <!-- Filter Tabs -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        <div class="flex border-b border-gray-100 px-4">
            <button onclick="stNavigate({{action:'wd_filter',status:''}})" class="{tab_cls('')}">Semua ({len(withdrawals)})</button>
            <button onclick="stNavigate({{action:'wd_filter',status:'pending'}})" class="{tab_cls('pending')}">Menunggu ({counts.get("pending",0)})</button>
            <button onclick="stNavigate({{action:'wd_filter',status:'processed'}})" class="{tab_cls('processed')}">Diproses ({counts.get("processed",0)})</button>
            <button onclick="stNavigate({{action:'wd_filter',status:'completed'}})" class="{tab_cls('completed')}">Selesai ({counts.get("completed",0)})</button>
            <button onclick="stNavigate({{action:'wd_filter',status:'rejected'}})" class="{tab_cls('rejected')}">Ditolak ({counts.get("rejected",0)})</button>
        </div>

        <!-- Table -->
        <div class="overflow-x-auto">
            <table class="w-full">
                <thead>
                    <tr class="bg-gray-50 text-left">
                        <th class="px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">#ID</th>
                        <th class="px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Seller</th>
                        <th class="px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Jumlah</th>
                        <th class="px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Rekening Tujuan</th>
                        <th class="px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Tanggal</th>
                        <th class="px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                        <th class="px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Aksi</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
    </div>
</div>
</body>
</html>'''

js_head = """<script>
function stNavigate(params) {
    params._ts = Date.now();
    if(window.Streamlit) { window.Streamlit.setComponentValue(params); }
}
</script>"""
page_html = page_html.replace("</head>", js_head + "</head>")

# Inject unified admin sidebar
page_html = inject_admin_sidebar(page_html, "20_Admin_Withdrawals")

action_data = render_original_html("belikuy_v2_admin_withdrawals", page_html, height=1200)

if action_data:
    act = action_data.get('action')
    if handle_admin_global_action(st, act):
        pass
    elif act == 'go_admin':  # fallback for the back arrow
        st.switch_page("pages/13_Admin_Dashboard.py")
    elif act == 'wd_filter':
        st.session_state['wd_filter'] = action_data.get('status', '')
        st.rerun()
    elif act in ('wd_approve', 'wd_reject', 'wd_complete'):
        wid = action_data.get('wid')
        status_map = {'wd_approve': 'processed', 'wd_reject': 'rejected', 'wd_complete': 'completed'}
        new_status = status_map[act]
        if wid:
            resp = _req.patch(f"http://localhost:3000/api/withdrawals/{wid}/status",
                              json={"status": new_status}, timeout=8)
            if resp.status_code == 200:
                label = {'processed': 'disetujui & diproses', 'rejected': 'ditolak', 'completed': 'ditandai selesai'}
                st.success(f"✅ Penarikan #{wid} berhasil {label[new_status]}!")
            else:
                st.error("Gagal memperbarui status.")
        st.rerun()
