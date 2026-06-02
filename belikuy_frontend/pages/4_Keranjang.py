import streamlit as st
import sys, os, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from utils import require_login, hide_streamlit_ui, format_rupiah
from html_bridge import render_original_html
from unified_navbar import inject_navbar, handle_global_action
from collections import defaultdict

st.set_page_config(page_title="BeliKuy - Keranjang", layout="wide", initial_sidebar_state="collapsed")
hide_streamlit_ui()
require_login()

FRONTEND_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def local_img(path):
    if not path: return ""
    if path.startswith("http"): return path
    try:
        full = os.path.join(FRONTEND_BASE, path.replace("\\", "/"))
        if os.path.exists(full):
            ext = os.path.splitext(full)[1].lower().lstrip(".")
            mime = {"jpg":"jpeg","jpeg":"jpeg","png":"png","gif":"gif","webp":"webp"}.get(ext,"jpeg")
            with open(full,"rb") as f:
                return f"data:image/{mime};base64,{base64.b64encode(f.read()).decode()}"
    except: pass
    return ""

cart = st.session_state.get('cart', [])

# Design tokens
P   = "#874e58"
BG  = "#f8f9fa"
W   = "#ffffff"
BD  = "#f3f4f5"
TXT = "#191c1d"
MUT = "#514345"
GRY = "#847375"

groups = defaultdict(list)
for idx, item in enumerate(cart):
    groups[item.get('company_name', 'Toko Lainnya')].append((idx, item))

subtotal      = sum(float(i.get('price', 0)) * int(i.get('qty', 1)) for i in cart)
shipping_cost = 15000
total_payment = subtotal + shipping_cost

# ── Build cart HTML ────────────────────────────────────────────────────────────
cart_html = ""
for shop_name, items in groups.items():
    shop_key = shop_name.replace('"', '').replace("'", "")
    items_html = ""
    for idx, item in items:
        img       = local_img(item.get('image_url', '')) or "https://via.placeholder.com/80?text=No+Img"
        raw_price = float(item.get('price', 0)) * int(item.get('qty', 1))
        price_fmt = format_rupiah(raw_price)
        iid       = str(item.get('id', ''))
        iname     = str(item.get('product_name', 'Produk')).replace('"', '&quot;')
        icat      = str(item.get('category_name', '—'))
        qty       = int(item.get('qty', 1))

        items_html += (
            # row wrapper
            '<div style="display:flex;align-items:flex-start;gap:14px;padding:14px 0;border-bottom:1px solid ' + BD + ';">'

            # checkbox with data-price and data-shop
            '<div style="display:flex;align-items:center;padding-top:4px;">'
            '<input type="checkbox" class="item-cb"'
            ' data-idx="' + str(idx) + '"'
            ' data-price="' + str(raw_price) + '"'
            ' data-shop="' + shop_key + '"'
            ' style="width:18px;height:18px;accent-color:' + P + ';cursor:pointer;flex-shrink:0;"'
            ' onchange="onItemChange()"/>'
            '</div>'

            # thumbnail
            '<img src="' + img + '"'
            ' onclick="stNavigate({action:\'go_detail\',pid:\'' + iid + '\'})"'
            ' onerror="this.src=\'https://via.placeholder.com/80?text=No+Img\'"'
            ' style="width:80px;height:80px;border-radius:12px;object-fit:cover;flex-shrink:0;cursor:pointer;background:#f3f4f5;"/>'

            # info block
            '<div style="flex:1;min-width:0;">'
            '<p onclick="stNavigate({action:\'go_detail\',pid:\'' + iid + '\'})"'
            ' style="font-family:\'Plus Jakarta Sans\',sans-serif;font-size:14px;font-weight:600;color:' + TXT + ';margin:0 0 4px;cursor:pointer;overflow:hidden;text-overflow:ellipsis;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;">'
            + iname + '</p>'
            '<p style="font-family:\'Inter\',sans-serif;font-size:12px;color:' + GRY + ';margin:0 0 10px;">' + icat + '</p>'

            '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">'
            '<span style="font-family:\'Plus Jakarta Sans\',sans-serif;font-size:16px;font-weight:800;color:' + P + ';">' + price_fmt + '</span>'

            # qty + delete buttons
            '<div style="display:flex;align-items:center;gap:6px;">'
            '<button onclick="stNavigate({action:\'dec_qty\',idx:' + str(idx) + '})"'
            ' style="width:30px;height:30px;border-radius:50%;border:1.5px solid #e1e3e4;background:white;display:flex;align-items:center;justify-content:center;cursor:pointer;">'
            '<span class="material-symbols-outlined" style="font-size:15px;color:' + MUT + ';">remove</span></button>'
            '<span style="font-family:\'Plus Jakarta Sans\',sans-serif;font-size:14px;font-weight:700;color:' + TXT + ';min-width:24px;text-align:center;">' + str(qty) + '</span>'
            '<button onclick="stNavigate({action:\'inc_qty\',idx:' + str(idx) + '})"'
            ' style="width:30px;height:30px;border-radius:50%;border:1.5px solid #e1e3e4;background:white;display:flex;align-items:center;justify-content:center;cursor:pointer;">'
            '<span class="material-symbols-outlined" style="font-size:15px;color:' + MUT + ';">add</span></button>'
            '<button onclick="stNavigate({action:\'remove_item\',idx:' + str(idx) + '})"'
            ' style="width:30px;height:30px;border-radius:50%;border:1.5px solid #fca5a5;background:#fef2f2;display:flex;align-items:center;justify-content:center;cursor:pointer;margin-left:4px;">'
            '<span class="material-symbols-outlined" style="font-size:15px;color:#b91c1c;">delete</span></button>'
            '</div>'  # qty row
            '</div>'  # price row
            '</div>'  # info
            '</div>'  # item row
        )

    # Shop card
    cart_html += (
        '<div style="background:' + W + ';border-radius:20px;box-shadow:0 2px 12px rgba(135,78,88,0.08);border:1px solid ' + BD + ';overflow:hidden;margin-bottom:16px;">'

        # shop header with per-shop checkbox
        '<div style="display:flex;align-items:center;padding:14px 20px;background:#fafafa;border-bottom:1px solid ' + BD + ';gap:10px;">'
        '<input type="checkbox" class="shop-cb" data-shop="' + shop_key + '"'
        ' style="width:18px;height:18px;accent-color:' + P + ';cursor:pointer;"'
        ' onchange="toggleShop(this)"/>'
        '<span class="material-symbols-outlined" style="font-size:18px;color:' + P + ';font-variation-settings:\'FILL\' 1;">storefront</span>'
        '<span style="font-family:\'Plus Jakarta Sans\',sans-serif;font-size:14px;font-weight:700;color:' + TXT + ';">' + shop_name + '</span>'
        '</div>'

        '<div style="padding:0 20px;">' + items_html + '</div>'
        '</div>'
    )

