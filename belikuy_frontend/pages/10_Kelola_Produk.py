import streamlit as st
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from utils import get_api, post_api, put_api, delete_api, require_role, hide_streamlit_ui, format_rupiah, get_image_base64
from html_bridge import render_original_html
from unified_sidebar import inject_seller_sidebar, handle_seller_global_action
import requests as _req

st.set_page_config(page_title="BeliKuy - Kelola Produk", layout="wide", initial_sidebar_state="collapsed")
hide_streamlit_ui()
require_role("seller")

user = st.session_state['user']
company = user.get('company', {}); company_id = company.get('company_id') if company else None

products, _ = get_api(f"products/seller/{company_id}")
if not products: products = []
categories, _ = get_api("categories")
if not categories: categories = []
supply_companies, _ = get_api("admin/supply-companies")
if not supply_companies: supply_companies = []


# Active filter from session
active_cat_filter = str(st.session_state.get('prod_cat_filter', ''))
active_search = st.session_state.get('prod_search', '').strip().lower()

# Filter products by category and search
display_products = products
if active_cat_filter:
    display_products = [p for p in display_products if str(p.get('category_id', '')) == active_cat_filter]
if active_search:
    display_products = [p for p in display_products if active_search in (p.get('product_name', '') or '').lower()]


HTML_BASE = r"D:\belikuy\belikuy_ui_templates"
with open(os.path.join(HTML_BASE, "seller_product_management/code.html"), encoding='utf-8') as f:
    html = f.read()

# ── Remove "Tambah Produk Baru" header button ────────────────────────────────
html = re.sub(
    r'<button[^>]*class="[^"]*gradient-btn[^"]*"[^>]*>.*?</button>',
    '', html, flags=re.DOTALL
)

# ── Replace static category select with dynamic one ─────────────────────────
cat_options_html = '<option value="">Semua Kategori</option>'
for c in categories:
    selected = 'selected' if active_cat_filter == str(c['id']) else ''
    cat_options_html += f'<option value="{c["id"]}" {selected}>{c["category_name"]}</option>'

html = re.sub(
    r'(<select[^>]*>)\s*<option[^>]*>Semua Kategori</option>.*?(</select>)',
    rf'\1{cat_options_html}\2', html, flags=re.DOTALL
)
# Wire up the category select to call stNavigate on change
html = html.replace(
    'class="w-full bg-surface-container-low border-none rounded-xl py-3.5 pl-12 pr-10 font-body-md text-body-md text-on-surface appearance-none focus:ring-0 focus:bg-surface-container-lowest focus:shadow-glow transition-all cursor-pointer"',
    'onchange="stNavigate({action:\'filter_cat\', cat_id: this.value})" class="w-full bg-surface-container-low border-none rounded-xl py-3.5 pl-12 pr-10 font-body-md text-body-md text-on-surface appearance-none focus:ring-0 focus:bg-surface-container-lowest focus:shadow-glow transition-all cursor-pointer"',
    1  # Only first occurrence (category filter, not status filter)
)
# Remove status filter select (second select, not connected to backend)
html = re.sub(
    r'<!-- Status Filter -->.*?</div>\s*</div>',
    '</div>', html, flags=re.DOTALL
)
# Remove the expand_more icon span that sits next to the category select (causes double arrow)
html = re.sub(
    r'<span class="material-symbols-outlined absolute right-4 top-1/2 -translate-y-1/2 text-outline pointer-events-none">expand_more</span>',
    '', html
)
# Remove Tailwind forms plugin (it adds its own select arrow via background-image → double arrow)
html = html.replace(
    'src="https://cdn.tailwindcss.com?plugins=forms,container-queries"',
    'src="https://cdn.tailwindcss.com?plugins=container-queries"'
)
# Add CSS arrow and wire search input
arrow_css = """<style>
select { background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24'%3E%3Cpath fill='%23847375' d='M7 10l5 5 5-5z'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 12px center; background-size: 20px; }
</style>"""
html = html.replace("</head>", arrow_css + "</head>")

# Wire search input: match actual placeholder in HTML
search_val = active_search.replace('"', '&quot;')
html = re.sub(
    r'(<input[^>]*placeholder="Cari nama produk[^"]*"[^>]*)(/>|>)',
    rf'\1 value="{search_val}" onkeydown="onSearchEnter(event,this.value)" \2',
    html, count=1
)


