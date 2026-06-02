import streamlit as st
import sys, os, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from utils import get_api, hide_streamlit_ui, format_rupiah, get_current_user
from html_bridge import render_original_html
from unified_navbar import inject_navbar, handle_global_action

st.set_page_config(page_title="BeliKuy - Profil Toko", layout="wide", initial_sidebar_state="collapsed")
hide_streamlit_ui()

user = get_current_user()

FRONTEND_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

company_id = st.session_state.get('viewing_company_id')
if not company_id:
    st.warning("Toko tidak ditemukan.")
    if st.button("← Kembali ke Beranda"):
        st.switch_page("pages/1_Storefront.py")
    st.stop()

# Fetch data
company, err = get_api(f"companies/{company_id}")
if err or not company:
    st.error("Gagal memuat profil toko.")
    st.stop()

products, _ = get_api(f"products/seller/{company_id}")
if not products:
    products = []

def local_img(path, placeholder_text="No+Image"):
    if not path:
        return f"https://via.placeholder.com/300?text={placeholder_text}"
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
    return f"https://via.placeholder.com/300?text={placeholder_text}"

def product_card(p):
    img = local_img(p.get('image_url', ''))
    name = str(p.get('product_name', '')).replace("'", "&#39;")
    price = format_rupiah(p.get('price', 0))
    rating = "4.8" # default placeholder rating for items
    pid = p.get('id', '')
    return f'''
    <div class="group flex flex-col bg-surface-container-lowest rounded-2xl shadow-glow hover:shadow-glow-hover transition-all duration-300 p-3 cursor-pointer border border-transparent hover:border-primary-container" onclick="stNavigate({{action:'go_detail', pid:'{pid}'}})">
        <div class="relative aspect-square rounded-xl overflow-hidden mb-3 bg-surface-bright">
            <img src="{img}" alt="{name}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" onerror="this.src='https://via.placeholder.com/300?text=No+Image'"/>
            <button onclick="event.stopPropagation(); stNavigate({{action:'add_cart', pid:'{pid}'}})" class="absolute top-2 right-2 w-8 h-8 bg-white/80 backdrop-blur-sm rounded-full flex items-center justify-center text-outline hover:text-primary transition-colors">
                <span class="material-symbols-outlined text-[18px]">shopping_cart</span>
            </button>
        </div>
        <div class="px-1 flex flex-col gap-1 flex-1">
            <h3 class="font-body-md text-body-sm font-medium text-on-surface line-clamp-2">{name}</h3>
            <div class="flex items-center gap-1 mt-auto pt-2">
                <span class="font-h3 text-body-md text-primary">{price}</span>
            </div>
        </div>
    </div>'''

cart_len = len(st.session_state.get('cart', []))
cart_badge_html = f'<span class="absolute -top-1 -right-1 bg-error text-on-error text-[10px] font-bold h-4 w-4 rounded-full flex items-center justify-center">{cart_len}</span>' if cart_len > 0 else ''

products_html = "".join(product_card(p) for p in products) if products else '<p class="text-on-surface-variant col-span-full py-8 text-center bg-surface-container-low rounded-2xl">Belum ada produk di toko ini.</p>'

shop_name = company.get("company_name", "Toko BeliKuy").replace("'", "&#39;")
shop_rating = str(company.get("rating", "0.0") or "0.0")
shop_address = company.get("address", "Alamat belum tersedia")
shop_initial = shop_name[:1].upper() if shop_name else "S"

