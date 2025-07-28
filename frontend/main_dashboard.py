import utils as u
from components import header, sidebar, footer
from modules.fuel_market import FuelMarketInformation
from modules.techno_economic_models import TechnoEconomicModels

def show():
    header.show()

    page, subsection, model, fuel_market = sidebar.show()
    if page == "Financial Inputs" and fuel_market:
        FuelMarketInformation(u.API_URL, fuel_market)()
    elif page == "Techno-Economic Inputs" and subsection:
        TechnoEconomicModels(u.API_URL, subsection, model, fuel_market)()

    footer.show()