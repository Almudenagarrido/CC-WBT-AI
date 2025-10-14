import os
import time
import streamlit as st
import utils as u

def show():
    st.markdown("### Select a country scenario to begin modeling:")
    
    if "selected_country" not in st.session_state:
        st.session_state.selected_country = None
    if "countries" not in st.session_state:
        st.session_state.countries = u.get_countries_from_backend()
    
    deleted_country = None
    added_country = None
    
    for country in st.session_state.countries:
        col1, col2, col3 = st.columns([0.8, 0.1, 0.1])
        
        with col1:
            if st.button(country, key=f"select_{country}"):
                u.create_templates_if_missing(country)
                st.session_state.selected_country = country
                st.rerun()
        
        if st.session_state.selected_country == country:
            with col2:
                content = u.download_country_files_from_backend(country)
                if content:
                    st.download_button(
                        "⬇️",
                        data=content,
                        file_name=f"{country}_files.zip",
                        mime="application/zip",
                        key=f"download_{country}"
                    )
            
            with col3:
                if st.button("🗑️", key=f"delete_{country}"):
                    if u.delete_country_from_backend(country):
                        deleted_country = country
                        st.session_state.selected_country = None
                        st.session_state.countries = u.get_countries_from_backend()

    if deleted_country:
        st.success(f"Country scenario '{deleted_country}' deleted successfully.")
        time.sleep(2)
        st.rerun()

    if st.session_state.selected_country:
        selected = st.session_state.selected_country
        st.markdown(f"#### Selected country: {selected}")
        
        image_path = f"public/{selected}.png"
        if os.path.exists(image_path):
            st.image(image_path, width=100)
        
        if st.button("Start modeling"):
            st.session_state.page = "main_dashboard"
            st.session_state.country = selected
            st.rerun()

    with st.expander("➕ Add a new country"):
        new_country = st.text_input("Country name", key="new_country_input")
        tax_rate = st.number_input("Tax Rate (%)", value=0.0)
        inflation = st.number_input("Inflation (%)", value=0.0)
        
        if st.button("Add", key="add_country_btn"):
            new_country = new_country.strip()
            if not new_country:
                st.error("Country name cannot be empty.")
            elif tax_rate < 0 or tax_rate > 100:
                st.error("Tax rate must be between 0% and 100%.")
            elif inflation < 0 or inflation > 100:
                st.error("Inflation rate must be between 0% and 100%.")
            else:
                if u.add_country_to_backend(new_country, tax_rate, inflation):
                    added_country = new_country
                    st.session_state.countries = u.get_countries_from_backend()
                else:
                    st.error("Failed to add country. Please try again.")

    if added_country:
        st.success(f"Country scenario '{added_country}' added successfully.")
        time.sleep(2)
        st.rerun()