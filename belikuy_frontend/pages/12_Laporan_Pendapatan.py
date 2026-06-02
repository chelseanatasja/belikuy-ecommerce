import streamlit as st
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from utils import get_api, post_api, require_role, hide_streamlit_ui, format_rupiah
from html_bridge import render_original_html
from unified_sidebar import inject_seller_sidebar, handle_seller_global_action

st.set_page_config(page_title="BeliKuy - Laporan Pendapatan", layout="wide", initial_sidebar_state="collapsed")
hide_streamlit_ui()
require_role("seller")

user = st.session_state['user']
company = user.get('company', {}); company_id = company.get('company_id') if company else None

income, _ = get_api(f"companies/{company_id}/income")
recent_orders, _ = get_api(f"companies/{company_id}/orders")
withdrawals, _ = get_api(f"withdrawals/{company_id}")
if not income: income = {}
if not recent_orders: recent_orders = []
if not withdrawals: withdrawals = []

total_omzet = income.get('total_omzet', 0) or 0
total_pesanan = income.get('total_pesanan', 0) or 0
avg_order = float(total_omzet) / int(total_pesanan) if total_pesanan else 0

# Saldo = omzet - total withdrawal yg sudah diproses/selesai (bukan pending/rejected)
total_withdrawn = sum(
    float(w.get('amount', 0) or 0)
    for w in withdrawals
    if w.get('status', '') in ('processed', 'completed')
)
saldo_saat_ini = float(total_omzet) - total_withdrawn


HTML_BASE = r"D:\belikuy\belikuy_ui_templates"
with open(os.path.join(HTML_BASE, "seller_income_report/code.html"), encoding='utf-8') as f:
    html = f.read()

# ── Replace stat cards with real data ────────────────────────────────────────
# Saldo card: font-h1 (Rp 12.450.000) → saldo_saat_ini
html = re.sub(
    r'(font-h1 text-h1 text-on-background mt-md">)Rp 12\.450\.000(</p>)',
    rf'\g<1>{format_rupiah(saldo_saat_ini)}\2', html
)
# Rata-rata per Pesanan card: font-h2 (Rp 8.200.000 or Rp 12.450.000 jika berbeda) → avg_order
html = html.replace('Rp 8.200.000', format_rupiah(avg_order))
# Label dan subtext
html = html.replace('Pendapatan Bulan Ini', 'Rata-rata per Pesanan')
html = html.replace('+15% dari bulan lalu', 'Nilai rata-rata transaksi')
# Total Transaksi card
html = html.replace('Rp 45.000.000', str(total_pesanan))
html = html.replace('Total Penarikan', 'Total Transaksi')
html = html.replace('Sejak akun dibuat', 'Pesanan selesai')
# Saldo subtext
html = html.replace('Siap ditarik ke rekening utama',
                    f'Sudah ditarik: <strong>{format_rupiah(total_withdrawn)}</strong>')


# ── Replace hardcoded weekly bar chart with real monthly data from DB ─────────
monthly_omzet = income.get('monthly_omzet', [])
month_map = {"01":"Jan","02":"Feb","03":"Mar","04":"Apr","05":"Mei","06":"Jun",
             "07":"Jul","08":"Ags","09":"Sep","10":"Okt","11":"Nov","12":"Des"}

if monthly_omzet:
    max_val = max(float(m.get('omzet', 0)) for m in monthly_omzet) or 1
    display = monthly_omzet[-8:]  # last 8 months
    bars = ""
    for m in display:
        val = float(m.get('omzet', 0))
        h_pct = max(8, int((val / max_val) * 100))
        mon = m.get('month', '')
        parts = mon.split('-')
        month_str = parts[1] if len(parts) > 1 else mon
        year_str = parts[0][2:] if len(parts) > 0 else ''
        label = f"{month_map.get(month_str, month_str)} '{year_str}"
        is_peak = val == max_val and val > 0
        col = "bg-primary" if is_peak else "bg-primary/40 hover:bg-primary/70"
        bars += f'''
        <div class="flex flex-col items-center gap-1 flex-1">
            <div class="w-full flex items-end justify-center" style="height:120px">
                <div class="{col} rounded-t-md w-full transition-colors relative group cursor-default" style="height:{h_pct}%">
                    <span class="absolute -top-7 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 bg-surface-variant text-on-surface font-label-caps text-[9px] px-2 py-1 rounded transition-opacity whitespace-nowrap z-10">
                        {format_rupiah(val)}
                    </span>
                </div>
            </div>
            <span class="text-[10px] text-on-surface-variant font-medium">{label}</span>
        </div>'''
    real_chart = f'''
<div class="w-full rounded-lg bg-gradient-to-t from-primary-container/10 to-transparent relative mt-4 flex items-end gap-2 px-md pb-md" style="min-height:150px">
    {bars}
</div>'''
else:
    real_chart = '<div class="w-full h-40 flex items-center justify-center text-sm text-on-surface-variant rounded-lg bg-surface-container-low mt-4">Belum ada data pendapatan</div>'

