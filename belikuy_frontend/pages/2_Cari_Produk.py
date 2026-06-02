import streamlit as st
import sys, os, base64, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from utils import get_api, require_login, hide_streamlit_ui, format_rupiah
from html_bridge import render_original_html
from unified_navbar import inject_navbar, handle_global_action

st.set_page_config(page_title="BeliKuy - Cari Produk", layout="wide", initial_sidebar_state="collapsed")
hide_streamlit_ui()
require_login()

if 'search_query' in st.session_state:
    q = st.session_state.pop('search_query')
    st.query_params['q'] = q
else:
    q = st.query_params.get("q", "")

if 'search_cat' in st.session_state:
    cat = st.session_state.pop('search_cat')
    st.query_params['cat'] = str(cat)
else:
    cat = st.query_params.get("cat", "")

min_price = st.query_params.get("min_price", "")
max_price = st.query_params.get("max_price", "")
sort_by   = st.query_params.get("sort", "newest")  # newest | price_asc | price_desc
page_str  = st.query_params.get("page", "1")
try: page = max(1, int(page_str))
except: page = 1

cart_len = len(st.session_state.get('cart', []))
cart_badge = f'<span class="absolute -top-1 -right-1 bg-error text-on-error text-[10px] font-bold h-4 w-4 rounded-full flex items-center justify-center">{cart_len}</span>' if cart_len > 0 else ''

api_p = {}
if q:         api_p["search"]      = q
if cat:       api_p["category_id"] = cat
if min_price: api_p["min_price"]   = min_price
if max_price: api_p["max_price"]   = max_price

products,   _ = get_api("products", params=api_p)
categories, _ = get_api("categories")
if not products:   products   = []
if not categories: categories = []

# ── Sort products ─────────────────────────────────────────────────────────────
if sort_by == "price_asc":
    products = sorted(products, key=lambda p: float(p.get("price", 0)))
elif sort_by == "price_desc":
    products = sorted(products, key=lambda p: float(p.get("price", 0)), reverse=True)
else:  # newest (default) — sort by id desc as proxy
    products = sorted(products, key=lambda p: int(p.get("id", 0)), reverse=True)

