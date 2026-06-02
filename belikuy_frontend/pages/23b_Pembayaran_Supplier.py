import streamlit as st
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from utils import require_login, require_role, hide_streamlit_ui, format_rupiah, post_api
from html_bridge import render_original_html

st.set_page_config(page_title="BeliKuy B2B - Pembayaran", layout="wide", initial_sidebar_state="collapsed")
hide_streamlit_ui()
require_login()
user = st.session_state['user']
require_role("seller")
company_id = user.get('company', {}).get('company_id')

# ── Guard: harus ada order pending ────────────────────────────────────────────
order_id      = st.session_state.get('_b2b_pending_order_id')
method_name   = st.session_state.get('_b2b_pending_method')
total         = st.session_state.get('_b2b_pending_total', 0)
method_type   = st.session_state.get('_b2b_pending_method_type', 'Bank')

if not order_id:
    st.switch_page("pages/23_Tagihan_Supplier.py")

# ── Generate VA / rekening number deterministically dari order_id ─────────────
random.seed(order_id)
va_number = "9988" + "".join([str(random.randint(0,9)) for _ in range(12)])
virtual_account = f"{va_number[:4]} {va_number[4:8]} {va_number[8:12]} {va_number[12:]}"

# Expiry: 24 jam
from datetime import datetime, timedelta
expire_time = datetime.now() + timedelta(hours=24)
expire_str  = expire_time.strftime("%d %b %Y, %H:%M WIB")

# ── Build page ─────────────────────────────────────────────────────────────────
P   = "#874e58"
BD  = "#f3f4f5"
TXT = "#191c1d"
MUT = "#514345"
GRY = "#847375"

is_ewallet = method_type and ('wallet' in method_type.lower() or 'fintech' in method_type.lower())
is_qr      = method_type and 'qr' in method_type.lower()

if is_qr or is_ewallet:
    payment_icon  = "qr_code_2"
    payment_label = "Kode QR / Dompet Digital"
    instructions  = [
        f"Buka aplikasi <strong>{method_name}</strong> di smartphone kamu",
        "Pilih menu <strong>Scan QR</strong> atau <strong>Bayar</strong>",
        f"Scan kode QR dan pastikan jumlah tagihan <strong>{format_rupiah(total)}</strong>",
        "Masukkan PIN dan konfirmasi pembayaran tagihan grosir",
        "Klik tombol <strong>'Konfirmasi Pembayaran B2B'</strong> di bawah ini",
    ]
    account_block = (
        '<div style="background:#f0fdf4;border-radius:16px;padding:20px;border:1.5px solid #bbf7d0;text-align:center;margin:20px 0;">'
        '<span class="material-symbols-outlined" style="font-size:80px;color:#22c55e;">qr_code_2</span>'
        f'<p style="font-size:13px;color:#15803d;font-weight:600;margin:8px 0 0;">Scan via {method_name}</p>'
        '</div>'
    )
else:
    payment_icon  = "account_balance"
    payment_label = "Transfer Bank / Virtual Account"
    instructions  = [
        f"Buka aplikasi <strong>mobile banking</strong> atau <strong>ATM</strong>",
        f"Pilih menu <strong>Transfer</strong> lalu masukkan nomor VA B2B di bawah",
        f"Masukkan nominal <strong>persis</strong> {format_rupiah(total)} (sudah termasuk kode unik)",
        "Selesaikan transfer dan <strong>simpan bukti pembayaran</strong>",
        "Klik tombol <strong>'Konfirmasi Pembayaran B2B'</strong> di bawah ini",
    ]
    account_block = (
        f'<div style="background:#f8f9fa;border-radius:16px;padding:20px;border:1.5px solid {BD};margin:20px 0;">'
        f'<p style="font-size:12px;color:{GRY};font-family:\'Inter\',sans-serif;margin:0 0 8px;text-transform:uppercase;letter-spacing:0.05em;">Nomor Virtual Account B2B</p>'
        f'<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;">'
        f'<span style="font-family:\'Plus Jakarta Sans\',sans-serif;font-size:22px;font-weight:800;color:{TXT};letter-spacing:0.08em;">{virtual_account}</span>'
        f'<button onclick="navigator.clipboard.writeText(\'{va_number}\').then(()=>this.textContent=\'Tersalin!\').catch(()=>{{}})" '
        f'style="border:1.5px solid #e1e3e4;background:white;padding:6px 14px;border-radius:20px;font-size:12px;font-weight:600;cursor:pointer;font-family:\'Inter\',sans-serif;color:{MUT};">'
        f'<span class="material-symbols-outlined" style="font-size:13px;vertical-align:middle;">content_copy</span> Salin</button>'
        f'</div>'
        f'<p style="font-size:12px;color:{GRY};font-family:\'Inter\',sans-serif;margin:8px 0 0;">Bank: <strong style="color:{TXT};">{method_name}</strong></p>'
        f'</div>'
    )

