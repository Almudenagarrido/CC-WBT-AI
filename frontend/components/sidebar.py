import streamlit as st

def render_sidebar():
    with st.sidebar:
        st.markdown("### Navegación")
        if st.button("Fuel Market Info"):
            st.session_state.page = "Fuel Market Information"
        if st.button("Techno-Economic Models"):
            st.session_state.page = "Techno-Economic Models"