# ── Build Product Cards ──────────────────────────────────────────────────────
cards = ""
for p in display_products:
    img_path = p.get('image_url', '') or ''
    img = get_image_base64(img_path) if img_path else 'https://via.placeholder.com/400?text=Produk'
    stok = p.get('stock', 0)
    is_active = int(p.get('is_active', 1))

    if not is_active:
        status_label = "Nonaktif"
        status_bg = "bg-zinc-200 text-zinc-600"
    elif stok <= 0:
        status_label = "Stok Habis"
        status_bg = "bg-error-container text-error"
    else:
        status_label = "Aktif"
        status_bg = "bg-tertiary-fixed text-on-tertiary-fixed"

    toggle_icon = "visibility_off" if is_active else "visibility"
    toggle_label = "Nonaktifkan" if is_active else "Aktifkan"
    toggle_action = f"stNavigate({{action:'toggle_product', pid:{p['id']}, is_active:{0 if is_active else 1}}})"
    toggle_cls = "text-on-surface-variant hover:text-primary hover:bg-primary-container" if is_active else "text-primary bg-primary-container/40 hover:bg-primary-container"
    name_safe = p.get('product_name', '').replace("'", "\\'").replace('"', '&quot;')

    cards += f'''
    <article class="bg-surface-container-lowest rounded-2xl p-4 shadow-ambient hover:-translate-y-1 transition-transform duration-300 flex flex-col group {'opacity-60' if not is_active else ''}">
        <div class="relative h-56 rounded-[12px] bg-surface-container overflow-hidden mb-4">
            <img alt="Product Image" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700 ease-out" src="{img}"/>
            <div class="absolute top-3 right-3 {status_bg} font-label-caps text-label-caps px-3 py-1.5 rounded-lg shadow-sm uppercase tracking-wider backdrop-blur-sm">
                {status_label}
            </div>
        </div>
        <div class="flex-1 flex flex-col">
            <h3 class="font-h3 text-h3 text-on-surface line-clamp-1 mb-1">{p.get("product_name","")}</h3>
            <p class="font-body-sm text-body-sm text-outline mb-1">Kategori: {p.get("category_name","–")}</p>
            <p class="font-body-sm text-body-sm text-outline mb-3">{'<span class="inline-flex items-center gap-1"><span class="material-symbols-outlined text-[13px]">factory</span>' + p.get("supply_company_name","") + '</span>' if p.get("supply_company_name") else '<span class="text-outline/50 italic">Tidak ada supplier</span>'}
            </p>
            <div class="flex justify-between items-end mt-auto mb-4">
                <div>
                    <p class="font-body-sm text-body-sm text-on-surface-variant mb-0.5">Harga</p>
                    <p class="font-h3 text-[20px] text-primary font-bold">{format_rupiah(p.get("price",0))}</p>
                </div>
                <div class="text-right">
                    <p class="font-body-sm text-body-sm text-on-surface-variant mb-0.5">Stok</p>
                    <p class="font-body-lg text-body-lg {'text-error' if stok <= 0 else 'text-on-surface'} font-semibold">{stok}</p>
                </div>
            </div>
        </div>
        <div class="pt-4 border-t border-surface-variant flex gap-2">
            <button onclick="{toggle_action}" class="flex-1 py-2 rounded-xl {toggle_cls} transition-colors flex items-center justify-center gap-1 text-sm font-medium" title="{toggle_label}">
                <span class="material-symbols-outlined text-[18px]">{toggle_icon}</span>
            </button>
            <button onclick="openEditModal({p['id']}, '{name_safe}', {p.get('price',0)}, {stok}, {p.get('category_id', 1)})"
                class="flex-1 py-2 rounded-xl text-outline hover:text-primary hover:bg-primary-container transition-colors flex items-center justify-center gap-2" title="Edit">
                <span class="material-symbols-outlined text-[20px]">edit</span>
            </button>
            <button onclick="stNavigate({{action:'delete_product', pid:{p['id']}}})"
                class="flex-1 py-2 rounded-xl text-outline hover:text-error hover:bg-error-container transition-colors flex items-center justify-center gap-2" title="Hapus">
                <span class="material-symbols-outlined text-[20px]">delete</span>
            </button>
        </div>
    </article>
    '''

