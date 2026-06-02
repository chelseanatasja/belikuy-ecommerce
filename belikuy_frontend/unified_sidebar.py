import re
import os

def inject_seller_sidebar(html, current_page, company_name="Kawaiify Official"):
    """
    Injects a unified sidebar into a seller page HTML.
    Strips existing <aside>...</aside> and mobile <nav>...</nav> and replaces it.
    """
    
    # Define links and determine active states
    links = [
        {"id": "dashboard", "icon": "dashboard", "text": "Dashboard", "action": "go_dashboard", "active_match": ["9_Seller_Dashboard"]},
        {"id": "products", "icon": "inventory_2", "text": "Produk", "action": "go_products", "active_match": ["10_Kelola_Produk"]},
        {"id": "orders", "icon": "shopping_bag", "text": "Pesanan", "action": "go_orders", "active_match": ["11_Kelola_Pesanan"]},
        {"id": "analytics", "icon": "analytics", "text": "Laporan", "action": "go_income", "active_match": ["12_Laporan_Pendapatan"]},
        {"id": "supplier_procurement", "icon": "local_shipping", "text": "Pesan Stok (B2B)", "action": "go_supplier_procurement", "active_match": ["22_Pesan_Stok_Supplier"]},
        {"id": "supplier_payment", "icon": "request_quote", "text": "Tagihan Supplier", "action": "go_supplier_payment", "active_match": ["23_Tagihan_Supplier"]},
        {"id": "settings", "icon": "settings", "text": "Pengaturan", "action": "go_settings", "active_match": ["19_Seller_Settings"]},
    ]
    
    desktop_links_html = ""
    for link in links:
        is_active = any(match in current_page for match in link["active_match"])
        if is_active:
            desktop_links_html += f'''
            <a href="javascript:void(0)" onclick="event.preventDefault(); stNavigate({{action:'{link['action']}'}});" class="bg-pink-100/50 dark:bg-pink-900/20 text-pink-600 dark:text-pink-300 rounded-xl px-4 py-3 mb-1 flex items-center gap-3 group">
                <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">{link['icon']}</span>
                <span>{link['text']}</span>
            </a>
            '''
        else:
            desktop_links_html += f'''
            <a href="javascript:void(0)" onclick="event.preventDefault(); stNavigate({{action:'{link['action']}'}});" class="text-zinc-500 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-xl px-4 py-3 mb-1 hover:translate-x-1 transition-all duration-300 flex items-center gap-3 group">
                <span class="material-symbols-outlined">{link['icon']}</span>
                <span>{link['text']}</span>
            </a>
            '''
    
    # Storefront and Logout at the bottom
    desktop_links_html += '''
            <a href="javascript:void(0)" onclick="event.preventDefault(); stNavigate({action:'go_storefront'});" class="text-zinc-500 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-xl px-4 py-3 mb-1 mt-4 hover:translate-x-1 transition-all duration-300 flex items-center gap-3 group border-t border-zinc-200 dark:border-zinc-800 pt-4">
                <span class="material-symbols-outlined">storefront</span>
                <span>Ke Storefront</span>
            </a>
            <a href="javascript:void(0)" onclick="event.preventDefault(); stNavigate({action:'logout'});" class="text-error hover:bg-error-container/20 rounded-xl px-4 py-3 mb-1 hover:translate-x-1 transition-all duration-300 flex items-center gap-3 group">
                <span class="material-symbols-outlined">logout</span>
                <span>Keluar</span>
            </a>
    '''
    
    sidebar_html = f'''
    <!-- SideNavBar -->
    <aside class="bg-zinc-50 dark:bg-zinc-900 text-pink-400 dark:text-pink-300 font-['Plus_Jakarta_Sans'] text-sm font-semibold h-screen w-64 fixed left-0 top-0 border-r border-zinc-200 dark:border-zinc-800 flex flex-col p-4 tap-highlight-transparent z-40 hidden md:flex">
        <!-- Header -->
        <div class="mb-8 px-4 flex items-center gap-3">
            <img alt="Store Logo" class="w-10 h-10 rounded-full object-cover shadow-[0_4px_10px_rgba(255,182,193,0.3)]" src="https://via.placeholder.com/150/ffb6c1/ffffff?text=Toko"/>
            <div>
                <h2 class="text-xl font-bold text-zinc-900 dark:text-white leading-tight line-clamp-1">{company_name}</h2>
                <p class="text-xs text-zinc-500 font-normal">BeliKuy Seller</p>
            </div>
        </div>
        
        <!-- Navigation Links -->
        <nav class="flex-1 space-y-1 overflow-y-auto">
            {desktop_links_html}
        </nav>
    </aside>
    '''
    
    # Generate mobile nav
    mobile_links_html = ""
    for link in links:
        is_active = any(match in current_page for match in link["active_match"])
        if is_active:
            mobile_links_html += f'''
            <a href="javascript:void(0)" onclick="event.preventDefault(); stNavigate({{action:'{link['action']}'}});" class="flex flex-col items-center justify-center bg-gradient-to-br from-pink-50 to-purple-50 dark:from-pink-950/30 dark:to-purple-950/30 text-pink-500 rounded-2xl px-5 py-2 scale-110 duration-500 ease-out">
                <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">{link['icon']}</span>
                <span class="mt-1">{link['text']}</span>
            </a>
            '''
        else:
            mobile_links_html += f'''
            <a href="javascript:void(0)" onclick="event.preventDefault(); stNavigate({{action:'{link['action']}'}});" class="flex flex-col items-center justify-center text-zinc-400 dark:text-zinc-500 px-5 py-2 hover:text-pink-400 scale-110 duration-500 ease-out">
                <span class="material-symbols-outlined">{link['icon']}</span>
                <span class="mt-1">{link['text']}</span>
            </a>
            '''
            
    mobile_nav_html = f'''
    <!-- BottomNavBar (Mobile Only) -->
    <nav class="bg-white/90 dark:bg-zinc-950/90 backdrop-blur-xl text-pink-400 dark:text-pink-300 font-['Plus_Jakarta_Sans'] text-[10px] uppercase tracking-widest border-t border-pink-100/30 dark:border-zinc-800 shadow-[0_-10px_40px_rgba(255,182,193,0.15)] fixed bottom-0 left-0 w-full z-50 flex justify-around items-center px-4 pb-6 pt-3 md:hidden">
        {mobile_links_html}
    </nav>
    '''
    
    # Strip existing sidebar - supports both <aside> and <nav> based templates
    html = re.sub(r'<aside[^>]*>.*?</aside>', '', html, flags=re.DOTALL)
    # Also strip nav-based sidebars (identified by w-64 fixed class pattern)
    html = re.sub(r'<nav[^>]*(?:w-64|fixed left-0)[^>]*>.*?</nav>', '', html, flags=re.DOTALL)
    # Strip existing mobile nav (md:hidden)
    html = re.sub(r'<nav[^>]*md:hidden[^>]*>.*?</nav>', '', html, flags=re.DOTALL)
    
    # Inject Plus Jakarta Sans font to ensure sidebar displays correctly
    if "Plus+Jakarta+Sans" not in html:
        font_link = '<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap" rel="stylesheet"/>'
        html = html.replace("</head>", f"    {font_link}\n</head>")
        
    # Re-inject our unified sidebar and mobile nav right after <body>
    html = re.sub(r'(<body[^>]*>)', rf'\1\n{sidebar_html}\n{mobile_nav_html}', html)
    
    return html

