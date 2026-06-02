import re

def inject_custom_sidebar(html, title, role_name, icon="admin_panel_settings", initials="X"):
    """
    Injects a minimalist unified sidebar for new roles (Supplier, Fintech, Delivery).
    """
    
    desktop_links_html = f'''
        <a href="javascript:void(0)" class="bg-primary-container/20 text-primary-fixed-dim rounded-xl px-4 py-3 mb-1 flex items-center gap-3 font-h3 font-semibold text-sm">
            <span class="material-symbols-outlined text-primary-fixed-dim" style="font-variation-settings: 'FILL' 1;">dashboard</span>
            <span>Dashboard</span>
        </a>
        <a href="javascript:void(0)" onclick="event.preventDefault(); stNavigate({{action:'logout'}});" class="text-error hover:bg-error-container/20 rounded-xl px-4 py-3 mb-1 transition-colors duration-200 flex items-center gap-3 font-h3 font-semibold text-sm mt-4 border-t border-surface-variant pt-4">
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
                <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">{icon}</span>
            </div>
            <div>
                <h1 class="text-xl font-bold text-on-background tracking-tight">{title}</h1>
                <p class="text-sm text-on-surface-variant">{role_name} BeliKuy</p>
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
                    {initials}
                </div>
                <div>
                    <p class="font-h3 font-semibold text-sm text-on-background">{title}</p>
                    <p class="font-body-sm text-xs text-on-surface-variant">Terverifikasi</p>
                </div>
            </div>
        </div>
    </nav>
    '''
    
    mobile_nav_html = f'''
    <!-- BottomNavBar (Mobile Only) -->
    <nav class="md:hidden fixed bottom-0 left-0 w-full z-50 flex justify-around items-center px-4 pb-6 pt-3 bg-surface-container-lowest/90 backdrop-blur-xl rounded-t-3xl border-t border-surface-variant shadow-[0_-10px_40px_rgba(255,182,193,0.15)]">
        <a href="javascript:void(0)" class="flex flex-col items-center justify-center bg-primary-container/20 text-primary-fixed-dim rounded-2xl px-5 py-2">
            <span class="material-symbols-outlined mb-1" style="font-variation-settings: 'FILL' 1;">dashboard</span>
            <span class="font-label-caps text-[10px]">Home</span>
        </a>
        <a href="javascript:void(0)" onclick="event.preventDefault(); stNavigate({{action:'logout'}});" class="flex flex-col items-center justify-center text-on-surface-variant hover:text-error px-5 py-2">
            <span class="material-symbols-outlined mb-1">logout</span>
            <span class="font-label-caps text-[10px]">Logout</span>
        </a>
    </nav>
    <style>
        @media (min-width: 768px) {{
            .block-container {{
                padding-left: 280px !important;
                padding-top: 2rem !important;
            }}
        }}
    </style>
    '''
    
    # Strip existing sidebars
    html = re.sub(r'<aside[^>]*>.*?</aside>', '', html, flags=re.DOTALL)
    html = re.sub(r'<nav[^>]*(?:w-64|fixed left-0)[^>]*>.*?</nav>', '', html, flags=re.DOTALL)
    html = re.sub(r'<nav[^>]*md:hidden[^>]*>.*?</nav>', '', html, flags=re.DOTALL)
    
    # Re-inject our unified sidebar and mobile nav right after <body>
    html = re.sub(r'(<body[^>]*>)', rf'\1\n{sidebar_html}\n{mobile_nav_html}', html)
    
    return html