# Add new product placeholder card
cards += '''
<article onclick="toggleModal()" class="bg-transparent rounded-2xl p-4 border-2 border-dashed border-outline-variant hover:border-primary transition-colors duration-300 flex flex-col items-center justify-center min-h-[400px] cursor-pointer group">
    <div class="w-16 h-16 rounded-full bg-surface-container-low group-hover:bg-primary-container flex items-center justify-center mb-4 transition-colors">
        <span class="material-symbols-outlined text-[32px] text-outline group-hover:text-primary transition-colors">add_circle</span>
    </div>
    <h3 class="font-h3 text-h3 text-on-surface-variant group-hover:text-primary transition-colors text-center">Tambah<br/>Produk Baru</h3>
</article>
'''

# Replace product grid
html = re.sub(
    r'(<section class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">)(.*?)(</section>)',
    rf'\1{cards}\3', html, flags=re.DOTALL
)

# ── Category & Supply Company Options for modals ─────────────────────────────
cat_opts = "".join([f'<option value="{c["id"]}">{c["category_name"]}</option>' for c in categories])
sc_opts = '<option value="">— Tidak ada / Pilih Supplier —</option>' + "".join(
    [f'<option value="{s["id"]}">{s["supply_company_name"]}</option>' for s in supply_companies]
)


