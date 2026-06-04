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
from unified_sidebar import inject_seller_sidebar
from html_bridge import render_original_html

st.set_page_config(
    page_title="Tagihan Supplier", layout="wide", initial_sidebar_state="collapsed"
)
hide_streamlit_ui()
require_login()
user = st.session_state["user"]
require_role("seller")
company_name = user.get("company", {}).get("company_name", "Toko Anda")

HTML_BASE = (
    r"D:\Tugas Kuliah\Semester 4\Workshop RPL\belikuy-ecommerce\belikuy_ui_templates"
)
with open(os.path.join(HTML_BASE, "b2b_billing/code.html"), encoding="utf-8") as f:
    html = f.read()

company_id = user.get("company", {}).get("company_id")
if not company_id:
    st.error("Gagal mendapatkan data Toko Anda.")
    st.stop()

orders_res, _ = get_api(f"suppliers/orders/{company_id}")
orders = orders_res.get("data", []) if orders_res else []

pending_orders = [o for o in orders if o["status"] == "pending"]
paid_orders = [
    o for o in orders if o["status"] in ["paid", "shipped", "completed", "cancelled"]
]

success_alert = ""
if st.session_state.get("_supplier_order_success"):
    st.session_state.pop("_supplier_order_success")
    success_alert = "<div class='bg-green-50 text-green-800 p-4 rounded-xl border border-green-200 mb-6'>✅ Pesanan B2B berhasil dibuat! Silakan lunasi tagihannya di bawah ini.</div>"
elif st.session_state.get("_supplier_pay_success"):
    st.session_state.pop("_supplier_pay_success")
    success_alert = "<div class='bg-green-50 text-green-800 p-4 rounded-xl border border-green-200 mb-6'>✅ Pembayaran berhasil! Tagihan Anda telah lunas.</div>"
elif st.session_state.get("_supplier_pay_error"):
    err = st.session_state.pop("_supplier_pay_error")
    success_alert = f"<div class='bg-red-50 text-red-800 p-4 rounded-xl border border-red-200 mb-6'>❌ Pembayaran gagal: {err}</div>"
elif st.session_state.get("_supplier_receive_success"):
    st.session_state.pop("_supplier_receive_success")
    success_alert = "<div class='bg-green-50 text-green-800 p-4 rounded-xl border border-green-200 mb-6'>✅ Pesanan grosir telah diterima! Stok otomatis ditambahkan ke etalase Anda.</div>"
elif st.session_state.get("_supplier_receive_error"):
    err = st.session_state.pop("_supplier_receive_error")
    success_alert = f"<div class='bg-red-50 text-red-800 p-4 rounded-xl border border-red-200 mb-6'>❌ Penerimaan gagal: {err}</div>"

# Fetch Payment Methods
methods_res, _ = get_api("payments/methods")
methods = methods_res if methods_res else []
method_options = '<option value="">-- Pilih --</option>'
for m in methods:
    method_options += f'<option value="{m["institution_name"]}">{m["institution_name"]} ({m["institution_type"]})</option>'

# Build Pending HTML
pending_html = ""
if not pending_orders:
    pending_html = "<div class='bg-green-50/50 p-8 rounded-2xl text-center text-green-700'><span class='material-symbols-outlined text-4xl mb-2'>sentiment_satisfied</span><p>Hore! Tidak ada tagihan yang belum lunas.</p></div>"
else:
    for order in pending_orders:
        items_html = ""
        for item in order["items"]:
            subtotal = float(item["quantity"]) * float(item["price"])
            items_html += f"<li class='flex justify-between py-2 border-b border-gray-100 last:border-0'><span class='text-gray-600'>{item['item_name']} (x{item['quantity']})</span><span class='font-semibold'>{format_rupiah(subtotal)}</span></li>"

        pending_html += f"""
        <div class="bg-surface-container-lowest border border-gray-200 rounded-2xl overflow-hidden shadow-sm">
            <div class="p-4 md:p-6 flex items-center justify-between cursor-pointer hover:bg-gray-50 transition-colors" onclick="toggleAccordion({order['id']})">
                <div class="flex items-center gap-4">
                    <div class="w-12 h-12 rounded-xl bg-orange-100 text-orange-600 flex items-center justify-center">
                        <span class="material-symbols-outlined">receipt_long</span>
                    </div>
                    <div>
                        <p class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Tagihan #{order['id']}</p>
                        <h3 class="font-h3 text-lg">{order['supply_company_name']}</h3>
                    </div>
                </div>
                <div class="flex items-center gap-4">
                    <div class="text-right hidden md:block">
                        <p class="text-xs text-gray-500 mb-1">Total Tagihan</p>
                        <p class="font-bold text-error">{format_rupiah(float(order['total_price']))}</p>
                    </div>
                    <span id="acc_icon_{order['id']}" class="accordion-icon material-symbols-outlined text-gray-400">expand_more</span>
                </div>
            </div>
            
            <div id="acc_content_{order['id']}" class="accordion-content bg-gray-50/50 border-t border-gray-100">
                <div class="p-4 md:p-6 flex flex-col md:flex-row gap-8">
                    <div class="flex-1">
                        <h4 class="font-bold text-sm mb-4">Rincian Pemesanan</h4>
                        <ul class="text-sm">
                            {items_html}
                        </ul>
                    </div>
                    <div class="w-full md:w-64 bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex flex-col justify-center">
                        <p class="text-sm font-bold mb-2">Metode Pembayaran</p>
                        <select id="pay_method_{order['id']}" class="w-full bg-gray-50 border-gray-300 rounded-lg text-sm focus:ring-primary-container mb-4">
                            {method_options}
                        </select>
                        <button onclick="payBill({order['id']})" class="w-full bg-primary hover:bg-primary/90 text-white font-bold py-2 rounded-lg transition-colors flex items-center justify-center gap-2">
                            <span class="material-symbols-outlined text-[18px]">payments</span> Lunasi
                        </button>
                    </div>
                </div>
            </div>
        </div>
        """