# Replace the entire static chart div (weekday bars) with real data
html = re.sub(
    r'<div class="w-full h-64 rounded-lg bg-gradient-to-t from-primary-container/20 to-transparent relative mt-4 flex items-end justify-between px-md pb-md">.*?</div>\s*</section>',
    real_chart + '\n</section>',
    html, flags=re.DOTALL, count=1
)
# Remove weekly/monthly toggle buttons (now always monthly)
html = re.sub(
    r'<div class="flex bg-surface-container-low rounded-lg p-1">.*?</div>',
    '<span class="font-body-sm text-body-sm text-on-surface-variant">Bulanan (dari DB)</span>',
    html, flags=re.DOTALL, count=1
)


# ── Wire "Tarik Dana" button ─────────────────────────────────────────────────
html = html.replace(
    '<button class="bg-primary hover:bg-primary-container text-on-primary hover:text-on-primary-container font-label-caps text-label-caps px-lg py-md rounded-full shadow-glow transition-all flex items-center gap-2">',
    '<button onclick="openWithdrawModal()" class="bg-primary hover:bg-primary-container text-on-primary hover:text-on-primary-container font-label-caps text-label-caps px-lg py-md rounded-full shadow-glow transition-all flex items-center gap-2">'
)

# ── Build Riwayat Penarikan table rows ───────────────────────────────────────
status_map = {
    'pending':   ('<span class="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-yellow-100 text-yellow-700 font-label-caps text-[10px]"><span class="w-1.5 h-1.5 rounded-full bg-yellow-400"></span>Menunggu</span>'),
    'processed': ('<span class="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-tertiary-container/40 text-tertiary font-label-caps text-[10px]"><span class="w-1.5 h-1.5 rounded-full bg-tertiary"></span>Diproses</span>'),
    'completed': ('<span class="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-primary-container/30 text-on-primary-container font-label-caps text-[10px]"><span class="w-1.5 h-1.5 rounded-full bg-primary"></span>Selesai</span>'),
    'rejected':  ('<span class="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-error-container/50 text-error font-label-caps text-[10px]"><span class="w-1.5 h-1.5 rounded-full bg-error"></span>Ditolak</span>'),
}

rows = ""
if withdrawals:
    for w in withdrawals[:10]:
        st_badge = status_map.get(w.get('status', 'pending'), status_map['pending'])
        bank_code = (w.get('bank_name', 'BANK') or 'BANK')[:3].upper()
        rows += f'''
        <tr class="border-b border-surface-container-low hover:bg-surface-bright transition-colors">
            <td class="p-md">{str(w.get("created_at",""))[:16]}</td>
            <td class="p-md font-medium">{format_rupiah(w.get("amount",0))}</td>
            <td class="p-md">
                <div class="flex items-center gap-2">
                    <div class="w-6 h-6 rounded bg-surface-container-high flex items-center justify-center text-[10px] font-bold text-on-surface">{bank_code}</div>
                    {w.get("bank_name","")} — {w.get("account_number","")}
                </div>
            </td>
            <td class="p-md">{st_badge}</td>
        </tr>'''
else:
    rows = '<tr><td colspan="4" class="p-md text-center text-on-surface-variant py-8">Belum ada riwayat penarikan dana.</td></tr>'

html = re.sub(
    r'(<tbody class="font-body-sm text-body-sm text-on-background">)(.*?)(</tbody>)',
    rf'\1{rows}\3', html, flags=re.DOTALL
)

# ── Remove Tailwind forms plugin (double arrow) ──────────────────────────────
html = html.replace(
    'src="https://cdn.tailwindcss.com?plugins=forms,container-queries"',
    'src="https://cdn.tailwindcss.com?plugins=container-queries"'
)

company_name = user.get('company', {}).get('company_name', 'Toko Saya')
html = inject_seller_sidebar(html, "12_Laporan_Pendapatan", company_name)

