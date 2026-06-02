import streamlit as st
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from utils import get_api, put_api, require_role, hide_streamlit_ui, format_rupiah, get_image_base64
from html_bridge import render_original_html
from unified_sidebar import inject_seller_sidebar, handle_seller_global_action
import requests as _req
import mysql.connector

@st.dialog("📋 Detail Transaksi")
def show_transaction_details(tid):
    conn = mysql.connector.connect(host="127.0.0.1", user="root", password="")
    c = conn.cursor(dictionary=True)
    c.execute("""
        SELECT oi.*, p.product_name 
        FROM belikuy_marketplace_db.order_items oi 
        LEFT JOIN belikuy_seller_db.products p ON oi.product_id = p.id 
        WHERE oi.order_id = %s
    """, (tid,))
    items = c.fetchall()
    
    c.execute("SELECT o.*, u.username, u.email FROM belikuy_marketplace_db.orders o LEFT JOIN belikuy_marketplace_db.users u ON o.user_id = u.id WHERE o.id = %s", (tid,))
    order = c.fetchone()
    conn.close()
    
    if order:
        st.markdown(f"**Order ID:** #{order['id']}  \n**Pembeli:** {order['username']} ({order['email']})  \n**Tanggal:** {order['created_at']}  \n**Status:** {str(order['status']).upper()}")
        st.divider()
        st.markdown("### Daftar Produk")
        for item in items:
            st.markdown(f"- **{item['product_name'] or 'Produk Dihapus'}** (x{item['quantity']}) — {format_rupiah(item['price'] or 0)}")
        st.divider()
        st.markdown(f"### Total Pembayaran (Semua Toko): **{format_rupiah(order['total_price'])}**")
    else:
        st.error("Transaksi tidak ditemukan.")

st.set_page_config(page_title="BeliKuy - Kelola Pesanan", layout="wide", initial_sidebar_state="collapsed")
hide_streamlit_ui()
require_role("seller")

user = st.session_state['user']
company = user.get('company', {}); company_id = company.get('company_id') if company else None

orders, _ = get_api(f"companies/{company_id}/orders")
if not orders: orders = []

# Get shipment companies for dropdown
shipment_companies, _ = get_api("admin/shipment-companies")
if not shipment_companies: shipment_companies = []

# Deduplication: query returns 1 row per order_item (JOIN),
# sehingga 1 pesanan dengan 3 item = 3 baris. Kita ambil 1 row per order_id.
seen = {}
for o in orders:
    oid = o.get('order_id')
    if oid not in seen:
        seen[oid] = o
unique_orders = list(seen.values())

active_filter = st.session_state.get('order_status_filter', '')
active_search = st.session_state.get('order_search', '').strip().lower()

def matches_filter(o, f):
    status = (o.get('order_status') or o.get('status') or 'pending').lower()
    return True if f == '' else status == f

def matches_search(o, q):
    if not q: return True
    return (q in str(o.get('order_id', '')).lower() or
            q in (o.get('customer_name', '') or '').lower())

display_orders = [o for o in unique_orders if matches_filter(o, active_filter) and matches_search(o, active_search)]


HTML_BASE = r"D:\belikuy\belikuy_ui_templates"
with open(os.path.join(HTML_BASE, "seller_order_management/code.html"), encoding='utf-8') as f:
    html = f.read()

# ── Wire original HTML tabs (based on Orders.status) ─────────────────────────
tab_map = [
    ('Semua',              ''),
    ('Belum Bayar',        'pending'),
    ('Perlu Dikirim',      'paid'),
    ('Dalam Pengiriman',   'shipped'),
    ('Selesai',            'completed'),
    ('Dibatalkan',         'cancelled'),
]

def count_tab(f):
    return sum(1 for o in unique_orders if matches_filter(o, f))

def make_tab(label, val):
    is_active = active_filter == val
    active_cls = "text-primary border-b-2 border-primary" if is_active else "text-on-surface-variant hover:text-primary transition-colors"
    return f'<button onclick="stNavigate({{action:\'filter_status\', status_val:\'{val}\'}})\" class="whitespace-nowrap px-4 py-2 font-body-sm text-body-sm font-semibold {active_cls}">{label} ({count_tab(val)})</button>'