# ── Modals ────────────────────────────────────────────────────────────────────
modals_html = f'''
<div id="productModal" class="fixed inset-0 bg-black/40 backdrop-blur-sm z-[200] hidden items-start pt-16 justify-center p-4 flex">
    <div class="bg-white rounded-2xl w-full max-w-2xl p-8 shadow-2xl relative max-h-[90vh] overflow-y-auto">
        <button onclick="toggleModal()" type="button" class="absolute top-5 right-5 text-gray-400 hover:text-red-500 transition-colors p-1">
            <span class="material-symbols-outlined">close</span>
        </button>
        <h2 class="text-2xl font-bold text-on-background mb-6">Tambah Produk Baru</h2>
        <div class="grid grid-cols-2 gap-4 mb-4">
            <div class="col-span-2">
                <label class="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Nama Produk *</label>
                <input id="p_name" type="text" class="w-full bg-gray-50 border border-gray-200 rounded-xl py-3 px-4 outline-none focus:ring-2 focus:ring-pink-200" placeholder="Nama produk"/>
            </div>
            <div>
                <label class="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Harga (Rp) *</label>
                <input id="p_price" type="number" class="w-full bg-gray-50 border border-gray-200 rounded-xl py-3 px-4 outline-none focus:ring-2 focus:ring-pink-200" placeholder="50000"/>
            </div>
            <div>
                <label class="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Stok *</label>
                <input id="p_stock" type="number" min="0" class="w-full bg-gray-50 border border-gray-200 rounded-xl py-3 px-4 outline-none focus:ring-2 focus:ring-pink-200" placeholder="0"/>
            </div>
            <div>
                <label class="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Kategori *</label>
                <select id="p_cat" class="w-full bg-gray-50 border border-gray-200 rounded-xl py-3 px-4 outline-none focus:ring-2 focus:ring-pink-200">
                    <option value="">Pilih Kategori</option>
                    {cat_opts}
                </select>
            </div>
            <div>
                <label class="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Supplier</label>
                <select id="p_sc" class="w-full bg-gray-50 border border-gray-200 rounded-xl py-3 px-4 outline-none focus:ring-2 focus:ring-pink-200">
                    {sc_opts}
                </select>
            </div>
            <div>
                <label class="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Brand</label>
                <input id="p_brand" type="text" class="w-full bg-gray-50 border border-gray-200 rounded-xl py-3 px-4 outline-none focus:ring-2 focus:ring-pink-200" placeholder="Opsional"/>
            </div>

            <div class="col-span-2">
                <label class="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">URL / Path Gambar</label>
                <input id="p_img" type="text" class="w-full bg-gray-50 border border-gray-200 rounded-xl py-3 px-4 outline-none focus:ring-2 focus:ring-pink-200" placeholder="https://... atau app/static/..."/>
            </div>
            <div class="col-span-2">
                <label class="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Deskripsi</label>
                <textarea id="p_desc" rows="3" class="w-full bg-gray-50 border border-gray-200 rounded-xl py-3 px-4 outline-none focus:ring-2 focus:ring-pink-200 resize-none" placeholder="Deskripsi produk..."></textarea>
            </div>
        </div>
        <p id="add_error" class="text-red-500 text-sm mb-3 hidden"></p>
        <div class="flex justify-end gap-3">
            <button onclick="toggleModal()" class="px-6 py-3 rounded-xl text-gray-500 hover:bg-gray-100 transition-colors font-medium">Batal</button>
            <button onclick="saveProduct()" class="px-8 py-3 rounded-xl bg-primary text-white font-semibold hover:opacity-90 shadow-md transition-all">Simpan Produk</button>
        </div>
    </div>
</div>

<div id="editModal" class="fixed inset-0 bg-black/40 backdrop-blur-sm z-[200] hidden items-start pt-16 justify-center p-4 flex">
    <div class="bg-white rounded-2xl w-full max-w-md p-8 shadow-2xl relative">
        <button onclick="closeEditModal()" type="button" class="absolute top-5 right-5 text-gray-400 hover:text-red-500 transition-colors p-1">
            <span class="material-symbols-outlined">close</span>
        </button>
        <h2 class="text-2xl font-bold text-on-background mb-6">Edit Produk</h2>
        <input type="hidden" id="e_pid"/>
        <div class="space-y-4">
            <div>
                <label class="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Nama Produk</label>
                <input id="e_name" type="text" class="w-full bg-gray-50 border border-gray-200 rounded-xl py-3 px-4 outline-none focus:ring-2 focus:ring-pink-200"/>
            </div>
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <label class="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Harga (Rp)</label>
                    <input id="e_price" type="number" class="w-full bg-gray-50 border border-gray-200 rounded-xl py-3 px-4 outline-none focus:ring-2 focus:ring-pink-200"/>
                </div>
                <div>
                    <label class="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Stok</label>
                    <input id="e_stock" type="number" min="0" class="w-full bg-gray-50 border border-gray-200 rounded-xl py-3 px-4 outline-none focus:ring-2 focus:ring-pink-200"/>
                </div>
            </div>
            <div>
                <label class="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Kategori</label>
                <select id="e_cat" class="w-full bg-gray-50 border border-gray-200 rounded-xl py-3 px-4 outline-none focus:ring-2 focus:ring-pink-200">
                    {cat_opts}
                </select>
            </div>
            <div>
                <label class="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Supplier</label>
                <select id="e_sc" class="w-full bg-gray-50 border border-gray-200 rounded-xl py-3 px-4 outline-none focus:ring-2 focus:ring-pink-200">
                    {sc_opts}
                </select>
            </div>

        </div>
        <div class="flex justify-end gap-3 mt-6">
            <button onclick="closeEditModal()" class="px-6 py-3 rounded-xl text-gray-500 hover:bg-gray-100 transition-colors font-medium">Batal</button>
            <button onclick="saveEdit()" class="px-8 py-3 rounded-xl bg-primary text-white font-semibold hover:opacity-90 shadow-md transition-all">Simpan</button>
        </div>
    </div>
</div>
'''
html = html.replace('</body>', modals_html + '</body>')

company_name = user.get('company', {}).get('company_name', 'Toko Saya') if user.get('company') else 'Toko Saya'
html = inject_seller_sidebar(html, "10_Kelola_Produk", company_name)

