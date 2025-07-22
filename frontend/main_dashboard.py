import streamlit as st
from components.sidebar import render_sidebar

def show():
    render_sidebar()
    st.markdown(f"### Panel principal para {st.session_state.country}")