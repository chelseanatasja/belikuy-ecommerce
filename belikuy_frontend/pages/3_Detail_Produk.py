import streamlit as st
import sys, os, re, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from utils import get_api, require_login, hide_streamlit_ui, format_rupiah
from html_bridge import render_original_html
from unified_navbar import inject_navbar, handle_global_action

st.set_page_config(page_title="BeliKuy - Detail Produk", layout="wide", initial_sidebar_state="collapsed")
hide_streamlit_ui()
require_login()

FRONTEND_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def local_img(path, placeholder_text="No+Image"):
    if not path:
        return f"https://via.placeholder.com/600?text={placeholder_text}"
    if path.startswith("http"):
        return path
    try:
        full = os.path.join(FRONTEND_BASE, path.replace("\\", "/"))
        if os.path.exists(full):
            ext = os.path.splitext(full)[1].lower().lstrip(".")
            mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "gif": "gif", "webp": "webp"}.get(ext, "jpeg")
            with open(full, "rb") as f:
                return f"data:image/{mime};base64,{base64.b64encode(f.read()).decode()}"
    except:
        pass
    return f"https://via.placeholder.com/600?text={placeholder_text}"

product_id = st.session_state.get('viewing_product_id')

cart_len = len(st.session_state.get('cart', []))
cart_badge_html = f'<span class="absolute -top-1 -right-1 bg-error text-on-error text-[10px] font-bold h-4 w-4 rounded-full flex items-center justify-center">{cart_len}</span>' if cart_len > 0 else ''

if not product_id:
    st.warning("Tidak ada produk dipilih.")
    if st.button("← Kembali ke Produk"):
        st.switch_page("pages/2_Cari_Produk.py")
    st.stop()

product, err = get_api(f"products/{product_id}")
if err or not product:
    st.error("Produk tidak ditemukan.")
    if st.button("← Kembali"):
        st.switch_page("pages/1_Storefront.py")
    st.stop()

img     = local_img(product.get('image_url', ''))
price   = format_rupiah(product.get('price', 0))
name    = str(product.get('product_name', 'Produk')).replace("'", "&#39;").replace('"', '&quot;')
desc    = str(product.get('description', '') or 'Produk berkualitas tinggi dari toko terpercaya.')
shop    = str(product.get('company_name', '') or 'BeliKuy Store')
cat     = str(product.get('category_name', '') or '')
stock   = int(product.get('stock', 0) or 0)
pid     = str(product.get('id', ''))
brand   = str(product.get('brand', '') or '')
color   = str(product.get('color', '') or '')
size    = str(product.get('size', '') or '')
shop_rating = str(product.get('company_rating', '0.0') or '0.0')
try:
    product_rating = float(product.get('product_rating', 0))
except:
    product_rating = 0.0
review_count = int(product.get('review_count', 0))

# Fetch reviews
reviews, _ = get_api(f"products/{product_id}/reviews")
if not reviews: reviews = []

# Fetch related products (same category)
related, _ = get_api("products", params={"category_id": product.get("category_id", "")})
if not related: related = []
related = [p for p in related if str(p.get('id', '')) != str(pid)][:4]

def rel_card(p):
    ri = local_img(p.get('image_url', ''))
    rn = str(p.get('product_name', '')).replace("'", "&#39;")
    rp = format_rupiah(p.get('price', 0))
    rpid = p.get('id', '')
    return f'''
    <div class="group cursor-pointer" onclick="stNavigate({{action:'go_detail', pid:'{rpid}'}})">
        <div class="bg-surface-container-lowest rounded-2xl aspect-[4/5] mb-4 overflow-hidden shadow-subtle relative">
            <img alt="{rn}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" src="{ri}" onerror="this.src='https://via.placeholder.com/300?text=No+Image'"/>
        </div>
        <h3 class="font-body-md text-body-md text-on-surface font-medium truncate">{rn}</h3>
        <div class="flex items-center justify-between mt-1">
            <span class="font-body-md text-body-md text-primary font-semibold">{rp}</span>
        </div>
    </div>'''

related_html = "".join(rel_card(p) for p in related) if related else '<p class="text-on-surface-variant col-span-4 py-8 text-center">Belum ada produk terkait.</p>'

# Build star rating display based on product rating
full_stars = int(product_rating)
half_star = 1 if (product_rating - full_stars) >= 0.5 else 0
empty_stars = 5 - full_stars - half_star

star_html = ""
for _ in range(full_stars):
    star_html += '<span class="material-symbols-outlined icon-fill">star</span>'
