import streamlit as st

def init_session_state():
    defaults = {
        "page": "home",
        "country": None,
        "section": None,
        "subsection": None,
        "model": None,
        "fuel": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