page_html = f"""<!DOCTYPE html>
<html class="light" lang="id"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>BeliKuy - Profil {shop_name}</title>
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
            }}
        }}
    }}
}}
</script>
<style>
.material-symbols-outlined {{ font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; }}
.icon-fill {{ font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24; }}
.shadow-glow {{ box-shadow: 0 10px 30px rgba(255,182,193,0.15); }}
.shadow-glow-hover {{ box-shadow: 0 15px 40px rgba(255,182,193,0.3); }}
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

<!-- Back & Breadcrumb -->
<div class="flex items-center gap-2 text-body-sm text-on-surface-variant mb-6 font-body-sm">
    <button class="hover:text-primary transition-colors flex items-center gap-1 cursor-pointer" onclick="stNavigate({{action:'go_home'}})">
        <span class="material-symbols-outlined text-sm">arrow_back</span> Kembali
    </button>
</div>

<!-- Shop Banner -->
<div class="bg-gradient-to-r from-primary-container/40 to-secondary-container/40 rounded-3xl p-8 mb-10 shadow-subtle border border-white/50 backdrop-blur-sm relative overflow-hidden flex flex-col md:flex-row items-center gap-8">
    <div class="absolute top-0 left-0 w-full h-full bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-10 pointer-events-none"></div>
    <div class="w-32 h-32 md:w-40 md:h-40 shrink-0 rounded-full bg-gradient-to-br from-pink-200 to-purple-200 shadow-glow flex items-center justify-center border-4 border-white z-10 relative">
        <span class="text-5xl md:text-6xl font-black text-primary">{shop_initial}</span>
    </div>
    <div class="flex flex-col text-center md:text-left z-10 w-full">
        <h1 class="font-h1 text-4xl text-on-surface mb-2 font-bold">{shop_name}</h1>
        <div class="flex flex-wrap items-center justify-center md:justify-start gap-4 mb-4">
            <div class="flex items-center gap-1 bg-white/60 px-3 py-1 rounded-full text-yellow-500 font-semibold shadow-sm">
                <span class="material-symbols-outlined icon-fill text-[18px]">star</span>
                {shop_rating}
            </div>
            <div class="flex items-center gap-1 bg-white/60 px-3 py-1 rounded-full text-on-surface-variant font-medium shadow-sm">
                <span class="material-symbols-outlined text-[18px]">inventory_2</span>
                {len(products)} Produk
            </div>
            <div class="flex items-center gap-1 bg-white/60 px-3 py-1 rounded-full text-on-surface-variant font-medium shadow-sm">
                <span class="material-symbols-outlined text-[18px]">location_on</span>
                {shop_address}
            </div>
        </div>
    </div>
</div>

<!-- Shop Products -->
<h2 class="font-h2 text-h2 text-on-background mb-6">Koleksi {shop_name}</h2>
<div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-6">
    {products_html}
</div>

</main>
</body>
</html>
"""

page_html = inject_navbar(page_html, cart_len)
action_data = render_original_html("belikuy_v2_shop_profile", page_html, height=1200)

if action_data:
    act = action_data.get('action')
    current_user = st.session_state.get('user')
    if handle_global_action(st, act, action_data, current_user):
        pass
    elif act == "go_home":
        st.switch_page("pages/1_Storefront.py")
    elif act == "go_search":
        st.switch_page("pages/2_Cari_Produk.py")
    elif act == "go_cart":
        st.switch_page("pages/4_Keranjang.py")
    elif act == "go_profile":
        st.switch_page("pages/8_Profil.py") if user else st.switch_page("app.py")
    elif act == "go_orders":
        st.switch_page("pages/6_Riwayat_Pesanan.py") if user else st.switch_page("app.py")
    elif act == "go_detail":
        st.session_state['viewing_product_id'] = action_data.get('pid')
        st.switch_page("pages/3_Detail_Produk.py")
    elif act == "add_cart":
        pid_act = str(action_data.get('pid', ''))
        if pid_act:
            prod_add, _ = get_api(f"products/{pid_act}")
            if prod_add:
                if 'cart' not in st.session_state: st.session_state['cart'] = []
                existing = next((x for x in st.session_state['cart'] if str(x.get('id')) == pid_act), None)
                if existing:
                    existing['qty'] = existing.get('qty', 0) + 1
                else:
                    prod_add['qty'] = 1
                    st.session_state['cart'].append(prod_add)
        st.rerun()
