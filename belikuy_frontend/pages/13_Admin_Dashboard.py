import streamlit as st
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils import (
    get_api,
    require_login,
    hide_streamlit_ui,
    format_rupiah,
    get_current_user,
)
from html_bridge import render_original_html
from unified_sidebar import inject_admin_sidebar, handle_admin_global_action

st.set_page_config(
    page_title="BeliKuy - Admin Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
)
hide_streamlit_ui()
require_login()

user = get_current_user()
if user and user.get("role") != "admin":
    st.error("🚫 Akses ditolak.")
    st.stop()

import mysql.connector
from datetime import datetime
import time

if "chart_filter" not in st.session_state:
    st.session_state.chart_filter = "7_days"

# ── Fetch real data from DB directly ──
try:
    conn = mysql.connector.connect(
        host="127.0.0.1", user="root", password="", database="belikuy_marketplace_db"
    )
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT COUNT(*) as c, SUM(total_price) as s FROM orders WHERE status != 'cancelled' AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)"
    )
    month_stats = cursor.fetchone() or {"c": 0, "s": 0}

    cursor.execute(
        "SELECT COUNT(*) as c, SUM(total_price) as s FROM orders WHERE status != 'cancelled'"
    )
    all_stats = cursor.fetchone() or {"c": 0, "s": 0}

    cursor.execute("SELECT COUNT(*) as c FROM belikuy_seller_db.companies")
    verified = cursor.fetchone() or {"c": 0}

    total_orders_month = month_stats["c"] or 0
    total_rev_month = month_stats["s"] or 0
    total_rev_all = all_stats["s"] or 0
    total_verified = verified["c"] or 0

    f = st.session_state.chart_filter
    if f == "30_days":
        days_to_pad = 30
        query_condition = "created_at >= DATE_SUB(CURDATE(), INTERVAL 29 DAY)"
        chart_title_sub = "Tren pemesanan 30 hari terakhir"
        dropdown_label = "30 Hari Terakhir"
        label_step = 5  # Only show label every 5 days to avoid clutter
    else:
        days_to_pad = 7
        query_condition = "created_at >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)"
        chart_title_sub = "Tren pemesanan 7 hari terakhir"
        dropdown_label = "7 Hari Terakhir"
        label_step = 1

    cursor.execute(f"""
        SELECT DATE(created_at) as d, COUNT(*) as c 
        FROM orders 
        WHERE {query_condition}
        GROUP BY DATE(created_at)
        ORDER BY d ASC
    """)
    db_chart_data = cursor.fetchall()

    # Pad to exactly days_to_pad days
    from datetime import timedelta

    today = datetime.now().date()
    chart_data = []
    for i in range(days_to_pad - 1, -1, -1):
        target_date = today - timedelta(days=i)
        found = next((row for row in db_chart_data if row["d"] == target_date), None)
        if found:
            chart_data.append(found)
        else:
            chart_data.append({"d": target_date, "c": 0})

    max_c = max([row["c"] for row in chart_data]) or 1
    chart_html_bars = ""
    chart_html_labels = ""
    for idx, row in enumerate(chart_data):
        pct = max(5, int((row["c"] / max_c) * 100))  # min height 5% for visibility
        bg_class = (
            "bg-primary"
            if pct == 100
            else "bg-primary-container/60 hover:bg-primary/80 transition-colors cursor-pointer"
        )
        shadow = "shadow-[0_0_15px_rgba(135,78,88,0.4)]" if pct == 100 else ""
        chart_html_bars += f'<div class="w-full {bg_class} rounded-t-md relative group {shadow}" style="height: {pct}%"><div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-surface-container-highest text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity z-20 whitespace-nowrap">{row["c"]} Order</div></div>'

        # Show label only if it matches step
        if idx % label_step == 0 or idx == len(chart_data) - 1:
            chart_html_labels += f'<span class="text-xs text-on-surface-variant truncate">{row["d"].strftime("%d %b")}</span>'
        else:
            chart_html_labels += f"<span></span>"

    chart_html = f"""
    <div class="relative h-64 w-full flex items-end justify-between gap-2 mt-8">
        {chart_html_bars}
    </div>
    <div class="flex justify-between items-center mt-3 text-[10px] font-body-sm text-outline px-1">
        {chart_html_labels}
    </div>
    """

    cursor.execute(
        "SELECT id, total_price, created_at, 'order' as type FROM orders ORDER BY created_at DESC LIMIT 5"
    )
    ro = cursor.fetchall()
    cursor.execute(
        "SELECT id, company_name as name, created_at, 'vendor' as type FROM belikuy_seller_db.companies ORDER BY created_at DESC LIMIT 5"
    )
    rv = cursor.fetchall()

    recent_activities = sorted(ro + rv, key=lambda x: x["created_at"], reverse=True)[:5]

except Exception as e:
    st.error(f"DB Error: {e}")
    total_orders_month = total_rev_month = total_rev_all = total_verified = 0
    chart_data = []
    recent_activities = []


HTML_BASE = (
    r"D:\Tugas Kuliah\Semester 4\Workshop RPL\belikuy-ecommerce\belikuy_ui_templates"
)
with open(
    os.path.join(HTML_BASE, "super_admin_dashboard_overview/code.html"),
    encoding="utf-8",
) as f:
    html = f.read()