empty_html = (
    '<div style="text-align:center;padding:60px 20px;background:' + W + ';border-radius:20px;box-shadow:0 2px 12px rgba(135,78,88,0.08);">'
    '<span class="material-symbols-outlined" style="font-size:64px;color:#ffb6c1;font-variation-settings:\'FILL\' 1;">shopping_cart</span>'
    '<h2 style="font-family:\'Plus Jakarta Sans\',sans-serif;font-size:22px;font-weight:700;color:' + TXT + ';margin:12px 0 8px;">Keranjangmu Kosong</h2>'
    '<p style="font-family:\'Inter\',sans-serif;font-size:14px;color:' + MUT + ';margin:0 0 20px;">Yuk temukan produk estetik favoritmu!</p>'
    '<button onclick="stNavigate({action:\'go_search\'})"'
    ' style="background:linear-gradient(135deg,#ffb6c1,#c084fc);color:white;border:none;padding:12px 28px;border-radius:20px;font-size:14px;font-weight:700;cursor:pointer;font-family:\'Plus Jakarta Sans\',sans-serif;">'
    'Mulai Belanja</button>'
    '</div>'
)

# ── Summary card HTML ──────────────────────────────────────────────────────────
summary_html = ""
if cart:
    summary_html = (
        '<div style="background:' + W + ';border-radius:20px;box-shadow:0 2px 16px rgba(135,78,88,0.1);border:1px solid ' + BD + ';overflow:hidden;margin-top:24px;">'
        '<div style="padding:20px;border-bottom:1px solid ' + BD + ';">'
        '<h3 style="font-family:\'Plus Jakarta Sans\',sans-serif;font-size:16px;font-weight:700;color:' + TXT + ';margin:0 0 16px;">Ringkasan Pesanan</h3>'
        '<div style="display:flex;justify-content:space-between;margin-bottom:8px;">'
        '<span id="dyn-label" style="font-family:\'Inter\',sans-serif;font-size:14px;color:' + MUT + ';">Subtotal (' + str(len(cart)) + ' item)</span>'
        '<span id="dyn-subtotal" style="font-family:\'Inter\',sans-serif;font-size:14px;font-weight:600;color:' + TXT + ';">' + format_rupiah(subtotal) + '</span>'
        '</div>'
        '<div style="border-top:1px dashed #e1e3e4;margin:12px 0;"></div>'
        '<div style="display:flex;justify-content:space-between;align-items:center;">'
        '<span style="font-family:\'Plus Jakarta Sans\',sans-serif;font-size:15px;font-weight:700;color:' + TXT + ';">Total Belanja</span>'
        '<span id="dyn-total" style="font-family:\'Plus Jakarta Sans\',sans-serif;font-size:22px;font-weight:800;color:' + P + ';">' + format_rupiah(subtotal) + '</span>'
        '</div>'
        '</div>'
        '<div style="padding:16px 20px;">'
        '<button id="dyn-checkout-btn" onclick="stNavigate({action:\'checkout\'})"'
        ' style="width:100%;background:linear-gradient(135deg,#ffb6c1,#c084fc);color:white;border:none;padding:16px;border-radius:16px;font-family:\'Plus Jakarta Sans\',sans-serif;font-size:15px;font-weight:800;cursor:pointer;">'
        'Checkout (' + str(len(cart)) + ' item) \u2192</button>'
        '<button onclick="stNavigate({action:\'go_search\'})"'
        ' style="width:100%;background:transparent;color:' + P + ';border:1.5px solid #ffb6c1;padding:12px;border-radius:16px;font-family:\'Inter\',sans-serif;font-size:13px;font-weight:600;cursor:pointer;margin-top:10px;">'
        '\u2190 Lanjut Belanja</button>'
        '</div>'
        '</div>'
    )

