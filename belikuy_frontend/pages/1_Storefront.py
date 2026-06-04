import streamlit as st
import sys, os, re, base64

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from utils import get_api, hide_streamlit_ui, format_rupiah, get_current_user
from html_bridge import render_original_html
from unified_navbar import inject_navbar, handle_global_action

st.set_page_config(
    page_title="BeliKuy - Beranda", layout="wide", initial_sidebar_state="collapsed"
)
hide_streamlit_ui()

user = get_current_user()

HTML_BASE = (
    r"D:\Tugas Kuliah\Semester 4\Workshop RPL\belikuy-ecommerce\belikuy_ui_templates"
)
FRONTEND_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

cart_len = len(st.session_state.get("cart", []))
cart_badge = (
    f'<span class="absolute -top-1 -right-1 bg-error text-on-error text-[10px] font-bold h-4 w-4 rounded-full flex items-center justify-center">{cart_len}</span>'
    if cart_len > 0
    else ""
)


with open(
    os.path.join(HTML_BASE, "homepage_storefront/code.html"), encoding="utf-8"
) as f:
    html = f.read()


# ── Helper: load local image as base64 ──
def local_img(path):
    if not path:
        return "https://via.placeholder.com/300?text=No+Image"
    if path.startswith("http"):
        return path
    try:
        full = os.path.join(FRONTEND_BASE, path.replace("\\", "/"))
        if os.path.exists(full):
            ext = os.path.splitext(full)[1].lower().lstrip(".")
            mime = {
                "jpg": "jpeg",
                "jpeg": "jpeg",
                "png": "png",
                "gif": "gif",
                "webp": "webp",
            }.get(ext, "jpeg")
            with open(full, "rb") as f:
                return f"data:image/{mime};base64,{base64.b64encode(f.read()).decode()}"
    except:
        pass
    return "https://via.placeholder.com/300?text=No+Image"


# ── Fetch live data from backend ──
products, _ = get_api("products")
if not products:
    products = []

companies, _ = get_api("companies")
if not companies:
    companies = []


# ── Build dynamic product cards ──
def product_card(p):
    img = local_img(p.get("image_url", ""))
    name = str(p.get("product_name", "")).replace("'", "&#39;")
    price = format_rupiah(p.get("price", 0))
    try:
        r_val = float(p.get("product_rating", 0))
    except:
        r_val = 0.0

    star_class = "style=\"font-variation-settings: 'FILL' 1;\"" if r_val > 0 else ""
    pid = p.get("id", "")
    return f"""
    <div class="group flex flex-col bg-surface-container-lowest rounded-2xl shadow-glow hover:shadow-glow-hover transition-all duration-300 p-3 cursor-pointer" onclick="stNavigate({{action:'go_detail', pid:'{pid}'}})">
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
                <div class="ml-auto flex items-center text-xs text-on-surface-variant">
                    <span class="material-symbols-outlined text-[14px] text-yellow-400 mr-0.5" {star_class}>star</span>
                    {r_val:.1f}
                </div>
            </div>
        </div>
    </div>"""


dynamic_products_html = "".join(product_card(p) for p in products[:8])

# ── Inject dynamic products into the product grid ──
# The original HTML has static 4 product cards in the grid, we replace them
pattern_products = (
    r'(<div class="grid grid-cols-2 md:grid-cols-4 gap-6">)(.*?)(</div>\s*</section>)'
)
if dynamic_products_html:
    html = re.sub(
        pattern_products, rf"\1\n{dynamic_products_html}\n\3", html, flags=re.DOTALL
    )


# ── Build dynamic Trending Boutiques ──
def company_card(c):
    name = str(c.get("company_name", "Store")).replace("'", "&#39;")
    cid = c.get("id", "")
    initial = name[:1].upper() if name else "S"
    return f"""
    <div class="snap-start flex flex-col items-center gap-2 min-w-[80px] cursor-pointer hover:scale-105 transition-transform" onclick="stNavigate({{action:'go_shop', cid:'{cid}'}})" title="{name}">
        <div class="w-14 h-14 rounded-full border-2 border-primary-fixed bg-gradient-to-br from-pink-100 to-purple-100 flex items-center justify-center overflow-hidden shadow-md">
            <span class="text-xl text-primary font-bold">{initial}</span>
        </div>
        <span class="font-body-sm text-[11px] text-on-surface-variant text-center leading-tight w-[72px] truncate">{name}</span>
    </div>"""


dynamic_companies_html = "".join(company_card(c) for c in companies[:10])

