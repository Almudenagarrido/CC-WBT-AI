import os

API_URL = "http://localhost:8001"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TEMPLATES_DIR = os.path.join(BASE_DIR, "{templates}")

COUNTRIES = ["Rwanda", "Mozambique"]

COUNTRY_YEAR_RANGES = {
    "template": {
        "start": 2020,
        "end": 2060,
    }
}

FUELS = {
        "template": {
        "normal": ["Electricity", "LPG"],
        "carbon": ["Electricity", "LPG", "Carbon Credits"],
        "rest": ["Electricity", "LPG", "Rest of subsidies or taxes"],
        "expanded": ["Electricity & E-Cooking", "Electricity (Just access)", "LPG"],
        "more_expanded": ["Electricity (Only E-Cooking)", "Electricity & E-Cooking", "Electricity (Just access)", "LPG"]
        }
    }

ELECTRICITY_VARIANTS = {
        "Electricity",
        "Electricity & E-Cooking",
        "Electricity (Just access)",
        "Electricity (Only E-Cooking)"
    }

MODELS = {}

SHARED_ROUTES = [
    "fuel-financial-inputs-{template}.xlsx",
    "carbon-credits-{template}.xlsx",
]

ROUTES = [
    "technoeconomic-inputs-{model}.xlsx",
    "capex-fuels-{model}.xlsx",
    "design-capital-{model}.xlsx",
    "financial-statements-{model}.xlsx"
]