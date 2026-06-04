import streamlit as st
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from utils import (
    get_api,
    post_api,
    require_login,
    require_role,
    hide_streamlit_ui,
    format_rupiah,
)
from b2b_sidebar import inject_custom_sidebar
from html_bridge import render_original_html

st.set_page_config(
    page_title="Supplier Dashboard", layout="wide", initial_sidebar_state="collapsed"
)
hide_streamlit_ui()
require_login()
user = st.session_state.get("user")
require_role("supplier")

HTML_BASE = (
    r"D:\Tugas Kuliah\Semester 4\Workshop RPL\belikuy-ecommerce\belikuy_ui_templates"
)
with open(os.path.join(HTML_BASE, "b2b_dashboard/code.html"), encoding="utf-8") as f:
    html = f.read()

# Mock or real data fetching
import mysql.connector

conn = mysql.connector.connect(
    host="127.0.0.1", user="root", password="", database="belikuy_supplier_db"
)
cursor = conn.cursor(dictionary=True)

cursor.execute(
    "SELECT * FROM supply_companies WHERE user_id = %s LIMIT 1", (user["id"],)
)
company = cursor.fetchone()
cursor.fetchall()

orders = []
if company:
    cursor.execute(
        "SELECT * FROM supplier_orders WHERE supplier_id = %s ORDER BY created_at DESC LIMIT 20",
        (company["id"],),
    )
    orders = cursor.fetchall()
conn.close()

total_revenue = sum(
    [o["total_price"] for o in orders if o["status"] in ("shipped", "completed")]
)
total_pending = sum(1 for o in orders if o["status"] in ("pending", "paid"))
total_shipped = sum(1 for o in orders if o["status"] == "shipped")

# Replace Placeholders
html = html.replace("{PAGE_TITLE}", "Supplier Dashboard")
html = html.replace("{USERNAME}", user["username"])
html = html.replace("{ROLE_CAPS}", "Supplier")
html = html.replace("{SUBTITLE}", "Kelola pesanan grosir B2B Anda di sini.")
html = html.replace("{USER_INITIAL}", user["username"][0].upper())

html = html.replace("{STAT1_TITLE}", "Pendapatan B2B")
html = html.replace("{STAT1_ICON}", "payments")
html = html.replace("{STAT1_VAL}", format_rupiah(total_revenue))
html = html.replace("{STAT1_DESC}", "Total pembayaran yang berhasil")

html = html.replace("{STAT2_TITLE}", "Pesanan Masuk")
html = html.replace("{STAT2_ICON}", "move_to_inbox")
html = html.replace("{STAT2_VAL}", str(total_pending))
html = html.replace("{STAT2_DESC}", "Menunggu pengiriman")

html = html.replace("{STAT3_TITLE}", "Pesanan Dikirim")
html = html.replace("{STAT3_ICON}", "local_shipping")
html = html.replace("{STAT3_VAL}", str(total_shipped))
html = html.replace("{STAT3_DESC}", "Dalam perjalanan")

html = html.replace("{STAT4_TITLE}", "Performa")
html = html.replace("{STAT4_ICON}", "speed")
html = html.replace("{STAT4_VAL}", "Sangat Baik")
html = html.replace("{STAT4_DESC}", "Tingkat respons 98%")

html = html.replace("{TABLE_TITLE}", "Pesanan Grosir Terbaru")
html = html.replace(
    "{TABLE_HEADERS}",
    "<tr><th class='p-4'>Order ID</th><th class='p-4'>Tanggal</th><th class='p-4'>Total</th><th class='p-4'>Status</th></tr>",
)

