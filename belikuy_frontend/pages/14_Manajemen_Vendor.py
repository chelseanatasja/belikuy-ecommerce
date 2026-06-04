import streamlit as st
import sys, os, re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from utils import get_api, delete_api, require_role, hide_streamlit_ui
from html_bridge import render_original_html
from unified_sidebar import inject_admin_sidebar, handle_admin_global_action

st.set_page_config(
    page_title="BeliKuy - Manajemen Vendor",
    layout="wide",
    initial_sidebar_state="collapsed",
)
hide_streamlit_ui()
require_role("admin")


@st.dialog("Detail Vendor")
def show_vendor_detail(vid, vendors_list):
    v = next((x for x in vendors_list if x["id"] == vid), None)
    if not v:
        st.error("Vendor tidak ditemukan.")
        return
    st.markdown(f"### 🏢 {v.get('company_name')}")
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Pemilik:**<br>{v.get('username')}", unsafe_allow_html=True)
        st.markdown(f"**Email:**<br>{v.get('email')}", unsafe_allow_html=True)
    with col2:
        from datetime import datetime

        def fmt_date(dt_str):
            if not dt_str:
                return "-"
            try:
                dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S.%fZ")
                return dt.strftime("%d %b %Y")
            except:
                return str(dt_str)[:10]

        st.write(f"**Tanggal Bergabung:**\n{fmt_date(v.get('created_at'))}")
        st.write(f"**Status:**\n{'Aktif' if v.get('is_active', 1) else 'Nonaktif'}")

    st.markdown("---")
    st.write(f"**Alamat:** {v.get('address') or 'Belum diisi'}")
    st.write(f"**Rating Toko:** ⭐️ {v.get('rating') or 'N/A'}")
    st.info(f"Total produk yang diunggah: **{v.get('product_count', 0)} produk**")

    if st.button("Tutup", use_container_width=True):
        st.rerun()


vendors, _ = get_api("admin/vendors")
if not vendors:
    vendors = []

# Search functionality
if "search_query" not in st.session_state:
    st.session_state.search_query = ""

if st.session_state.search_query:
    q = st.session_state.search_query.lower()
    vendors = [
        v
        for v in vendors
        if q in str(v.get("company_name", "")).lower()
        or q in str(v.get("username", "")).lower()
        or q in str(v.get("email", "")).lower()
    ]

HTML_BASE = (
    r"D:\Tugas Kuliah\Semester 4\Workshop RPL\belikuy-ecommerce\belikuy_ui_templates"
)
with open(
    os.path.join(HTML_BASE, "super_admin_vendor_management/code.html"), encoding="utf-8"
) as f:
    html = f.read()

# Build Table Rows
from datetime import datetime


def format_date(dt_str):
    if not dt_str:
        return "-"
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        return dt.strftime("%d %b %Y")
    except:
        return str(dt_str)[:10]