steps_html = ""
for i, step in enumerate(instructions, 1):
    steps_html += (
        f'<div style="display:flex;align-items:flex-start;gap:14px;padding:12px 0;border-bottom:1px solid {BD};">'
        f'<div style="width:28px;height:28px;border-radius:50%;background:linear-gradient(135deg,#ffb6c1,#c084fc);'
        f'display:flex;align-items:center;justify-content:center;flex-shrink:0;">'
        f'<span style="font-family:\'Plus Jakarta Sans\',sans-serif;font-size:12px;font-weight:800;color:white;">{i}</span>'
        f'</div>'
        f'<p style="font-family:\'Inter\',sans-serif;font-size:14px;color:{MUT};line-height:1.5;margin:4px 0 0;">{step}</p>'
        f'</div>'
    )

page_html = (
    "<!DOCTYPE html><html lang='id'><head>"
    "<meta charset='utf-8'/><meta name='viewport' content='width=device-width, initial-scale=1.0'/>"
    "<title>BeliKuy B2B - Pembayaran</title>"
    "<script src='https://cdn.tailwindcss.com?plugins=forms,container-queries'></script>"
    "<link href='https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Plus+Jakarta+Sans:wght@500;600;700;800;900&display=swap' rel='stylesheet'/>"
    "<link href='https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap' rel='stylesheet'/>"
    "<style>*{box-sizing:border-box;margin:0;padding:0;}body{font-family:'Inter',sans-serif;background:#f8f9fa;min-height:100vh;padding-bottom:40px;}::-webkit-scrollbar{display:none;}</style>"
    "</head><body>"
    "<div style='max-width:560px;margin:0 auto;padding:40px 16px 40px;'>"
    f"<div style='background:white;border-radius:20px;box-shadow:0 2px 16px rgba(135,78,88,0.10);border:1px solid {BD};overflow:hidden;margin-bottom:16px;'>"
    f"<div style='background:linear-gradient(135deg,#fff7ed,#fef3c7);padding:16px 20px;border-bottom:1px solid #fed7aa;display:flex;align-items:center;gap:12px;'>"
    f"<span class='material-symbols-outlined' style='font-size:24px;color:#d97706;font-variation-settings:\"FILL\" 1;'>pending</span>"
    f"<div>"
    f"<p style='font-family:\"Plus Jakarta Sans\",sans-serif;font-size:14px;font-weight:700;color:#92400e;margin:0;'>Menunggu Pembayaran B2B</p>"
    f"<p style='font-family:\"Inter\",sans-serif;font-size:12px;color:#b45309;margin:2px 0 0;'>Tagihan #{order_id} &middot; Bayar sebelum {expire_str}</p>"
    f"</div>"
    f"</div>"
    f"<div style='padding:20px;border-bottom:1px solid {BD};'>"
    f"<p style='font-family:\"Inter\",sans-serif;font-size:12px;color:{GRY};margin:0 0 4px;text-transform:uppercase;letter-spacing:0.05em;'>Total Tagihan Grosir</p>"
    f"<p style='font-family:\"Plus Jakarta Sans\",sans-serif;font-size:28px;font-weight:800;color:{P};margin:0;'>{format_rupiah(total)}</p>"
    f"<p style='font-family:\"Inter\",sans-serif;font-size:12px;color:{GRY};margin:4px 0 0;'>via {method_name} &middot; {payment_label}</p>"
    f"</div>"
    f"<div style='padding:0 20px;'>{account_block}</div>"
    f"</div>"
    f"<div style='background:white;border-radius:20px;box-shadow:0 2px 16px rgba(135,78,88,0.08);border:1px solid {BD};overflow:hidden;margin-bottom:16px;'>"
    f"<div style='padding:16px 20px;border-bottom:1px solid {BD};display:flex;align-items:center;gap:8px;'>"
    f"<span class='material-symbols-outlined' style='font-size:20px;color:{P};'>checklist</span>"
    f"<h2 style='font-family:\"Plus Jakarta Sans\",sans-serif;font-size:15px;font-weight:700;color:{TXT};margin:0;'>Cara Pembayaran</h2>"
    f"</div>"
    f"<div style='padding:4px 20px 8px;'>{steps_html}</div>"
    f"</div>"
    f"<div style='background:white;border-radius:20px;box-shadow:0 2px 16px rgba(135,78,88,0.08);border:1px solid {BD};padding:20px;margin-bottom:16px;'>"
    f"<button onclick=\"stNavigate({{action:'confirm_payment'}})\""
    f" style='width:100%;background:linear-gradient(135deg,#22c55e,#16a34a);color:white;border:none;padding:16px;"
    f"border-radius:16px;font-family:\"Plus Jakarta Sans\",sans-serif;font-size:15px;font-weight:800;cursor:pointer;"
    f"display:flex;align-items:center;justify-content:center;gap:8px;margin-bottom:10px;'>"
    f"<span class='material-symbols-outlined' style='font-size:20px;'>check_circle</span>"
    f"Konfirmasi Pembayaran B2B</button>"
    f"<button onclick=\"stNavigate({{action:'cancel_payment'}})\""
    f" style='width:100%;background:transparent;color:{GRY};border:1.5px solid {BD};padding:12px;"
    f"border-radius:16px;font-family:\"Inter\",sans-serif;font-size:13px;font-weight:600;cursor:pointer;'>"
    f"Kembali (Tunda Bayar)</button>"
    f"</div>"
    f"<p style='font-family:\"Inter\",sans-serif;font-size:12px;color:{GRY};text-align:center;line-height:1.6;'>"
    f"Tagihan B2B akan dibatalkan otomatis jika tidak dibayar sebelum {expire_str}.<br/>"
    f"Hubungi Tim Support Grosir jika ada kendala."
    f"</p>"
    "</div></body></html>"
)

action_data = render_original_html("belikuy_b2b_payment", page_html, height=900)

if action_data:
    act = action_data.get('action', '')
    if act == "confirm_payment":
        # Call API
        payload = {
            "supplier_order_id": order_id,
            "company_id": company_id,
            "amount": total,
            "payment_method": method_name
        }
        res, status = post_api("payments/supplier_pay", payload)
        if status in (200, 201):
            for k in ['_b2b_pending_order_id','_b2b_pending_method','_b2b_pending_total','_b2b_pending_method_type']:
                st.session_state.pop(k, None)
            st.session_state['_supplier_pay_success'] = True
            st.switch_page("pages/23_Tagihan_Supplier.py")
        else:
            st.error("Gagal memproses pembayaran, coba lagi.")
            st.session_state['_supplier_pay_error'] = res.get("error") if res else "Unknown Error"
            st.switch_page("pages/23_Tagihan_Supplier.py")
    elif act == "cancel_payment":
        for k in ['_b2b_pending_order_id','_b2b_pending_method','_b2b_pending_total','_b2b_pending_method_type']:
            st.session_state.pop(k, None)
        st.switch_page("pages/23_Tagihan_Supplier.py")
