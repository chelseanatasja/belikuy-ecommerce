import streamlit as st
import sys, os, re, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from utils import get_api, post_api, require_login, hide_streamlit_ui, format_rupiah
from html_bridge import render_original_html
from unified_navbar import inject_navbar, handle_global_action
import mysql.connector

FRONTEND_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def local_img(path):
    if not path: return ""
    if path.startswith("http"): return path
    try:
        full = os.path.join(FRONTEND_BASE, path.replace("\\", "/"))
        if os.path.exists(full):
            ext = os.path.splitext(full)[1].lower().lstrip(".")
            mime = {"jpg":"jpeg","jpeg":"jpeg","png":"png","gif":"gif","webp":"webp"}.get(ext,"jpeg")
            with open(full,"rb") as f:
                return f"data:image/{mime};base64,{base64.b64encode(f.read()).decode()}"
    except: pass
    return ""

# ── Dialog: Detail Transaksi ─────────────────────────────────────────────────
@st.dialog("Detail Pesanan")
def show_transaction_details(tid):
    conn = mysql.connector.connect(host="127.0.0.1", user="root", password="")
    c = conn.cursor(dictionary=True)
    c.execute("""
        SELECT oi.*, p.product_name, p.image_url, comp.company_name
        FROM belikuy_marketplace_db.order_items oi
        LEFT JOIN belikuy_seller_db.products p ON oi.product_id = p.id
        LEFT JOIN belikuy_seller_db.companies comp ON p.company_id = comp.id
        WHERE oi.order_id = %s
    """, (tid,))
    items = c.fetchall()
    c.execute("""SELECT o.*, u.username, u.email, pm.institution_name as payment_method,
                        sh.company_name as ship_co, sh.service_type as ship_svc
                 FROM belikuy_marketplace_db.orders o
                 LEFT JOIN belikuy_marketplace_db.users u ON o.user_id = u.id 
                 LEFT JOIN belikuy_payment_db.payments pay ON o.id = pay.order_id
                 LEFT JOIN belikuy_payment_db.payment_methods pm ON pay.payment_method_id = pm.id
                 LEFT JOIN belikuy_delivery_db.shipments shi ON o.id = shi.order_id
                 LEFT JOIN belikuy_delivery_db.shipment_companies sh ON shi.shipment_company_id = sh.id
                 WHERE o.id = %s ORDER BY pay.id DESC LIMIT 1""", (tid,))
    order = c.fetchone()
    conn.close()

    if order:
        status_map = {
            'pending':   ('Menunggu Pembayaran', '#c2410c', '#fff7ed'),
            'paid':      ('Sedang Dikemas',      '#1d4ed8', '#eff6ff'),
            'shipped':   ('Dalam Pengiriman',    '#7c3aed', '#f5f3ff'),
            'completed': ('Selesai',             '#15803d', '#f0fdf4'),
            'cancelled': ('Dibatalkan',          '#b91c1c', '#fef2f2'),
        }
        label, color, bg = status_map.get(order['status'], (order['status'].capitalize(), '#374151', '#f9fafb'))
        st.markdown(f"""
        <div style="font-family: 'Plus Jakarta Sans', sans-serif; padding: 4px 0 12px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <span style="font-size:20px; font-weight:700; color:#874e58;">Order #{order['id']}</span>
                <span style="background:{bg}; color:{color}; padding:4px 12px; border-radius:20px; font-size:12px; font-weight:600;">{label}</span>
            </div>
            <div style="color:#514345; font-size:13px; margin-bottom:4px;"><b>Tanggal:</b> {str(order['created_at'])[:16]}</div>
            <div style="color:#514345; font-size:13px; margin-bottom:4px;"><b>Pembeli:</b> {order['username']} &middot; {order['email']}</div>
            <div style="color:#514345; font-size:13px; margin-bottom:4px;"><b>Metode Pembayaran:</b> {order.get('payment_method') or 'Belum Dipilih'}</div>
            <div style="color:#514345; font-size:13px;"><b>Pengiriman:</b> {((order.get('ship_co') or '') + ' ' + (order.get('ship_svc') or '')).strip() or 'Belum Dipilih'}</div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        st.markdown("**Daftar Produk:**")
        for item in items:
            img_url = local_img(item.get('image_url', '')) or "https://via.placeholder.com/60?text=No+Img"
            col1, col2 = st.columns([1, 4])
            with col1:
                st.image(img_url, width=60)
            with col2:
                st.markdown(f"""**{item['product_name'] or 'Produk Dihapus'}**  
{item.get('company_name') or '–'} &middot; x{item['quantity']}  
{format_rupiah(float(item['price']) * int(item['quantity']))}""")
        st.divider()
        st.markdown(f"### Total: **{format_rupiah(order['total_price'])}**")
    else:
        st.error("Transaksi tidak ditemukan.")

# ── Dialog: Lacak Pesanan ─────────────────────────────────────────────────────
@st.dialog("Lacak Pesanan")
def show_track_order(tid):
    conn = mysql.connector.connect(host="127.0.0.1", user="root", password="")
    c = conn.cursor(dictionary=True)
    c.execute("""SELECT o.*, sh.company_name as ship_co, sh.service_type,
                        shi.tracking_number, shi.shipping_status
                 FROM belikuy_marketplace_db.orders o
                 LEFT JOIN belikuy_delivery_db.shipments shi ON o.id = shi.order_id
                 LEFT JOIN belikuy_delivery_db.shipment_companies sh ON shi.shipment_company_id = sh.id
                 WHERE o.id = %s""", (tid,))
    order = c.fetchone()
    conn.close()

    if not order:
        st.error("Pesanan tidak ditemukan.")
        return

    status = order.get('status', 'pending')
    track_no = order.get('tracking_number') or ''
    ship_co = order.get('ship_co') or ''
    ship_svc = order.get('service_type') or ''

    # Step index
    step_keys = ['pending', 'paid', 'shipped', 'completed']
    order_idx = step_keys.index(status) if status in step_keys else (3 if status == 'completed' else -1)

    steps = [
        ('receipt_long',   'Pesanan Dibuat',      'Pesanan berhasil dibuat'),
        ('inventory_2',    'Sedang Dikemas',       'Seller sedang memproses pesananmu'),
        ('local_shipping', 'Dalam Pengiriman',     (ship_co + ' ' + ship_svc).strip() or 'Paket sedang dikirim'),
        ('check_circle',   'Pesanan Diterima',     'Pesanan berhasil diterima'),
    ]

    # Inject fonts
    st.markdown('<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet"/>', unsafe_allow_html=True)
    st.markdown('<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>', unsafe_allow_html=True)

    if status == 'cancelled':
        st.markdown("""
        <div style="font-family:'Plus Jakarta Sans',sans-serif; text-align:center; padding:24px 0;">
            <span class="material-symbols-outlined" style="font-size:48px; color:#b91c1c; font-variation-settings:'FILL' 1;">cancel</span>
            <p style="font-size:16px; font-weight:700; color:#b91c1c; margin:8px 0 4px;">Pesanan Dibatalkan</p>
        </div>""", unsafe_allow_html=True)
        return

    parts = []
    parts.append('<div style="font-family:\'Plus Jakarta Sans\',sans-serif; padding:4px 0;">')
    parts.append('<p style="font-size:12px; color:#874e58; font-weight:700; margin-bottom:20px; letter-spacing:0.06em; text-transform:uppercase;">Order #' + str(tid) + '</p>')

    for i, (icon, title, subtitle) in enumerate(steps):
        is_done   = i < order_idx
        is_active = i == order_idx
        is_last   = (i == len(steps) - 1)

        if is_done:
            dot_bg, dot_color, title_color, sub_color, line_color = "#874e58","white","#191c1d","#514345","#874e58"
            ring = ""
        elif is_active:
            dot_bg, dot_color, title_color, sub_color, line_color = "#874e58","white","#191c1d","#514345","#e1e3e4"
            ring = "box-shadow:0 0 0 4px rgba(135,78,88,0.18);"
        else:
            dot_bg, dot_color, title_color, sub_color, line_color = "#f3f4f5","#847375","#847375","#a8b0b4","#e1e3e4"
            ring = ""

        connector = '' if is_last else '<div style="width:2px; height:36px; background:' + line_color + '; margin:2px 0;"></div>'
        pb = '0' if is_last else '4px'

        parts.append(
            '<div style="display:flex; gap:14px; align-items:flex-start;">'
            '<div style="display:flex; flex-direction:column; align-items:center; flex-shrink:0;">'
            '<div style="width:36px; height:36px; border-radius:50%; background:' + dot_bg + '; display:flex; align-items:center; justify-content:center; ' + ring + '">'
            '<span class="material-symbols-outlined" style="font-size:18px; color:' + dot_color + '; font-variation-settings:\'FILL\' 1;">' + icon + '</span>'
            '</div>'
            + connector +
            '</div>'
            '<div style="padding-top:6px; padding-bottom:' + pb + ';">'
            '<p style="font-size:14px; font-weight:700; color:' + title_color + '; margin:0;">' + title + '</p>'
            '<p style="font-size:12px; color:' + sub_color + '; margin:3px 0 0;">' + subtitle + '</p>'
            '</div>'
            '</div>'
        )

    if track_no:
        parts.append(
            '<div style="margin-top:20px; padding:14px 16px; background:linear-gradient(135deg,#fff0f3,#fdf4ff); border-radius:14px; border:1px solid #ffb6c1;">'
            '<p style="font-size:11px; color:#874e58; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; margin:0 0 4px;">Nomor Resi</p>'
            '<p style="font-size:16px; font-weight:800; color:#191c1d; margin:0;">' + track_no + '</p>'
            '<p style="font-size:12px; color:#514345; margin:4px 0 0;">' + ship_co + ' ' + ship_svc + '</p>'
            '</div>'
        )

    parts.append('</div>')
    st.markdown(''.join(parts), unsafe_allow_html=True)


# ── Page setup ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="BeliKuy - Riwayat Pesanan", layout="wide", initial_sidebar_state="collapsed")
hide_streamlit_ui()
require_login()

user = st.session_state['user']
all_orders, _ = get_api(f"orders/user/{user['id']}")
if not all_orders: all_orders = []

current_status = st.query_params.get("status", "all")
orders = all_orders if current_status == "all" else [o for o in all_orders if o.get("status") == current_status]

# Success banner
success_banner = ""
if st.session_state.pop('order_success', False):
    order_id = st.session_state.pop('last_order_id', '')
    success_banner = f'''
    <div style="background:linear-gradient(135deg,#f0fdf4,#dcfce7); border:1px solid #86efac; border-radius:16px; padding:16px 20px; margin-bottom:20px; display:flex; align-items:center; gap:16px;">
        <span class="material-symbols-outlined" style="font-size:36px; color:#16a34a; font-variation-settings:'FILL' 1;">check_circle</span>
        <div>
            <p style="font-weight:700; font-size:15px; color:#15803d; margin:0;">Pesanan berhasil dibuat!</p>
            <p style="font-size:12px; color:#166534; margin:4px 0 0;">ID Pesanan: #{order_id} &middot; Terima kasih sudah belanja di BeliKuy!</p>
        </div>
    </div>'''

# ── Status badge ────────────────────────────────────────────────────────────
def status_badge(status):
    cfg = {
        'pending':   ('#fff7ed', '#c2410c', 'schedule',       'Menunggu Pembayaran'),
        'paid':      ('#eff6ff', '#1d4ed8', 'inventory_2',    'Sedang Dikemas'),
        'shipped':   ('#f5f3ff', '#7c3aed', 'local_shipping', 'Dalam Pengiriman'),
        'completed': ('#f0fdf4', '#15803d', 'check_circle',   'Selesai'),
        'cancelled': ('#fef2f2', '#b91c1c', 'cancel',         'Dibatalkan'),
    }
    bg, color, icon, label = cfg.get(status, ('#f9fafb', '#374151', 'info', status.capitalize()))
    return f'''<span style="display:inline-flex; align-items:center; gap:5px; background:{bg}; color:{color}; padding:4px 12px; border-radius:20px; font-size:11px; font-weight:700; letter-spacing:0.03em;">
        <span class="material-symbols-outlined" style="font-size:13px; font-variation-settings:'FILL' 1;">{icon}</span>{label}
    </span>'''

# ── Build order cards ──────────────────────────────────────────────────────────
orders_html = ""
for o in orders:
    status = o.get("status", "pending")
    items = o.get("items", [])
    shipment = o.get("shipment") or {}
    ship_co = shipment.get("shipment_company", "") or ""
    ship_svc = shipment.get("shipment_service", "") or ""
    tracking = shipment.get("tracking_number", "") or ""
    oid = o.get("order_id", "")

    # Items list
    items_html = ""
    for item in items:
        raw_img = item.get("image_url", "") or ""
        img_url = local_img(raw_img) or "https://via.placeholder.com/56?text=No+Img"
        pname = str(item.get("product_name", "Produk")).replace('"', '&quot;')
        seller = item.get("seller_name", "") or "–"
        qty = item.get("quantity", 1)
        subtotal_item = format_rupiah(item.get("subtotal", 0))
        items_html += f'''
        <div style="display:flex; align-items:center; gap:14px; padding:10px 0; border-bottom:1px solid #f3f4f5;">
            <img src="{img_url}" onerror="this.src='https://via.placeholder.com/56?text=No+Img'"
                 style="width:56px; height:56px; border-radius:12px; object-fit:cover; background:#f3f4f5; flex-shrink:0;"/>
            <div style="flex:1; min-width:0;">
                <p style="font-weight:600; font-size:14px; color:#191c1d; margin:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{pname}</p>
                <p style="font-size:12px; color:#514345; margin:2px 0 0;">{seller} &middot; x{qty}</p>
            </div>
            <p style="font-size:14px; font-weight:700; color:#874e58; flex-shrink:0; margin:0;">{subtotal_item}</p>
        </div>'''

    if not items_html:
        items_html = '<p style="font-size:13px; color:#847375; padding:12px 0;">Detail produk tidak tersedia</p>'

    # Shipment pill
    ship_pill = ""
    if status in ('shipped', 'completed') and ship_co:
        ship_pill = f'''
        <div style="display:inline-flex; align-items:center; gap:6px; background:#eff6ff; color:#1d4ed8; padding:5px 12px; border-radius:20px; font-size:12px; font-weight:600; margin-top:10px;">
            <span class="material-symbols-outlined" style="font-size:14px;">local_shipping</span>
            {ship_co}{(' &middot; ' + ship_svc) if ship_svc else ''}{(' &middot; Resi: ' + tracking) if tracking else ''}
        </div>'''
    elif status == 'paid':
        ship_pill = '''
        <div style="display:inline-flex; align-items:center; gap:6px; background:#fff7ed; color:#c2410c; padding:5px 12px; border-radius:20px; font-size:12px; font-weight:600; margin-top:10px;">
            <span class="material-symbols-outlined" style="font-size:14px;">inventory_2</span>
            Seller sedang memproses pesananmu
        </div>'''

    btn_style_outline = "border:1.5px solid #e1e3e4; color:#514345; background:transparent; padding:7px 14px; border-radius:20px; font-size:12px; font-weight:700; cursor:pointer; font-family:'Plus Jakarta Sans',sans-serif; display:inline-flex; align-items:center; gap:5px; transition:background .15s;"
    btn_style_primary = "border:none; background:linear-gradient(135deg,#ffb6c1,#fcb3be); color:#7b444e; padding:7px 14px; border-radius:20px; font-size:12px; font-weight:700; cursor:pointer; font-family:'Plus Jakarta Sans',sans-serif; display:inline-flex; align-items:center; gap:5px;"
    btn_style_detail  = "border:1.5px solid #874e58; color:#874e58; background:transparent; padding:7px 14px; border-radius:20px; font-size:12px; font-weight:700; cursor:pointer; font-family:'Plus Jakarta Sans',sans-serif; display:inline-flex; align-items:center; gap:5px;"
    btn_style_green   = "border:none; background:linear-gradient(135deg,#22c55e,#16a34a); color:white; padding:7px 14px; border-radius:20px; font-size:12px; font-weight:700; cursor:pointer; font-family:'Plus Jakarta Sans',sans-serif; display:inline-flex; align-items:center; gap:5px;"
    btn_style_red     = "border:1.5px solid #fca5a5; color:#b91c1c; background:#fef2f2; padding:7px 14px; border-radius:20px; font-size:12px; font-weight:700; cursor:pointer; font-family:'Plus Jakarta Sans',sans-serif; display:inline-flex; align-items:center; gap:5px;"

    btns = f'''
    <button onclick="stNavigate({{action:'view_txn', oid:{oid}}})" style="{btn_style_detail}">
        <span class="material-symbols-outlined" style="font-size:14px;">receipt_long</span> Detail
    </button>
    <button onclick="stNavigate({{action:'track_order', oid:{oid}}})" style="{btn_style_outline}">
        <span class="material-symbols-outlined" style="font-size:14px;">radar</span> Lacak
    </button>'''

    if status == 'pending':
        btns += f'''
        <button onclick="stNavigate({{action:'pay_order', oid:{oid}, total:{o.get('total_price', 0)}}})" style="{btn_style_green}">
            <span class="material-symbols-outlined" style="font-size:14px;">payments</span> Bayar Sekarang
        </button>
        <button onclick="if(confirm('Yakin ingin membatalkan pesanan ini?')) stNavigate({{action:'cancel_order', oid:{oid}}})" style="{btn_style_red}">
            <span class="material-symbols-outlined" style="font-size:14px;">cancel</span> Batalkan
        </button>'''

    if status == 'shipped':
        btns += f'''
        <button onclick="stNavigate({{action:'confirm_received', oid:{oid}}})" style="{btn_style_green}">
            <span class="material-symbols-outlined" style="font-size:14px;">verified</span> Konfirmasi Diterima
        </button>'''

    if status in ('completed', 'cancelled'):
        btns += f'''
        <button onclick="stNavigate({{action:'go_search'}})" style="{btn_style_primary}">
            <span class="material-symbols-outlined" style="font-size:14px;">shopping_bag</span> Beli Lagi
        </button>'''

    orders_html += f'''
    <div style="background:white; border-radius:20px; box-shadow:0 2px 12px rgba(135,78,88,0.08); border:1px solid #f3f4f5; overflow:hidden; margin-bottom:16px; font-family:'Plus Jakarta Sans',sans-serif;">
        <div style="display:flex; justify-content:space-between; align-items:center; padding:14px 20px; background:#fafafa; border-bottom:1px solid #f3f4f5;">
            <div style="display:flex; align-items:center; gap:10px;">
                <span class="material-symbols-outlined" style="font-size:18px; color:#874e58; font-variation-settings:'FILL' 1;">receipt_long</span>
                <span style="font-weight:700; font-size:14px; color:#191c1d;">Order #{oid}</span>
                <span style="font-size:12px; color:#847375;">{str(o.get("created_at",""))[:10]}</span>
            </div>
            {status_badge(status)}
        </div>
        <div style="padding:4px 20px 0;">{items_html}</div>
        {('<div style="padding:0 20px;">' + ship_pill + '</div>') if ship_pill else ''}
        <div style="display:flex; justify-content:space-between; align-items:center; padding:14px 20px; border-top:1px solid #f3f4f5; margin-top:12px; flex-wrap:wrap; gap:10px;">
            <div>
                <p style="font-size:11px; color:#847375; margin:0; text-transform:uppercase; letter-spacing:0.05em;">Total Pembayaran</p>
                <p style="font-size:20px; font-weight:800; color:#874e58; margin:2px 0 0;">{format_rupiah(o.get("total_price",0))}</p>
            </div>
            <div style="display:flex; gap:8px; flex-wrap:wrap;">{btns}</div>
        </div>
    </div>'''

empty_html = '''
<div style="text-align:center; padding:60px 20px; font-family:'Plus Jakarta Sans',sans-serif; background:white; border-radius:20px; box-shadow:0 2px 12px rgba(135,78,88,0.08);">
    <span class="material-symbols-outlined" style="font-size:64px; color:#ffb6c1; font-variation-settings:'FILL' 1;">receipt_long</span>
    <h2 style="font-size:22px; font-weight:700; color:#191c1d; margin:12px 0 8px;">Belum Ada Pesanan</h2>
    <p style="color:#514345; margin:0 0 20px;">Mulai belanja untuk membuat pesanan pertamamu!</p>
    <button onclick="stNavigate({action:'go_search'})"
        style="background:linear-gradient(135deg,#ffb6c1,#c084fc); color:white; border:none; padding:12px 28px; border-radius:20px; font-size:14px; font-weight:700; cursor:pointer; font-family:'Plus Jakarta Sans',sans-serif;">
        Mulai Belanja
    </button>
</div>'''

# ── Filter tabs ─────────────────────────────────────────────────────────────
tabs_cfg = [
    ("Semua",               "all"),
    ("Menunggu",            "pending"),
    ("Dikemas",             "paid"),
    ("Dikirim",             "shipped"),
    ("Selesai",             "completed"),
    ("Dibatalkan",          "cancelled"),
]
tabs_html = '<div style="display:flex; gap:8px; overflow-x:auto; padding-bottom:8px; margin-bottom:20px; scrollbar-width:none; -ms-overflow-style:none;">'
for label, val in tabs_cfg:
    count = len(all_orders) if val == "all" else sum(1 for o in all_orders if o.get("status") == val)
    active = current_status == val
    if active:
        btn_s = "background:linear-gradient(135deg,#ffb6c1,#fcb3be); color:#7b444e; border:none; box-shadow:0 2px 8px rgba(255,182,193,.4);"
    else:
        btn_s = "background:white; color:#514345; border:1.5px solid #e1e3e4;"
    tabs_html += f'''<button onclick="stNavigate({{action:'filter_orders', status:'{val}'}})"
        style="{btn_s} padding:8px 16px; border-radius:20px; font-size:12px; font-weight:700; white-space:nowrap; cursor:pointer; font-family:'Plus Jakarta Sans',sans-serif; display:inline-flex; align-items:center; gap:6px;">
        {label}
        <span style="background:rgba(0,0,0,.1); border-radius:10px; padding:1px 7px; font-size:10px;">{count}</span>
    </button>'''
tabs_html += '</div>'

# ── Assemble full page HTML ──────────────────────────────────────────────────
page_html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>BeliKuy - Riwayat Pesanan</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<script>
tailwind.config = {{
    theme: {{
        extend: {{
            colors: {{
                "primary": "#874e58",
                "primary-container": "#ffb6c1",
                "on-primary": "#ffffff",
                "on-primary-container": "#7b444e",
                "inverse-primary": "#fcb3be",
                "surface-bright": "#f8f9fa",
                "surface-container-lowest": "#ffffff",
                "surface-container": "#edeeef",
                "surface-variant": "#e1e3e4",
                "on-surface": "#191c1d",
                "on-surface-variant": "#514345",
                "error": "#ba1a1a",
                "on-error": "#ffffff",
                "outline": "#847375",
                "background": "#f8f9fa",
                "on-background": "#191c1d",
                "pink-50": "#fff0f3",
            }}
        }}
    }}
}}
</script>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
<style>
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ font-family:'Plus Jakarta Sans',sans-serif; background:#f8f9fa; min-height:100vh; padding-bottom:90px; }}
::-webkit-scrollbar {{ display:none; }}
</style>
</head>
<body>
<div style="max-width:740px; margin:0 auto; padding:84px 16px 24px;">
    {success_banner}
    <h1 style="font-size:28px; font-weight:800; color:#191c1d; margin-bottom:20px;">Riwayat Pesanan</h1>
    {tabs_html}
    {orders_html if orders else empty_html}
</div>
</body>
</html>"""

cart_len = len(st.session_state.get('cart', []))
page_html = inject_navbar(page_html, cart_len)

action_data = render_original_html("belikuy_v2_orders", page_html, height=1200)

if action_data:
    act = action_data.get('action')
    current_user = st.session_state.get('user')
    if handle_global_action(st, act, action_data, current_user):
        pass
    elif act == "go_home":
        st.switch_page("pages/1_Storefront.py")
    elif act == "go_search":
        st.switch_page("pages/2_Cari_Produk.py")
    elif act == "filter_orders":
        sv = action_data.get("status", "all")
        if sv == "all":
            st.query_params.clear()
        else:
            st.query_params["status"] = sv
        st.rerun()
    elif act == "view_txn":
        show_transaction_details(action_data.get("oid"))
    elif act == "track_order":
        show_track_order(action_data.get("oid"))
    elif act == 'confirm_received':
        order_id = action_data.get("oid")
        try:
            import requests as _req
            _req.put(f"http://localhost:5000/api/orders/{order_id}/status",
                     json={"status": "completed", "user_id": user['id']}, timeout=8)
            st.success("Pesanan dikonfirmasi diterima!")
        except Exception as e:
            st.error(f"Gagal konfirmasi: {e}")
        st.rerun()
    elif act == 'cancel_order':
        order_id = action_data.get("oid")
        try:
            import requests as _req
            _req.put(f"http://localhost:5000/api/orders/{order_id}/status",
                     json={"status": "cancelled", "user_id": user['id']}, timeout=8)
            st.success("Pesanan berhasil dibatalkan.")
        except Exception as e:
            st.error(f"Gagal membatalkan: {e}")
        st.rerun()
    elif act == 'pay_order':
        oid   = action_data.get("oid")
        total = float(action_data.get("total", 0))
        # Ambil detail pembayaran yang sudah tersimpan (jika ada) dari data order
        order_detail = next((o for o in orders if str(o.get("order_id")) == str(oid)), None)
        saved_method_name = ""
        if order_detail:
            saved_method_name = order_detail.get("payment_method") or ""
        # Ambil semua metode pembayaran untuk bisa pilih
        payment_methods, _ = get_api("payments/methods")
        if not payment_methods: payment_methods = []
        # Cari method_id berdasarkan nama yang tersimpan, atau pakai yang pertama
        chosen = next(
            (m for m in payment_methods if m.get("institution_name") == saved_method_name),
            payment_methods[0] if payment_methods else None
        )
        st.session_state['pending_order_id']       = oid
        st.session_state['pending_total']          = total
        st.session_state['pending_payment_method'] = int(chosen['id']) if chosen else 1
        st.session_state['pending_payment_name']   = chosen.get('institution_name', '') if chosen else ''
        st.session_state['pending_payment_type']   = chosen.get('institution_type', 'transfer') if chosen else 'transfer'
        st.switch_page("pages/5b_Pembayaran.py")