rows_html = ""
for o in orders:
    s_color = (
        "bg-yellow-100 text-yellow-800"
        if o["status"] == "pending"
        else (
            "bg-blue-100 text-blue-800"
            if o["status"] == "shipped"
            else "bg-green-100 text-green-800"
        )
    )

    action_btn = ""
    if o["status"] == "paid":
        action_btn = f"<button onclick=\"stNavigate({{action:'ship_order', oid:{o['id']}}})\" class='px-3 py-1 bg-primary text-white rounded text-xs hover:bg-primary-container hover:text-on-primary-container transition-colors font-semibold'>Kirim Barang</button>"
    elif o["status"] == "pending":
        action_btn = (
            "<span class='text-xs text-outline italic'>Menunggu Pembayaran</span>"
        )
    else:
        action_btn = "<span class='text-xs text-green-600 italic'>Selesai</span>"

    rows_html += f"<tr class='hover:bg-surface-bright transition-colors'><td class='p-4 font-semibold'>#{o['id']}</td><td class='p-4'>{o['created_at'].strftime('%d %b %Y')}</td><td class='p-4'>{format_rupiah(o['total_price'])}</td><td class='p-4'><span class='px-2 py-1 rounded-full text-[10px] uppercase font-bold tracking-wider {s_color}'>{o['status']}</span></td><td class='p-4 text-right'>{action_btn}</td></tr>"

if not orders:
    html = html.replace(
        "{EMPTY_STATE}",
        "<div class='p-8 text-center text-on-surface-variant'>Belum ada pesanan B2B.</div>",
    )
else:
    html = html.replace("{EMPTY_STATE}", "")

html = html.replace("{TABLE_ROWS}", rows_html)