# Replace the static boutique section content — target the specific flex container
pattern_boutiques = r'(<div class="flex gap-4 overflow-x-auto pb-4 snap-x snap-mandatory">.*?</div>\s*</section>)'
if companies:
    new_boutiques_section = f"""
<div class="relative group">
    <button onclick="this.nextElementSibling.scrollBy({{left: -300, behavior: 'smooth'}})" class="absolute left-0 top-[40%] -translate-y-1/2 -ml-2 w-10 h-10 bg-white rounded-full shadow-[0_4px_10px_rgba(0,0,0,0.1)] flex items-center justify-center z-10 text-primary transition-transform hover:scale-110 border border-surface-variant"><span class="material-symbols-outlined">chevron_left</span></button>
    <div class="flex gap-4 overflow-x-auto pb-4 snap-x snap-mandatory px-2 w-full scrollbar-hide" style="scroll-behavior: smooth;">
{dynamic_companies_html}
    </div>
    <button onclick="this.previousElementSibling.scrollBy({{left: 300, behavior: 'smooth'}})" class="absolute right-0 top-[40%] -translate-y-1/2 -mr-2 w-10 h-10 bg-white rounded-full shadow-[0_4px_10px_rgba(0,0,0,0.1)] flex items-center justify-center z-10 text-primary transition-transform hover:scale-110 border border-surface-variant"><span class="material-symbols-outlined">chevron_right</span></button>
</div>
</section>"""
    html = re.sub(pattern_boutiques, new_boutiques_section, html, flags=re.DOTALL)

# Rename section title
html = html.replace("Trending Boutiques", "Trending Shops")

# ── Wire all navigation links ──

# Inject Unified Navbar
html = inject_navbar(html, cart_len)

# Shop Now button in the hero banner
html = html.replace(
    ">Shop Now</button>",
    " onclick=\"stNavigate({action:'go_search'})\">Shop Now</button>",
)

# Fetch categories from DB
categories_db, _ = get_api("categories")
if not categories_db:
    categories_db = []

category_icons = {
    "Accessories": "watch",
    "Automotive": "directions_car",
    "Books": "menu_book",
    "Clothing": "checkroom",
    "Collectibles": "diamond",
    "Electronics": "devices",
    "Food": "restaurant",
    "Health": "health_and_safety",
    "Home Decor": "chair",
    "Makeup": "face_retouching_natural",
    "Shoes": "steps",
    "Skincare": "spa",
    "Sports Equipment": "sports_basketball",
    "Stationery": "edit_document",
    "Toys": "toys",
}

# Build dynamic categories HTML
dynamic_categories_html = ""
for cat in categories_db:
    name = cat.get("category_name", "")
    cid = cat.get("id", "")
    icon = category_icons.get(name, "category")  # fallback to 'category' icon
    dynamic_categories_html += f"""
    <a class="snap-start flex flex-col items-center gap-3 min-w-[100px] group" href="javascript:void(0);" onclick="stNavigate({{action:'go_search', cat:'{cid}'}})">
        <div class="w-16 h-16 rounded-2xl bg-surface-bright shadow-glow group-hover:-translate-y-1 transition-all duration-300 flex items-center justify-center text-primary">
            <span class="material-symbols-outlined text-[32px] font-light" style="font-variation-settings: 'wght' 200;">{icon}</span>
        </div>
        <span class="font-body-sm text-body-sm text-on-surface-variant group-hover:text-primary transition-colors">{name}</span>
    </a>"""

# Inject dynamic categories into the container with Slider Arrows
pattern_categories = r'(<h2 class="font-h2 text-h3 text-on-surface mb-2">Explore Categories</h2>\s*)(<div class="flex overflow-x-auto gap-4 pb-4 snap-x snap-mandatory scrollbar-hide">.*?</div>\s*</section>)'
if dynamic_categories_html:
    new_categories_section = f"""\\1
<div class="relative group">
    <button onclick="this.nextElementSibling.scrollBy({{left: -300, behavior: 'smooth'}})" class="absolute left-0 top-[40%] -translate-y-1/2 -ml-2 w-10 h-10 bg-white rounded-full shadow-[0_4px_10px_rgba(0,0,0,0.1)] flex items-center justify-center z-10 text-primary transition-transform hover:scale-110 border border-surface-variant"><span class="material-symbols-outlined">chevron_left</span></button>
    <div class="flex overflow-x-auto gap-4 pb-4 snap-x snap-mandatory scrollbar-hide px-2 w-full" style="scroll-behavior: smooth;">
{dynamic_categories_html}
    </div>
    <button onclick="this.previousElementSibling.scrollBy({{left: 300, behavior: 'smooth'}})" class="absolute right-0 top-[40%] -translate-y-1/2 -mr-2 w-10 h-10 bg-white rounded-full shadow-[0_4px_10px_rgba(0,0,0,0.1)] flex items-center justify-center z-10 text-primary transition-transform hover:scale-110 border border-surface-variant"><span class="material-symbols-outlined">chevron_right</span></button>
</div>
</section>"""
    html = re.sub(pattern_categories, new_categories_section, html, flags=re.DOTALL)


# Search input - Enter key search
html = html.replace(
    'id="search" placeholder="Search aesthetic items..."',
    'id="search" placeholder="Search aesthetic items..." onkeydown="if(event.key===\'Enter\') stNavigate({action:\'go_search\', q:this.value})"',
)

# See All buttons
html = re.sub(
    r'(<button class="text-primary[^>]*>)\s*See All',
    r'\1 onclick="event.preventDefault(); stNavigate({action:\'go_search\'})">\nSee All',
    html,
    flags=re.IGNORECASE,
)

