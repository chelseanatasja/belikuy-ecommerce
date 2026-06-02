import re

def inject_navbar(html, cart_len, sq=""):
    cart_badge_html = f'<span class="absolute -top-1 -right-1 bg-error text-on-error text-[10px] font-bold h-4 w-4 rounded-full flex items-center justify-center">{cart_len}</span>' if cart_len > 0 else ''
    
    navbar_html = f"""
<nav class="bg-white/90 backdrop-blur-md fixed top-0 w-full z-50 border-b border-pink-50/50 shadow-[0_4px_20px_rgba(255,182,193,0.1)]">
<div class="flex justify-between items-center px-6 py-3 max-w-7xl mx-auto">
    <a class="text-2xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-purple-500 cursor-pointer" style="font-family: 'Plus Jakarta Sans', sans-serif;" onclick="stNavigate({{action:'go_home'}})">BeliKuy</a>
    
    <div class="flex items-center gap-2 sm:gap-4">
        <button onclick="stNavigate({{action:'go_cart'}})" class="p-2 text-pink-400 hover:text-pink-500 hover:bg-pink-50 rounded-full transition-colors relative">
            <span class="material-symbols-outlined">shopping_cart</span>
            {cart_badge_html}
        </button>
        <button onclick="stNavigate({{action:'go_orders'}})" class="p-2 text-pink-400 hover:text-pink-500 hover:bg-pink-50 rounded-full transition-colors relative" title="Riwayat Pesanan">
            <span class="material-symbols-outlined">receipt_long</span>
        </button>
        <button onclick="stNavigate({{action:'go_profile'}})" class="p-2 text-pink-400 hover:text-pink-500 hover:bg-pink-50 rounded-full transition-colors relative" title="Profil">
            <span class="material-symbols-outlined">person</span>
        </button>
    </div>
</div>
</nav>
"""
    # Try to replace the first <nav> or <header> in the page
    new_html = re.sub(r'(<nav[^>]*>.*?</nav>|<header[^>]*>.*?</header>)', navbar_html, html, count=1, flags=re.DOTALL)
    # If nothing was replaced (custom page with no nav/header), inject right after <body>
    if new_html == html:
        new_html = re.sub(r'(<body[^>]*>)', rf'\1\n{navbar_html}', html, count=1)
    return new_html

def handle_global_action(st, act, action_data, user):
    if act == "global_search":
        if action_data.get('q'):
            st.session_state['search_query'] = action_data.get('q')
        st.switch_page("pages/2_Cari_Produk.py")
        return True
    elif act == "go_home":
        st.switch_page("pages/1_Storefront.py")
        return True
    elif act in ("go_search", "search"):
        if action_data.get('q'):
            st.session_state['search_query'] = action_data.get('q')
        if action_data.get('cat'):
            st.session_state['search_cat'] = action_data.get('cat')
        st.switch_page("pages/2_Cari_Produk.py")
        return True
    elif act == "go_cart":
        st.switch_page("pages/4_Keranjang.py")
        return True
    elif act == "go_orders":
        if user:
            st.switch_page("pages/6_Riwayat_Pesanan.py")
        else:
            st.switch_page("app.py")
        return True
    elif act == "go_profile":
        if user:
            st.switch_page("pages/8_Profil.py")
        else:
            st.switch_page("app.py")
        return True
    return False
