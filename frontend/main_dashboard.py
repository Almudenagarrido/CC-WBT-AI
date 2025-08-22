import utils as u
import streamlit as st
from components import header, sidebar, footer
from modules.excel_editor import ExcelEditor
from modules.fuel_financial_inputs import FuelFinancialInformation
from modules.techno_economic_models import TechnoEconomicModels

def show():
    header.show()

    section, subsection, model, fuel = sidebar.show()
    country = st.session_state.country
    excel_editor = ExcelEditor()
    
    if section == "financial_inputs" and (fuel or subsection):
        FuelFinancialInformation(excel_editor, country, subsection, fuel)()
    elif section == "technoeconomic_models" and subsection:
        TechnoEconomicModels(excel_editor, country, subsection, model, fuel)()

    footer.show()