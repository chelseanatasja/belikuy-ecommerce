import streamlit as st
import sys, os, re, base64, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from utils import get_api, post_api, require_login, hide_streamlit_ui, format_rupiah
from html_bridge import render_original_html
from unified_navbar import inject_navbar, handle_global_action

st.set_page_config(
    page_title="BeliKuy - Checkout", layout="wide", initial_sidebar_state="collapsed"
)
hide_streamlit_ui()
require_login()

FRONTEND_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def local_img(path):
    if not path:
        return "https://via.placeholder.com/150?text=No+Image"
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
    return "https://via.placeholder.com/150?text=No+Image"


cart = st.session_state.get("cart", [])
user = st.session_state["user"]

if not cart:
    st.session_state["_checkout_empty"] = True
    st.switch_page("pages/4_Keranjang.py")

addresses, _ = get_api(f"addresses/{user['id']}")
shipment_cos, _ = get_api("admin/shipment-companies")
payment_methods, _ = get_api("payments/methods")
if not addresses:
    addresses = []
if not shipment_cos:
    shipment_cos = []
if not payment_methods:
    payment_methods = []

subtotal = sum(float(i.get("price", 0)) * int(i.get("qty", 1)) for i in cart)


def get_ship_price(service_type):
    stype = str(service_type).lower()
    if "instant" in stype:
        return 60000
    if "sameday" in stype:
        return 40000
    if "yes" in stype or "best" in stype or "super" in stype:
        return 35000
    if "ez" in stype or "halu" in stype:
        return 20000
    return 15000


# Setup selected shipping
if "selected_shipping_id" not in st.session_state and shipment_cos:
    st.session_state["selected_shipping_id"] = str(shipment_cos[0]["id"])

selected_ship_id = st.session_state.get("selected_shipping_id")
shipping_cost = 15000
for s in shipment_cos:
    if str(s["id"]) == str(selected_ship_id):
        shipping_cost = get_ship_price(s["service_type"])
        break

service_fee = 2500
discount = 25000
total = subtotal + shipping_cost + service_fee - discount


# ── Load HTML ────────────────────────────────────────────────────────────────
HTML_BASE = (
    r"D:\Tugas Kuliah\Semester 4\Workshop RPL\belikuy-ecommerce\belikuy_ui_templates"
)
with open(os.path.join(HTML_BASE, "checkout_page/code.html"), encoding="utf-8") as f:
    html = f.read()

# ── Address section ──────────────────────────────────────────────────────────
if addresses:
    addr_options = "".join(
        f'<option value="{a["id"]}">{a["address"]}, {a["city"]}</option>'
        for a in addresses
    )
    addr_html = f"""
    <h2 class="font-h3 text-h3 text-on-surface flex items-center gap-2 mb-md">
        <span class="material-symbols-outlined text-primary">location_on</span> Alamat Pengiriman
    </h2>
    <select id="addr-sel"
        class="w-full bg-surface-container-low border border-outline-variant rounded-lg px-3 py-2 font-body-sm outline-none focus:border-primary mb-md">
        {addr_options}
    </select>
    <div class="bg-surface-container-low rounded-lg p-md">
        <p class="font-body-lg text-body-lg font-semibold mb-xs">{user.get('username','User')} &mdash; {user.get('email','')}</p>
        <p class="font-body-md text-body-md text-on-surface-variant">{addresses[0]["address"]}, {addresses[0]["city"]} {addresses[0].get("postal_code","")}</p>
    </div>"""
else:
    addr_html = """
    <h2 class="font-h3 text-h3 text-on-surface flex items-center gap-2 mb-md">
        <span class="material-symbols-outlined text-primary">location_on</span> Alamat Pengiriman
    </h2>
    <div class="bg-error-container rounded-lg p-md text-on-error-container mb-md">
        Belum ada alamat tersimpan.
        <a onclick="stNavigate({action:\'go_address\'})" class="underline cursor-pointer font-semibold ml-1">Tambah alamat sekarang</a>
    </div>
    <input type="hidden" id="addr-sel" value=""/>"""

