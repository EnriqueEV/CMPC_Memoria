"""
CMPC – Gestor de Accesos SAP
Streamlit application entry-point.

Run with:
    streamlit run app/app.py
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path so all internal imports work
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

# ── Page config (must be first Streamlit call) ──────────────────
st.set_page_config(
    page_title="CMPC – Gestor de Accesos SAP",
    page_icon=":material/forest:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Imports after set_page_config ───────────────────────────────
from app.styles import get_custom_css
from app.views import home, new_analysis, analysis_detail
from database.db import get_all_analyses, init_db

# Make sure DB is initialized
init_db()

# Inject custom CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# Session state defaults
# ════════════════════════════════════════════════════════════════
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"
if "selected_analysis_id" not in st.session_state:
    st.session_state.selected_analysis_id = None


# ════════════════════════════════════════════════════════════════
# Sidebar
# ════════════════════════════════════════════════════════════════
with st.sidebar:
    with open("img/LogoCMPC-1.png", "rb") as _f:
        import base64
        _logo_b64 = base64.b64encode(_f.read()).decode()
    st.markdown(
        f'<div class="sidebar-logo"><img src="data:image/png;base64,{_logo_b64}" width="120"></div>',
        unsafe_allow_html=True,
    )

    if st.button("Inicio", use_container_width=True, key="sidebar_home", type="primary", icon=":material/home:"):
        st.session_state.current_page = "home"
        st.rerun()

    if st.button("Nuevo análisis", use_container_width=True, key="sidebar_new", type="primary", icon=":material/add:"):
        st.session_state.current_page = "new"
        st.session_state.selected_analysis_id = None
        st.rerun()

    st.markdown("---")

    # ── Analysis list ───────────────────────────────────────────
    st.markdown("**Análisis previos**")

    analyses = get_all_analyses()
    if analyses:
        for a in analyses[:15]:  # show last 15
            if st.button(a["name"], key=f"sidebar_{a['id']}", use_container_width=True):
                st.session_state.current_page = "detail"
                st.session_state.selected_analysis_id = a["id"]
                st.rerun()
    else:
        st.caption("Sin análisis aún.")


# ════════════════════════════════════════════════════════════════
# Page router
# ════════════════════════════════════════════════════════════════
page = st.session_state.current_page

if page == "home":
    home.render()
elif page == "new":
    new_analysis.render()
elif page == "detail":
    analysis_detail.render()
else:
    home.render()
