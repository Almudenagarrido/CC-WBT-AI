import streamlit as st

def render_sidebar():
    with st.sidebar:
        st.markdown("### Navegación")
        if st.button("⌂"):
            st.session_state.page = "country_selector"
            st.session_state.selected_country = None
            st.rerun()