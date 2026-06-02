import streamlit as st
import sys, os, re
import mysql.connector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from utils import require_role, hide_streamlit_ui, format_rupiah
from html_bridge import render_original_html
from unified_sidebar import inject_admin_sidebar, handle_admin_global_action

st.set_page_config(page_title="BeliKuy - Monitoring Transaksi", layout="wide", initial_sidebar_state="collapsed")
hide_streamlit_ui()
require_role("admin")

@st.dialog("📋 Detail Transaksi")
def show_transaction_details(tid):
    conn = mysql.connector.connect(host="127.0.0.1", user="root", password="", database="belikuy_marketplace_db")
    c = conn.cursor(dictionary=True)
    c.execute("""
        SELECT oi.*, p.product_name 
        FROM order_items oi 
        LEFT JOIN belikuy_seller_db.products p ON oi.product_id = p.id 
        WHERE oi.order_id = %s
    """, (tid,))
    items = c.fetchall()
    
    c.execute("SELECT o.*, u.username, u.email FROM orders o LEFT JOIN users u ON o.user_id = u.id WHERE o.id = %s", (tid,))
    order = c.fetchone()
    conn.close()
    
    if order:
        st.markdown(f"**Order ID:** #{order['id']}  \n**Pembeli:** {order['username']} ({order['email']})  \n**Tanggal:** {order['created_at']}  \n**Status:** {str(order['status']).upper()}")
        st.divider()
        st.markdown("### Daftar Produk")
        for item in items:
            st.markdown(f"- **{item['product_name'] or 'Produk Dihapus'}** (x{item['quantity']}) — {format_rupiah(item['price'] or 0)}")
        st.divider()
        st.markdown(f"### Total Pembayaran: **{format_rupiah(order['total_price'])}**")
    else:
        st.error("Transaksi tidak ditemukan.")


# --- Fetch Data ---
def fetch_transactions():
    conn = mysql.connector.connect(host="127.0.0.1", user="root", password="", database="belikuy_marketplace_db")
    cursor = conn.cursor(dictionary=True)
    query = """
    SELECT o.id, o.created_at, o.total_price, o.status, u.username, c.company_name
    FROM orders o
    LEFT JOIN users u ON o.user_id = u.id
    LEFT JOIN order_items oi ON o.id = oi.order_id
    LEFT JOIN belikuy_seller_db.products p ON oi.product_id = p.id
    LEFT JOIN belikuy_seller_db.companies c ON p.company_id = c.id
    GROUP BY o.id, o.created_at, o.total_price, o.status, u.username, c.company_name
    ORDER BY o.created_at DESC
    """
    cursor.execute(query)
    res = cursor.fetchall()
    conn.close()
    return res

recent = fetch_transactions()

HTML_BASE = r"D:\belikuy\belikuy_ui_templates"
with open(os.path.join(HTML_BASE, "super_admin_transaction_monitoring/code.html"), encoding='utf-8') as f:
    html = f.read()

# Build Table Rows
rows = ""
status_cfg = {
    'pending': ('Processing', 'bg-tertiary-container text-on-tertiary-container'),
    'paid': ('Processing', 'bg-tertiary-container text-on-tertiary-container'),
    'shipped': ('Shipped', 'bg-primary-container text-on-primary-container'),
    'completed': ('Completed', 'bg-surface-variant text-on-surface-variant'),
    'cancelled': ('Cancelled', 'bg-error-container text-on-error-container')
}