if half_star:
    star_html += '<span class="material-symbols-outlined">star_half</span>'
for _ in range(empty_stars):
    star_html += '<span class="material-symbols-outlined">star</span>'

# Build reviews HTML
def review_card(r):
    from datetime import datetime
    try:
        dt = datetime.strptime(r.get('created_at', ''), "%Y-%m-%dT%H:%M:%S.%fZ")
        d_str = dt.strftime("%d %b %Y")
    except:
        d_str = r.get('created_at', '')[:10]
        
    uname = r.get('username', 'User') if r.get('username') else 'Pengguna'
    comment = str(r.get('comment', ''))
    rt = int(r.get('rating', 5) or 5)
    stars = '<span class="material-symbols-outlined icon-fill text-[14px]">star</span>' * rt
    stars += '<span class="material-symbols-outlined text-[14px]">star</span>' * (5 - rt)
    
    return f'''
    <div class="bg-surface-bright rounded-2xl p-5 border border-outline-variant/30">
        <div class="flex justify-between items-start mb-2">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-full bg-primary-container text-on-primary-container flex items-center justify-center font-bold text-lg">
                    {uname[:1].upper()}
                </div>
                <div>
                    <h4 class="font-body-sm text-on-surface font-semibold">{uname}</h4>
                    <div class="flex text-yellow-400 gap-0.5 mt-0.5">
                        {stars}
                    </div>
                </div>
            </div>
            <span class="font-body-sm text-outline text-[12px]">{d_str}</span>
        </div>
        <p class="font-body-sm text-on-surface-variant leading-relaxed mt-3">{comment}</p>
    </div>'''

reviews_html = ""
if reviews:
    reviews_html = f'<div class="grid grid-cols-1 md:grid-cols-2 gap-4">{"".join(review_card(r) for r in reviews)}</div>'
else:
    reviews_html = '<div class="text-center py-8 text-outline bg-surface-bright rounded-2xl border border-dashed border-outline-variant/50">Belum ada ulasan untuk produk ini.</div>'

# Spec badges
specs_html = ""
if brand:
    specs_html += f'<span class="px-3 py-1 bg-surface-container text-on-surface-variant font-label-caps text-label-caps rounded-full">{brand}</span>'
if cat:
    specs_html += f'<span class="px-3 py-1 bg-secondary-container text-on-secondary-container font-label-caps text-label-caps rounded-full">{cat}</span>'

# Attributes row (Color, Size) — only show if data exists
attrs_html = ""
if color:
    attrs_html += f'''
    <div class="mb-4">
        <span class="font-body-sm text-body-sm text-on-surface-variant">Warna: <strong class="text-on-surface">{color}</strong></span>
    </div>'''
if size:
    attrs_html += f'''
    <div class="mb-4">
        <span class="font-body-sm text-body-sm text-on-surface-variant">Ukuran: <strong class="text-on-surface">{size}</strong></span>
    </div>'''

