import streamlit as st
import sys, os, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from utils import (
    get_api,
    post_api,
    require_login,
    require_role,
    hide_streamlit_ui,
    format_rupiah,
)
from unified_sidebar import inject_seller_sidebar
from html_bridge import render_original_html

st.set_page_config(
    page_title="Pesan Stok Supplier", layout="wide", initial_sidebar_state="collapsed"
)
hide_streamlit_ui()
require_login()
user = st.session_state["user"]
require_role("seller")
company_name = user.get("company", {}).get("company_name", "Toko Anda")

HTML_BASE = (
    r"D:\Tugas Kuliah\Semester 4\Workshop RPL\belikuy-ecommerce\belikuy_ui_templates"
)
with open(os.path.join(HTML_BASE, "b2b_procurement/code.html"), encoding="utf-8") as f:
    html = f.read()

# Session State for Selection
if "selected_supplier_id" not in st.session_state:
    st.session_state["selected_supplier_id"] = ""

# Fetch Suppliers
suppliers_res, _ = get_api("suppliers")
suppliers = suppliers_res.get("data", []) if suppliers_res else []

supplier_options = "<option value=''>-- Pilih Supplier --</option>"
empty_state = ""
catalog_html = ""
supplier_info = ""
checkout_bar = ""

if not suppliers:
    empty_state = "<div class='bg-yellow-50 text-yellow-800 p-4 rounded-xl text-center'>Belum ada Supplier yang terdaftar di BeliKuy.</div>"
else:
    for s in suppliers:
        sel = (
            "selected"
            if str(s["id"]) == str(st.session_state.get("selected_supplier_id"))
            else ""
        )
        supplier_options += (
            f"<option value='{s['id']}' {sel}>{s['supply_company_name']}</option>"
        )

sid = st.session_state.get("selected_supplier_id")
if sid:
    # Fetch Catalog
    catalog_res, _ = get_api(f"suppliers/{sid}/catalog")
    catalog = catalog_res.get("data", []) if catalog_res else []

    sup = next((s for s in suppliers if str(s["id"]) == str(sid)), None)
    if sup:
        supplier_info = f"<div class='hidden md:block w-px h-10 bg-gray-200'></div><div class='flex-shrink-0 text-right'><p class='text-[10px] uppercase font-bold text-gray-400'>Terverifikasi</p><p class='font-bold text-primary'>{sup['supply_company_name']}</p></div>"

    if not catalog:
        catalog_html = "<div class='text-center p-12 bg-white rounded-2xl border border-dashed border-gray-300'><span class='material-symbols-outlined text-4xl text-gray-300 mb-2'>inventory_2</span><p class='text-gray-500'>Supplier ini belum menambahkan barang ke katalog B2B mereka.</p></div>"
    else:
        cards = ""
        for c in catalog:
            img_path = c.get("image_url", "") or ""
            from utils import get_image_base64

            img = (
                get_image_base64(img_path)
                if img_path
                else "https://via.placeholder.com/400?text=Produk"
            )
            is_active = int(c.get("is_active", 1))
            if not is_active:
                continue  # Don't show inactive products

            sc_text = []
            if c.get("size"):
                sc_text.append(f"Ukuran: {c['size']}")
            if c.get("color"):
                sc_text.append(f"Warna: {c['color']}")
            sc_str = " | ".join(sc_text) if sc_text else "All Size/Color"

            cards += f"""
            <article class="bg-surface-container-lowest rounded-2xl p-4 shadow-sm border border-gray-100 hover:border-primary-container hover:shadow-md transition-all duration-300 flex flex-col">
                <div class="flex gap-4 mb-4">
                    <img src="{img}" class="w-20 h-20 rounded-xl object-cover" />
                    <div class="flex-1">
                        <h3 class="font-h3 text-md text-on-surface line-clamp-1 mb-1">{c.get("product_name","")}</h3>
                        <p class="text-[10px] text-gray-500 mb-2">{sc_str}</p>
                        <p class="font-bold text-primary">{format_rupiah(c.get("price",0))}</p>
                    </div>
                </div>
                <div class="mt-auto pt-4 border-t border-gray-100 flex items-center justify-between">
                    <span class="text-xs text-gray-500">Stok: <b>{c.get('stock', 0)}</b></span>
                    <div class="flex items-center gap-2 bg-gray-50 rounded-lg p-1 border border-gray-200">
                        <button onclick="decrementQty({c['id']})" class="w-8 h-8 flex items-center justify-center rounded-md bg-white text-gray-500 hover:text-primary shadow-sm">-</button>
                        <input type="number" id="qty_{c['id']}" data-id="{c['id']}" data-price="{c['price']}" class="qty-input w-12 text-center bg-transparent border-none text-sm font-bold p-0 focus:ring-0" value="0" min="0" max="{c['stock']}" readonly />
                        <button onclick="incrementQty({c['id']}, {c['stock']})" class="w-8 h-8 flex items-center justify-center rounded-md bg-white text-gray-500 hover:text-primary shadow-sm">+</button>
                    </div>
                </div>
            </article>
            """

        catalog_html = f"""
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {cards}
        </div>
        """

        checkout_bar = """
        <div class="bg-primary-container/20 rounded-2xl border border-primary-container p-6 shadow-sm flex flex-col md:flex-row justify-between items-center gap-4">
            <div>
                <h3 class="font-bold text-lg text-on-surface">Ringkasan Pesanan B2B</h3>
                <div id="checkoutSummary" class="text-on-surface-variant font-medium mt-1">Belum ada barang dipilih</div>
            </div>
            <button id="checkoutBtn" onclick="submitOrder()" disabled class="bg-primary hover:bg-primary/90 text-white font-bold py-3 px-8 rounded-xl shadow-[0_4px_14px_rgba(135,78,88,0.39)] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2">
                <span class="material-symbols-outlined">shopping_cart_checkout</span>
                Pesan Sekarang
            </button>
        </div>
        """

