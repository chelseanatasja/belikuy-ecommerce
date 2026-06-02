import streamlit as st
import sys, os, random, string
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from utils import require_login, hide_streamlit_ui, format_rupiah, post_api
from html_bridge import render_original_html
from unified_navbar import inject_navbar, handle_global_action

st.set_page_config(page_title="BeliKuy - Pembayaran", layout="wide", initial_sidebar_state="collapsed")
hide_streamlit_ui()
require_login()

# ── Guard: harus ada order pending ────────────────────────────────────────────
order_id      = st.session_state.get('pending_order_id')
method_id     = st.session_state.get('pending_payment_method')
total         = st.session_state.get('pending_total', 0)
method_name   = st.session_state.get('pending_payment_name', 'Transfer Bank')
method_type   = st.session_state.get('pending_payment_type', 'transfer')

if not order_id:
    st.switch_page("pages/6_Riwayat_Pesanan.py")

# ── Generate VA / rekening number deterministically dari order_id ─────────────
random.seed(order_id)
va_number = "8808" + "".join([str(random.randint(0,9)) for _ in range(12)])
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

# Tentukan instruksi berdasarkan tipe metode
is_ewallet = method_type and ('wallet' in method_type.lower() or 'fintech' in method_type.lower())
is_qr      = method_type and 'qr' in method_type.lower()

if is_qr or is_ewallet:
    payment_icon  = "qr_code_2"
    payment_label = "Kode QR / Dompet Digital"
    instructions  = [
        f"Buka aplikasi <strong>{method_name}</strong> di smartphone kamu",
        "Pilih menu <strong>Scan QR</strong> atau <strong>Bayar</strong>",
        f"Scan kode QR dan pastikan jumlah <strong>{format_rupiah(total)}</strong>",
        "Masukkan PIN dan konfirmasi pembayaran",
        "Klik tombol <strong>'Konfirmasi Sudah Bayar'</strong> di bawah ini",
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
        f"Pilih menu <strong>Transfer</strong> lalu masukkan nomor VA di bawah",
        f"Masukkan nominal <strong>persis</strong> {format_rupiah(total)} (sudah termasuk kode unik)",
        "Selesaikan transfer dan <strong>simpan bukti pembayaran</strong>",
        "Klik tombol <strong>'Konfirmasi Sudah Bayar'</strong> di bawah ini",
    ]
    account_block = (
        f'<div style="background:#f8f9fa;border-radius:16px;padding:20px;border:1.5px solid {BD};margin:20px 0;">'
        f'<p style="font-size:12px;color:{GRY};font-family:\'Inter\',sans-serif;margin:0 0 8px;text-transform:uppercase;letter-spacing:0.05em;">Nomor Virtual Account</p>'
        f'<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;">'
        f'<span style="font-family:\'Plus Jakarta Sans\',sans-serif;font-size:22px;font-weight:800;color:{TXT};letter-spacing:0.08em;">{virtual_account}</span>'
        f'<button onclick="navigator.clipboard.writeText(\'{va_number}\').then(()=>this.textContent=\'Tersalin!\').catch(()=>{{}})" '
        f'style="border:1.5px solid #e1e3e4;background:white;padding:6px 14px;border-radius:20px;font-size:12px;font-weight:600;cursor:pointer;font-family:\'Inter\',sans-serif;color:{MUT};">'
        f'<span class="material-symbols-outlined" style="font-size:13px;vertical-align:middle;">content_copy</span> Salin</button>'
        f'</div>'
        f'<p style="font-size:12px;color:{GRY};font-family:\'Inter\',sans-serif;margin:8px 0 0;">Bank: <strong style="color:{TXT};">{method_name}</strong></p>'
        f'</div>'
    )