def handle_seller_global_action(st, act):
    """
    Handles routing for the unified seller sidebar.
    Returns True if an action was handled, False otherwise.
    """
    if act == "go_dashboard":
        st.switch_page("pages/9_Seller_Dashboard.py")
        return True
    elif act == "go_products":
        st.switch_page("pages/10_Kelola_Produk.py")
        return True
    elif act == "go_orders":
        st.switch_page("pages/11_Kelola_Pesanan.py")
        return True
    elif act == "go_income":
        st.switch_page("pages/12_Laporan_Pendapatan.py")
        return True
    elif act == "go_settings":
        st.switch_page("pages/19_Seller_Settings.py")
        return True
    elif act == "go_supplier_procurement":
        st.switch_page("pages/22_Pesan_Stok_Supplier.py")
        return True
    elif act == "go_supplier_payment":
        st.switch_page("pages/23_Tagihan_Supplier.py")
        return True
    elif act == "go_storefront":
        st.switch_page("pages/1_Storefront.py")
        return True
    elif act == "logout":
        st.session_state.clear()
        st.session_state['_auto_logout'] = True
        st.switch_page("app.py")
        return True
    return False

def inject_admin_sidebar(html, current_page, admin_name="Admin Utama"):
    """
    Injects a unified sidebar into an admin page HTML.
    Strips existing <aside>...</aside> and mobile <nav>...</nav> and replaces it.
    """
    
    # Define links and determine active states
    links = [
        {"id": "dashboard", "icon": "dashboard", "text": "Dashboard", "action": "go_admin_dashboard", "active_match": ["13_Admin_Dashboard"]},
        {"id": "vendors", "icon": "store", "text": "Manajemen Toko", "action": "go_admin_vendors", "active_match": ["14_Manajemen_Vendor"]},
        {"id": "suppliers", "icon": "inventory_2", "text": "Manajemen Supplier", "action": "go_admin_suppliers", "active_match": ["17_Manajemen_Supplier"]},
        {"id": "shipments", "icon": "local_shipping", "text": "Manajemen Ekspedisi", "action": "go_admin_shipments", "active_match": ["16_Manajemen_Ekspedisi"]},
        {"id": "payments", "icon": "account_balance", "text": "Manajemen Pembayaran", "action": "go_admin_payments", "active_match": ["21_Manajemen_Pembayaran"]},
        {"id": "withdrawals", "icon": "account_balance_wallet", "text": "Penarikan Dana", "action": "go_admin_withdrawals", "active_match": ["20_Admin_Withdrawals"]},
        {"id": "transactions", "icon": "monitoring", "text": "Monitoring Transaksi", "action": "go_admin_transactions", "active_match": ["15_Monitoring_Transaksi"]},
    ]
    
    desktop_links_html = ""
    for link in links:
        is_active = any(match in current_page for match in link["active_match"])
        if is_active:
            desktop_links_html += f'''
            <a href="javascript:void(0)" onclick="event.preventDefault(); stNavigate({{action:'{link['action']}'}});" class="bg-primary-container/20 text-primary-fixed-dim rounded-xl px-4 py-3 mb-1 flex items-center gap-3 font-h3 font-semibold text-sm">
                <span class="material-symbols-outlined text-primary-fixed-dim" style="font-variation-settings: 'FILL' 1;">{link['icon']}</span>
                <span>{link['text']}</span>
            </a>
            '''
        else:
            desktop_links_html += f'''
            <a href="javascript:void(0)" onclick="event.preventDefault(); stNavigate({{action:'{link['action']}'}});" class="text-on-surface-variant hover:bg-surface-container hover:text-on-background rounded-xl px-4 py-3 mb-1 flex items-center gap-3 transition-colors duration-200 font-h3 font-semibold text-sm">
                <span class="material-symbols-outlined text-outline">{link['icon']}</span>
                <span>{link['text']}</span>
            </a>
            '''
    
    # Storefront and Logout at the bottom
    desktop_links_html += '''
            <a href="javascript:void(0)" onclick="event.preventDefault(); stNavigate({action:'go_storefront'});" class="text-on-surface-variant hover:bg-surface-container hover:text-on-background rounded-xl px-4 py-3 mb-1 mt-4 transition-colors duration-200 flex items-center gap-3 font-h3 font-semibold text-sm border-t border-surface-variant pt-4">
                <span class="material-symbols-outlined text-outline">storefront</span>
                <span>Ke Storefront</span>
            </a>
            <a href="javascript:void(0)" onclick="event.preventDefault(); stNavigate({action:'logout'});" class="text-error hover:bg-error-container/20 rounded-xl px-4 py-3 mb-1 transition-colors duration-200 flex items-center gap-3 font-h3 font-semibold text-sm">
                <span class="material-symbols-outlined">logout</span>
                <span>Keluar</span>
            </a>
    '''
    
    sidebar_html = f'''
    <!-- SideNavBar -->
    <nav class="hidden md:flex flex-col h-screen fixed left-0 top-0 border-r bg-surface-container-lowest border-surface-variant z-40 p-4" style="width: 256px; min-width: 256px; max-width: 256px;">
        <!-- Header -->
        <div class="mb-8 px-2 flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-primary-container flex items-center justify-center text-on-primary-container">
                <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">admin_panel_settings</span>
            </div>
            <div>
                <h1 class="text-xl font-bold text-on-background tracking-tight">Super Admin</h1>
                <p class="text-sm text-on-surface-variant">BeliKuy Platform</p>
            </div>
        </div>
        
        <!-- Links -->
        <div class="flex flex-col gap-1 flex-1 overflow-y-auto no-scrollbar">
            {desktop_links_html}
        </div>
        
        <!-- Bottom User Info -->
        <div class="mt-auto border-t border-surface-variant pt-4 px-2">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-full bg-primary flex items-center justify-center text-on-primary font-bold shadow-sm">
                    {admin_name[0]}
                </div>
                <div>
                    <p class="font-h3 font-semibold text-sm text-on-background">{admin_name}</p>
                    <p class="font-body-sm text-xs text-on-surface-variant">System Owner</p>
                </div>
            </div>
        </div>
    </nav>
    '''
    
    mobile_links_html = ""
    for link in links[:4]: # only show first 4 on mobile
        is_active = any(match in current_page for match in link["active_match"])
        if is_active:
            mobile_links_html += f'''
            <a href="javascript:void(0)" onclick="event.preventDefault(); stNavigate({{action:'{link['action']}'}});" class="flex flex-col items-center justify-center bg-primary-container/20 text-primary-fixed-dim rounded-2xl px-5 py-2">
                <span class="material-symbols-outlined mb-1" style="font-variation-settings: 'FILL' 1;">{link['icon']}</span>
                <span class="font-label-caps text-[10px]">{link['text'].split()[0]}</span>
            </a>
            '''
        else:
            mobile_links_html += f'''
            <a href="javascript:void(0)" onclick="event.preventDefault(); stNavigate({{action:'{link['action']}'}});" class="flex flex-col items-center justify-center text-on-surface-variant hover:text-on-background px-5 py-2">
                <span class="material-symbols-outlined mb-1">{link['icon']}</span>
                <span class="font-label-caps text-[10px]">{link['text'].split()[0]}</span>
            </a>
            '''
    
    mobile_nav_html = f'''
    <!-- BottomNavBar (Mobile Only) -->
    <nav class="md:hidden fixed bottom-0 left-0 w-full z-50 flex justify-around items-center px-4 pb-6 pt-3 bg-surface-container-lowest/90 backdrop-blur-xl rounded-t-3xl border-t border-surface-variant shadow-[0_-10px_40px_rgba(255,182,193,0.15)]">
        {mobile_links_html}
    </nav>
    '''
    
    # Strip existing sidebar - supports both <aside> and <nav> based templates
    html = re.sub(r'<aside[^>]*>.*?</aside>', '', html, flags=re.DOTALL)
    # Also strip nav-based sidebars (identified by w-64 fixed class pattern)
    html = re.sub(r'<nav[^>]*(?:w-64|fixed left-0)[^>]*>.*?</nav>', '', html, flags=re.DOTALL)
    # Strip existing mobile nav (md:hidden)
    html = re.sub(r'<nav[^>]*md:hidden[^>]*>.*?</nav>', '', html, flags=re.DOTALL)
    
    # Standardize main content header
    title_map = {
        "13_Admin_Dashboard": "Overview Platform",
        "14_Manajemen_Vendor": "Manajemen Vendor",
        "15_Monitoring_Transaksi": "Monitoring Transaksi",
        "16_Manajemen_Ekspedisi": "Manajemen Ekspedisi",
        "17_Manajemen_Supplier": "Manajemen Supplier",
        "20_Admin_Withdrawals": "Penarikan Dana",
        "21_Manajemen_Pembayaran": "Manajemen Pembayaran"
    }
    
    correct_title = next((title_map[key] for key in title_map if key in current_page), "Super Admin")
    
    # Replace the FIRST matching h1/h2/h3 that looks like a page title with our standardized h1
    # We skip the sidebar's own "Super Admin" header since we inject the sidebar *after* this step.
    html = re.sub(
        r'<h[123][^>]*>(Platform Overview|Overview Platform|Manajemen Vendor|Transaction Monitoring|Seller Center|Monitoring Transaksi|Kelola Penarikan Dana Seller)</h[123]>',
        rf'<h1 style="font-family: \'Plus Jakarta Sans\', sans-serif !important; font-size: 32px !important; font-weight: 700 !important; color: #191c1d !important; margin-bottom: 24px !important;">{correct_title}</h1>',
        html,
        count=1
    )
    
    # Inject Plus Jakarta Sans font to ensure sidebar displays correctly
    if "Plus+Jakarta+Sans" not in html:
        font_link = '<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap" rel="stylesheet"/>'
        html = html.replace("</head>", f"    {font_link}\n</head>")
        
    # Re-inject our unified sidebar and mobile nav right after <body>
    html = re.sub(r'(<body[^>]*>)', rf'\1\n{sidebar_html}\n{mobile_nav_html}', html)
    
    # Fix main canvas padding if necessary
    # Ensure <main> has ml-64 to accommodate the new fixed sidebar
    if 'ml-64' not in html and '<main' in html:
        html = re.sub(r'(<main[^>]*class="([^"]*)")', lambda m: m.group(1).replace(m.group(2), m.group(2) + " ml-0 md:ml-64"), html)
        
    return html

def handle_admin_global_action(st, act):
    """
    Handles routing for the unified admin sidebar.
    Returns True if an action was handled, False otherwise.
    """
    if act == "go_admin_dashboard":
        st.switch_page("pages/13_Admin_Dashboard.py")
        return True
    elif act == "go_admin_vendors":
        st.switch_page("pages/14_Manajemen_Vendor.py")
        return True
    elif act == "go_admin_shipments":
        st.switch_page("pages/16_Manajemen_Ekspedisi.py")
        return True
    elif act == "go_admin_suppliers":
        st.switch_page("pages/17_Manajemen_Supplier.py")
        return True
    elif act == "go_admin_transactions":
        st.switch_page("pages/15_Monitoring_Transaksi.py")
        return True
    elif act == "go_admin_payments":
        st.switch_page("pages/21_Manajemen_Pembayaran.py")
        return True
    elif act == "go_admin_withdrawals":
        st.switch_page("pages/20_Admin_Withdrawals.py")
        return True
    elif act == "go_storefront":
        st.switch_page("pages/1_Storefront.py")
        return True
    elif act == "logout":
        st.session_state.clear()
        st.session_state['_auto_logout'] = True
        st.switch_page("app.py")
        return True
    return False

