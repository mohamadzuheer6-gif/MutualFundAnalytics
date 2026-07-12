"""Sidebar navigation."""
import base64
import importlib
from pathlib import Path

import streamlit as st
import streamlit_app.constants as constants

importlib.reload(constants)

_LOGO_PATH = Path(__file__).resolve().parents[1] / "assets" / "bluestock_full_logo.webp"
_LOGO_B64 = base64.b64encode(_LOGO_PATH.read_bytes()).decode() if _LOGO_PATH.exists() else ""

def render_sidebar(current_page: str) -> None:
    """Render side navigation bar."""
    if _LOGO_B64:
        st.sidebar.markdown(
            f"""
            <div style="text-align: center; padding: 18px 12px 8px 12px;">
                <img src="data:image/webp;base64,{_LOGO_B64}"
                     alt="BlueStock.in"
                     style="width: 100%; max-width: 200px; height: auto; object-fit: contain;" />
            </div>
            <hr style="margin-top: 12px; margin-bottom: 18px; border-color: #E2E8F0;">
            """,
            unsafe_allow_html=True
        )
    else:
        st.sidebar.markdown(
            """
            <div style="text-align: center; padding: 20px 0 10px 0;">
                <h2 style="color: #2E3192; font-weight: 800; margin: 0; font-size: 26px; font-family: 'Inter', sans-serif;">
                    BlueStock
                </h2>
                <span style="color: #F58220; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; font-family: 'Inter', sans-serif;">
                    Analytics Platform
                </span>
            </div>
            <hr style="margin-top: 15px; margin-bottom: 20px; border-color: #E2E8F0;">
            """,
            unsafe_allow_html=True
        )
    
    st.sidebar.markdown("<div class='sidebar-menu'>", unsafe_allow_html=True)
    
    resolved_current = current_page
    for page in constants.PAGES_LIST:
        if page.lower() == current_page.lower() or page.lower() in current_page.lower():
            resolved_current = page
            break
            
    for page in constants.PAGES_LIST:
        is_active = (page == resolved_current)
        btn_type = "primary" if is_active else "secondary"
        label = page
        btn_key = f"nav_btn_{page.lower().replace(' ', '_')}"
        
        if st.sidebar.button(label, key=btn_key, type=btn_type, width="stretch"):
            if not is_active:
                target_file = constants.PAGE_FILES[page]
                st.switch_page(target_file)

    st.sidebar.markdown(
        """
        <script>
            (function() {
                const applyNavClasses = () => {
                    const doc = window.parent.document || document;
                    const buttons = doc.querySelectorAll('div[data-testid="stSidebar"] button');
                    buttons.forEach(btn => {
                        const textEl = btn.querySelector('p') || btn;
                        const text = textEl.textContent || textEl.innerText || "";
                        const cleanText = text.trim().toLowerCase().replace(/[^a-z0-9]+/g, "-");
                        if (cleanText) {
                            btn.classList.add("nav-" + cleanText);
                        }
                    });
                };
                applyNavClasses();
                if (!window.navObserver) {
                    window.navObserver = new MutationObserver(applyNavClasses);
                    window.navObserver.observe(window.parent.document || document, { childList: true, subtree: true });
                }
            })();
        </script>
        """,
        unsafe_allow_html=True
    )
                
    st.sidebar.markdown("</div>", unsafe_allow_html=True)