# Steps HTML
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
    "<title>BeliKuy - Pembayaran</title>"
    "<script src='https://cdn.tailwindcss.com?plugins=forms,container-queries'></script>"
    "<link href='https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Plus+Jakarta+Sans:wght@500;600;700;800;900&display=swap' rel='stylesheet'/>"
    "<link href='https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap' rel='stylesheet'/>"
    "<style>*{box-sizing:border-box;margin:0;padding:0;}body{font-family:'Inter',sans-serif;background:#f8f9fa;min-height:100vh;padding-bottom:40px;}::-webkit-scrollbar{display:none;}</style>"
    "</head><body>"

    "<div style='max-width:560px;margin:0 auto;padding:84px 16px 40px;'>"

    # Header card
    f"<div style='background:white;border-radius:20px;box-shadow:0 2px 16px rgba(135,78,88,0.10);border:1px solid {BD};overflow:hidden;margin-bottom:16px;'>"

    # Status bar - orange/amber for pending
    f"<div style='background:linear-gradient(135deg,#fff7ed,#fef3c7);padding:16px 20px;border-bottom:1px solid #fed7aa;display:flex;align-items:center;gap:12px;'>"
    f"<span class='material-symbols-outlined' style='font-size:24px;color:#d97706;font-variation-settings:\"FILL\" 1;'>pending</span>"
    f"<div>"
    f"<p style='font-family:\"Plus Jakarta Sans\",sans-serif;font-size:14px;font-weight:700;color:#92400e;margin:0;'>Menunggu Pembayaran</p>"
    f"<p style='font-family:\"Inter\",sans-serif;font-size:12px;color:#b45309;margin:2px 0 0;'>Order #{order_id} &middot; Bayar sebelum {expire_str}</p>"
    f"</div>"
    f"</div>"

    # Total amount
    f"<div style='padding:20px;border-bottom:1px solid {BD};'>"
    f"<p style='font-family:\"Inter\",sans-serif;font-size:12px;color:{GRY};margin:0 0 4px;text-transform:uppercase;letter-spacing:0.05em;'>Total Pembayaran</p>"
    f"<p style='font-family:\"Plus Jakarta Sans\",sans-serif;font-size:28px;font-weight:800;color:{P};margin:0;'>{format_rupiah(total)}</p>"
    f"<p style='font-family:\"Inter\",sans-serif;font-size:12px;color:{GRY};margin:4px 0 0;'>via {method_name} &middot; {payment_label}</p>"
    f"</div>"

    # VA / QR block
    f"<div style='padding:0 20px;'>{account_block}</div>"

    f"</div>"  # end header card

    # Instructions card
    f"<div style='background:white;border-radius:20px;box-shadow:0 2px 16px rgba(135,78,88,0.08);border:1px solid {BD};overflow:hidden;margin-bottom:16px;'>"
    f"<div style='padding:16px 20px;border-bottom:1px solid {BD};display:flex;align-items:center;gap:8px;'>"
    f"<span class='material-symbols-outlined' style='font-size:20px;color:{P};'>checklist</span>"
    f"<h2 style='font-family:\"Plus Jakarta Sans\",sans-serif;font-size:15px;font-weight:700;color:{TXT};margin:0;'>Cara Pembayaran</h2>"
    f"</div>"
    f"<div style='padding:4px 20px 8px;'>{steps_html}</div>"
    f"</div>"

    # Confirm button card
    f"<div style='background:white;border-radius:20px;box-shadow:0 2px 16px rgba(135,78,88,0.08);border:1px solid {BD};padding:20px;margin-bottom:16px;'>"

    f"<button onclick=\"stNavigate({{action:'confirm_payment'}})\""
    f" style='width:100%;background:linear-gradient(135deg,#22c55e,#16a34a);color:white;border:none;padding:16px;"
    f"border-radius:16px;font-family:\"Plus Jakarta Sans\",sans-serif;font-size:15px;font-weight:800;cursor:pointer;"
    f"display:flex;align-items:center;justify-content:center;gap:8px;margin-bottom:10px;'>"
    f"<span class='material-symbols-outlined' style='font-size:20px;'>check_circle</span>"
    f"Konfirmasi Sudah Bayar</button>"

    f"<button onclick=\"stNavigate({{action:'cancel_payment'}})\""
    f" style='width:100%;background:transparent;color:{GRY};border:1.5px solid {BD};padding:12px;"
    f"border-radius:16px;font-family:\"Inter\",sans-serif;font-size:13px;font-weight:600;cursor:pointer;'>"
    f"Batalkan Pesanan</button>"

    f"</div>"  # end confirm card

    # Note
    f"<p style='font-family:\"Inter\",sans-serif;font-size:12px;color:{GRY};text-align:center;line-height:1.6;'>"
    f"Pesanan akan otomatis dibatalkan jika pembayaran tidak dilakukan sebelum {expire_str}.<br/>"
    f"Hubungi CS BeliKuy jika ada kendala pembayaran."
    f"</p>"

    "</div></body></html>"
)

page_html = inject_navbar(page_html, 0)
action_data = render_original_html("belikuy_v2_payment", page_html, height=900)

if action_data:
    act = action_data.get('action', '')
    current_user = st.session_state.get('user')
    if handle_global_action(st, act, action_data, current_user):
        pass
    elif act == "confirm_payment":
        # Panggil endpoint pembayaran
        res, status = post_api("payments/pay", {
            "order_id":          order_id,
            "payment_method_id": method_id
        })
        if status == 200 or (isinstance(res, dict) and res.get('success')):
            # Bersihkan session pending
            for k in ['pending_order_id','pending_payment_method','pending_total',
                      'pending_payment_name','pending_payment_type']:
                st.session_state.pop(k, None)
            st.session_state['order_success'] = True
            st.session_state['last_order_id'] = order_id
            st.success("Pembayaran berhasil dikonfirmasi!")
            st.switch_page("pages/6_Riwayat_Pesanan.py")
        else:
            st.error("Gagal memproses pembayaran, coba lagi.")
            st.rerun()
    elif act == "cancel_payment":
        from utils import put_api
        try:
            put_api(f"orders/{order_id}/status", {"status": "cancelled", "user_id": current_user['id']})
        except: pass
        for k in ['pending_order_id','pending_payment_method','pending_total',
                  'pending_payment_name','pending_payment_type']:
            st.session_state.pop(k, None)
        st.warning("Pesanan dibatalkan.")
        st.switch_page("pages/6_Riwayat_Pesanan.py")
    elif act == "go_orders":
        st.switch_page("pages/6_Riwayat_Pesanan.py")