PAGE_SIZE = 12
total_pages = max(1, (len(products) + PAGE_SIZE - 1) // PAGE_SIZE)
page = min(page, total_pages)
products_paged = products[(page-1)*PAGE_SIZE : page*PAGE_SIZE]

FRONTEND_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def local_img(path):
    if not path: return "https://via.placeholder.com/300?text=No+Image"
    if path.startswith("http"): return path
    try:
        full = os.path.join(FRONTEND_BASE, path.replace("\\", "/"))
        if os.path.exists(full):
            ext  = os.path.splitext(full)[1].lower().lstrip(".")
            mime = {"jpg":"jpeg","jpeg":"jpeg","png":"png","gif":"gif","webp":"webp"}.get(ext,"jpeg")
            with open(full,"rb") as f:
                return f"data:image/{mime};base64,{base64.b64encode(f.read()).decode()}"
    except: pass
    return "https://via.placeholder.com/300?text=No+Image"

def card(p):
    img    = local_img(p.get("image_url",""))
    name   = str(p.get("product_name","")).replace("'","&#39;").replace('"','&quot;')
    price  = format_rupiah(p.get("price",0))
    pid    = str(p.get("id",""))
    try: r_val = float(p.get("product_rating", 0))
    except: r_val = 0.0
    
    star_class = "fill" if r_val > 0 else ""
    rhtml  = (f'<div class="flex items-center gap-1 mb-1 text-primary-container">'
              f'<span class="material-symbols-outlined {star_class} text-[14px]">star</span>'
              f'<span class="font-body-sm text-[12px] font-medium text-on-surface-variant">{r_val:.1f}</span>'
              f'</div>')
    shop   = str(p.get("company_name","") or "")
    return (f'<div class="bg-white rounded-2xl p-4 shadow-[0_8px_30px_rgb(255,182,193,0.08)] '
            f'hover:shadow-[0_12px_40px_rgb(255,182,193,0.15)] transition-all group flex flex-col cursor-pointer" '
            f"onclick=\"stNavigate({{action:'go_detail',pid:'{pid}'}})\">"
            f'<div class="relative w-full aspect-square rounded-xl overflow-hidden mb-4 bg-surface-bright">'
            f'<img alt="{name}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" '
            f"src=\"{img}\" onerror=\"this.src='https://via.placeholder.com/300?text=No+Image'\"/>"
            f"<button onclick=\"event.stopPropagation();stNavigate({{action:'add_cart',pid:'{pid}'}})\""
            f' class="absolute top-3 right-3 w-8 h-8 bg-white/90 backdrop-blur-sm rounded-full flex items-center justify-center text-outline hover:text-primary hover:bg-white transition-colors shadow-sm">'
            f'<span class="material-symbols-outlined text-[18px]">add_shopping_cart</span></button></div>'
            f'<div class="flex-1 flex flex-col">{rhtml}'
            f'<h3 class="font-h3 text-body-md font-semibold text-on-surface line-clamp-2 mb-1 group-hover:text-primary transition-colors">{name}</h3>'
            f'<p class="font-body-sm text-[12px] text-outline mb-3">{shop}</p>'
            f'<div class="mt-auto flex items-center justify-between">'
            f'<span class="font-h2 text-h3 text-primary font-bold">{price}</span>'
            f"<button onclick=\"event.stopPropagation();stNavigate({{action:'add_cart',pid:'{pid}'}})\""
            f' class="w-8 h-8 bg-primary-container text-on-primary-container rounded-full flex items-center justify-center hover:bg-primary hover:text-white transition-colors">'
            f'<span class="material-symbols-outlined text-[18px]">add_shopping_cart</span></button>'
            f'</div></div></div>')

products_html = "".join(card(p) for p in products_paged) if products_paged else (
    '<div class="col-span-full py-20 text-center">'
    '<div class="text-6xl mb-4">🔍</div>'
    '<h3 class="font-h3 text-h3 text-on-surface mb-2">Produk tidak ditemukan</h3>'
    '<p class="text-on-surface-variant">Coba kata kunci atau kategori lain</p></div>'
)

# Pagination UI
prev_btn = f"<button onclick=\"stNavigate({{action:'paginate', page:{page-1}}})\" class=\"px-4 py-2 rounded-lg bg-surface-bright border border-outline-variant hover:bg-surface-container-low transition-colors disabled:opacity-50\" {'disabled' if page<=1 else ''}>Previous</button>"
next_btn = f"<button onclick=\"stNavigate({{action:'paginate', page:{page+1}}})\" class=\"px-4 py-2 rounded-lg bg-surface-bright border border-outline-variant hover:bg-surface-container-low transition-colors disabled:opacity-50\" {'disabled' if page>=total_pages else ''}>Next</button>"
page_info = f"<span class=\"font-body-md text-on-surface\">Page {page} of {total_pages}</span>"
pagination_html = f'<div class="flex items-center justify-center gap-4 mt-8">{prev_btn}{page_info}{next_btn}</div>'


cat_items = ""
cat_list = str(cat).split(",") if cat else []
for c in categories:
    cid   = str(c["id"])
    cname = str(c.get("category_name","")).replace("'","&#39;")
    chk   = 'checked=""' if cid in cat_list else ""
    cat_items += (f'<label class="flex items-center gap-3 cursor-pointer group">'
                  f'<input class="checkbox-custom" type="checkbox" data-cid="{cid}" {chk}/>'
                  f'<span class="font-body-sm text-body-sm text-on-surface-variant group-hover:text-primary transition-colors">{cname}</span>'
                  f'</label>\n')

prices = [float(p.get("price",0)) for p in products] if products else [0,0]
min_rp = format_rupiah(min(prices))
max_rp = format_rupiah(max(prices))

info = f'Showing <strong class="text-on-surface font-semibold">{len(products)}</strong> hasil'
if q:   info += f' untuk &ldquo;{q}&rdquo;'
if cat:
    cn = next((c["category_name"] for c in categories if str(c["id"]) == cat), cat)
    info += f' &mdash; <em>{cn}</em>'

sq = q.replace('"','&quot;')

HTML_BASE = r"D:\belikuy\belikuy_ui_templates"
with open(os.path.join(HTML_BASE, "search_filter_page/code.html"), encoding="utf-8") as f:
    html = f.read()

# ── Inject JS helpers ─────────────────────────────────────────────────────────
helper_js = """<script>
function applyFilters(){
    var q=(document.getElementById('srch')||{value:''}).value;
    var chks=Array.from(document.querySelectorAll('.checkbox-custom:checked')).map(e=>e.getAttribute('data-cid')).join(',');
    var c=chks;
    var pmin=(document.getElementById('price-min')||{value:''}).value;
    var pmax=(document.getElementById('price-max')||{value:''}).value;
    var sortEl=document.getElementById('sort-select');
    var s=sortEl?sortEl.value:'newest';
    stNavigate({action:'filter',q:q,cat:c,min_price:pmin,max_price:pmax,sort:s});
}
function resetFilters(){
    document.querySelectorAll('.checkbox-custom').forEach(function(e){e.checked=false;});
    if(document.getElementById('price-min')) document.getElementById('price-min').value='';
    if(document.getElementById('price-max')) document.getElementById('price-max').value='';
    var q=(document.getElementById('srch')||{value:''}).value;
    stNavigate({action:'filter',q:q,cat:'',min_price:'',max_price:'',sort:'newest'});
}
function applySort(){
    var q=(document.getElementById('srch')||{value:''}).value;
    var chks=Array.from(document.querySelectorAll('.checkbox-custom:checked')).map(e=>e.getAttribute('data-cid')).join(',');
    var c=chks;
    var pmin=(document.getElementById('price-min')||{value:''}).value;
    var pmax=(document.getElementById('price-max')||{value:''}).value;
    var sortEl=document.getElementById('sort-select');
    var s=sortEl?sortEl.value:'newest';
    stNavigate({action:'filter',q:q,cat:c,min_price:pmin,max_price:pmax,sort:s,page:1});
}
</script>"""
html = html.replace("</head>", helper_js + "\n</head>", 1)

# ── Replace product grid and pagination ───────────────────────────────────────
search_bar_html = f'''
<div class="mb-6 relative">
    <span class="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-outline">search</span>
    <input id="srch" class="w-full bg-white border border-outline-variant/30 rounded-full py-3 pl-12 pr-4 text-on-surface shadow-sm focus:ring-2 focus:ring-primary-container transition-all font-body-md outline-none" placeholder="Cari produk BeliKuy..." type="text" value="{sq}" onkeydown="if(event.key==='Enter') applyFilters()" />
</div>
'''
html = re.sub(
    r'(<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">).*?(<!-- Pagination -->)',
    rf'{search_bar_html}\n\1\n{products_html}\n</div>\n\2',
    html, flags=re.DOTALL
)

html = re.sub(
    r'(<!-- Pagination -->\s*<div class="mt-12 flex justify-center items-center gap-2">.*?</div>)',
    f'<!-- Pagination -->\n{pagination_html}', html, flags=re.IGNORECASE|re.DOTALL
)

# ── Replace category checkboxes ───────────────────────────────────────────────
html = re.sub(
    r'(<h3 class="font-h2 text-body-lg font-semibold text-on-surface mb-4">Categories</h3>\s*<div class="space-y-3">).*?(</div>\s*</div>)',
    rf'\1\n{cat_items}\2',
    html, flags=re.DOTALL
)

# ── Remove Rating filter section entirely ─────────────────────────────────────
html = re.sub(r'<!-- Rating -->.*?(?=<!-- Apply Button -->)', '', html, flags=re.DOTALL)

# ── Wire RESET button (exact match verified from template)
html = html.replace(
    'class="text-primary font-label-caps text-label-caps hover:text-primary-container transition-colors">RESET</button>',
    'class="text-primary font-label-caps text-label-caps hover:text-primary-container transition-colors" onclick="resetFilters()">RESET</button>'
)

# ── Wire APPLY FILTERS button
html = html.replace(
    'transition-all active:scale-95">\n                    APPLY FILTERS\n                </button>',
    'transition-all active:scale-95" onclick="applyFilters()">\n                    APPLY FILTERS\n                </button>'
)

# ── Price Range ───────────────────────────────────────────────────────────────
price_html = f'''<h3 class="font-h2 text-body-lg font-semibold text-on-surface mb-4">Price Range</h3>
<div class="flex items-center gap-2 mb-6">
    <input type="number" id="price-min" value="{min_price}" placeholder="Min (Rp)" class="w-full bg-surface-bright rounded-lg p-2 border border-outline-variant font-body-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none">
    <span class="text-on-surface-variant">-</span>
    <input type="number" id="price-max" value="{max_price}" placeholder="Max (Rp)" class="w-full bg-surface-bright rounded-lg p-2 border border-outline-variant font-body-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none">
</div>'''

html = re.sub(
    r'(<!-- Price Range -->.*?)(<!-- Apply Button -->)',
    f'<!-- Price Range -->\n<div class="mb-8">\n{price_html}\n</div>\n\\2', html, flags=re.IGNORECASE|re.DOTALL
)

# ── Result count & sort dropdown ─────────────────────────────────────────────
html = re.sub(
    r'Showing <strong[^>]*>\d+</strong> results for "Kawaii Accessories"',
    info, html
)

# Wire sort dropdown — replace static select with dynamic one
sel_newest  = 'selected' if sort_by == 'newest'     else ''
sel_asc     = 'selected' if sort_by == 'price_asc'  else ''
sel_desc    = 'selected' if sort_by == 'price_desc' else ''
sort_select = (
    f'<div class="flex items-center gap-2">'
    f'<span class="font-body-sm text-body-sm text-outline">Sort by:</span>'
    f'<select id="sort-select" onchange="applySort()" class="bg-surface-bright border-none text-on-surface font-body-sm text-body-sm rounded-lg py-2 pl-3 pr-8 focus:ring-2 focus:ring-primary-container outline-none cursor-pointer">'
    f'<option value="newest" {sel_newest}>Terbaru</option>'
    f'<option value="price_asc" {sel_asc}>Harga Terendah</option>'
    f'<option value="price_desc" {sel_desc}>Harga Tertinggi</option>'
    f'</select></div>'
)
html = re.sub(
    r'<div class="flex items-center gap-2">\s*<span class="font-body-sm text-body-sm text-outline">Sort by:</span>.*?</div>',
    sort_select, html, flags=re.DOTALL
)

# ── Top Navbar ─────────────────────────────────────────────────────────────────
html = inject_navbar(html, cart_len, sq)

# ── Sidebar scrollable ────────────────────────────────────────────────────────
html = html.replace(
    'class="bg-white rounded-xl p-6 shadow-[0_8px_30px_rgb(255,182,193,0.08)] sticky top-28"',
    'class="bg-white rounded-xl p-6 shadow-[0_8px_30px_rgb(255,182,193,0.08)] sticky top-28 max-h-[calc(100vh-7rem)] overflow-y-auto"'
)

# ── Nav links ─────────────────────────────────────────────────────────────────
for lbl in ['Categories','Flash Sale','Brands']:
    html = html.replace(
        f'>{lbl}</a>',
        f" onclick=\"event.preventDefault();stNavigate({{action:'filter',q:'',cat:''}})\">{lbl}</a>", 1
    )

# ── Mobile nav ────────────────────────────────────────────────────────────────
html = re.sub(r'href="#"', 'href="#" onclick="event.preventDefault();"', html)

action_data = render_original_html("belikuy_v2_search", html, height=2100)

if action_data:
    act = action_data.get("action","")
    current_user = st.session_state.get('user')
    if handle_global_action(st, act, action_data, current_user):
        pass
    elif act == "go_home":    st.switch_page("pages/1_Storefront.py")
    elif act == "go_cart":    st.switch_page("pages/4_Keranjang.py")
    elif act == "go_profile": st.switch_page("pages/8_Profil.py")
    elif act == "go_orders":  st.switch_page("pages/6_Riwayat_Pesanan.py")
    elif act == "go_detail":
        st.session_state["viewing_product_id"] = action_data.get("pid")
        st.switch_page("pages/3_Detail_Produk.py")
    elif act == "filter":
        nq   = str(action_data.get("q","")).strip()
        nc   = str(action_data.get("cat","")).strip()
        nmin = str(action_data.get("min_price","")).strip()
        nmax = str(action_data.get("max_price","")).strip()
        nsrt = str(action_data.get("sort","newest")).strip()
        st.query_params.clear()
        if nq:   st.query_params["q"]         = nq
        if nc:   st.query_params["cat"]       = nc
        if nmin: st.query_params["min_price"] = nmin
        if nmax: st.query_params["max_price"] = nmax
        if nsrt and nsrt != "newest": st.query_params["sort"] = nsrt
        st.query_params["page"] = "1"
        st.rerun()
    elif act == "paginate":
        st.query_params["page"] = str(action_data.get("page", 1))
        st.rerun()
    elif act == "add_cart":
        pid = action_data.get("pid")
        if pid:
            prod, _ = get_api(f"products/{pid}")
            if prod:
                if "cart" not in st.session_state: st.session_state["cart"] = []
                ex = next((x for x in st.session_state["cart"] if str(x.get("id"))==str(pid)), None)
                if ex: ex["qty"] = ex.get("qty",1)+1
                else:
                    prod["qty"] = 1
                    st.session_state["cart"].append(prod)
        st.rerun()
