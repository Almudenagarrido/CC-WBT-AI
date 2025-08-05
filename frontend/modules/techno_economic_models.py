import streamlit as st
from modules.cell_validator import CellValidator
from modules.manage_models import ManageModels
from modules.design_capital import DesignCapitalStructure
from modules.techno_economic_inputs import TechnoEconomicInputs
from modules.carbon_credits import CarbonCredits
from modules.financial_statements import FinancialStatements
from modules.capex_fuels import CapexFuelMarket
from modules.summary_financing import SummaryFinancing


class TechnoEconomicModels:
    
    def __init__(self, excel_editor, api_url, subsection, model, fuel):
        self.excel_editor = excel_editor
        self.api_url = api_url
        self.subsection = subsection
        self.model = model
        self.fuel = fuel
        #self.excell = CellValidator()
        self.subsections = {
            "manage_models": ManageModels(),
            "technoeconomic_inputs": TechnoEconomicInputs(api_url, subsection, model, fuel),
            "carbon_credits": CarbonCredits(api_url, subsection, model),
            "capex_fuels": CapexFuelMarket(api_url, subsection, model, fuel),
            "design_capital": DesignCapitalStructure(api_url, subsection, model, fuel),
            "financial_statements": FinancialStatements(api_url, subsection, model, fuel),
            "summary_financing": SummaryFinancing(self.api_url)
        }

    def __call__(self):
        if self.subsection in self.subsections:
            self.subsections[self.subsection]()
        else:
            st.info("Please select a valid subsection.")

