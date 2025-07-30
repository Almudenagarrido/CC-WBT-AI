import utils as u
from components import header, sidebar, footer
from modules.fuel_market import FuelMarketInformation
from modules.techno_economic_models import TechnoEconomicModels

def show():
    header.show()

    section, subsection, model, fuel = sidebar.show()
    if section == "financial_inputs" and (fuel or subsection):
        FuelMarketInformation(u.API_URL, subsection, fuel)()
    elif section == "technoeconomic_models" and subsection:
        TechnoEconomicModels(u.API_URL, subsection, model, fuel)()

    footer.show()