html = html.replace("{SUPPLIER_OPTIONS}", supplier_options)
html = html.replace("{EMPTY_STATE}", empty_state)
html = html.replace("{SUPPLIER_INFO}", supplier_info)
html = html.replace("{CATALOG_HTML}", catalog_html)
html = html.replace("{CHECKOUT_BAR}", checkout_bar)

html = inject_seller_sidebar(html, "22_Pesan_Stok_Supplier", company_name)
action_data = render_original_html("pesan_stok_supplier_v2", html, height=1200)

if action_data:
    action = action_data.get("action")
    if action == "select_supplier":
        st.session_state["selected_supplier_id"] = action_data.get("supplier_id")
        st.rerun()
    elif action == "submit_order":
        items_str = action_data.get("items")
        if not items_str or not str(items_str).strip():
            st.error("Data pesanan kosong atau tidak valid.")
        else:
            try:
                items = json.loads(items_str)
            except json.JSONDecodeError:
                st.error("Data pesanan tidak valid.")
                items = []

            if items:
                # Fetch company ID
                company_id = user.get("company", {}).get("company_id")
                if company_id:
                    # Match to catalog to get prices
                    catalog_res, _ = get_api(
                        f"suppliers/{st.session_state['selected_supplier_id']}/catalog"
                    )
                    catalog = catalog_res.get("data", []) if catalog_res else []
                    cat_dict = {c["id"]: c["price"] for c in catalog}

                    order_items = []
                    for it in items:
                        order_items.append(
                            {
                                "catalog_id": it["id"],
                                "quantity": it["qty"],
                                "price": cat_dict[it["id"]],
                                "subtotal": it["qty"] * float(cat_dict[it["id"]]),
                            }
                        )

                    payload = {
                        "company_id": company_id,
                        "supplier_id": st.session_state["selected_supplier_id"],
                        "items": order_items,
                    }
                    order_res, status = post_api("suppliers/orders", payload)
                    if status in (200, 201):
                        # Reset
                        st.session_state["selected_supplier_id"] = ""
                        st.session_state["_supplier_order_success"] = True
                        st.switch_page("pages/23_Tagihan_Supplier.py")
                    else:
                        st.error(
                            f"Gagal memproses: {order_res.get('error') if order_res else 'Unknown'}"
                        )
                else:
                    st.error("Gagal mendapat ID perusahaan Anda.")

    elif action == "logout":
        st.session_state.clear()
        st.session_state["_auto_logout"] = True
        st.switch_page("app.py")
    else:
        from unified_sidebar import handle_seller_global_action

        handle_seller_global_action(st, action)
