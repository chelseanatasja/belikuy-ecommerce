import streamlit as st
import sys, os, re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from utils import require_login, hide_streamlit_ui
from html_bridge import render_original_html
from unified_navbar import inject_navbar, handle_global_action

st.set_page_config(
    page_title="BeliKuy - Profil Saya", layout="wide", initial_sidebar_state="collapsed"
)
hide_streamlit_ui()
require_login()

user = st.session_state["user"]
username = str(user.get("username", "User"))
email = str(user.get("email", ""))
role = str(user.get("role", "customer")).capitalize()

phone = str(user.get("phone", ""))
gender = str(user.get("gender", "female"))
dob_raw = str(user.get("dob", ""))
dob = dob_raw[:10] if len(dob_raw) >= 10 else ""

HTML_BASE = (
    r"D:\Tugas Kuliah\Semester 4\Workshop RPL\belikuy-ecommerce\belikuy_ui_templates"
)
with open(
    os.path.join(HTML_BASE, "user_profile_page/code.html"), encoding="utf-8"
) as f:
    html = f.read()

# Dynamic data injection
html = html.replace('value="Amanda Putri"', f'id="inp_name" value="{username}"')
html = html.replace(
    'value="amanda.putri@example.com"', f'id="inp_email" value="{email}"'
)
html = html.replace('value="0812-3456-7890"', f'id="inp_phone" value="{phone}"')
html = html.replace('value="1995-08-15"', f'id="inp_dob" value="{dob}"')

if gender == "male":
    html = html.replace('value="male"', 'id="gender_male" value="male" checked')
    html = html.replace(
        'checked="" class="text-primary focus:ring-primary-container" name="gender" type="radio" value="female"',
        'id="gender_female" class="text-primary focus:ring-primary-container" name="gender" type="radio" value="female"',
    )
else:
    html = html.replace('value="male"', 'id="gender_male" value="male"')
    html = html.replace(
        'checked="" class="text-primary focus:ring-primary-container" name="gender" type="radio" value="female"',
        'id="gender_female" checked class="text-primary focus:ring-primary-container" name="gender" type="radio" value="female"',
    )

html = html.replace("Amanda Putri", username)
html = html.replace("amanda.putri@example.com", email)
html = html.replace("Gold Member", role)

# Replace sidebar nav with functional links
sidebar_replacement = """<nav class="flex flex-col gap-sm">
    <a href="javascript:void(0)" onclick="event.preventDefault();" class="flex items-center gap-3 bg-pink-100/50 text-pink-600 rounded-lg px-4 py-3 font-h3 text-body-sm font-semibold transition-all">
        <span class="material-symbols-outlined text-[20px]" style="font-variation-settings: 'FILL' 1;">person</span>
        Profil Saya
    </a>
    <a href="javascript:void(0)" onclick="event.preventDefault(); stNavigate({action:'go_addresses'});" class="flex items-center gap-3 text-on-surface-variant hover:bg-surface-bright rounded-lg px-4 py-3 font-body-md text-body-sm transition-all">
        <span class="material-symbols-outlined text-[20px]">location_on</span>
        Alamat
    </a>
    <a href="javascript:void(0)" onclick="event.preventDefault(); stNavigate({action:'logout'});" class="flex items-center gap-3 text-error hover:bg-error-container/20 rounded-lg px-4 py-3 font-body-md text-body-sm transition-all mt-4 border-t border-surface-variant">
        <span class="material-symbols-outlined text-[20px]">logout</span>
        Keluar
    </a>
</nav>"""

html = re.sub(
    r'<nav class="flex flex-col gap-sm">.*?</nav>',
    sidebar_replacement,
    html,
    flags=re.DOTALL,
)

# Add save action
html = re.sub(
    r'(<button class="[^"]*from-pink-400[^"]*")( type="button">)',
    r'\1 onclick="submitProfile()"\2',
    html,
)

js_helper = """
<script>
function submitProfile() {
    var name = document.getElementById("inp_name").value;
    var email = document.getElementById("inp_email").value;
    var phone = document.getElementById("inp_phone").value;
    var dob = document.getElementById("inp_dob").value;
    var gender = document.getElementById("gender_male").checked ? "male" : "female";
    stNavigate({action: 'save_profile', name: name, email: email, phone: phone, dob: dob, gender: gender});
}
</script>
"""
html = html.replace("</head>", js_helper + "</head>")


# ── Inject Unified Navbar ───────────────────────────────────────────────────
cart_len = len(st.session_state.get("cart", []))
html = inject_navbar(html, cart_len)

# Disable plain href="#"
html = html.replace('href="#"', 'href="#" onclick="event.preventDefault();"')

action_data = render_original_html("belikuy_v2_profile", html, height=1000)

with open("debug_profile.txt", "a") as f:
    f.write(f"ACTION: {action_data}\n")

if action_data:
    act = action_data.get("action")
    current_user = st.session_state.get("user")
    if handle_global_action(st, act, action_data, current_user):
        pass
    elif act == "go_home":
        st.switch_page("pages/1_Storefront.py")
    elif act == "go_orders":
        st.switch_page("pages/6_Riwayat_Pesanan.py")
    elif act == "go_addresses":
        st.switch_page("pages/7_Alamat.py")
    elif act == "logout":
        st.session_state.clear()
        st.session_state["_auto_logout"] = True
        st.switch_page("app.py")
    elif act == "save_profile":
        from utils import put_api

        res, status = put_api(
            f"auth/profile/{user['id']}",
            {
                "name": action_data.get("name"),
                "email": action_data.get("email"),
                "phone": action_data.get("phone"),
                "dob": action_data.get("dob"),
                "gender": action_data.get("gender"),
            },
        )
        if status == 200 and res.get("user"):
            st.session_state["user"] = res["user"]
            st.success("Profil berhasil diperbarui!")
            st.rerun()
        else:
            st.error("Gagal memperbarui profil")
