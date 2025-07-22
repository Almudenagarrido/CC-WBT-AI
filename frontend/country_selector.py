import os
import time
import streamlit as st
from config import COUNTRIES as INITIAL_COUNTRIES

def show():
    st.title("Select a country:")

    if "countries" not in st.session_state:
        st.session_state.countries = INITIAL_COUNTRIES.copy()

    selected = st.session_state.get("selected_country", None)

    for country in st.session_state.countries:
        col1, col2 = st.columns([0.9, 0.1])

        with col1:
            if st.button(f"{country}", key=f"btn_{country}"):
                st.session_state.selected_country = country
                st.rerun()

        if selected == country:
            with col2:
                if st.button("🗑️", key=f"delete_{country}"):
                    st.session_state.countries.remove(country)
                    del st.session_state.selected_country
                    st.rerun()
                
    if selected:
        st.markdown(f"### Selected country: {selected}")

        image_path = f"public/{selected}.png"
        if os.path.exists(image_path):
            st.image(image_path, width=100)

        if st.button("Start modeling", key=f"start_{selected}"):
            st.session_state.country = selected
            st.session_state.page = "main_dashboard"
            st.rerun()

    with st.expander("➕ Add a new country"):
        new_country = st.text_input("New country name")
        if st.button("Add country"):
            new_country = new_country.strip()
            if new_country and new_country not in st.session_state.countries:
                st.session_state.countries.append(new_country)
                st.success(f"{new_country} added to the list.")
                time.sleep(1)
                st.rerun()
            elif new_country in st.session_state.countries:
                st.warning(f"{new_country} already exists.")