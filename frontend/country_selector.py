import os
import time
import streamlit as st
import utils as u

def show():
    st.markdown("### Select a country scenario to begin modeling:")

    if "countries" not in st.session_state:
        st.session_state.countries = u.get_countries_from_backend()

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
                    result = u.delete_country_from_backend(country)
                    if result is not None:
                        st.session_state.countries = u.get_countries_from_backend()
                        if "selected_country" in st.session_state:
                            del st.session_state.selected_country
                        st.success(f"{country} deleted.")
                        st.rerun()

    if selected:
        st.markdown(f"### Selected country: {selected}")

        image_path = f"public/{selected}.png"
        if os.path.exists(image_path):
            st.image(image_path, width=100)

        if st.button("Start modeling", key=f"start_{selected}"):
            st.session_state.country = selected
            st.session_state.page = "main_dashboard"
            u.create_templates_if_missing(country)
            st.rerun()

    with st.expander("➕ Add a new country"):
        new_country = st.text_input("New country name")
        if st.button("Add country"):
            new_country = new_country.strip()
            if new_country:
                if new_country not in st.session_state.countries:
                    result = u.add_country_to_backend(new_country)
                    if result is not None:
                        st.session_state.countries = u.get_countries_from_backend()
                        st.success(f"{new_country} added to the list.")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.warning(f"{new_country} already exists.")