# ── Full page ──────────────────────────────────────────────────────────────────
select_bar = ""
if cart:
    select_bar = (
        '<div style="background:white;border-radius:16px;border:1px solid ' + BD + ';padding:12px 20px;margin-bottom:16px;display:flex;align-items:center;justify-content:space-between;box-shadow:0 2px 8px rgba(135,78,88,0.06);">'
        '<label style="display:flex;align-items:center;gap:10px;cursor:pointer;">'
        '<input type="checkbox" id="select-all" onchange="toggleAll(this)"'
        ' style="width:18px;height:18px;accent-color:' + P + ';cursor:pointer;"/>'
        '<span style="font-family:\'Inter\',sans-serif;font-size:13px;font-weight:600;color:' + TXT + ';">Pilih Semua (' + str(len(cart)) + ' item)</span>'
        '</label>'
        '<button id="delete-selected-btn" onclick="deleteSelected()"'
        ' style="display:none;align-items:center;gap:5px;border:1.5px solid #fca5a5;color:#b91c1c;background:#fef2f2;padding:6px 14px;border-radius:20px;font-size:12px;font-weight:600;cursor:pointer;font-family:\'Inter\',sans-serif;">'
        '<span class="material-symbols-outlined" style="font-size:14px;">delete</span> Hapus Terpilih</button>'
        '</div>'
    )