# Mobile Bottom NavBar links  — target by visible text content
html = re.sub(
    r'(<a [^>]*href="#"[^>]*>\s*<span[^>]*>\s*home\s*</span>\s*)Home(\s*</a>)',
    r'<a href="#" onclick="event.preventDefault(); stNavigate({action:\'go_home\'})" class="flex flex-col items-center justify-center bg-gradient-to-br from-pink-50 to-purple-50 text-pink-500 rounded-2xl px-5 py-2 scale-110 duration-500 ease-out font-[\'Plus_Jakarta_Sans\'] text-[10px] uppercase tracking-widest">\n<span class="material-symbols-outlined mb-1" style="font-variation-settings: \'FILL\' 1;">home</span>\n            Home\n        </a>',
    html,
    flags=re.DOTALL,
)
html = re.sub(
    r'(<a [^>]*href="#"[^>]*>\s*<span[^>]*>\s*favorite\s*</span>\s*)Wishlist(\s*</a>)',
    r'<a href="#" onclick="event.preventDefault(); stNavigate({action:\'go_search\'})" class="flex flex-col items-center justify-center text-zinc-400 px-5 py-2 hover:text-pink-400 scale-110 duration-500 ease-out font-[\'Plus_Jakarta_Sans\'] text-[10px] uppercase tracking-widest">\n<span class="material-symbols-outlined mb-1">favorite</span>\n            Wishlist\n        </a>',
    html,
    flags=re.DOTALL,
)
html = re.sub(
    r'(<a [^>]*href="#"[^>]*>\s*<span[^>]*>\s*receipt_long\s*</span>\s*)Orders(\s*</a>)',
    r'<a href="#" onclick="event.preventDefault(); stNavigate({action:\'go_orders\'})" class="flex flex-col items-center justify-center text-zinc-400 px-5 py-2 hover:text-pink-400 scale-110 duration-500 ease-out font-[\'Plus_Jakarta_Sans\'] text-[10px] uppercase tracking-widest">\n<span class="material-symbols-outlined mb-1">receipt_long</span>\n            Orders\n        </a>',
    html,
    flags=re.DOTALL,
)
html = re.sub(
    r'(<a [^>]*href="#"[^>]*>\s*<span[^>]*>\s*person\s*</span>\s*)Profile(\s*</a>)',
    r'<a href="#" onclick="event.preventDefault(); stNavigate({action:\'go_profile\'})" class="flex flex-col items-center justify-center text-zinc-400 px-5 py-2 hover:text-pink-400 scale-110 duration-500 ease-out font-[\'Plus_Jakarta_Sans\'] text-[10px] uppercase tracking-widest">\n<span class="material-symbols-outlined mb-1">person</span>\n            Profile\n        </a>',
    html,
    flags=re.DOTALL,
)

# Inject Unified Navbar
html = inject_navbar(html, cart_len)

# Add CSS to hide scrollbars globally in this iframe
scrollbar_css = """
<style>
.scrollbar-hide::-webkit-scrollbar {
    display: none;
}
.scrollbar-hide {
    -ms-overflow-style: none;
    scrollbar-width: none;
}
</style>
"""
html = html.replace("</head>", scrollbar_css + "\n</head>")

# Shop Now button in the hero banner
html = html.replace(
    ">Shop Now</button>",
    " onclick=\"stNavigate({action:'go_search'})\">Shop Now</button>",
)

# ── Render ──
with open("debug_storefront.html", "w", encoding="utf-8") as f:
    f.write(html)
action_data = render_original_html("belikuy_v2_storefront", html, height=1400)

if action_data:
    act = action_data.get("action")
    if handle_global_action(st, act, action_data, user):
        pass
    elif act == "go_detail":
        st.session_state["viewing_product_id"] = action_data.get("pid")
        st.switch_page("pages/3_Detail_Produk.py")
    elif act == "go_cart":
        st.switch_page("pages/4_Keranjang.py")
    elif act == "go_shop":
        st.session_state["viewing_company_id"] = action_data.get("cid")
        st.switch_page("pages/18_Profil_Toko.py")
    elif act == "go_profile":
        st.switch_page("pages/8_Profil.py") if user else st.switch_page("app.py")
    elif act in ("go_search", "search"):
        q = action_data.get("q")
        cat_id = action_data.get("cat")
        if q:
            st.session_state["search_query"] = q
        if cat_id:
            st.session_state["search_cat"] = cat_id
        st.switch_page("pages/2_Cari_Produk.py")
    elif act == "go_orders":
        (
            st.switch_page("pages/6_Riwayat_Pesanan.py")
            if user
            else st.switch_page("app.py")
        )
    elif act == "go_home":
        st.rerun()
    elif act == "add_cart":
        pid = action_data.get("pid")
        if pid:
            prod, _ = get_api(f"products/{pid}")
            if prod:
                if "cart" not in st.session_state:
                    st.session_state["cart"] = []
                existing = next(
                    (
                        x
                        for x in st.session_state["cart"]
                        if str(x.get("id")) == str(pid)
                    ),
                    None,
                )
                if existing:
                    existing["qty"] = existing.get("qty", 1) + 1
                else:
                    prod["qty"] = 1
                    st.session_state["cart"].append(prod)
        st.rerun()