# Build Paid HTML
paid_html = ""
if not paid_orders:
    paid_html = "<div class='bg-gray-50 p-8 rounded-2xl text-center text-gray-500'><p>Belum ada tagihan lunas.</p></div>"
else:
    for order in paid_orders:
        items_html = ""
        for item in order["items"]:
            items_html += f"<li class='flex justify-between py-1'><span class='text-gray-500'>{item['item_name']} (x{item['quantity']})</span></li>"

        action_btn_html = ""
        if order["status"] == "shipped":
            action_btn_html = f"""
            <button onclick="stNavigate({{action:'receive_order', order_id:{order['id']}}})" class="mt-4 w-full md:w-auto bg-primary text-white font-semibold text-xs px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors shadow-sm flex items-center justify-center gap-2">
                <span class="material-symbols-outlined text-[16px]">inventory_2</span> Terima Pesanan
            </button>
            """

        paid_html += f"""
        <div class="bg-surface-container-lowest border border-gray-200 rounded-2xl p-4 md:p-6 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div class="flex items-center gap-4">
                <div class="w-10 h-10 rounded-full bg-green-100 text-green-600 flex items-center justify-center">
                    <span class="material-symbols-outlined text-[20px]">check_circle</span>
                </div>
                <div>
                    <h3 class="font-bold">{order['supply_company_name']}</h3>
                    <p class="text-xs text-gray-500">#{order['id']} &bull; Pembayaran Berhasil</p>
                </div>
            </div>
            <div class="w-full md:w-auto flex-1">
                <ul class="text-xs bg-gray-50 p-3 rounded-lg border border-gray-100 mb-2 md:mb-0">
                    {items_html}
                </ul>
            </div>
            <div class="text-right w-full md:w-auto mt-2 md:mt-0 md:ml-4">
                <p class="font-bold text-green-700">{format_rupiah(float(order['total_price']))}</p>
                <span class="inline-block px-2 py-0.5 bg-green-100 text-green-800 text-[10px] font-bold rounded uppercase tracking-wider mt-1">{order['status']}</span>
                {action_btn_html}
            </div>
        </div>
        """

html = html.replace("{SUCCESS_ALERT}", success_alert)
html = html.replace("{PENDING_HTML}", pending_html)
html = html.replace("{PAID_HTML}", paid_html)

html = inject_seller_sidebar(html, "23_Tagihan_Supplier", company_name)
action_data = render_original_html("tagihan_supplier_v2", html, height=1200)

if action_data:
    action = action_data.get("action")
    if action == "pay_bill":
        order_id = action_data.get("order_id")
        method = action_data.get("method")

        # Find order amount
        amt = 0
        for o in pending_orders:
            if str(o["id"]) == str(order_id):
                amt = o["total_price"]
                break

        # Store to session and redirect
        st.session_state["_b2b_pending_order_id"] = order_id
        st.session_state["_b2b_pending_method"] = method
        st.session_state["_b2b_pending_total"] = amt

        m_type = "transfer"
        for m in methods:
            if m["institution_name"] == method:
                m_type = m["institution_type"]
                break
        st.session_state["_b2b_pending_method_type"] = m_type

        st.switch_page("pages/23b_Pembayaran_Supplier.py")
    elif action == "receive_order":
        from utils import put_api

        order_id = action_data.get("order_id")
        res, status = put_api(
            f"suppliers/orders/{order_id}/receive", {"company_id": company_id}
        )
        if status in (200, 201):
            st.session_state["_supplier_receive_success"] = True
            st.rerun()
        else:
            st.session_state["_supplier_receive_error"] = (
                res.get("error") if res else "Unknown Error"
            )
            st.rerun()
    elif action == "logout":
        st.session_state.clear()
        st.session_state["_auto_logout"] = True
        st.switch_page("app.py")
    else:
        from unified_sidebar import handle_seller_global_action

        handle_seller_global_action(st, action)
