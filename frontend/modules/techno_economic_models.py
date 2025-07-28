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
    
    def __init__(self, api_url, subsection, model, fuel_market):
        self.api_url = api_url
        self.subsection = subsection
        self.model = model
        self.fuel_market = fuel_market
        self.cell_validator = CellValidator()
        self.subsections = {
            "Manage Techno-Economic Inputs": ManageModels(self.api_url),
            "Design Capital Structure": DesignCapitalStructure(api_url, subsection, model, fuel_market, self.cell_validator),
            "Techno-Economic Inputs": TechnoEconomicInputs(api_url, subsection, model, fuel_market, self.cell_validator),
            "Carbon Credits": CarbonCredits(api_url, subsection, model, self.cell_validator),
            "Financial Statements": FinancialStatements(api_url, subsection, model, fuel_market),
            "Capex Fuel Market": CapexFuelMarket(api_url, subsection, model, fuel_market),
            "Summary Financing": SummaryFinancing(self.api_url)
        }

    def __call__(self):
        if self.subsection in self.subsections:
            self.subsections[self.subsection]()
        else:
            st.info("Please select a valid subsection.")

