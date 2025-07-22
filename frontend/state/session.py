import streamlit as st

def init_session_state():
    defaults = {
        "page": "home",
        "country": None,
        "model": None,
        "section": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