# --- Catalog Section ---
catalog_html = ""
if company:
    conn = mysql.connector.connect(
        host="127.0.0.1", user="root", password="", database="belikuy_seller_db"
    )
    cur2 = conn.cursor(dictionary=True)
    cur2.execute(
        "SELECT * FROM products WHERE supply_company_id = %s ORDER BY product_name ASC",
        (company["id"],),
    )
    catalog_items = cur2.fetchall()
    conn.close()

    cards = ""
    for c in catalog_items:
        img_path = c.get("image_url", "") or ""
        from utils import get_image_base64

        img = (
            get_image_base64(img_path)
            if img_path
            else "https://via.placeholder.com/400?text=Produk"
        )
        stok = c.get("stock", 0)
        is_active = int(c.get("is_active", 1))

        status_label = "Aktif" if is_active else "Nonaktif"
        status_bg = (
            "bg-tertiary-fixed text-on-tertiary-fixed"
            if is_active
            else "bg-zinc-200 text-zinc-600"
        )
        toggle_icon = "visibility_off" if is_active else "visibility"
        toggle_cls = (
            "text-on-surface-variant hover:text-primary hover:bg-primary-container"
            if is_active
            else "text-primary bg-primary-container/40 hover:bg-primary-container"
        )

        size_color = []
        if c.get("size"):
            size_color.append(f"Ukuran: {c['size']}")
        if c.get("color"):
            size_color.append(f"Warna: {c['color']}")
        sc_text = " | ".join(size_color) if size_color else "All Size/Color"

        cards += f"""
        <article class="bg-surface-container-lowest rounded-2xl p-4 shadow-ambient hover:-translate-y-1 transition-transform duration-300 flex flex-col group {'opacity-60' if not is_active else ''}">
            <div class="relative h-48 rounded-[12px] bg-surface-container overflow-hidden mb-4">
                <img alt="Product" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700" src="{img}"/>
                <div class="absolute top-3 right-3 {status_bg} font-label-caps text-[10px] px-2 py-1 rounded-lg shadow-sm uppercase tracking-wider backdrop-blur-sm">
                    {status_label}
                </div>
            </div>
            <div class="flex-1 flex flex-col">
                <h3 class="font-h3 text-h3 text-on-surface line-clamp-1 mb-1">{c.get("product_name","")}</h3>
                <p class="font-body-sm text-[11px] text-outline mb-2">{sc_text}</p>
                <div class="flex justify-between items-end mt-auto pt-2">
                    <div>
                        <p class="font-body-sm text-body-sm text-on-surface-variant mb-0.5">Harga Grosir</p>
                        <p class="font-h3 text-[18px] text-primary font-bold">{format_rupiah(c.get("price",0))}</p>
                    </div>
                    <div class="text-right">
                        <p class="font-body-sm text-body-sm text-on-surface-variant mb-0.5">Stok</p>
                        <p class="font-body-lg text-body-lg text-on-surface font-semibold">{stok}</p>
                    </div>
                </div>
            </div>
            <div class="pt-4 mt-4 border-t border-surface-variant flex gap-2">
                <button onclick="stNavigate({{action:'toggle_product', pid:{c['id']}, is_active:{0 if is_active else 1}}})" class="flex-1 py-2 rounded-xl {toggle_cls} transition-colors flex items-center justify-center gap-1 text-sm font-medium">
                    <span class="material-symbols-outlined text-[18px]">{toggle_icon}</span>
                </button>
                <button onclick="stNavigate({{action:'delete_product', pid:{c['id']}}})" class="flex-1 py-2 rounded-xl text-outline hover:text-error hover:bg-error-container transition-colors flex items-center justify-center gap-2">
                    <span class="material-symbols-outlined text-[20px]">delete</span>
                </button>
            </div>
        </article>
        """

    cards += """
    <article onclick="toggleModal()" class="bg-transparent rounded-2xl p-4 border-2 border-dashed border-outline-variant hover:border-primary transition-colors duration-300 flex flex-col items-center justify-center min-h-[300px] cursor-pointer group">
        <div class="w-16 h-16 rounded-full bg-surface-container-low group-hover:bg-primary-container flex items-center justify-center mb-4 transition-colors">
            <span class="material-symbols-outlined text-[32px] text-outline group-hover:text-primary transition-colors">add_circle</span>
        </div>
        <h3 class="font-h3 text-h3 text-on-surface-variant group-hover:text-primary transition-colors text-center">Tambah<br/>Produk B2B</h3>
    </article>
    """

    catalog_html = f"""
    <div class="mb-8 mt-8">
        <h3 class="font-h3 text-[24px] font-semibold text-on-background mb-6">Katalog Produk Grosir Anda</h3>
        <section class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {cards}
        </section>
    </div>
    
    <div id="productModal" class="fixed inset-0 bg-black/40 backdrop-blur-sm z-[200] hidden items-start pt-16 justify-center p-4 flex">
        <div class="bg-white rounded-2xl w-full max-w-md p-8 shadow-2xl relative">
            <button onclick="toggleModal()" type="button" class="absolute top-5 right-5 text-gray-400 hover:text-red-500 transition-colors p-1">
                <span class="material-symbols-outlined">close</span>
            </button>
            <h2 class="text-2xl font-bold text-on-background mb-6">Tambah Produk B2B</h2>
            <div class="space-y-4 mb-6">
                <div>
                    <label class="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Nama Produk *</label>
                    <input id="p_name" type="text" class="w-full bg-gray-50 border border-gray-200 rounded-xl py-3 px-4 outline-none focus:ring-2 focus:ring-pink-200" placeholder="Kain Katun 100 Roll"/>
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Harga Grosir (Rp) *</label>
                        <input id="p_price" type="number" class="w-full bg-gray-50 border border-gray-200 rounded-xl py-3 px-4 outline-none focus:ring-2 focus:ring-pink-200" placeholder="5000000"/>
                    </div>
                    <div>
                        <label class="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Stok (Pcs) *</label>
                        <input id="p_stock" type="number" min="0" class="w-full bg-gray-50 border border-gray-200 rounded-xl py-3 px-4 outline-none focus:ring-2 focus:ring-pink-200" placeholder="100"/>
                    </div>
                    <div>
                        <label class="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Ukuran (Opsional)</label>
                        <input id="p_size" type="text" class="w-full bg-gray-50 border border-gray-200 rounded-xl py-3 px-4 outline-none focus:ring-2 focus:ring-pink-200" placeholder="Misal: XL, M, 42"/>
                    </div>
                    <div>
                        <label class="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Warna (Opsional)</label>
                        <input id="p_color" type="text" class="w-full bg-gray-50 border border-gray-200 rounded-xl py-3 px-4 outline-none focus:ring-2 focus:ring-pink-200" placeholder="Misal: Merah, Putih"/>
                    </div>
                </div>
                <div>
                    <label class="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">URL Gambar / Path</label>
                    <input id="p_img" type="text" class="w-full bg-gray-50 border border-gray-200 rounded-xl py-3 px-4 outline-none focus:ring-2 focus:ring-pink-200" placeholder="app/static/products/..."/>
                </div>
            </div>
            <div class="flex justify-end gap-3">
                <button onclick="toggleModal()" class="px-6 py-3 rounded-xl text-gray-500 hover:bg-gray-100 transition-colors font-medium">Batal</button>
                <button onclick="saveProduct()" class="px-8 py-3 rounded-xl bg-primary text-white font-semibold hover:opacity-90 shadow-md transition-all">Simpan</button>
            </div>
        </div>
    </div>
    <script>
    function toggleModal() {{
        const m = document.getElementById('productModal');
        m.classList.toggle('hidden');
        m.style.display = m.classList.contains('hidden') ? 'none' : 'flex';
    }}
    function saveProduct() {{
        const name = document.getElementById('p_name').value.trim();
        const price = document.getElementById('p_price').value;
        const stock = document.getElementById('p_stock').value;
        const img = document.getElementById('p_img').value;
        const size = document.getElementById('p_size') ? document.getElementById('p_size').value : '';
        const color = document.getElementById('p_color') ? document.getElementById('p_color').value : '';
        if (!name || !price) return alert('Nama dan Harga wajib diisi!');
        if(typeof stNavigate === "function") {{
            stNavigate({{action: 'add_supplier_product', name, price, stock, img, size, color}});
        }} else if(window.Streamlit) {{
            window.Streamlit.setComponentValue({{action: 'add_supplier_product', name, price, stock, img, size, color, _ts: Date.now()}});
        }}
    }}
    document.addEventListener('DOMContentLoaded', () => {{
        const m = document.getElementById('productModal');
        if(m) m.style.display = 'none';
    }});
    </script>
    """

