import streamlit as st
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from utils import get_api, post_api, require_login, hide_streamlit_ui, format_rupiah, get_current_user, get_company_id, get_image_base64
from html_bridge import render_original_html
from unified_sidebar import inject_seller_sidebar, handle_seller_global_action

st.set_page_config(page_title="BeliKuy - Seller Dashboard", layout="wide", initial_sidebar_state="collapsed")
hide_streamlit_ui()
require_login()

user = get_current_user()
if user and user.get('role') != 'seller':
    st.error("🚫 Akses ditolak."); st.stop()

company = user.get('company', {}); company_id = company.get('company_id') if company else None

# Fetch data
income, _ = get_api(f"companies/{company_id}/income") if company_id else ({}, None)
orders, _ = get_api(f"companies/{company_id}/orders") if company_id else ([], None)
products, _ = get_api(f"products/seller/{company_id}") if company_id else ([], None)
company_info, _ = get_api(f"companies/{company_id}") if company_id else ({}, None)
if not income: income = {}
if not orders: orders = []
if not products: products = []
if not company_info: company_info = {}

total_omzet = format_rupiah(income.get('total_omzet', 0))
total_pesanan_selesai = income.get('total_pesanan', 0)
# Hanya hitungg paid = sudah bayar, butuh aksi seller (kirim)
# Deduplicate orders first so we don't double count orders with multiple items
seen = {}
for o in orders:
    oid = o.get('order_id')
    if oid not in seen:
        seen[oid] = o
unique_orders = list(seen.values())

pesanan_baru = sum(1 for o in unique_orders if str(o.get('order_status', o.get('status',''))).lower() == 'paid')
produk_aktif = sum(1 for p in products if p.get('is_active', 1) and p.get('stock', 0) > 0)
total_produk = len(products)
company_name = company_info.get('company_name') or (user.get('company', {}).get('company_name', 'Toko Saya') if user.get('company') else 'Toko Saya')
# Rating langsung dari DB Companies table
rating_toko = float(company_info.get('rating', 0) or 0)

HTML_BASE = r"D:\belikuy\belikuy_ui_templates"
with open(os.path.join(HTML_BASE, "seller_dashboard/code.html"), encoding='utf-8') as f:
    html = f.read()

# Recent orders: prioritaskan yang paid (perlu dikirim), lalu lainnya
paid_orders = [o for o in unique_orders if str(o.get('order_status', o.get('status',''))).lower() == 'paid']
other_orders = [o for o in unique_orders if str(o.get('order_status', o.get('status',''))).lower() != 'paid']
recent_display = (paid_orders + other_orders)[:5]

recent_orders_html = ""
for o in recent_display:
    img = get_image_base64(o.get('image_url')) if o.get('image_url') else "https://via.placeholder.com/100?text=Produk"
    os_ = str(o.get('order_status', o.get('status', ''))).lower()
    if os_ == 'paid':
        badge_bg = "bg-yellow-50 text-yellow-600"
        badge_text = "Perlu Dikirim"
    elif os_ == 'shipped':
        badge_bg = "bg-blue-50 text-blue-600"
        badge_text = "Dikirim"
    elif os_ == 'completed':
        badge_bg = "bg-green-50 text-green-600"
        badge_text = "Selesai"
    elif os_ == 'cancelled':
        badge_bg = "bg-red-50 text-red-600"
        badge_text = "Dibatalkan"
    else:
        badge_bg = "bg-zinc-100 text-zinc-600"
        badge_text = "Belum Bayar"

    recent_orders_html += f'''
    <div onclick="stNavigate({{action:'go_orders'}})" class="flex items-center gap-4 p-3 rounded-xl hover:bg-surface-bright transition-colors cursor-pointer group">
        <div class="w-12 h-12 rounded-lg overflow-hidden bg-surface-container-low shrink-0">
            <img alt="Product Image" class="w-full h-full object-cover" src="{img}"/>
        </div>
        <div class="flex-1 min-w-0">
            <h4 class="font-body-md text-sm font-semibold text-on-background truncate group-hover:text-primary transition-colors">{o.get('product_name','')}</h4>
            <p class="font-body-sm text-xs text-on-surface-variant">ORD-{o.get('order_id')} • {o.get('customer_name')}</p>
        </div>
        <div class="shrink-0 text-right">
            <span class="inline-block px-2 py-1 rounded {badge_bg} text-[10px] font-bold tracking-wider uppercase">{badge_text}</span>
        </div>
    </div>
    '''