# ── JS — define AFTER sidebar inject, will be placed before </head> ───────────
js_head = """<script>
function stNavigate(params) {
    params._ts = Date.now();
    if(window.Streamlit) { window.Streamlit.setComponentValue(params); }
}
// Search: only on Enter
function onSearchEnter(e, val) {
    if (e.key === 'Enter') {
        stNavigate({action: 'search_prod', q: val.trim()});
    }
}
function toggleModal() {
    const m = document.getElementById('productModal');
    m.classList.toggle('hidden');
    m.style.display = m.classList.contains('hidden') ? 'none' : 'flex';
}
function openEditModal(pid, name, price, stock, catId) {
    document.getElementById('e_pid').value = pid;
    document.getElementById('e_name').value = name;
    document.getElementById('e_price').value = price;
    document.getElementById('e_stock').value = stock;
    const sel = document.getElementById('e_cat');
    if(sel) { for(let o of sel.options) { o.selected = (o.value == String(catId)); } }
    const m = document.getElementById('editModal');
    m.classList.remove('hidden');
    m.style.display = 'flex';
}
function closeEditModal() {
    const m = document.getElementById('editModal');
    m.classList.add('hidden');
    m.style.display = 'none';
}
function saveProduct() {
    const name = document.getElementById('p_name').value.trim();
    const price = document.getElementById('p_price').value;
    const stock = document.getElementById('p_stock').value;
    const cat = document.getElementById('p_cat').value;
    const desc = document.getElementById('p_desc').value;
    const img = document.getElementById('p_img').value;
    const brand = document.getElementById('p_brand').value;
    const errEl = document.getElementById('add_error');
    if (!name || !price || !cat) {
        errEl.textContent = 'Nama, harga, dan kategori wajib diisi!';
        errEl.classList.remove('hidden');
        return;
    }
    errEl.classList.add('hidden');
    stNavigate({action: 'add_product', name, price, stock: stock||'0', cat, desc, img, brand, sc_id: document.getElementById('p_sc').value || ''});
}

function saveEdit() {
    const pid = document.getElementById('e_pid').value;
    const name = document.getElementById('e_name').value.trim();
    const price = document.getElementById('e_price').value;
    const stock = document.getElementById('e_stock').value;
    const cat = document.getElementById('e_cat').value;
    const sc_id = document.getElementById('e_sc') ? document.getElementById('e_sc').value : '';
    stNavigate({action: 'edit_product', pid, name, price, stock: stock||'0', cat, sc_id: sc_id||''});
}

// Fix modal initial display
document.addEventListener('DOMContentLoaded', function() {
    ['productModal','editModal'].forEach(id => {
        const m = document.getElementById(id);
        if(m) m.style.display = 'none';
    });
});
</script>"""
html = html.replace("</head>", js_head + "</head>")
html = html.replace('href="#"', 'href="#" onclick="event.preventDefault();"')

action_data = render_original_html("belikuy_v2_products", html, height=1500)

if action_data:
    act = action_data.get('action')
    if handle_seller_global_action(st, act):
        pass
    elif act == "filter_cat":
        st.session_state['prod_cat_filter'] = str(action_data.get('cat_id', ''))
        st.session_state['order_page'] = 1
        st.rerun()
    elif act == "search_prod":
        st.session_state['prod_search'] = action_data.get('q', '')
        st.rerun()
    elif act == "delete_product":
        pid = action_data.get("pid")
        if pid:
            delete_api(f"products/{pid}")
        st.rerun()
    elif act == "toggle_product":
        pid = action_data.get("pid")
        is_active = action_data.get("is_active", 1)
        if pid:
            import requests as _req
            _req.patch(f"http://localhost:5000/api/products/{pid}/toggle",
                       json={"company_id": company_id, "is_active": int(is_active)}, timeout=8)
        st.rerun()
    elif act == "add_product":
        name = action_data.get("name", "").strip()
        price = action_data.get("price", "0")
        stock = action_data.get("stock", "0")
        cat = action_data.get("cat", "")
        desc = action_data.get("desc", "")
        img = action_data.get("img", "")
        brand = action_data.get("brand", "")
        if name and price and cat:
            payload = {
                "product_name": name,
                "price": float(price),
                "stock": int(float(stock)),
                "category_id": int(cat),
                "description": desc,
                "image_url": img,
                "brand": brand,
                "company_id": company_id
            }
            sc_id = action_data.get("sc_id", "")
            if sc_id:
                payload["supply_company_id"] = int(sc_id)
            resp, code = post_api("products", payload)
            if code != 201:
                st.error(f"Gagal tambah produk: {resp}")
        else:
            st.error("Nama, harga, dan kategori wajib diisi!")
        st.rerun()
    elif act == "edit_product":
        pid = action_data.get("pid")
        name = action_data.get("name", "").strip()
        price = action_data.get("price", "0")
        stock = action_data.get("stock", "0")
        cat = action_data.get("cat", "")
        if pid and name:
            payload = {
                "product_name": name,
                "price": float(price),
                "stock": int(float(stock)),
                "category_id": int(cat) if cat else None,
                "company_id": company_id
            }
            sc_id = action_data.get("sc_id", "")
            if sc_id:
                payload["supply_company_id"] = int(sc_id)
            put_api(f"products/{pid}", payload)
        st.rerun()

