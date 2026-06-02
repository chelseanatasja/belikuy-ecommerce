import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from utils import get_api, post_api, require_login, require_role, hide_streamlit_ui, format_rupiah
from b2b_sidebar import inject_custom_sidebar
from html_bridge import render_original_html

st.set_page_config(page_title="Fintech Dashboard", layout="wide", initial_sidebar_state="collapsed")
hide_streamlit_ui()
require_login()
user = st.session_state.get('user')
require_role("fintech")

HTML_BASE = r"D:\belikuy\belikuy_ui_templates"
with open(os.path.join(HTML_BASE, "b2b_dashboard/code.html"), encoding='utf-8') as f:
    html = f.read()

import mysql.connector
def get_payment_db():
    return mysql.connector.connect(host="127.0.0.1", user="root", password="", database="belikuy_fintech_db")

conn = get_payment_db()
cursor = conn.cursor(dictionary=True)

# Determine if Fintech has a user_id mapped
cursor.execute("SELECT * FROM payment_methods WHERE user_id = %s LIMIT 1", (user['id'],))
fintech = cursor.fetchone()
cursor.fetchall()

transactions = []
if fintech:
    # B2C Payments
    cursor.execute("""
        SELECT p.id, o.total_price as amount, p.payment_status as status, p.paid_at as date, 'B2C' as type
        FROM payments p
        JOIN belikuy_marketplace_db.orders o ON p.order_id = o.id
        WHERE p.payment_method_id = %s
        ORDER BY p.id DESC LIMIT 15
    """, (fintech['id'],))
    b2c = cursor.fetchall()
    
    # B2B Payments
    cursor.execute("""
        SELECT id, amount, status, paid_at as date, 'B2B' as type
        FROM supplier_payments
        WHERE payment_method = %s
        ORDER BY id DESC LIMIT 15
    """, (fintech['institution_name'],))
    b2b = cursor.fetchall()
    
    transactions = b2c + b2b
    # Sort by date (fallback to id if None)
    import datetime
    transactions.sort(key=lambda x: x['date'] or datetime.datetime.min, reverse=True)
conn.close()

total_processed = sum([float(t['amount']) for t in transactions if t['status'] in ('paid', 'success')])
total_success = sum(1 for t in transactions if t['status'] in ('paid', 'success'))
total_failed = sum(1 for t in transactions if t['status'] == 'failed')

# Replace Placeholders
html = html.replace("{PAGE_TITLE}", "Fintech Dashboard")
html = html.replace("{USERNAME}", user['username'])
html = html.replace("{ROLE_CAPS}", "Fintech")
html = html.replace("{SUBTITLE}", "Pantau transaksi lintas sistem BeliKuy di sini.")
html = html.replace("{USER_INITIAL}", user['username'][0].upper())

html = html.replace("{STAT1_TITLE}", "Total Transaksi")
html = html.replace("{STAT1_ICON}", "account_balance")
html = html.replace("{STAT1_VAL}", format_rupiah(total_processed))
html = html.replace("{STAT1_DESC}", "Dana sukses dicairkan")

html = html.replace("{STAT2_TITLE}", "Transaksi Sukses")
html = html.replace("{STAT2_ICON}", "check_circle")
html = html.replace("{STAT2_VAL}", str(total_success))
html = html.replace("{STAT2_DESC}", "Gateway stabil 100%")

html = html.replace("{STAT3_TITLE}", "Transaksi Gagal")
html = html.replace("{STAT3_ICON}", "cancel")
html = html.replace("{STAT3_VAL}", str(total_failed))
html = html.replace("{STAT3_DESC}", "Bisa karena saldo tidak cukup")

html = html.replace("{STAT4_TITLE}", "Status Node")
html = html.replace("{STAT4_ICON}", "dns")
html = html.replace("{STAT4_VAL}", "Online")
html = html.replace("{STAT4_DESC}", "Ping: 12ms")

html = html.replace("{TABLE_TITLE}", "Mutasi Rekening Terbaru")
html = html.replace("{TABLE_HEADERS}", "<tr><th class='p-4'>Mutasi ID</th><th class='p-4'>Tipe/Bank</th><th class='p-4'>Tanggal</th><th class='p-4'>Jumlah</th><th class='p-4'>Status</th></tr>")

rows_html = ""
for t in transactions:
    s_color = "bg-yellow-100 text-yellow-800" if t['status'] == 'pending' else ("bg-red-100 text-red-800" if t['status'] == 'failed' else "bg-green-100 text-green-800")
    date_str = t['date'].strftime('%d %b %Y %H:%M') if t['date'] else '-'
    type_badge = f"<span class='bg-blue-100 text-blue-800 px-2 py-0.5 rounded text-[10px] font-bold mr-2'>{t['type']}</span>"
    
    rows_html += f"<tr class='hover:bg-surface-bright transition-colors'><td class='p-4 font-semibold'>#{t['id']}</td><td class='p-4'>{type_badge}{(fintech['institution_name'] if fintech else 'Gateway')}</td><td class='p-4'>{date_str}</td><td class='p-4'>{format_rupiah(t['amount'])}</td><td class='p-4'><span class='px-2 py-1 rounded-full text-[10px] uppercase font-bold tracking-wider {s_color}'>{t['status']}</span></td></tr>"

if not transactions:
    html = html.replace("{EMPTY_STATE}", "<div class='p-8 text-center text-on-surface-variant'>Belum ada transaksi B2C/B2B masuk.</div>")
else:
    html = html.replace("{EMPTY_STATE}", "")

html = html.replace("{TABLE_ROWS}", rows_html)
html = html.replace("{EXTRA_CONTENT}", "")

# Inject Sidebar
html = inject_custom_sidebar(html, "Fintech", "Payment", "account_balance", user['username'][0].upper())

# Render
action = render_original_html("fintech_dashboard_v2", html, height=1200)

if action:
    if action.get("action") == "logout":
        st.session_state.clear()
        st.session_state['_auto_logout'] = True
        st.switch_page("app.py")