for t in recent:
    s_label, s_class = status_cfg.get(t.get("status", ""), ('Unknown', 'bg-surface-variant text-on-surface-variant'))
    rows += f'''
    <tr class="border-b border-surface-variant hover:bg-surface-bright transition-colors group cursor-pointer txn-row" 
        data-date="{str(t.get("created_at",""))[:10]}" 
        data-amount="{t.get("total_price",0)}" 
        data-seller="{t.get("company_name") or "BeliKuy Vendor"}" 
        data-buyer="{t.get("username") or ""}">
        <td class="p-md font-semibold text-primary">#ORD-{t.get("id","")}</td>
        <td class="p-md text-on-surface-variant">{str(t.get("created_at",""))[:10]}</td>
        <td class="p-md">{t.get("username","")}</td>
        <td class="p-md">{t.get("company_name") or "BeliKuy Vendor"}</td>
        <td class="p-md font-semibold text-on-background">{format_rupiah(t.get("total_price",0))}</td>
        <td class="p-md">
            <span class="px-3 py-1 {s_class} rounded-full font-label-caps text-[10px] uppercase">{s_label}</span>
        </td>
        <td class="p-md text-right">
            <button onclick="stNavigate({{action:'view_txn', tid:{t.get('id','')}}})" class="text-on-surface-variant hover:text-primary transition-colors">
                <span class="material-symbols-outlined">visibility</span>
            </button>
        </td>
    </tr>
    '''

if not rows:
    rows = '<tr><td colspan="7" class="py-12 text-center text-on-surface-variant">Belum ada transaksi.</td></tr>'

# Build dynamic filters HTML for Seller Dropdown
sellers = sorted(list(set([t.get("company_name") for t in recent if t.get("company_name")])))
seller_opts = '<option value="">Semua Seller</option>' + ''.join([f'<option value="{s}">{s}</option>' for s in sellers])

