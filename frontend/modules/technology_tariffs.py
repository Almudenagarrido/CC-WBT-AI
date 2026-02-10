import os
import time
import json
import utils as u
import pandas as pd
import streamlit as st


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.dirname(BASE_DIR)
PROJECT_ROOT = os.path.dirname(FRONTEND_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
CONFIG_FILE = os.path.join(BACKEND_DIR, "config.json")


class TechnologyTariffs:
    def __init__(self, excel_editor, country, subsection, model, fuel):
        self.excel_editor = excel_editor
        self.country = country
        self.subsection = subsection
        self.model = model
        self.route_ffss = os.path.join(country, f"financial-statements-{model}.xlsx")
        self.template_route_ffss = os.path.join(country, "financial-statements-{model}.xlsx")
        self.fuel = fuel
        self.key_fuels = "normal"
        self.key_fuels_ffss = "more_expanded"
        self.config = self.load_config()
        self.year_range = self._get_year_range()
        self.inflation_rate = self._get_inflation_rate()
        self.tariff_config = self._get_tariff_config()
        self.df = None
        self.edited_df = None
        self.df_heights = {"LPG": 90}
        self.editable_columns = [str(year) for year in range(2020, 2061)]
        self.empty_rows = {"LPG": {"col": "", "partial": [], "full": []}}
        
    def load_config(self):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    
    def save_config(self, config):
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    
    def _get_year_range(self):
        country_ranges = self.config.get("COUNTRY_YEAR_RANGES", {})
        if self.country in country_ranges:
            country_config = country_ranges[self.country]
            start = country_config.get("start", 2020)
            end = country_config.get("end", 2060)
            return list(range(start, end + 1))
        
        template_config = country_ranges["template"]
        start = template_config.get("start")
        end = template_config.get("end")
        return list(range(start, end + 1))
    
    def _get_inflation_rate(self):
        inflations = self.config.get("INFLATIONS", {})
        return inflations.get(self.country, 5.0)
    
    def _get_tariff_config(self):
        
        tariffs = self.config.get("TARIFFS", {})
        if self.country in tariffs:
            country_tariffs = tariffs[self.country]
            if self.model in country_tariffs:
                model_tariffs = country_tariffs[self.model]
                if self.fuel in model_tariffs:
                    return model_tariffs[self.fuel]
        
        return None
    
    def _create_df_from_values(self, values):

        data = {}
        for year in self.year_range:
            value = values.get(str(year), 0.0)
            data[str(year)] = [value]
        
        df = pd.DataFrame(data)
        df.insert(0, "Tariff", "$/kWh")
        
        return df
    
    def _ask_for_tariff_method(self):

        st.subheader(f"Tariff Configuration for {self.fuel}")
        st.write(f"**Country:** {self.country} | **Model:** {self.model}")
        st.write(f"**Year Range:** {self.year_range[0]} - {self.year_range[-1]}")
        st.write(f"**Inflation Rate:** {self.inflation_rate}%")
        
        method = st.radio(
            "How would you like to define the tariff?",
            options=["initial_inflation", "annual"],
            format_func=lambda x: {
                "initial_inflation": "Initial value + inflation (autofill based on inflation rate)",
                "annual": "Annual values (enter each year separately)"
            }[x],
            key=f"tariff_method_{self.country}_{self.model}_{self.fuel}"
        )
        
        return method
    
    def _get_initial_value_input(self):

        st.write("### Initial Tariff Value")

        initial_value = st.number_input(
            "Enter initial tariff value:",
            min_value=0.0,
            value=0.0,
            step=0.01,
            key=f"initial_value_{self.country}_{self.model}_{self.fuel}"
        )
        
        if st.button("Apply Inflation Calculation", key=f"apply_inflation_{self.country}_{self.model}_{self.fuel}"):
            return initial_value
        
        return None
    
    def _calculate_inflation_values(self, initial_value):
        
        values = {}
        current_value = initial_value
        
        for year in self.year_range:
            values[str(year)] = current_value
            current_value *= (1 + self.inflation_rate / 100)
        
        return values
     
    def _save_tariff_data(self):
        
        if self.edited_df is not None:
            
            values = {}
            for col in self.edited_df.columns:
                if col != "Tariff" and col.isdigit():
                    year = int(col)
                    raw_value = self.edited_df[col].iloc[0]
                    if pd.isna(raw_value) or raw_value is None:
                        value = 0.0
                    else:
                        value = float(raw_value)
                    values[year] = value
            
            if self.country not in self.config["TARIFFS"]:
                self.config["TARIFFS"][self.country] = {}
            
            if self.model not in self.config["TARIFFS"][self.country]:
                self.config["TARIFFS"][self.country][self.model] = {}
                
            self.config["TARIFFS"][self.country][self.model][self.fuel] = {year: value for year, value in values.items()}
            
            st.session_state["tariff_values"] = None
            self.save_config(self.config)
    
    def _reset_tariff_data(self):
        
        tariffs = self.config.get("TARIFFS", {})
        if self.country in tariffs:
            country_tariffs = tariffs[self.country]
            if self.model in country_tariffs:
                model_tariffs = country_tariffs[self.model]
                if self.fuel in model_tariffs:
                    del self.config["TARIFFS"][self.country][self.model][self.fuel]
                    self.save_config(self.config)
        
        st.session_state["tariff_values"] = None
        return None
    
    def _show_tariff_editor(self, df):
        
        st.subheader(f"{self.fuel} Tariff Editor")
        
        height = self.df_heights.get(self.fuel, self.df_heights["LPG"])
        empty_rows = self.empty_rows.get(self.fuel, self.empty_rows["LPG"])
        
        self.excel_editor.load_data(df, self.fuel, height, self.editable_columns, empty_rows)
        self.edited_df = self.excel_editor.show(decimals=2)
        
        if st.button("Save", key=f"save_tariff_{self.country}_{self.model}_{self.fuel}"):
            self._save_tariff_data()
            st.success(f"Tariff Configuration for {self.fuel} saved successfully.")
            
            fuel_ffss = self.config.get("FUELS", {}).get(self.country, {}).get(self.key_fuels_ffss, [])[0]
            _ = u.get_sheet_from_backend(
                self.country,
                self.route_ffss,
                self.template_route_ffss,
                fuel_ffss,
                self.key_fuels_ffss
            )
            st.rerun()
    
        if st.button("Reset", key=f"reset_tariff_{self.country}_{self.model}_{self.fuel}"):
            self._reset_tariff_data()
            st.success(f"Tariff Configuration for {self.fuel} reset successfully.")
            
            fuel_ffss = self.config.get("FUELS", {}).get(self.country, {}).get(self.key_fuels_ffss, [])[0]
            _ = u.get_sheet_from_backend(
                self.country,
                self.route_ffss,
                self.template_route_ffss,
                fuel_ffss,
                self.key_fuels_ffss
            )
            st.rerun()
    
    def __call__(self):

        existing_values = self._get_tariff_config()

        if existing_values is None:
            st.info(f"No tariff configuration found for {self.fuel}. Please set it up.")

            method = self._ask_for_tariff_method()
            values = st.session_state.get("tariff_values")

            if method == "initial_inflation":
                initial_value = self._get_initial_value_input()

                if initial_value is not None:
                    values = self._calculate_inflation_values(initial_value)
                    st.session_state["tariff_values"] = values

                if values is None:
                    return

            else:
                values = {str(year): 0.0 for year in self.year_range}

            final_values = values
        else:
            final_values = existing_values

        for year in self.year_range:
            if str(year) not in final_values:
                final_values[str(year)] = 0.0

        self.df = self._create_df_from_values(final_values)
        self._show_tariff_editor(self.df)