rows = ""
for v in vendors:
    created_at = format_date(v.get("created_at"))
    is_active = v.get("is_active", 1) == 1
    status_badge = (
        '<span class="inline-flex items-center px-3 py-1 rounded-full bg-primary-fixed text-on-primary-fixed-variant font-label-caps text-label-caps uppercase shadow-[0_2px_10px_rgba(255,217,222,0.5)]">Aktif</span>'
        if is_active
        else '<span class="inline-flex items-center px-3 py-1 rounded-full bg-surface-variant text-on-surface-variant font-label-caps text-label-caps uppercase">Nonaktif</span>'
    )

    # Toggle button icon and text
    toggle_icon = "block" if is_active else "check_circle"
    toggle_title = "Nonaktifkan Toko" if is_active else "Aktifkan Toko"
    toggle_color = (
        "text-on-surface-variant hover:bg-surface-variant"
        if is_active
        else "text-emerald-600 hover:bg-emerald-100"
    )

    rows += f"""
    <tr class="hover:bg-surface-bright transition-colors duration-200 group">
        <td class="py-4 px-6">
            <div class="flex items-center gap-sm">
                <div class="w-10 h-10 rounded-lg bg-primary-container flex items-center justify-center shadow-sm text-primary font-bold">
                    {str(v.get("company_name", "V"))[0].upper()}
                </div>
                <div class="flex flex-col">
                    <span class="font-body-sm text-body-sm font-semibold text-on-surface">{v.get("company_name","")}</span>
                    <span class="text-[10px] text-outline">{v.get("product_count",0)} Produk</span>
                </div>
            </div>
        </td>
        <td class="py-4 px-6 font-body-sm text-body-sm text-on-surface-variant">
            <div class="flex flex-col">
                <span class="font-medium text-on-surface">{v.get("username","")}</span>
                <span class="text-xs">{v.get("email","")}</span>
            </div>
        </td>
        <td class="py-4 px-6 font-body-sm text-body-sm text-on-surface-variant">{created_at}</td>
        <td class="py-4 px-6">
            {status_badge}
        </td>
        <td class="py-4 px-6 text-right">
            <div class="flex items-center justify-end gap-xs opacity-80 group-hover:opacity-100 transition-opacity">
                <button onclick="stNavigate({{action:'detail_vendor', vid:{v.get('id')}}})" class="p-2 text-primary hover:bg-primary-container hover:text-on-primary-container rounded-full transition-colors" title="Lihat Detail">
                    <span class="material-symbols-outlined">visibility</span>
                </button>
                <button onclick="stNavigate({{action:'toggle_status', vid:{v.get('id')}}})" class="p-2 {toggle_color} rounded-full transition-colors" title="{toggle_title}">
                    <span class="material-symbols-outlined">{toggle_icon}</span>
                </button>
            </div>
        </td>
    </tr>
    """

if not rows:
    rows = '<tr><td colspan="5" class="py-12 text-center text-on-surface-variant">Belum ada vendor terdaftar.</td></tr>'

html = re.sub(
    r'(<tbody class="divide-y divide-surface-variant">)(.*?)(</tbody>)',
    rf"\1{rows}\3",
    html,
    flags=re.DOTALL,
)
html = re.sub(
    r"(Menampilkan 1-3 dari 124 vendor)", rf"Total {len(vendors)} vendor", html
)

js_head = """<script>
function stNavigate(params) {
    if(window.Streamlit) {
        window.Streamlit.setComponentValue(params);
    }
}
document.addEventListener('DOMContentLoaded', function() {
    // Attach search event
    const searchInput = document.querySelector('input[placeholder*="Cari"]');
    if (searchInput) {
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                stNavigate({action:'search', query: this.value});
            }
        });
    }
});
</script>"""
html = html.replace("</head>", js_head + "</head>")
html = html.replace('href="#"', 'href="#" onclick="event.preventDefault();"')
html = html.replace('"Inter"', '"Plus Jakarta Sans"')
html = html.replace(">Pemilik<", ">Info Owner<")

# Inject search value
if st.session_state.search_query:
    html = html.replace(
        'placeholder="Cari nama toko atau SKU..."',
        f'value="{st.session_state.search_query}" placeholder="Cari nama toko atau SKU..."',
    )


html = inject_admin_sidebar(html, "14_Manajemen_Vendor")

action_data = render_original_html("belikuy_v2_admin_vendors", html, height=1000)

if action_data:
    act = action_data.get("action")
    if handle_admin_global_action(st, act):
        pass
    elif act == "search":
        st.session_state.search_query = action_data.get("query", "")
        st.rerun()
    elif act == "detail_vendor":
        show_vendor_detail(action_data.get("vid"), vendors)
    elif act == "toggle_status":
        vid = action_data.get("vid")
        import mysql.connector

        try:
            conn = mysql.connector.connect(
                host="127.0.0.1", user="root", password="", database="belikuy"
            )
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE belikuy_seller_db.Companies SET is_active = NOT is_active WHERE id = %s",
                (vid,),
            )
            cursor.execute(
                "UPDATE companies SET is_active = NOT is_active WHERE id = %s", (vid,)
            )
            conn.commit()
            st.toast(f"Status vendor berhasil diperbarui!")
        except Exception as e:
            st.error(f"Gagal memperbarui status: {e}")
        st.rerun()
