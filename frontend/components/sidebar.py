import utils as u
import streamlit as st
from modules.fuel_market import FuelMarketInformation
from modules.design_capital import DesignCapitalStructure
from modules.techno_economic_inputs import TechnoEconomicInputs
from modules.financial_statements import FinancialStatements
from modules.capex_fuels import CapexFuelMarket


def show():

    if "page" not in st.session_state:
        st.session_state.page = "Techno-Economic Inputs"
    if "subsection" not in st.session_state:
        st.session_state.subsection = None
    if "model" not in st.session_state:
        st.session_state.model = None
    if "fuel_market" not in st.session_state:
        st.session_state.fuel_market = None

    fm = FuelMarketInformation(u.API_URL, st.session_state.subsection)
    fuel_market_sheets = fm.get_fuel_markets()
    if 'Electricity' in fuel_market_sheets:
        fuel_market_sheets = ['Electricity'] + [m for m in fuel_market_sheets if m != 'Electricity']

    dcs = DesignCapitalStructure(u.API_URL, st.session_state.subsection, st.session_state.model, st.session_state.fuel_market, None)
    design_capital_sections = dcs.get_design_capital()
    if 'Electricity & E-Cooking' in design_capital_sections and 'Electricity (Low access)' in design_capital_sections:
        design_capital_sections = ['Electricity & E-Cooking', 'Electricity (Low access)'] + [s for s in design_capital_sections if s != 'Electricity & E-Cooking' and s != 'Electricity (Low access)']

    ti = TechnoEconomicInputs(u.API_URL, st.session_state.subsection, st.session_state.model, st.session_state.fuel_market, None)
    technoeconomic_input_sheets = ti.get_technoeconomic_inputs()
    if 'Electricity' in technoeconomic_input_sheets:
        technoeconomic_input_sheets = ['Electricity'] + [t for t in technoeconomic_input_sheets if t != 'Electricity']

    ffss = FinancialStatements(u.API_URL, st.session_state.subsection, st.session_state.model, st.session_state.fuel_market)
    financial_statement_sections = ffss.get_financial_statements()
    if 'E-Cooking' in design_capital_sections and 'Electricity' in design_capital_sections and 'Electricity (Low access)' in design_capital_sections:
        design_capital_sections = ['E-Cooking', 'Electricity', 'Electricity (Low access)'] + [s for s in design_capital_sections if s != 'E-Cooking' and s != 'Electricity' and s != 'Electricity (Low access)']

    cfm = CapexFuelMarket(u.API_URL, st.session_state.subsection, st.session_state.model, st.session_state.fuel_market)
    capex_market_sections = cfm.get_capex_markets()
    if 'Electricity' in capex_market_sections:
        capex_market_sections = ['Electricity'] + [s for s in capex_market_sections if s !='Electricity']

    with st.sidebar:
        if st.button("⌂"):
            st.session_state.page = "country_selector"
            st.session_state.selected_country = None
            st.rerun()
        
        # Financial Inputs
        with st.expander("Financial Inputs", expanded=False):
            
            for sheet in fuel_market_sheets:
                if sheet != "Carbon":
                    if st.button(f"{sheet} Financial Inputs"):
                        st.session_state.page = "Financial Inputs"
                        st.session_state.fuel_market = f"{sheet}"
                        st.session_state.subsection = None
                        st.session_state.model = None

            st.markdown("---")
            if st.button("➕ Add new fuel market"):
                st.session_state.page = "Financial Inputs"
                st.session_state.fuel_market = "Add"
                st.session_state.subsection = None
                st.session_state.model = None
            
            if st.session_state.page == "Financial Inputs" and st.session_state.fuel_market is None:
                if fuel_market_sheets:
                    st.session_state.fuel_market = f"{fuel_market_sheets[0]}"
                    st.session_state.subsection = None
                    st.session_state.model = None
            
            market_to_delete = st.selectbox("Delete fuel market", options=fuel_market_sheets)
            if st.button("🗑️"):
                if fm.delete_market(market_to_delete):
                    st.session_state.fuel_market = f"{fuel_market_sheets[0]}"
                    st.session_state.subsection = None
                    st.session_state.model = None
                    st.rerun()

            st.markdown("---")
            if "Carbon" in fuel_market_sheets:
                if st.button(f"Carbon Credits Financial Inputs"):
                        st.session_state.page = "Financial Inputs"
                        st.session_state.fuel_market = "Carbon"
                        st.session_state.subsection = None
                        st.session_state.model = None

    # Techno-Economic Inputs
    with st.sidebar:
        if st.session_state.model: 
            st.markdown(f"##### Techno-Economic Model: {st.session_state.model}")
        else:
            st.markdown("##### Techno-Economic Inputs")

        if st.button("Manage Techno-Economic Inputs"):
            st.session_state.page = "Techno-Economic Inputs"
            st.session_state.subsection = "Manage Techno-Economic Inputs"
            st.session_state.model = None
            st.session_state.fuel_market = None
            st.rerun()

        if st.session_state.model:
            if st.session_state.model != "BAU":

                st.markdown("##### Inputs")
                with st.expander("Techno-Economic Inputs", expanded=False):
                    for sheet in technoeconomic_input_sheets:
                        if st.button(f"{sheet} Inputs"):
                            st.session_state.page = "Techno-Economic Inputs"
                            st.session_state.subsection = "Techno-Economic Inputs"
                            st.session_state.fuel_market = f"{sheet}"
                            st.rerun()

                    if st.session_state.page == "Techno-Economic Inputs" and st.session_state.subsection == "Techno-Economic Inputs" and st.session_state.fuel_market == None:
                        st.session_state.fuel_market = fuel_market_sheets[0]
                
            if st.button("Carbon Credits"):
                st.session_state.page = "Techno-Economic Inputs"
                st.session_state.subsection = "Carbon Credits"
                st.rerun()
            
            if st.session_state.model != "BAU":

                with st.expander("Capex Fuel Market", expanded=False):
                    for sheet in capex_market_sections:
                        if st.button(f"{sheet} - CAPEX"):
                            st.session_state.page = "Techno-Economic Inputs"
                            st.session_state.subsection = "Capex Fuel Market"
                            st.session_state.fuel_market = f"{sheet}"
                            st.rerun()
                
                with st.expander("Design Capital Structure", expanded=False):
                    for sheet in design_capital_sections:
                        if st.button(f"{sheet} Financial Plan"):
                            st.session_state.page = "Techno-Economic Inputs"
                            st.session_state.subsection = "Design Capital Structure"
                            st.session_state.fuel_market = f"{sheet}"
                            st.rerun()

                    if st.session_state.page == "Techno-Economic Inputs" and st.session_state.subsection == "Design Capital Structure" and st.session_state.fuel_market == None:
                        st.session_state.fuel_market = design_capital_sections[0]

                
                st.markdown("##### Outputs")
                with st.expander("Financial Statements", expanded=False):
                    for sheet in financial_statement_sections:
                        sheet_button = sheet
                        if sheet == "Electricity":
                            sheet_button = "Electricity & E-Cooking"
                        if sheet == "E-Cooking":
                            sheet_button = "Only E-Cooking"
                        if st.button(f"{sheet_button} - FFSS"):
                            st.session_state.page = "Techno-Economic Inputs"
                            st.session_state.subsection = "Financial Statements"
                            st.session_state.fuel_market = f"{sheet}"
                            st.rerun()

            if st.session_state.model != "BAU":
                if st.button("Summary Financing"):
                    st.session_state.page = "Techno-Economic Inputs"
                    st.session_state.subsection = "Summary Financing"
                    st.rerun()

        if st.session_state.page == "Techno-Economic Inputs" and st.session_state.subsection == None:
            st.session_state.subsection = "Manage Techno-Economic Inputs"
            st.session_state.model = None

    return st.session_state.page, st.session_state.subsection, st.session_state.model, st.session_state.fuel_market