page_html = f"""<!DOCTYPE html>
<html class="light" lang="id"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>BeliKuy - {name}</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
<script id="tailwind-config">
tailwind.config = {{
    darkMode: "class",
    theme: {{
        extend: {{
            colors: {{
                "inverse-primary": "#fcb3be", "primary": "#874e58", "surface-bright": "#f8f9fa",
                "primary-container": "#ffb6c1", "on-primary-container": "#7b444e",
                "secondary-container": "#f8d5f7", "on-secondary-container": "#755977",
                "surface-container-lowest": "#ffffff", "surface-container": "#edeeef",
                "surface-container-low": "#f3f4f5", "surface-variant": "#e1e3e4",
                "outline-variant": "#d6c2c3", "outline": "#847375",
                "on-surface": "#191c1d", "on-surface-variant": "#514345",
                "on-background": "#191c1d", "background": "#f8f9fa",
                "error": "#ba1a1a", "error-container": "#ffdad6", "on-error-container": "#93000a",
                "primary-fixed": "#ffd9de", "primary-fixed-dim": "#fcb3be",
                "on-primary-fixed-variant": "#6b3741", "secondary": "#715572",
            }},
            fontFamily: {{
                "h1": ["Plus Jakarta Sans"], "h2": ["Plus Jakarta Sans"], "h3": ["Plus Jakarta Sans"],
                "body-md": ["Inter"], "body-lg": ["Inter"], "body-sm": ["Inter"], "label-caps": ["Inter"]
            }},
            fontSize: {{
                "h1": ["36px", {{"lineHeight": "1.2", "fontWeight": "700"}}],
                "h2": ["28px", {{"lineHeight": "1.3", "fontWeight": "600"}}],
                "h3": ["22px", {{"lineHeight": "1.4", "fontWeight": "600"}}],
                "body-md": ["16px", {{"lineHeight": "1.6"}}],
                "body-lg": ["18px", {{"lineHeight": "1.6"}}],
                "body-sm": ["14px", {{"lineHeight": "1.5"}}],
                "label-caps": ["11px", {{"letterSpacing": "0.06em", "fontWeight": "600"}}]
            }}
        }}
    }}
}}
</script>
<style>
.material-symbols-outlined {{ font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; }}
.icon-fill {{ font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24; }}
.shadow-glow {{ box-shadow: 0 10px 30px rgba(255,182,193,0.15); }}
.shadow-subtle {{ box-shadow: 0 4px 20px rgba(0,0,0,0.04); }}
</style>
</head>
<body class="bg-background text-on-background font-body-md antialiased pt-20 pb-16">

<!-- Top Nav -->
<nav class="bg-white/90 backdrop-blur-md fixed top-0 w-full z-50 border-b border-pink-50/50 shadow-[0_4px_20px_rgba(255,182,193,0.1)]">
<div class="flex justify-between items-center px-6 py-3 max-w-7xl mx-auto">
    <a class="text-2xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-purple-500 cursor-pointer" onclick="stNavigate({{action:'go_home'}})">BeliKuy</a>
    <div class="flex items-center gap-4">
        <button onclick="stNavigate({{action:'go_search'}})" class="p-2 text-pink-400 hover:text-pink-500 hover:bg-pink-50 rounded-full transition-colors">
            <span class="material-symbols-outlined">search</span>
        </button>
        <button onclick="stNavigate({{action:'go_cart'}})" class="p-2 text-pink-400 hover:text-pink-500 hover:bg-pink-50 rounded-full transition-colors relative">
            <span class="material-symbols-outlined">shopping_cart</span>
            {cart_badge_html}
        </button>
        <button onclick="stNavigate({{action:'go_profile'}})" class="p-2 text-pink-400 hover:text-pink-500 hover:bg-pink-50 rounded-full transition-colors">
            <span class="material-symbols-outlined">person</span>
        </button>
    </div>
</div>
</nav>

<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">

<!-- Breadcrumb -->
<div class="flex items-center gap-2 text-body-sm text-on-surface-variant mb-6 font-body-sm">
    <a class="hover:text-primary transition-colors cursor-pointer" onclick="stNavigate({{action:'go_home'}})">Home</a>
    <span class="material-symbols-outlined text-sm">chevron_right</span>
    <a class="hover:text-primary transition-colors cursor-pointer" onclick="stNavigate({{action:'go_search'}})">Produk</a>
    <span class="material-symbols-outlined text-sm">chevron_right</span>
    <a class="hover:text-primary transition-colors cursor-pointer" onclick="stNavigate({{action:'go_search', cat:'{product.get('category_id','')}'}})">{cat}</a>
    <span class="material-symbols-outlined text-sm">chevron_right</span>
    <span class="text-on-surface font-medium truncate max-w-[200px]">{name}</span>
</div>

<!-- Product Detail Grid -->
<div class="grid grid-cols-1 lg:grid-cols-2 gap-10 lg:gap-16">
    <!-- Left: Main Image -->
    <div class="flex flex-col gap-4">
        <div class="bg-surface-container-lowest rounded-3xl aspect-square overflow-hidden shadow-glow relative">
            <img alt="{name}" class="w-full h-full object-cover hover:scale-105 transition-transform duration-700" src="{img}" onerror="this.src='https://via.placeholder.com/600?text=No+Image'"/>
        </div>
    </div>

    <!-- Right: Info & Actions -->
    <div class="flex flex-col">
        <!-- Badges -->
        <div class="mb-3 flex gap-2 flex-wrap">
            {specs_html}
        </div>

        <!-- Product Name -->
        <h1 class="font-h1 text-h1 text-on-background mb-3">{name}</h1>

        <!-- Rating Row (product rating) -->
        <div class="flex items-center gap-3 mb-5">
            <div class="flex items-center text-yellow-400">
                {star_html}
            </div>
            <span class="font-body-md text-body-md text-on-surface font-semibold">{product_rating:.1f}</span>
            <span class="font-body-sm text-outline">({review_count} ulasan)</span>
            <span class="text-outline-variant">|</span>
            <span class="font-body-sm text-body-sm text-on-surface-variant">Stok: <strong class="text-on-surface">{stock}</strong></span>
        </div>

        <!-- Price -->
        <div class="mb-6">
            <span class="font-h2 text-h2 text-primary font-bold">{price}</span>
        </div>

        <!-- Description -->
        <p class="font-body-md text-body-md text-on-surface-variant mb-6 leading-relaxed">{desc}</p>

        <!-- Attrs (color, size if available) -->
        {attrs_html}

        <!-- Quantity Selector -->
        <div class="bg-surface-container-lowest rounded-2xl p-5 shadow-subtle mb-6 border border-surface-variant/50">
            <span class="font-body-sm text-body-sm font-semibold text-on-surface block mb-3">Jumlah</span>
            <div class="flex items-center gap-4">
                <div class="flex items-center bg-surface-bright rounded-full p-1 shadow-inner border border-surface-variant/50">
                    <button onclick="changeQty(-1)" class="w-9 h-9 flex items-center justify-center rounded-full text-on-surface-variant hover:bg-white transition-all">
                        <span class="material-symbols-outlined text-sm">remove</span>
                    </button>
                    <span id="qty-display" class="w-12 text-center font-body-md font-medium text-on-surface">1</span>
                    <button onclick="changeQty(1)" class="w-9 h-9 flex items-center justify-center rounded-full text-on-surface-variant hover:bg-white transition-all">
                        <span class="material-symbols-outlined text-sm">add</span>
                    </button>
                </div>
                <span class="font-body-sm text-body-sm text-on-surface-variant">Tersisa <strong class="text-primary">{stock}</strong> stok</span>
            </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex flex-col sm:flex-row gap-4 mb-8">
            <button onclick="stNavigate({{action:'add_cart', pid:'{pid}', qty:qty}})" class="flex-1 py-4 px-6 rounded-full bg-surface-bright text-on-surface-variant font-label-caps text-label-caps border border-surface-variant hover:bg-white hover:shadow-subtle transition-all flex items-center justify-center gap-2">
                <span class="material-symbols-outlined">add_shopping_cart</span>
                Tambah ke Keranjang
            </button>
            <button onclick="stNavigate({{action:'buy_now', pid:'{pid}', qty:qty}})" class="flex-1 py-4 px-6 rounded-full bg-gradient-to-r from-primary-container to-inverse-primary text-on-primary-container font-label-caps text-label-caps shadow-glow hover:shadow-[0_15px_40px_rgba(255,182,193,0.35)] transition-all flex items-center justify-center gap-2">
                <span class="material-symbols-outlined">bolt</span>
                Beli Sekarang
            </button>
        </div>

        <!-- Store Info -->
        <div class="bg-surface-container-lowest rounded-2xl p-5 shadow-subtle border border-surface-variant/30 flex items-center justify-between">
            <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-full bg-gradient-to-br from-pink-100 to-purple-100 flex items-center justify-center text-lg font-bold text-primary">
                    {shop[:1].upper()}
                </div>
                <div>
                    <h3 class="font-body-lg text-body-lg font-semibold text-on-surface">{shop}</h3>
                    <div class="flex items-center gap-1 text-yellow-400">
                        <span class="material-symbols-outlined icon-fill text-sm">star</span>
                        <span class="font-body-sm text-body-sm text-on-surface-variant">{shop_rating} rating toko</span>
                    </div>
                </div>
            </div>
            <button onclick="stNavigate({{action:'go_shop', cid:'{product.get("company_id","")}'}})" class="px-4 py-2 rounded-full border border-primary text-primary font-label-caps text-[10px] hover:bg-primary-fixed hover:text-on-primary-container transition-colors">
                Lihat Toko
            </button>
        </div>
    </div>
</div>

<!-- Ulasan Produk -->
<div class="mt-16 mb-8">
    <div class="flex items-center justify-between mb-6">
        <h2 class="font-h2 text-h2 text-on-background">Ulasan Pembeli</h2>
    </div>
    {reviews_html}
</div>

<!-- Related Products -->
<div class="mt-16 mb-8">
    <div class="flex items-center justify-between mb-6">
        <h2 class="font-h2 text-h2 text-on-background">Produk Sejenis</h2>
        <a class="font-label-caps text-label-caps text-primary hover:text-on-primary-container transition-colors flex items-center gap-1 cursor-pointer" onclick="stNavigate({{action:'go_search', cat:'{product.get("category_id","")}'}})">
            Lihat Semua <span class="material-symbols-outlined text-sm">arrow_forward</span>
        </a>
    </div>
    <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
        {related_html}
    </div>
</div>

</main>

<!-- Mobile Bottom Nav -->
<nav class="md:hidden bg-white/90 backdrop-blur-xl fixed bottom-0 w-full rounded-t-3xl border-t border-pink-100/30 shadow-[0_-10px_40px_rgba(255,182,193,0.15)] z-50">
<div class="flex justify-around items-center px-4 pb-6 pt-3">
    <a class="flex flex-col items-center justify-center text-zinc-400 px-5 py-2 hover:text-pink-400 transition-colors" onclick="stNavigate({{action:'go_home'}})">
        <span class="material-symbols-outlined mb-1">home</span>
        <span class="text-[10px] uppercase tracking-widest">Home</span>
    </a>
    <a class="flex flex-col items-center justify-center text-zinc-400 px-5 py-2 hover:text-pink-400 transition-colors" onclick="stNavigate({{action:'go_search'}})">
        <span class="material-symbols-outlined mb-1">search</span>
        <span class="text-[10px] uppercase tracking-widest">Cari</span>
    </a>
    <a class="flex flex-col items-center justify-center text-zinc-400 px-5 py-2 hover:text-pink-400 transition-colors" onclick="stNavigate({{action:'go_orders'}})">
        <span class="material-symbols-outlined mb-1">receipt_long</span>
        <span class="text-[10px] uppercase tracking-widest">Pesanan</span>
    </a>
    <a class="flex flex-col items-center justify-center text-zinc-400 px-5 py-2 hover:text-pink-400 transition-colors" onclick="stNavigate({{action:'go_profile'}})">
        <span class="material-symbols-outlined mb-1">person</span>
        <span class="text-[10px] uppercase tracking-widest">Profil</span>
    </a>
</div>
</nav>

<script>
let qty = 1;
const maxStock = {stock};
function changeQty(d) {{
    qty = Math.max(1, Math.min(maxStock, qty + d));
    document.getElementById('qty-display').textContent = qty;
}}
</script>
</body></html>"""

