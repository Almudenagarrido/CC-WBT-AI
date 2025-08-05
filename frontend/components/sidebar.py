import utils as u
import streamlit as st


def show():
    
    if "section" not in st.session_state or not st.session_state.section:
        st.session_state.section = "technoeconomic_models"
    if "subsection" not in st.session_state or not st.session_state.subsection:
        st.session_state.subsection = "manage_models"
    if "model" not in st.session_state:
        st.session_state.model = None
    if "fuel" not in st.session_state:
        st.session_state.fuel = None
    if "reload_fuels" not in st.session_state:
        st.session_state.reload_fuels = True

    if st.session_state.reload_fuels:
        country = st.session_state.country
        st.session_state.fuels = u.get_fuels_from_backend("normal", country)
        st.session_state.fuels_carbon = u.get_fuels_from_backend("carbon", country)
        st.session_state.fuels_expanded = u.get_fuels_from_backend("expanded", country)
        st.session_state.fuels_rest = u.get_fuels_from_backend("rest", country)
        st.session_state.fuels_more_expanded = u.get_fuels_from_backend("more_expanded", country)
        st.session_state.reload_fuels = False

    with st.sidebar:

        if st.button("⌂ Country selection"):
            st.session_state.page = "country_selector"
            st.session_state.section = None
            st.session_state.subsection = None
            st.session_state.models = None
            st.session_state.model = None
            st.session_state.fuel = None
            st.session_state.selected_country = None
            st.session_state.reload_fuels = True
            st.rerun()
        
        # Financial Inputs
        with st.expander("Financial Inputs", expanded=False):
            for fuel in st.session_state.fuels_carbon:
                if fuel != "Carbon Credits":
                    if st.button(f"{fuel} Financial Inputs"):
                        st.session_state.section = "financial_inputs"
                        st.session_state.fuel = fuel
                        st.session_state.subsection = None
                        st.session_state.model = None

            st.markdown("---")
            if st.button("➕ Add new fuel market"):
                st.session_state.section = "financial_inputs"
                st.session_state.subsection = "add"
                st.session_state.fuel = None
                st.session_state.model = None
            
            if st.session_state.section == "financial_inputs" and st.session_state.subsection is None and st.session_state.fuel is None:
                if st.session_state.fuels_carbon:
                    st.session_state.fuel = st.session_state.fuels_carbon[0]
                    st.session_state.subsection = None
                    st.session_state.model = None
            
            fuel_to_delete = st.selectbox("Delete fuel market", options=st.session_state.fuels_carbon)
            if st.button("🗑️"):
                if u.delete_fuel_from_backend(fuel_to_delete, st.session_state.country):
                    st.session_state.fuel = st.session_state.fuels_carbon[0]
                    st.session_state.subsection = None
                    st.session_state.model = None
                    st.session_state.reload_fuels = True
                    st.rerun()

            st.markdown("---")
            if "Carbon Credits" in st.session_state.fuels_carbon:
                if st.button(f"Carbon Credits Financial Inputs"):
                        st.session_state.section = "financial_inputs"
                        st.session_state.fuel = "Carbon Credits"
                        st.session_state.subsection = None
                        st.session_state.model = None

        # Techno-Economic Models
        if st.session_state.model: 
            st.markdown(f"##### Techno-Economic Model: {st.session_state.model}")
        else:
            st.markdown("##### Techno-Economic Models")

        if st.button("Manage Techno-Economic Models"):
            st.session_state.section = "technoeconomic_models"
            st.session_state.subsection = "manage_models"
            st.session_state.model = None
            st.session_state.fuel = None
            st.rerun()

        if st.session_state.model:
            if st.session_state.model != "BAU":

                st.markdown("##### Inputs")

                with st.expander("Techno-Economic Inputs", expanded=False):
                    for fuel in st.session_state.fuels_rest:
                        if st.button(f"{fuel} Inputs"):
                            st.session_state.section = "technoeconomic_models"
                            st.session_state.subsection = "technoeconomic_inputs"
                            st.session_state.fuel = fuel
                            st.rerun()
                        
                    if st.session_state.section == "technoeconomic_models" and st.session_state.subsection == "technoeconomic_inputs " and not st.session_state.fuel:
                        st.session_state.fuel = st.session_state.fuels_rest[0]

            if st.button("Carbon Credits"):
                st.session_state.section = "technoeconomic_models"
                st.session_state.subsection = "carbon_credits"
                st.rerun()

            if st.session_state.model != "BAU":
                with st.expander("Capex Fuel Market", expanded=False):
                    for fuel in st.session_state.fuels:
                        if st.button(f"{fuel} - CAPEX"):
                            st.session_state.section = "technoeconomic_models"
                            st.session_state.subsection = "capex_fuels"
                            st.session_state.fuel = fuel
                            st.rerun()
                        
                    if st.session_state.section == "technoeconomic_models" and st.session_state.subsection == "capex_fuels " and not st.session_state.fuel:
                        st.session_state.fuel = st.session_state.fuels[0]

                with st.expander("Design Capital Structure", expanded=False):
                    for fuel in st.session_state.fuels_expanded:
                        if st.button(f"{fuel} Financial Plan"):
                            st.session_state.section = "technoeconomic_models"
                            st.session_state.subsection = "design_capital"
                            st.session_state.fuel = fuel
                            st.rerun()

                    if st.session_state.section == "technoeconomic_models" and st.session_state.subsection == "design_capital" and not st.session_state.fuel:
                        st.session_state.fuel = st.session_state.fuels_expanded[0]

                st.markdown("##### Outputs")

                with st.expander("Financial Statements", expanded=False):
                    for fuel in st.session_state.fuels_more_expanded:
                        if st.button(f"{fuel} - FFSS"):
                            st.session_state.section = "technoeconomic_models"
                            st.session_state.subsection = "financial_statements"
                            st.session_state.fuel = sheet
                            st.rerun()

                    if st.session_state.section == "technoeconomic_models" and st.session_state.subsection == "financial_statements" and not st.session_state.fuel:
                        st.session_state.fuel = st.session_state.fuels_more_expanded[0]
                
                if st.button("Summary Financing"):
                    st.session_state.section = "technoeconomic_models"
                    st.session_state.subsection = "summary_financing"
                    st.rerun()

    return st.session_state.section, st.session_state.subsection, st.session_state.model, st.session_state.fuel