if not recent_orders_html:
    recent_orders_html = '<p class="text-sm text-outline p-4 text-center">Belum ada pesanan terbaru.</p>'


# Build Chart HTML
monthly_omzet = income.get('monthly_omzet', [])
chart_html = ""
import datetime
current_year = datetime.datetime.now().year

if monthly_omzet:
    min_year = min(int(row.get('month', '').split('-')[0]) for row in monthly_omzet if row.get('month'))
    max_year = max(int(row.get('month', '').split('-')[0]) for row in monthly_omzet if row.get('month'))
else:
    min_year = current_year
    max_year = current_year
    
available_years = [str(y) for y in range(max(current_year, max_year), min_year - 1, -1)]
selected_year = st.session_state.get('dashboard_year_filter', str(max_year))

if not monthly_omzet:
    chart_html = '<div class="w-full h-full flex items-center justify-center text-sm text-on-surface-variant">Belum ada data penjualan</div>'
else:
    continuous_months = [f"{selected_year}-{str(m).zfill(2)}" for m in range(1, 13)]
        
    omzet_dict = {row.get('month', ''): float(row.get('omzet', 0)) for row in monthly_omzet}
    
    display_months = []
    for cm in continuous_months:
        display_months.append({
            'month': cm,
            'omzet': omzet_dict.get(cm, 0)
        })
        
    max_omzet = max([m['omzet'] for m in display_months] + [1])
    
    for m in display_months:
        omzet_val = m['omzet']
        height_pct = max(5, int((omzet_val / max_omzet) * 100))
        # Format month e.g., '2026-05' to 'Mei'
        month_str = m.get('month', '')
        month_name = month_str.split('-')[1] if '-' in month_str else month_str
        
        # Simple mapping for display
        month_map = {"01":"Jan", "02":"Feb", "03":"Mar", "04":"Apr", "05":"Mei", "06":"Jun", "07":"Jul", "08":"Ags", "09":"Sep", "10":"Okt", "11":"Nov", "12":"Des"}
        display_name = month_map.get(month_name, month_name)

        if omzet_val == max_omzet and omzet_val > 0:
            # Highlight peak
            chart_html += f'''
            <div class="w-1/12 bg-gradient-to-t from-primary-container to-secondary-container rounded-t-md shadow-[0_0_15px_rgba(255,182,193,0.5)] relative group transition-all" style="height: {height_pct}%">
                <span class="absolute -top-8 left-1/2 -translate-x-1/2 bg-surface px-2 py-1 rounded text-[10px] shadow-sm font-bold text-primary opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">{format_rupiah(omzet_val)}</span>
                <span class="absolute -bottom-6 left-1/2 -translate-x-1/2 text-xs text-on-surface-variant font-bold text-primary">{display_name}</span>
            </div>
            '''
        else:
            chart_html += f'''
            <div class="w-1/12 bg-primary-container rounded-t-md opacity-70 hover:!opacity-100 transition-all relative group" style="height: {height_pct}%">
                <span class="absolute -top-8 left-1/2 -translate-x-1/2 bg-surface px-2 py-1 rounded text-[10px] shadow-sm font-bold text-primary opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">{format_rupiah(omzet_val)}</span>
                <span class="absolute -bottom-6 left-1/2 -translate-x-1/2 text-xs text-on-surface-variant">{display_name}</span>
            </div>
            '''

