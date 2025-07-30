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
    
    def __init__(self, api_url, subsection, model, fuel):
        self.api_url = api_url
        self.subsection = subsection
        self.model = model
        self.fuel = fuel
        self.cell_validator = CellValidator()
        self.subsections = {
            "manage_models": ManageModels(self.api_url),
            "design_capital": DesignCapitalStructure(api_url, subsection, model, fuel, self.cell_validator),
            "technoeconomic_inputs": TechnoEconomicInputs(api_url, subsection, model, fuel, self.cell_validator),
            "carbon_credits": CarbonCredits(api_url, subsection, model, self.cell_validator),
            "financial_statements": FinancialStatements(api_url, subsection, model, fuel),
            "capex_fuels": CapexFuelMarket(api_url, subsection, model, fuel),
            "summary_financing": SummaryFinancing(self.api_url)
        }

    def __call__(self):
        if self.subsection in self.subsections:
            self.subsections[self.subsection]()
        else:
            st.info("Please select a valid subsection.")