html = re.sub(
    r"(<!-- Address Selection -->\s*<section[^>]*>)(.*?)(</section>)",
    rf"\1{addr_html}\3",
    html,
    flags=re.DOTALL,
)

# ── Order items ──────────────────────────────────────────────────────────────
items_html = f'<h2 class="font-h3 text-h3 text-on-surface mb-md flex items-center gap-2"><span class="material-symbols-outlined text-primary">shopping_bag</span> Pesanan Anda ({len(cart)} item)</h2>'
for i in cart:
    img = local_img(i.get("image_url", ""))
    pr_sub = format_rupiah(float(i.get("price", 0)) * int(i.get("qty", 1)))
    items_html += f"""
    <div class="flex gap-md border-b border-outline-variant/30 pb-md mb-md">
        <div class="w-24 h-24 rounded-lg overflow-hidden shrink-0 shadow-sm bg-surface-bright">
            <img src="{img}" class="w-full h-full object-cover" onerror="this.src='https://via.placeholder.com/150?text=No+Image'"/>
        </div>
        <div class="flex flex-col justify-center flex-grow">
            <h3 class="font-body-lg text-body-lg font-semibold text-on-surface mb-xs">{i.get("product_name","")}</h3>
            <p class="font-body-md text-body-md text-on-surface-variant mb-2">Toko: {i.get("company_name","")}</p>
            <div class="flex justify-between items-center w-full">
                <span class="font-body-md text-body-md text-primary font-semibold">{pr_sub}</span>
                <span class="font-body-sm text-body-sm text-on-surface-variant">x{i.get("qty",1)}</span>
            </div>
        </div>
    </div>"""

html = re.sub(
    r'(<!-- Order Items Preview.*?<section[^>]*>)(.*?)(<div class="flex items-center justify-between pt-xs">)',
    rf"\1{items_html}\3",
    html,
    flags=re.DOTALL,
)

# ── Shipping options ─────────────────────────────────────────────────────────
if shipment_cos:
    ship_html = '<h2 class="font-h3 text-h3 text-on-surface mb-md flex items-center gap-2"><span class="material-symbols-outlined text-primary">local_shipping</span> Pilih Pengiriman</h2><div class="grid grid-cols-1 md:grid-cols-2 gap-md">'
    for s in shipment_cos:
        sid = str(s["id"])
        checked = "checked" if sid == str(selected_ship_id) else ""
        pr = get_ship_price(s["service_type"])
        ship_html += f"""
        <label class="cursor-pointer">
            <input {checked} onchange="stNavigate({{action:'update_shipping', ship_id: '{sid}'}})" class="peer sr-only" name="shipping" type="radio" value="{sid}"/>
            <div class="border-2 border-outline-variant/50 rounded-xl p-md peer-checked:border-primary peer-checked:bg-primary-container/10 transition-all hover:bg-surface-container-low flex flex-col gap-2">
                <div class="flex justify-between items-center">
                    <span class="font-body-lg text-body-lg font-semibold">{s['company_name']}</span>
                    <span class="font-body-md text-body-md text-primary">{s['service_type']}</span>
                </div>
                <p class="font-body-sm text-body-sm text-on-surface-variant">{format_rupiah(pr)}</p>
            </div>
        </label>"""
    ship_html += "</div>"
else:
    ship_html = '<h2 class="font-h3 text-h3 text-on-surface mb-md">Pengiriman</h2><p class="text-on-surface-variant">Pengiriman standar — Rp 25.000</p>'

html = re.sub(
    r"(<!-- Shipping Method -->\s*<section[^>]*>)(.*?)(</section>)",
    rf"\1{ship_html}\3",
    html,
    flags=re.DOTALL,
)

