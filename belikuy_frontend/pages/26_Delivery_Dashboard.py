import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from utils import get_api, post_api, require_login, require_role, hide_streamlit_ui, format_rupiah
from b2b_sidebar import inject_custom_sidebar
from html_bridge import render_original_html

st.set_page_config(page_title="Delivery Dashboard", layout="wide", initial_sidebar_state="collapsed")
hide_streamlit_ui()
require_login()
user = st.session_state.get('user')
require_role("delivery")

HTML_BASE = r"D:\belikuy\belikuy_ui_templates"
with open(os.path.join(HTML_BASE, "b2b_dashboard/code.html"), encoding='utf-8') as f:
    html = f.read()

import mysql.connector
def get_delivery_db():
    return mysql.connector.connect(host="127.0.0.1", user="root", password="", database="belikuy_delivery_db")

conn = get_delivery_db()
cursor = conn.cursor(dictionary=True)

# Determine if Delivery has a user_id mapped
cursor.execute("SELECT * FROM shipment_companies WHERE user_id = %s LIMIT 1", (user['id'],))
courier = cursor.fetchone()
# Consume any remaining results just in case
cursor.fetchall()

shipments = []
if courier:
    cursor.execute("""
        SELECT s.* 
        FROM belikuy_delivery_db.shipments s
        JOIN belikuy_marketplace_db.orders o ON s.order_id = o.id
        WHERE s.shipment_company_id = %s AND o.status NOT IN ('cancelled', 'pending', 'paid') AND s.shipping_status != 'pending'
        ORDER BY s.id DESC LIMIT 20
    """, (courier['id'],))
    shipments = cursor.fetchall()
conn.close()

total_delivered = sum(1 for s in shipments if s['shipping_status'] == 'delivered')
total_in_transit = sum(1 for s in shipments if s['shipping_status'] in ('shipped', 'in_transit', 'picked_up'))
total_pending = sum(1 for s in shipments if s['shipping_status'] == 'pending')

# Replace Placeholders
html = html.replace("{PAGE_TITLE}", "Delivery Dashboard")
html = html.replace("{USERNAME}", user['username'])
html = html.replace("{ROLE_CAPS}", "Delivery")
html = html.replace("{SUBTITLE}", "Pantau pengiriman logistik BeliKuy di sini.")
html = html.replace("{USER_INITIAL}", user['username'][0].upper())

html = html.replace("{STAT1_TITLE}", "Paket Menunggu")
html = html.replace("{STAT1_ICON}", "inventory_2")
html = html.replace("{STAT1_VAL}", str(total_pending))
html = html.replace("{STAT1_DESC}", "Siap dijemput di kurir")

html = html.replace("{STAT2_TITLE}", "Sedang Dikirim")
html = html.replace("{STAT2_ICON}", "local_shipping")
html = html.replace("{STAT2_VAL}", str(total_in_transit))
html = html.replace("{STAT2_DESC}", "Dalam perjalanan")

html = html.replace("{STAT3_TITLE}", "Paket Terkirim")
html = html.replace("{STAT3_ICON}", "check_circle")
html = html.replace("{STAT3_VAL}", str(total_delivered))
html = html.replace("{STAT3_DESC}", "Sudah diterima customer")

html = html.replace("{STAT4_TITLE}", "Rating Ekspedisi")
html = html.replace("{STAT4_ICON}", "star")
html = html.replace("{STAT4_VAL}", "4.8")
html = html.replace("{STAT4_DESC}", "Ketepatan waktu 95%")

html = html.replace("{TABLE_TITLE}", "Daftar Paket Terbaru")
html = html.replace("{TABLE_HEADERS}", "<tr><th class='p-4'>Resi</th><th class='p-4'>Tanggal</th><th class='p-4'>Ongkir</th><th class='p-4'>Status</th><th class='p-4 text-right'>Aksi</th></tr>")

import datetime
now_date = datetime.datetime.now().strftime('%d %b %Y')

def get_ship_price(service_type):
    stype = str(service_type).lower() if service_type else ""
    if 'instant' in stype: return 60000
    if 'sameday' in stype: return 40000
    if 'yes' in stype or 'best' in stype or 'super' in stype: return 35000
    if 'ez' in stype or 'halu' in stype: return 20000
    return 15000

ship_cost_val = get_ship_price(courier.get('service_type')) if courier else 15000

rows_html = ""
for s in shipments:
    status_val = s.get('shipping_status', 'pending')
    s_color = "bg-yellow-100 text-yellow-800" if status_val == 'pending' else ("bg-blue-100 text-blue-800" if status_val in ('shipped', 'in_transit') else "bg-green-100 text-green-800")
    
    action_btn = ""
    if status_val in ('shipped', 'in_transit'):
        action_btn = f"<button onclick=\"stNavigate({{action:'deliver_order', sid:{s['id']}}})\" class='px-3 py-1 bg-primary text-white rounded text-xs hover:bg-primary-container hover:text-on-primary-container transition-colors font-semibold'>Tandai Terkirim</button>"
    elif status_val == 'pending':
        action_btn = "<span class='text-xs text-outline italic'>Belum dikirim</span>"
    else:
        action_btn = "<span class='text-xs text-green-600 italic'>Selesai</span>"

    rows_html += f"<tr class='hover:bg-surface-bright transition-colors'><td class='p-4 font-semibold'>{s.get('tracking_number', 'N/A')}</td><td class='p-4'>{now_date}</td><td class='p-4'>{format_rupiah(ship_cost_val)}</td><td class='p-4'><span class='px-2 py-1 rounded-full text-[10px] uppercase font-bold tracking-wider {s_color}'>{status_val}</span></td><td class='p-4 text-right'>{action_btn}</td></tr>"

if not shipments:
    html = html.replace("{EMPTY_STATE}", "<div class='p-8 text-center text-on-surface-variant'>Belum ada paket untuk dikirim.</div>")
else:
    html = html.replace("{EMPTY_STATE}", "")

html = html.replace("{TABLE_ROWS}", rows_html)
html = html.replace("{EXTRA_CONTENT}", "")

# Inject Sidebar
html = inject_custom_sidebar(html, "Delivery", "Ekspedisi", "local_shipping", user['username'][0].upper())

# Render
action = render_original_html("delivery_dashboard_v2", html, height=1200)

if action:
    if action.get("action") == "deliver_order":
        sid = action.get("sid")
        conn = get_delivery_db()
        cur = conn.cursor(dictionary=True)
        # Update shipment status
        cur.execute("UPDATE shipments SET shipping_status = 'delivered' WHERE id = %s", (sid,))
        # Get order_id
        cur.execute("SELECT order_id FROM shipments WHERE id = %s", (sid,))
        shipment = cur.fetchone()
        conn.commit()
        conn.close()
        
        # Update order status in marketplace
        if shipment and shipment.get('order_id'):
            m_conn = mysql.connector.connect(host="127.0.0.1", user="root", password="", database="belikuy_marketplace_db")
            m_cur = m_conn.cursor()
            m_cur.execute("UPDATE orders SET status = 'delivered' WHERE id = %s", (shipment['order_id'],))
            m_conn.commit()
            m_conn.close()
            
        st.rerun()
    elif action.get("action") == "logout":
        st.session_state.clear()
        st.session_state['_auto_logout'] = True
        st.switch_page("app.py")