page_html = inject_navbar(page_html, cart_len)
action_data = render_original_html("belikuy_v2_detail", page_html, height=1800)

if action_data:
    act = action_data.get('action')
    current_user = st.session_state.get('user')
    if handle_global_action(st, act, action_data, current_user):
        pass
    elif act in ("go_home",):
        st.switch_page("pages/1_Storefront.py")
    elif act in ("go_search", "go_cart_from_search"):
        st.switch_page("pages/2_Cari_Produk.py")
    elif act == "go_cart":
        st.switch_page("pages/4_Keranjang.py")
    elif act == "go_profile":
        st.switch_page("pages/8_Profil.py")
    elif act == "go_orders":
        st.switch_page("pages/6_Riwayat_Pesanan.py")
    elif act == "go_shop":
        st.session_state['viewing_company_id'] = action_data.get('cid')
        st.switch_page("pages/18_Profil_Toko.py")
    elif act == "go_detail":
        st.session_state['viewing_product_id'] = action_data.get('pid')
        st.rerun()
    elif act == "add_cart":
        pid_act = str(action_data.get('pid', ''))
        qty_act = int(float(str(action_data.get('qty', 1) or 1)))
        if pid_act:
            prod_add, _ = get_api(f"products/{pid_act}")
            if prod_add:
                if 'cart' not in st.session_state: st.session_state['cart'] = []
                existing = next((x for x in st.session_state['cart'] if str(x.get('id')) == pid_act), None)
                if existing:
                    existing['qty'] = existing.get('qty', 0) + qty_act
                else:
                    prod_add['qty'] = qty_act
                    st.session_state['cart'].append(prod_add)
        st.switch_page("pages/4_Keranjang.py")
    elif act == "buy_now":
        pid_act = str(action_data.get('pid', ''))
        qty_act = int(float(str(action_data.get('qty', 1) or 1)))
        if pid_act:
            prod_add, _ = get_api(f"products/{pid_act}")
            if prod_add:
                if 'cart' not in st.session_state: st.session_state['cart'] = []
                existing = next((x for x in st.session_state['cart'] if str(x.get('id')) == pid_act), None)
                if existing:
                    existing['qty'] = qty_act # Overwrite qty for buy_now or add? Let's just set it.
                else:
                    prod_add['qty'] = qty_act
                    st.session_state['cart'].append(prod_add)
        st.switch_page("pages/5_Checkout.py")