# ── Payment options ─────────────────────────────────────────────────────────
if payment_methods:
    pay_html = '<h2 class="font-h3 text-h3 text-on-surface mb-md flex items-center gap-2"><span class="material-symbols-outlined text-primary">payments</span> Metode Pembayaran</h2><div class="flex flex-col gap-sm">'
    for idx3, p in enumerate(payment_methods):
        icon = "account_balance"
        if p["institution_type"] == "Fintech":
            icon = "account_balance_wallet"
        elif p["institution_type"] == "Virtual Account":
            icon = "credit_card"

        pay_html += f"""
        <label class="cursor-pointer">
            <input {"checked" if idx3==0 else ""} class="peer sr-only" name="payment" type="radio" value="{p['id']}"/>
            <div class="flex items-center justify-between border border-outline-variant/50 rounded-lg p-md peer-checked:border-primary peer-checked:bg-primary-container/10 hover:bg-surface-container-low transition-all">
                <div class="flex items-center gap-md">
                    <div class="w-10 h-10 bg-white rounded-md shadow-sm flex items-center justify-center p-1 border border-outline-variant/20">
                        <span class="material-symbols-outlined text-primary">{icon}</span>
                    </div>
                    <div>
                        <p class="font-body-md text-body-md font-semibold">{p['institution_name']}</p>
                        <p class="font-body-sm text-body-sm text-on-surface-variant">{p['institution_type']}</p>
                    </div>
                </div>
                <div class="w-5 h-5 rounded-full border-2 border-outline-variant peer-checked:border-primary flex items-center justify-center">
                    <div class="w-2.5 h-2.5 rounded-full bg-primary opacity-0 peer-checked:opacity-100 transition-opacity"></div>
                </div>
            </div>
        </label>"""
    pay_html += "</div>"
else:
    pay_html = '<h2 class="font-h3 text-h3 text-on-surface mb-md">Pembayaran</h2><p class="text-on-surface-variant">Belum ada metode pembayaran.</p>'

html = re.sub(
    r"(<!-- Payment Method -->\s*<section[^>]*>)(.*?)(</section>)",
    rf"\1{pay_html}\3",
    html,
    flags=re.DOTALL,
)

# ── Summary prices ────────────────────────────────────────────────────────────
summary_html = f"""<h2 class="font-h3 text-h3 text-on-surface mb-xs border-b border-outline-variant/30 pb-sm">Ringkasan Belanja</h2>
<div class="flex flex-col gap-sm">
<div class="flex justify-between items-center font-body-md text-body-md text-on-surface-variant">
<span>Total Harga ({len(cart)} Barang)</span>
<span>{format_rupiah(subtotal)}</span>
</div>
<div class="flex justify-between items-center font-body-md text-body-md text-on-surface-variant">
<span>Total Ongkos Kirim</span>
<span>{format_rupiah(shipping_cost)}</span>
</div>
<div class="flex justify-between items-center font-body-md text-body-md text-on-surface-variant">
<span>Biaya Layanan &amp; Jasa</span>
<span>{format_rupiah(service_fee)}</span>
</div>
<div class="flex justify-between items-center font-body-md text-body-md text-primary mt-xs">
<span>Diskon Belanja</span>
<span>- {format_rupiah(discount)}</span>
</div>
</div>
<div class="border-t border-outline-variant/30 pt-md mt-sm flex justify-between items-end">
<span class="font-body-lg text-body-lg font-semibold text-on-surface">Total Tagihan</span>
<span class="font-h2 text-h2 text-primary">{format_rupiah(total)}</span>
</div>"""

html = re.sub(
    r'(<h2 class="font-h3 text-h3 text-on-surface mb-xs border-b border-outline-variant/30 pb-sm">Ringkasan Belanja</h2>.*?</button>)',
    summary_html
    + r'\n<button onclick="placeOrder()" class="w-full py-4 mt-md bg-gradient-to-r from-pink-400 to-purple-500 hover:from-pink-500 hover:to-purple-600 text-white font-label-caps text-label-caps rounded-full shadow-md hover:shadow-lg transition-all active:scale-95 flex items-center justify-center gap-2">\n<span class="material-symbols-outlined text-[18px]">lock</span> KONFIRMASI PESANAN </button>',
    html,
    flags=re.DOTALL,
)