# Build Filters + Table HTML
main_content = f'''
<main class="flex-1 md:ml-64 p-lg overflow-y-auto">
<header class="flex justify-between items-center mb-lg">
    <div>
        <h1 class="font-h1 text-h1 text-on-background">Transaction Monitoring</h1>
        <p class="font-body-sm text-body-sm text-on-surface-variant mt-1">Super Admin Overview</p>
    </div>
    <button onclick="exportCSV()" class="px-6 py-3 bg-surface-container-low border border-surface-variant text-on-surface-variant rounded-full font-label-caps text-label-caps hover:bg-surface-bright transition-colors flex items-center gap-2 shadow-[0_4px_15px_rgba(0,0,0,0.05)]">
        <span class="material-symbols-outlined text-[18px]">download</span>
        Export CSV
    </button>
</header>

<section class="bg-surface-container-lowest rounded-xl p-lg shadow-[0_4px_20px_rgba(255,182,193,0.1)] mb-lg flex flex-col gap-md">
    <h3 class="font-h3 text-h3 text-on-surface mb-sm">Advanced Filters</h3>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-md">
        <div class="flex flex-col gap-xs">
            <label class="font-label-caps text-label-caps text-on-surface-variant uppercase">Date Range</label>
            <div class="flex items-center gap-2">
                <input class="w-full px-3 py-2 bg-surface-bright border border-surface-variant rounded-lg font-body-sm text-body-sm text-on-surface focus:ring-2 focus:ring-primary-container" type="date" id="filter_date_start"/>
                <span class="text-on-surface-variant">-</span>
                <input class="w-full px-3 py-2 bg-surface-bright border border-surface-variant rounded-lg font-body-sm text-body-sm text-on-surface focus:ring-2 focus:ring-primary-container" type="date" id="filter_date_end"/>
            </div>
        </div>
        <div class="flex flex-col gap-xs">
            <label class="font-label-caps text-label-caps text-on-surface-variant uppercase">Amount Range (Rp)</label>
            <div class="flex items-center gap-2">
                <input class="w-full px-3 py-2 bg-surface-bright border border-surface-variant rounded-lg font-body-sm text-body-sm text-on-surface focus:ring-2 focus:ring-primary-container" placeholder="Min" type="number" id="filter_amount_min"/>
                <span class="text-on-surface-variant">-</span>
                <input class="w-full px-3 py-2 bg-surface-bright border border-surface-variant rounded-lg font-body-sm text-body-sm text-on-surface focus:ring-2 focus:ring-primary-container" placeholder="Max" type="number" id="filter_amount_max"/>
            </div>
        </div>
        <div class="flex flex-col gap-xs">
            <label class="font-label-caps text-label-caps text-on-surface-variant uppercase">Seller</label>
            <select id="filter_seller" class="w-full px-3 py-2.5 bg-surface-bright border border-surface-variant rounded-lg font-body-sm text-body-sm text-on-surface focus:ring-2 focus:ring-primary-container">
                {seller_opts}
            </select>
        </div>
        <div class="flex flex-col gap-xs">
            <label class="font-label-caps text-label-caps text-on-surface-variant uppercase">Buyer</label>
            <input id="filter_buyer" class="w-full px-3 py-2.5 bg-surface-bright border border-surface-variant rounded-lg font-body-sm text-body-sm text-on-surface focus:ring-2 focus:ring-primary-container" placeholder="Cari nama pembeli..." type="text">
        </div>
        <div class="flex flex-col gap-xs">
            <label class="font-label-caps text-label-caps text-on-surface-variant uppercase">Status</label>
            <select id="filter_status" class="w-full px-3 py-2.5 bg-surface-bright border border-surface-variant rounded-lg font-body-sm text-body-sm text-on-surface focus:ring-2 focus:ring-primary-container">
                <option value="">Semua Status</option>
                <option value="pending">Pending</option>
                <option value="paid">Paid</option>
                <option value="shipped">Shipped</option>
                <option value="completed">Completed</option>
                <option value="cancelled">Cancelled</option>
            </select>
        </div>
    </div>
    <div class="flex justify-end mt-sm">
        <button type="button" onclick="applyFilters()" class="px-6 py-2 bg-primary text-white rounded-full font-label-caps text-label-caps hover:bg-[#6c3e46] shadow-sm transition-all duration-300">
            Apply Filters
        </button>
    </div>
</section>

<section class="bg-surface-container-lowest rounded-xl shadow-[0_4px_20px_rgba(255,182,193,0.1)] flex-1 overflow-hidden flex flex-col">
    <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
            <thead>
                <tr class="border-b border-surface-variant bg-surface-bright">
                    <th class="p-md font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider">Order ID</th>
                    <th class="p-md font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider">Date</th>
                    <th class="p-md font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider">Buyer</th>
                    <th class="p-md font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider">Seller</th>
                    <th class="p-md font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider">Total Amount</th>
                    <th class="p-md font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider">Status</th>
                    <th class="p-md font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider text-right">Actions</th>
                </tr>
            </thead>
            <tbody class="font-body-sm text-body-sm text-on-surface">
                {rows}
            </tbody>
        </table>
    </div>
    <div class="p-md border-t border-surface-variant flex justify-between items-center text-on-surface-variant font-body-sm text-body-sm">
        <span id="page-info">Menampilkan total 0 transaksi</span>
        <div class="flex gap-2" id="pagination-controls">
            <!-- Numbers will be injected here -->
        </div>
    </div>
</section>
</main>
'''

html = re.sub(r'<main class="ml-64 flex-1 flex flex-col p-lg min-h-screen">.*?</main>', main_content, html, flags=re.DOTALL)