# Add custom JS bridge commands
# Generate Recent Activity HTML
def time_ago(dt):
    if not dt:
        return ""
    if isinstance(dt, str):
        dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
    diff = (datetime.now() - dt).total_seconds()
    if diff < 3600:
        return f"{int(diff/60)} menit yang lalu"
    if diff < 86400:
        return f"{int(diff/3600)} jam yang lalu"
    return f"{int(diff/86400)} hari yang lalu"


activity_html = ""
for a in recent_activities:
    icon = "store" if a["type"] == "vendor" else "monetization_on"
    color = (
        "bg-tertiary-container/30 text-tertiary border-surface-container-lowest"
        if a["type"] == "vendor"
        else "bg-emerald-100 text-emerald-700 border-surface-container-lowest"
    )
    title = "Toko Baru Mendaftar" if a["type"] == "vendor" else "Pesanan Baru"
    desc = (
        f"Vendor '{a.get('name','')}' bergabung."
        if a["type"] == "vendor"
        else f"Order #{a['id']} senilai {format_rupiah(a['total_price'])} diproses."
    )

    activity_html += f"""
    <div class="flex gap-4 items-start relative">
        <div class="absolute left-5 top-10 bottom-[-24px] w-[2px] bg-surface-variant"></div>
        <div class="w-10 h-10 rounded-full {color} flex items-center justify-center shrink-0 z-10 border-4">
            <span class="material-symbols-outlined text-[20px]">{icon}</span>
        </div>
        <div>
            <p class="font-body-md text-sm font-medium text-on-background">{title}</p>
            <p class="font-body-sm text-xs text-on-surface-variant mt-1">{desc}</p>
            <span class="text-[10px] text-outline font-medium mt-2 block">{time_ago(a['created_at'])}</span>
        </div>
    </div>
    """

# Inject values into HTML
import re

html = html.replace("Rp 4.2B", format_rupiah(total_rev_month))
html = html.replace("Rp 350M", format_rupiah(total_rev_all))
html = html.replace("1,248", str(total_verified))

# Remove Active Users (Stat 4)
html = re.sub(r"<!-- Stat 4 -->.*?(?=</section>)", "", html, flags=re.DOTALL)

# Replace Recent Activities
html = re.sub(
    r'(<h3 class="font-h3 text-\[20px\] font-semibold text-on-background mb-6">Aktivitas Terbaru</h3>\s*<div class="flex flex-col gap-6">).*?(</div>\s*<button)',
    rf"\1{activity_html}\2",
    html,
    flags=re.DOTALL,
)

# Replace Chart
html = re.sub(
    r"(<!-- Mock Graph Area \(Stylized\) -->).*?(</section>)",
    rf"\1\n{chart_html}\n\2",
    html,
    flags=re.DOTALL,
)
html = html.replace("Tren pemesanan 7 hari terakhir", chart_title_sub)

import re

dropdown_html = f"""<div class="relative group">
    <button class="flex items-center gap-2 text-sm font-medium text-on-surface-variant hover:text-primary transition-colors px-3 py-1.5 rounded-lg border border-surface-variant hover:bg-surface-bright">
        {dropdown_label}
        <span class="material-symbols-outlined text-[18px]">expand_more</span>
    </button>
    <div class="absolute right-0 mt-1 w-40 bg-surface-container-lowest rounded-xl shadow-[0_8px_30px_rgb(255,182,193,0.2)] border border-surface-variant opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-[100] overflow-hidden">
        <button onclick="stNavigate({{action: 'chart_filter', val: '7_days'}})" class="block w-full text-left px-4 py-2.5 text-sm text-on-surface hover:bg-primary-container/30 hover:text-primary transition-colors">7 Hari Terakhir</button>
        <button onclick="stNavigate({{action: 'chart_filter', val: '30_days'}})" class="block w-full text-left px-4 py-2.5 text-sm text-on-surface hover:bg-primary-container/30 hover:text-primary transition-colors">30 Hari Terakhir</button>
    </div>
</div>"""
html = re.sub(
    r'<button class="flex items-center gap-2 text-sm font-medium text-on-surface-variant hover:text-primary transition-colors px-3 py-1.5 rounded-lg border border-surface-variant hover:bg-surface-bright">\s*Minggu Ini\s*<span class="material-symbols-outlined text-\[18px\]">expand_more</span>\s*</button>',
    dropdown_html,
    html,
)


js_head = """<script>
function stNavigate(params) {
    params._ts = Date.now();
    if(window.Streamlit) { window.Streamlit.setComponentValue(params); }
}

document.addEventListener('DOMContentLoaded', function() {
    // (Removed specific element overrides to let unified sidebar work)
});
</script>"""

html = html.replace("</head>", js_head + "</head>")

# Inject Unified Admin Sidebar
html = inject_admin_sidebar(html, "13_Admin_Dashboard")

# Render using exact HTML bridge
action_data = render_original_html("belikuy_v2_admin", html, height=1200)

if action_data:
    act = action_data.get("action")
    if handle_admin_global_action(st, act):
        pass
    elif act == "chart_filter":
        st.session_state.chart_filter = action_data.get("val", "7_days")
        st.rerun()