# Build Year Filter HTML
year_options = ""
for y in available_years:
    sel = "selected" if y == selected_year else ""
    year_options += f'<option value="{y}" {sel}>{y}</option>'

year_filter_html = f'''
<div class="flex justify-between items-center mb-6">
    <h3 class="font-h3 text-h3 text-on-background">Performa Penjualan</h3>
    <select onchange="stNavigate({{action: 'filter_year', year: this.value}})" class="bg-surface-container-low border-none rounded-full text-sm font-body-sm px-4 py-2 focus:ring-2 focus:ring-primary-container outline-none cursor-pointer">
        {year_options}
    </select>
</div>
'''

html = html.replace('{year_filter_html}', year_filter_html)

# Inject Dynamic Values
html = html.replace('Kawaiify Official', company_name)
html = html.replace('Rp 12.500.000', total_omzet)
html = re.sub(r'(<h3 class="font-h3 text-h3 text-on-background">)(42)(</h3>)', rf'\g<1>{pesanan_baru}\3', html)
html = re.sub(r'(<h3 class="font-h3 text-h3 text-on-background">)(156)(</h3>)', rf'\g<1>{produk_aktif}\3', html)
html = re.sub(r'(<h3 class="font-h3 text-h3 text-on-background">)(4\.9)(<span class="text-sm text-on-surface-variant font-normal">/5\.0</span></h3>)', rf'\g<1>{rating_toko:.1f}\3', html)

# Remove mock data & replace with real subtexts
html = re.sub(r'<p[^>]*>\s*<span[^>]*>trending_up</span> \+15% dari bulan lalu\s*</p>',
    f'<p class="font-body-sm text-sm text-on-surface-variant mt-1 flex items-center gap-1">Dari {total_pesanan_selesai} pesanan selesai</p>', html)
html = re.sub(r'Menunggu diproses', 'Menunggu diproses seller', html)
html = re.sub(r'Dari total 180 produk', f'Dari total {total_produk} produk', html)
html = re.sub(r'<p[^>]*>\s*Berdasarkan 320 ulasan\s*</p>',
    f'<p class="font-body-sm text-sm text-on-surface-variant mt-1">Rating toko kamu</p>', html)

# Replace Recent Orders Content
html = re.sub(r'(<div class="flex flex-col gap-4 flex-1">)(.*?)(</div>\s*<button)', rf'\1{recent_orders_html}\3', html, flags=re.DOTALL)

# Replace Chart Content
html = re.sub(r'(<div class="relative z-10 w-full flex justify-between items-end h-full group">)(.*?)(</div>\s*</div>\s*</div>)', rf'\1\n{chart_html}\n\3', html, flags=re.DOTALL)

# Inject Sidebar
html = inject_seller_sidebar(html, "9_Seller_Dashboard", company_name)

js_head = """<script>
function stNavigate(params) {
    params._ts = Date.now();
    if(window.Streamlit) { window.Streamlit.setComponentValue(params); }
}
</script>"""
html = html.replace("</head>", js_head + "</head>")
# Wire "Lihat Semua" / "Kelola Pesanan" buttons with direct onclick
html = html.replace('href="#" onclick="event.preventDefault();"', 'href="#" onclick="event.preventDefault();"')
# Fix the Lihat Semua button in recent orders
html = re.sub(
    r'(<button[^>]*>[^<]*(?:Lihat Semua|Kelola Pesanan)[^<]*</button>)',
    lambda m: m.group(0).replace('<button', '<button onclick="stNavigate({action:\'go_orders\'})"', 1),
    html
)

action_data = render_original_html("belikuy_v2_seller", html, height=1300)

if action_data:
    act = action_data.get('action')
    if handle_seller_global_action(st, act):
        pass
    elif act == 'filter_year':
        st.session_state['dashboard_year_filter'] = action_data.get('year')
        st.rerun()