# ── Inject JS — placeOrder function ──────────────────────────────────────────
js = """<script>
function placeOrder() {
    var addrSel = document.getElementById('addr-sel');
    var addr = addrSel ? addrSel.value : '';
    var payEl = document.querySelector('input[name="payment"]:checked');
    var pay  = payEl ? payEl.value : '';
    var shipEl = document.querySelector('input[name="shipping"]:checked');
    var ship = shipEl ? shipEl.value : '';
    stNavigate({action:'place_order', address_id: addr, payment_method: pay, shipping_method: ship});
}
</script>"""
html = html.replace("</head>", js + "\n</head>", 1)

# ── Wire checkout button removed because it is now inline above ──

# ── Inject Unified Navbar ───────────────────────────────────────────────────
html = inject_navbar(html, len(cart))

html = html.replace('href="#"', 'href="#" onclick="event.preventDefault();"')

action_data = render_original_html("belikuy_v2_checkout", html, height=1500)

if action_data:
    act = action_data.get("action", "")
    current_user = st.session_state.get("user")
    if handle_global_action(st, act, action_data, current_user):
        pass
    elif act == "go_cart":
        st.switch_page("pages/4_Keranjang.py")
    elif act == "go_search":
        st.switch_page("pages/2_Cari_Produk.py")
    elif act == "go_profile":
        st.switch_page("pages/8_Profil.py")
    elif act == "go_orders":
        st.switch_page("pages/6_Riwayat_Pesanan.py")
    elif act == "go_address":
        st.switch_page("pages/7_Alamat.py")
    elif act == "update_shipping":
        st.session_state["selected_shipping_id"] = str(action_data.get("ship_id"))
        st.rerun()
    elif act == "place_order":
        address_id = action_data.get("address_id")
        payment_method_id = action_data.get("payment_method")
        shipping_method_id = action_data.get("shipping_method")

        if not address_id:
            st.error("Harap pilih alamat pengiriman!")
            st.stop()
        if not payment_method_id:
            st.error("Harap pilih metode pembayaran!")
            st.stop()

        cart_items = [
            {
                "product_id": i["id"],
                "quantity": int(i.get("qty", 1)),
                "price": float(i.get("price", 0)),
                "subtotal": float(i.get("price", 0)) * int(i.get("qty", 1)),
                "company_id": int(i.get("company_id", 1)),
            }
            for i in cart
        ]

        res, status = post_api(
            "orders/checkout",
            {
                "user_id": user["id"],
                "address_id": int(address_id),
                "total_price": total,
                "cart_items": cart_items,
                "payment_method_id": int(payment_method_id),
                "shipping_method_id": (
                    int(shipping_method_id) if shipping_method_id else None
                ),
            },
        )

        if status == 201:
            order_id = res.get("orderId")
            # Simpan ke session — pembayaran dilakukan di halaman terpisah
            st.session_state["cart"] = []
            st.session_state["pending_order_id"] = order_id
            st.session_state["pending_payment_method"] = int(payment_method_id)
            st.session_state["pending_total"] = total
            # Cari nama metode pembayaran
            chosen_method = next(
                (
                    m
                    for m in payment_methods
                    if str(m.get("id")) == str(payment_method_id)
                ),
                None,
            )
            st.session_state["pending_payment_name"] = (
                chosen_method.get("institution_name", "") if chosen_method else ""
            )
            st.session_state["pending_payment_type"] = (
                chosen_method.get("institution_type", "transfer")
                if chosen_method
                else "transfer"
            )
            st.switch_page("pages/5b_Pembayaran.py")
        else:
            err_msg = (res or {}).get("error", "Gagal memproses checkout")
            st.error(f"Checkout gagal: {err_msg}")