# ── Modal Tarik Dana ──────────────────────────────────────────────────────────
withdraw_modal = f'''
<div id="withdrawModal" class="fixed inset-0 bg-black/40 backdrop-blur-sm z-[200] hidden items-start pt-20 justify-center p-4 flex">
    <div class="bg-white rounded-2xl w-full max-w-md p-8 shadow-2xl relative">
        <button onclick="closeWithdrawModal()" type="button" class="absolute top-5 right-5 text-gray-400 hover:text-red-500 transition-colors p-1">
            <span class="material-symbols-outlined">close</span>
        </button>
        <h2 class="text-2xl font-bold text-on-background mb-2">Tarik Dana</h2>
        <p class="text-sm text-on-surface-variant mb-6">Total Omzet: <strong>{format_rupiah(total_omzet)}</strong></p>
        <div class="space-y-4">
            <div>
                <label class="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Jumlah Penarikan (Rp) *</label>
                <input id="w_amount" type="number" min="10000" max="{int(float(total_omzet or 0))}"
                    class="w-full bg-gray-50 border border-gray-200 rounded-xl py-3 px-4 outline-none focus:ring-2 focus:ring-pink-200"
                    placeholder="Misal: 500000"/>
            </div>
            <div>
                <label class="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Nama Bank *</label>
                <input id="w_bank" type="text"
                    class="w-full bg-gray-50 border border-gray-200 rounded-xl py-3 px-4 outline-none focus:ring-2 focus:ring-pink-200"
                    placeholder="BCA, Mandiri, BNI, dll"/>
            </div>
            <div>
                <label class="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Nomor Rekening *</label>
                <input id="w_account" type="text"
                    class="w-full bg-gray-50 border border-gray-200 rounded-xl py-3 px-4 outline-none focus:ring-2 focus:ring-pink-200"
                    placeholder="1234567890"/>
            </div>
            <div>
                <label class="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Nama Pemilik Rekening *</label>
                <input id="w_holder" type="text"
                    class="w-full bg-gray-50 border border-gray-200 rounded-xl py-3 px-4 outline-none focus:ring-2 focus:ring-pink-200"
                    placeholder="Nama sesuai buku rekening"/>
            </div>
        </div>
        <p id="w_error" class="text-red-500 text-sm mt-3 hidden"></p>
        <div class="flex justify-end gap-3 mt-6">
            <button onclick="closeWithdrawModal()" class="px-6 py-3 rounded-xl text-gray-500 hover:bg-gray-100 transition-colors font-medium">Batal</button>
            <button onclick="submitWithdraw()" class="px-8 py-3 rounded-xl bg-primary text-white font-semibold hover:opacity-90 shadow-md transition-all">Ajukan Penarikan</button>
        </div>
    </div>
</div>
'''
html = html.replace('</body>', withdraw_modal + '</body>')

js_head = """<script>
function stNavigate(params) {
    params._ts = Date.now();
    if(window.Streamlit) { window.Streamlit.setComponentValue(params); }
}
function openWithdrawModal() {
    const m = document.getElementById('withdrawModal');
    m.classList.remove('hidden');
    m.style.display = 'flex';
}
function closeWithdrawModal() {
    const m = document.getElementById('withdrawModal');
    m.classList.add('hidden');
    m.style.display = 'none';
}
function submitWithdraw() {
    const amount = document.getElementById('w_amount').value;
    const bank = document.getElementById('w_bank').value.trim();
    const account = document.getElementById('w_account').value.trim();
    const holder = document.getElementById('w_holder').value.trim();
    const errEl = document.getElementById('w_error');
    if (!amount || !bank || !account || !holder) {
        errEl.textContent = 'Semua field wajib diisi!';
        errEl.classList.remove('hidden');
        return;
    }
    if (parseFloat(amount) < 10000) {
        errEl.textContent = 'Minimum penarikan Rp 10.000';
        errEl.classList.remove('hidden');
        return;
    }
    errEl.classList.add('hidden');
    stNavigate({action: 'withdraw', amount, bank, account, holder});
}
document.addEventListener('DOMContentLoaded', function() {
    const m = document.getElementById('withdrawModal');
    if(m) m.style.display = 'none';
});
</script>"""
html = html.replace("</head>", js_head + "</head>")
html = html.replace('href="#"', 'href="#" onclick="event.preventDefault();"')

action_data = render_original_html("belikuy_v2_income", html, height=1600)

if action_data:
    act = action_data.get('action')
    if handle_seller_global_action(st, act):
        pass
    elif act == "withdraw":
        amount = action_data.get("amount", "0")
        bank = action_data.get("bank", "")
        account = action_data.get("account", "")
        holder = action_data.get("holder", "")
        if amount and bank and account and holder:
            resp, code = post_api("withdrawals", {
                "company_id": company_id,
                "amount": float(amount),
                "bank_name": bank,
                "account_number": account,
                "account_holder": holder
            })
            if code == 201:
                st.success("✅ Permintaan tarik dana berhasil diajukan! Akan diproses dalam 1-3 hari kerja.")
            else:
                st.error(f"Gagal: {resp}")
        st.rerun()