html = html.replace("{EXTRA_CONTENT}", catalog_html)

# Inject Sidebar
html = inject_custom_sidebar(
    html, "Supplier", "Mitra", "inventory_2", user["username"][0].upper()
)

# Render
action = render_original_html("supplier_dashboard_b2b_v2", html, height=1200)

if action:
    if action.get("action") == "ship_order":
        oid = action.get("oid")
        conn = mysql.connector.connect(
            host="127.0.0.1", user="root", password="", database="belikuy_supplier_db"
        )
        cur = conn.cursor()
        cur.execute(
            "UPDATE supplier_orders SET status = 'shipped' WHERE id = %s", (oid,)
        )
        conn.commit()
        conn.close()
        st.rerun()
    elif action.get("action") == "add_supplier_product":
        name = action.get("name")
        price = action.get("price")
        stock = action.get("stock")
        img = action.get("img")
        size = action.get("size")
        color = action.get("color")
        conn = mysql.connector.connect(
            host="127.0.0.1", user="root", password="", database="belikuy_seller_db"
        )
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO products (product_name, price, stock, category_id, supply_company_id, image_url, size, color, brand, description, is_active) VALUES (%s, %s, %s, 1, %s, %s, %s, %s, 'B2B Brand', 'B2B Wholesale Product', 1)",
            (name, price, stock, company["id"], img, size, color),
        )
        conn.commit()
        conn.close()
        st.rerun()
    elif action.get("action") == "toggle_product":
        pid = action.get("pid")
        new_active = action.get("is_active")
        conn = mysql.connector.connect(
            host="127.0.0.1", user="root", password="", database="belikuy_seller_db"
        )
        cur = conn.cursor()
        cur.execute(
            "UPDATE products SET is_active = %s WHERE id = %s AND supply_company_id = %s",
            (new_active, pid, company["id"]),
        )
        conn.commit()
        conn.close()
        st.rerun()
    elif action.get("action") == "delete_product":
        pid = action.get("pid")
        conn = mysql.connector.connect(
            host="127.0.0.1", user="root", password="", database="belikuy_seller_db"
        )
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM products WHERE id = %s AND supply_company_id = %s",
            (pid, company["id"]),
        )
        conn.commit()
        conn.close()
        st.rerun()
    elif action.get("action") == "logout":
        st.session_state.clear()
        st.session_state["_auto_logout"] = True
        st.switch_page("app.py")
