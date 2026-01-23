import streamlit as st
from state.session import init_session_state
import home, country_selector, main_dashboard

st.markdown("""
    <style>
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
        max-width: 100% !important;
    }
    .stApp {
        max-width: 100vw !important;
    }
    </style>
""", unsafe_allow_html=True)

init_session_state()

if st.session_state.page == "home":
    home.show()
elif st.session_state.page == "country_selector":
    country_selector.show()
elif st.session_state.page == "main_dashboard":
    main_dashboard.show()