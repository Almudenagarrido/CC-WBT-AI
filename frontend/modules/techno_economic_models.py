import streamlit as st
from modules.manage_models import ManageModels
from modules.techno_economic_inputs import TechnoEconomicInputs
from modules.carbon_credits import CarbonCredits
from modules.capex_fuels import CapexFuelMarket
from modules.technology_tariffs import TechnologyTariffs
from modules.technology_upstreams import TechnologyUpstreams
from modules.design_capital import DesignCapitalStructure
from modules.financial_statements import FinancialStatements
from modules.summary_financing import SummaryFinancing


class TechnoEconomicModels:
    
    def __init__(self, excel_editor, country, subsection, model, fuel):
        self.excel_editor = excel_editor
        self.country = country
        self.subsection = subsection
        self.model = model
        self.fuel = fuel
        self.subsections = {
            "manage_models": ManageModels(country),
            "technoeconomic_inputs": TechnoEconomicInputs(excel_editor, country, subsection, model, fuel),
            "carbon_credits": CarbonCredits(excel_editor, country, subsection, model),
            "capex_fuels": CapexFuelMarket(excel_editor, country, subsection, model, fuel),
            "design_capital": DesignCapitalStructure(excel_editor, country, subsection, model, fuel),
            "technology_tariffs": TechnologyTariffs(excel_editor, country, subsection, model, fuel),
            "technology_upstreams": TechnologyUpstreams(excel_editor, country, subsection, model, fuel),
            "financial_statements": FinancialStatements(excel_editor, country, subsection, model, fuel),
            "summary_financing": SummaryFinancing(country)
        }

    def __call__(self):
        if self.subsection in self.subsections:
            self.subsections[self.subsection]()
        else:
            st.info("Please select a valid subsection.")