page_html = (
    "<!DOCTYPE html><html lang='id'><head>"
    "<meta charset='utf-8'/>"
    "<meta name='viewport' content='width=device-width, initial-scale=1.0'/>"
    "<title>BeliKuy - Keranjang</title>"
    "<script src='https://cdn.tailwindcss.com?plugins=forms,container-queries'></script>"
    "<link href='https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Plus+Jakarta+Sans:wght@500;600;700;800;900&display=swap' rel='stylesheet'/>"
    "<link href='https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap' rel='stylesheet'/>"
    "<style>*{box-sizing:border-box;margin:0;padding:0;}body{font-family:'Inter',sans-serif;background:#f8f9fa;min-height:100vh;padding-bottom:40px;}::-webkit-scrollbar{display:none;}</style>"
    "</head><body>"
    "<div style='max-width:900px;margin:0 auto;padding:84px 16px 32px;'>"
    "<h1 style=\"font-family:'Plus Jakarta Sans',sans-serif;font-size:28px;font-weight:800;color:#191c1d;margin-bottom:20px;\">Keranjang Belanja</h1>"
    + select_bar
    + "<div id='cart-items'>"
    + (cart_html if cart else empty_html)
    + "</div>"
    + summary_html
    + "</div>"

    # JS
    + "<script>"
    "function fmtRupiah(n){"
    "  return 'Rp '+Math.round(n).toLocaleString('id-ID');"
    "}"
    "function recalc(){"
    "  const all=document.querySelectorAll('.item-cb');"
    "  const checked=document.querySelectorAll('.item-cb:checked');"
    "  let sub=0,count=0;"
    "  if(checked.length===0){"
    "    sub=0;count=0;"
    "  } else {"
    "    checked.forEach(cb=>{sub+=parseFloat(cb.dataset.price||0);});count=checked.length;"
    "  }"
    "  const total=sub;"
    "  const elSub=document.getElementById('dyn-subtotal');"
    "  const elTot=document.getElementById('dyn-total');"
    "  const elLbl=document.getElementById('dyn-label');"
    "  const elBtn=document.getElementById('dyn-checkout-btn');"
    "  if(elSub)elSub.textContent=fmtRupiah(sub);"
    "  if(elTot)elTot.textContent=fmtRupiah(total);"
    "  if(elLbl)elLbl.textContent='Subtotal ('+count+' item)';"
    "  if(elBtn)elBtn.textContent='Checkout ('+count+' item) \u2192';"
    "}"
    "function onItemChange(){"
    "  const all=document.querySelectorAll('.item-cb');"
    "  const checked=document.querySelectorAll('.item-cb:checked');"
    "  const sa=document.getElementById('select-all');"
    "  if(sa){sa.checked=all.length>0&&checked.length===all.length;sa.indeterminate=checked.length>0&&checked.length<all.length;}"
    "  document.querySelectorAll('.shop-cb').forEach(scb=>{"
    "    const s=scb.dataset.shop;"
    "    const si=document.querySelectorAll('.item-cb[data-shop=\"'+s+'\"]');"
    "    const sc=document.querySelectorAll('.item-cb[data-shop=\"'+s+'\"]:checked');"
    "    scb.checked=si.length>0&&sc.length===si.length;"
    "    scb.indeterminate=sc.length>0&&sc.length<si.length;"
    "  });"
    "  const btn=document.getElementById('delete-selected-btn');"
    "  if(btn)btn.style.display=checked.length>0?'inline-flex':'none';"
    "  recalc();"
    "}"
    "function toggleAll(el){"
    "  document.querySelectorAll('.item-cb,.shop-cb').forEach(cb=>cb.checked=el.checked);"
    "  const btn=document.getElementById('delete-selected-btn');"
    "  const checked=document.querySelectorAll('.item-cb:checked');"
    "  if(btn)btn.style.display=checked.length>0?'inline-flex':'none';"
    "  recalc();"
    "}"
    "function toggleShop(shopEl){"
    "  const s=shopEl.dataset.shop;"
    "  document.querySelectorAll('.item-cb[data-shop=\"'+s+'\"]').forEach(cb=>cb.checked=shopEl.checked);"
    "  onItemChange();"
    "}"
    "function deleteSelected(){"
    "  const checked=document.querySelectorAll('.item-cb:checked');"
    "  const indices=Array.from(checked).map(cb=>parseInt(cb.dataset.idx)).sort((a,b)=>b-a);"
    "  if(indices.length>0)stNavigate({action:'delete_selected',indices:indices.join(',')});"
    "}"
    "document.addEventListener('DOMContentLoaded',recalc);"
    "window.addEventListener('load',recalc);"
    "setTimeout(recalc,100);"
    "</script>"
    "</body></html>"
)

page_html = inject_navbar(page_html, len(cart))
action_data = render_original_html("belikuy_v2_cart", page_html, height=1000)

if action_data:
    act = action_data.get('action', '')
    current_user = st.session_state.get('user')
    if handle_global_action(st, act, action_data, current_user):
        pass
    elif act == "go_home":
        st.switch_page("pages/1_Storefront.py")
    elif act == "go_search":
        st.switch_page("pages/2_Cari_Produk.py")
    elif act == "go_detail":
        pid = action_data.get('pid')
        if pid: st.session_state['viewing_product_id'] = pid
        st.switch_page("pages/3_Detail_Produk.py")
    elif act == "go_orders":
        st.switch_page("pages/6_Riwayat_Pesanan.py")
    elif act == "remove_item":
        idx = int(action_data.get("idx", -1))
        c = st.session_state.get('cart', [])
        if 0 <= idx < len(c): c.pop(idx)
        st.rerun()
    elif act == "delete_selected":
        indices_str = action_data.get("indices", "")
        indices = [int(i) for i in indices_str.split(',') if i.strip().isdigit()]
        indices.sort(reverse=True)
        c = st.session_state.get('cart', [])
        for i in indices:
            if 0 <= i < len(c): c.pop(i)
        st.rerun()
    elif act == "inc_qty":
        idx = int(action_data.get("idx", -1))
        c = st.session_state.get('cart', [])
        if 0 <= idx < len(c): c[idx]['qty'] = c[idx].get('qty', 1) + 1
        st.rerun()
    elif act == "dec_qty":
        idx = int(action_data.get("idx", -1))
        c = st.session_state.get('cart', [])
        if 0 <= idx < len(c):
            if c[idx].get('qty', 1) > 1: c[idx]['qty'] -= 1
            else: c.pop(idx)
        st.rerun()
    elif act == "checkout":
        if cart:
            st.switch_page("pages/5_Checkout.py")
        else:
            st.rerun()