tabs_html = ''.join([make_tab(label, val) for label, val in tab_map])
html = re.sub(
    r'<div class="flex overflow-x-auto no-scrollbar gap-2 mb-lg border-b border-surface-variant pb-xs">.*?</div>',
    f'<div class="flex overflow-x-auto no-scrollbar gap-2 mb-lg border-b border-surface-variant pb-xs">{tabs_html}</div>',
    html, flags=re.DOTALL
)

# ── Wire search input ──────────────────────────────────────────────────────────
order_search_val = active_search.replace('"', '&quot;')
html = re.sub(
    r'(<input[^>]*placeholder="Cari Order ID[^"]*"[^>]*)(/>|>)',
    rf'\1 value="{order_search_val}" onkeydown="onOrderSearchEnter(event,this.value)" \2',
    html, count=1
)

# ── Shipment company options HTML ──────────────────────────────────────────────
sc_opts = '<option value="">— Pilih Ekspedisi —</option>'
for sc in shipment_companies:
    sc_opts += f'<option value="{sc["id"]}">{sc["company_name"]} ({sc.get("service_type","")})</option>'


# ── Pagination ────────────────────────────────────────────────────────────────
PAGE_SIZE = 10
total_orders = len(display_orders)
total_pages = max(1, -(-total_orders // PAGE_SIZE))  # ceiling division

# Reset page ke 1 kalau ganti tab filter
if st.session_state.get('_last_filter') != active_filter:
    st.session_state['order_page'] = 1
    st.session_state['_last_filter'] = active_filter

current_page = max(1, min(st.session_state.get('order_page', 1), total_pages))
page_start = (current_page - 1) * PAGE_SIZE
page_orders = display_orders[page_start : page_start + PAGE_SIZE]

# ── Build Order Cards ─────────────────────────────────────────────────────────
cards = ""
for o in page_orders:
    # Use Orders.status as primary label driver
    os_ = (o.get('order_status') or o.get('status') or 'pending').lower()
    # Shipments data only for display (not for filtering)
    ss = (o.get('shipping_status') or 'pending').lower()
    tracking = o.get("tracking_number", "") or ""
    ship_co = o.get("shipment_company_name", "") or ""
    ship_svc = o.get("shipment_service", "") or ""

    label_map = {
        'pending':   ("Belum Bayar",       "text-secondary bg-secondary-container/50"),
        'paid':      ("Perlu Dikirim",      "text-yellow-700 bg-yellow-100"),
        'shipped':   ("Dalam Pengiriman",   "text-blue-700 bg-blue-100"),
        'completed': ("Selesai",            "text-green-700 bg-green-100"),
        'cancelled': ("Dibatalkan",         "text-error bg-error-container/50"),
    }
    label_txt, label_bg = label_map.get(os_, ("Belum Bayar", "text-secondary bg-secondary-container/50"))
    opacity = ""

    action_btn = ""
    if os_ == 'paid':   # Belum dikirim → tampilkan form resi + ekspedisi

        action_btn = f'''
        <div class="flex flex-col gap-3 w-full">
            <div class="flex flex-col sm:flex-row items-start sm:items-center gap-3">
                <div class="flex-1">
                    <p class="font-body-sm text-body-sm text-on-surface-variant flex items-center gap-1">
                        <span class="material-symbols-outlined text-[16px]">local_shipping</span>
                        <strong>{ship_co}{(' · ' + ship_svc) if ship_svc else ''}</strong>
                    </p>
                </div>
                <input id="resi_{o.get('order_id')}" type="text" placeholder="Nomor Resi (opsional)"
                    class="bg-surface-bright border border-outline-variant rounded-full py-2 px-4 text-sm outline-none focus:ring-2 focus:ring-primary-container w-full sm:w-auto"
                    value="{tracking}"/>
            </div>
            <div class="flex gap-2 flex-wrap">
                <button onclick="kirimOrder({o.get('order_id')})"
                    class="bg-gradient-to-r from-pink-400 to-purple-400 text-white font-label-caps text-label-caps px-6 py-2.5 rounded-full hover:shadow-lg hover:-translate-y-0.5 transition-all">
                    Konfirmasi Kirim
                </button>
                <button onclick="if(confirm('Yakin ingin membatalkan pesanan ini?')) stNavigate({{action:'cancel_order', oid:{o.get('order_id')}}})"
                    class="border border-red-200 text-red-600 bg-red-50 font-label-caps text-label-caps px-5 py-2.5 rounded-full hover:bg-red-100 transition-all flex items-center gap-1">
                    <span class="material-symbols-outlined text-[14px]">cancel</span> Batalkan
                </button>
            </div>
        </div>'''
    elif os_ == 'shipped':   # Dalam pengiriman → tampilkan info ekspedisi
        action_btn = f'''
        <div class="flex flex-col sm:flex-row items-start sm:items-center gap-3 w-full">
            <div class="flex-1">
                <p class="font-body-sm text-body-sm text-on-surface-variant flex items-center gap-1">
                    <span class="material-symbols-outlined text-[16px]">local_shipping</span>
                    <strong>{ship_co}{(' · ' + ship_svc) if ship_svc else 'Ekspedisi tidak diset'}</strong>
                </p>
                <p class="font-body-sm text-body-sm text-on-surface-variant mt-0.5">
                    {'Resi: <strong>' + tracking + '</strong>' if tracking else 'Belum ada nomor resi'}
                </p>
                <p class="font-body-sm text-body-sm text-blue-600 mt-0.5">
                    Status pengiriman: <strong>{ss.capitalize()}</strong>
                </p>
            </div>
        </div>'''

    img_path = o.get('image_url', '') or ''
    img_b64 = get_image_base64(img_path) if img_path else 'https://via.placeholder.com/64'

    cards += f'''
    <div class="bg-surface-container-lowest rounded-xl p-lg shadow-glow relative overflow-hidden group hover:shadow-glow-lg transition-shadow {opacity}">
        <div class="absolute top-0 right-0 w-24 h-24 bg-primary-container/20 rounded-bl-full -z-10 group-hover:scale-110 transition-transform"></div>
        <div class="flex justify-between items-start mb-md pb-md border-b border-surface-variant/50">
            <div>
                <span class="font-label-caps text-label-caps px-2 py-1 rounded-md inline-block mb-xs {label_bg}">{label_txt}</span>
                <p class="font-body-md text-body-md font-semibold text-on-surface">ORD-{o.get("order_id","")}</p>
                <p class="font-body-sm text-body-sm text-on-surface-variant flex items-center gap-1 mt-1">
                    <span class="material-symbols-outlined text-[16px]">person</span> {o.get("customer_name","")}
                </p>
            </div>
            <div class="text-right">
                <p class="font-body-sm text-body-sm text-on-surface-variant mb-xs">{str(o.get("created_at",""))[:10]}</p>
                <p class="font-h3 text-h3 text-primary">{format_rupiah(o.get("subtotal",0))}</p>
                <p class="text-xs text-on-surface-variant">x{o.get("quantity",1)}</p>
            </div>
        </div>
        <div class="flex gap-4 mb-md items-center">
            <img class="w-16 h-16 rounded-lg object-cover bg-surface-container-low shrink-0" src="{img_b64}"/>
            <div class="flex-1">
                <p class="font-body-md text-body-md text-on-surface line-clamp-1 font-medium">{o.get("product_name","")}</p>
            </div>
            <button onclick="stNavigate({{action:'view_txn', oid:{o.get('order_id')}}})" class="font-label-caps text-[11px] text-primary hover:underline flex items-center gap-1 px-4 py-2 border border-primary rounded-full">
                <span class="material-symbols-outlined text-[14px]">visibility</span> LIHAT DETAIL (SEMUA PRODUK)
            </button>
        </div>
        {f'<div class="flex justify-end pt-md border-t border-surface-variant/50">{action_btn}</div>' if action_btn else ''}
    </div>
    '''

if not display_orders:
    cards = '<div class="col-span-2 text-center py-16 text-on-surface-variant"><span class="material-symbols-outlined text-[48px] mb-4 block">inbox</span>Tidak ada pesanan.</div>'

# Pagination controls
if total_pages > 1:
    prev_disabled = 'opacity-40 cursor-not-allowed pointer-events-none' if current_page <= 1 else 'hover:bg-primary-container/50 cursor-pointer'
    next_disabled = 'opacity-40 cursor-not-allowed pointer-events-none' if current_page >= total_pages else 'hover:bg-primary-container/50 cursor-pointer'

    # Page number buttons (show max 5 pages around current)
    page_btns = ""
    start_p = max(1, current_page - 2)
    end_p = min(total_pages, start_p + 4)
    if end_p - start_p < 4:
        start_p = max(1, end_p - 4)

    for p in range(start_p, end_p + 1):
        active_cls = "bg-primary text-white shadow-glow" if p == current_page else "text-on-surface-variant hover:bg-primary-container/40"
        page_btns += f'<button onclick="stNavigate({{action:\'go_page\', page:{p}}})" class="w-9 h-9 rounded-full font-semibold text-sm transition-all {active_cls}">{p}</button>'

    pagination_html = f'''
    <div class="col-span-2 flex items-center justify-between pt-4 mt-2 border-t border-surface-variant/50">
        <p class="text-sm text-on-surface-variant">
            Menampilkan <strong>{page_start+1}–{min(page_start+PAGE_SIZE, total_orders)}</strong> dari <strong>{total_orders}</strong> pesanan
        </p>
        <div class="flex items-center gap-1">
            <button onclick="stNavigate({{action:'go_page', page:{current_page-1}}})"
                class="w-9 h-9 rounded-full flex items-center justify-center text-on-surface-variant transition-all {prev_disabled}">
                <span class="material-symbols-outlined text-[18px]">chevron_left</span>
            </button>
            {page_btns}
            <button onclick="stNavigate({{action:'go_page', page:{current_page+1}}})"
                class="w-9 h-9 rounded-full flex items-center justify-center text-on-surface-variant transition-all {next_disabled}">
                <span class="material-symbols-outlined text-[18px]">chevron_right</span>
            </button>
        </div>
    </div>'''
else:
    pagination_html = ""

html = re.sub(
    r'(<div class="grid grid-cols-1 xl:grid-cols-2 gap-lg">)(.*?)(</main>)',
    rf'\1{cards}</div>{pagination_html}\3', html, flags=re.DOTALL
)

company_name = user.get('company', {}).get('company_name', 'Toko Saya')
html = inject_seller_sidebar(html, "11_Kelola_Pesanan", company_name)

js_head = """<script>
function stNavigate(params) {
    params._ts = Date.now();
    if(window.Streamlit) { window.Streamlit.setComponentValue(params); }
}
// Search: only on Enter
function onOrderSearchEnter(e, val) {
    if (e.key === 'Enter') {
        stNavigate({action: 'search_order', q: val.trim()});
    }
}
function kirimOrder(orderId) {
    const resi = document.getElementById('resi_' + orderId);
    const trackingNumber = resi ? resi.value.trim() : '';
    stNavigate({action: 'kirim_order', oid: orderId, tracking: trackingNumber});
}
</script>"""
html = html.replace("</head>", js_head + "</head>")
html = html.replace('href="#"', 'href="#" onclick="event.preventDefault();"')

action_data = render_original_html("belikuy_v2_orders", html, height=1400)

if action_data:
    act = action_data.get('action')
    if handle_seller_global_action(st, act):
        pass
    elif act == "filter_status":
        st.session_state['order_status_filter'] = action_data.get('status_val', '')
        st.session_state['order_page'] = 1
        st.rerun()
    elif act == "search_order":
        st.session_state['order_search'] = action_data.get('q', '')
        st.session_state['order_page'] = 1
        st.rerun()
    elif act == "view_txn":
        show_transaction_details(action_data.get("oid"))
    elif act == "go_page":
        page = int(action_data.get('page', 1))
        st.session_state['order_page'] = max(1, min(page, total_pages))
        st.rerun()
    elif act == "update_status":
        order_id = action_data.get("oid")
        status = action_data.get("status")
        if order_id and status:
            put_api(f"orders/{order_id}/status", {"status": status, "company_id": company_id})
        st.rerun()
    elif act == "kirim_order":
        order_id = action_data.get("oid")
        tracking = action_data.get("tracking", "")
        sc_id = action_data.get("sc_id", "") or None
        if order_id:
            payload = {"company_id": company_id, "tracking_number": tracking}
            if sc_id:
                payload["shipment_company_id"] = int(sc_id)
            put_api(f"orders/shipment/{order_id}", payload)
        st.rerun()
    elif act == "cancel_order":
        order_id = action_data.get("oid")
        if order_id:
            put_api(f"orders/{order_id}/status", {"status": "cancelled", "company_id": company_id})
        st.rerun()
