import streamlit as st
from state.session import init_session_state
import home, country_selector, main_dashboard

init_session_state()

if st.session_state.page == "home":
    home.show()
elif st.session_state.page == "country_selector":
    country_selector.show()
elif st.session_state.page == "main_dashboard":
    main_dashboard.show()