js_head = """<script>
function stNavigate(params) {
    if(window.Streamlit) {
        window.Streamlit.setComponentValue(params);
    }
}

let currentPage = 1;
const rowsPerPage = 15;
let filteredRows = [];

function applyFilters() {
    const ds = document.getElementById('filter_date_start').value;
    const de = document.getElementById('filter_date_end').value;
    const amin = parseInt(document.getElementById('filter_amount_min').value) || 0;
    const amax = parseInt(document.getElementById('filter_amount_max').value) || Infinity;
    const sel = document.getElementById('filter_seller').value;
    const buy = document.getElementById('filter_buyer').value.toLowerCase();
    const stat = document.getElementById('filter_status').value.toLowerCase();
    
    filteredRows = [];
    document.querySelectorAll('.txn-row').forEach(row => {
        let show = true;
        const rDate = row.getAttribute('data-date');
        const rAmount = parseInt(row.getAttribute('data-amount')) || 0;
        const rSeller = row.getAttribute('data-seller');
        const rBuyer = row.getAttribute('data-buyer').toLowerCase();
        const rStatus = row.querySelector('td:nth-child(6) span').innerText.toLowerCase();
        
        if (ds && rDate < ds) show = false;
        if (de && rDate > de) show = false;
        if (rAmount < amin) show = false;
        if (rAmount > amax) show = false;
        if (sel && rSeller !== sel) show = false;
        if (buy && !rBuyer.includes(buy)) show = false;
        if (stat && rStatus !== stat && stat !== '') show = false;
        
        if(show) filteredRows.push(row);
        row.style.display = 'none';
    });
    
    currentPage = 1;
    renderPage();
}

function renderPage() {
    const totalPages = Math.ceil(filteredRows.length / rowsPerPage) || 1;
    if (currentPage > totalPages) currentPage = totalPages;
    if (currentPage < 1) currentPage = 1;
    
    document.querySelectorAll('.txn-row').forEach(r => r.style.display = 'none');
    
    const start = (currentPage - 1) * rowsPerPage;
    const end = start + rowsPerPage;
    for (let i = start; i < end && i < filteredRows.length; i++) {
        filteredRows[i].style.display = '';
    }
    
    document.getElementById('page-info').innerText = `Menampilkan ${filteredRows.length > 0 ? start + 1 : 0}-${Math.min(end, filteredRows.length)} dari ${filteredRows.length} transaksi`;
    
    // Render numeric pagination
    const pControl = document.getElementById('pagination-controls');
    let pHTML = `<button onclick="prevPage()" class="w-8 h-8 flex items-center justify-center rounded-md hover:bg-surface-bright transition-colors"><span class="material-symbols-outlined">chevron_left</span></button>`;
    
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, currentPage + 2);
    
    for(let i = startPage; i <= endPage; i++) {
        if(i === currentPage) {
            pHTML += `<button class="w-8 h-8 flex items-center justify-center rounded-md bg-primary-container text-on-primary-container font-semibold">${i}</button>`;
        } else {
            pHTML += `<button onclick="gotoPage(${i})" class="w-8 h-8 flex items-center justify-center rounded-md hover:bg-surface-bright transition-colors">${i}</button>`;
        }
    }
    pHTML += `<button onclick="nextPage()" class="w-8 h-8 flex items-center justify-center rounded-md hover:bg-surface-bright transition-colors"><span class="material-symbols-outlined">chevron_right</span></button>`;
    pControl.innerHTML = pHTML;
}

function gotoPage(p) {
    currentPage = p;
    renderPage();
}

function exportCSV() {
    let csv = "Order ID,Date,Buyer,Seller,Total Amount,Status\\n";
    filteredRows.forEach(r => {
        let cols = r.querySelectorAll('td');
        let rowData = Array.from(cols).slice(0,6).map(c => '"' + c.innerText.replace(/"/g, '""') + '"').join(",");
        csv += rowData + "\\n";
    });
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.setAttribute('href', url);
    a.setAttribute('download', 'transaksi_belikuy.csv');
    a.click();
}

function prevPage() { 
    if(currentPage > 1) {
        currentPage--; 
        renderPage(); 
    }
}
function nextPage() { 
    const totalPages = Math.ceil(filteredRows.length / rowsPerPage) || 1;
    if(currentPage < totalPages) {
        currentPage++; 
        renderPage(); 
    }
}

document.addEventListener('DOMContentLoaded', function() {
    applyFilters();
});
</script>"""

html = html.replace("</head>", js_head + "</head>")
html = html.replace('href="#"', 'href="#" onclick="event.preventDefault();"')

html = inject_admin_sidebar(html, "15_Monitoring_Transaksi")

action_data = render_original_html("belikuy_v2_admin_txn", html, height=1200)

if action_data:
    act = action_data.get('action')
    if handle_admin_global_action(st, act):
        pass
    elif act == 'view_txn':
        show_transaction_details(action_data.get('tid'))
