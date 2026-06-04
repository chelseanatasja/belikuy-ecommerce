import streamlit as st
import streamlit.components.v1 as components
import os, sys

if "html_bridge" not in sys.modules:
    sys.modules["html_bridge"] = sys.modules[__name__]

JS_LIB = """
window.Streamlit={
setComponentReady:function(){window.parent.postMessage({isStreamlitMessage:true,type:"streamlit:componentReady",apiVersion:1},"*");},
setFrameHeight:function(h){if(!h)h=Math.max(document.body.scrollHeight,document.documentElement.scrollHeight)+40;window.parent.postMessage({isStreamlitMessage:true,type:"streamlit:setFrameHeight",height:h},"*");},
setComponentValue:function(v){window.parent.postMessage({isStreamlitMessage:true,type:"streamlit:setComponentValue",value:v},"*");}
};
window.addEventListener("message",function(e){if(e.data.type==="streamlit:render")Streamlit.setFrameHeight();});
"""

BRIDGE = """
<script src="./streamlit-component-lib.js"></script>
<script>
function stNavigate(p){p._ts=Date.now();Streamlit.setComponentValue(p);}
function _uh(){var h=Math.max(document.body.scrollHeight,document.documentElement.scrollHeight)+40;Streamlit.setFrameHeight(h);}
document.addEventListener("DOMContentLoaded",function(){
    document.body.style.minHeight='auto';
    Streamlit.setComponentReady();
    setTimeout(_uh,300);setTimeout(_uh,900);setTimeout(_uh,2000);
    if(window.ResizeObserver)new ResizeObserver(_uh).observe(document.body);
    
    // Global Auto-Login Trigger
    var user_json = localStorage.getItem('bk_user');
    if (!window.stUserLoggedIn) {
        if (user_json) {
            setTimeout(function() {
                stNavigate({ action: 'global_auto_login', user_json: user_json });
            }, 300);
        } else {
            setTimeout(function() {
                stNavigate({ action: 'global_auto_login_failed' });
            }, 300);
        }
    }
});
</script>
"""

_declared = {}


def _do_declare(page_id, comp_dir):
    return components.declare_component(page_id, path=comp_dir)


def render_original_html(page_id, html_content, height=800):
    html_content = inject_localstorage_sync(html_content)
    comp_dir = os.path.realpath(
        os.path.join(os.path.dirname(__file__), "st_components", page_id)
    )
    os.makedirs(comp_dir, exist_ok=True)
    with open(
        os.path.join(comp_dir, "streamlit-component-lib.js"), "w", encoding="utf-8"
    ) as f:
        f.write(JS_LIB)
    final = (
        html_content.replace("</body>", BRIDGE + "\n</body>", 1)
        if "</body>" in html_content
        else html_content + BRIDGE
    )
    with open(os.path.join(comp_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(final)
    if page_id not in _declared:
        _declared[page_id] = _do_declare(page_id, comp_dir)

    # We must pass html_hash as an argument so Streamlit re-renders the iframe if html changes
    # But more importantly, we MUST debounce the action_data using the _ts timestamp!
    # Otherwise Streamlit component retains the last value, causing an infinite rerun loop.
    action_data = _declared[page_id](html_hash=hash(final))

    if action_data and isinstance(action_data, dict):
        ts = action_data.get("_ts")
        state_key = f"last_ts_{page_id}"
        if ts and ts != st.session_state.get(state_key):
            st.session_state[state_key] = ts

            # Global interceptor for auto-login
            if action_data.get("action") == "global_auto_login":
                import json

                try:
                    uj = action_data.get("user_json", "{}")
                    if not uj or not str(uj).strip():
                        uj = "{}"
                    st.session_state["user"] = json.loads(uj)
                    st.rerun()
                except Exception:
                    pass
            elif action_data.get("action") == "global_auto_login_failed":
                st.session_state["_redirect_to_login"] = True
                st.rerun()

            return action_data
    return None


def inject_localstorage_sync(html_content):
    import json

    if st.session_state.get("user"):
        u_str = (
            json.dumps(st.session_state["user"]).replace("'", "\\'").replace('"', '\\"')
        )
        script = f"<script>window.stUserLoggedIn = true; localStorage.setItem('bk_user', '{u_str}');</script>"
        html_content = html_content.replace("</head>", script + "\n</head>", 1)
    elif st.session_state.get("_auto_logout"):
        st.session_state.pop("_auto_logout")
        script = "<script>window.stUserLoggedIn = false; localStorage.removeItem('bk_user');</script>"
        html_content = html_content.replace("</head>", script + "\n</head>", 1)
    else:
        script = "<script>window.stUserLoggedIn = false;</script>"
        html_content = html_content.replace("</head>", script + "\n</head>", 1)
    return html_content
