import time
import requests
import numpy as np
import pandas as pd
from io import BytesIO
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

class TechnoEconomicInputs:
    
    def __init__(self, api_base, subsection, model, fuel_market):
        self.api_base = api_base
        self.fuel_market_get_url = f"{self.api_base}/fuel-market-information"
        self.get_url = f"{self.api_base}/technoeconomic-inputs"
        self.save_url = f"{self.api_base}/save-technoeconomic-inputs"
        self.reset_url = f"{self.api_base}/reset-technoeconomic-inputs"
        self.subsection = subsection
        self.model = model
        self.fuel_market = fuel_market
        self.df_fuel_market_inputs = None
        self.df_heights_fuel_market_inputs = {"Electricity": 170, "LPG": 230, "C02": 170}
        self.df = None
        self.df_heights = {"Electricity": 580, "LPG": 500, "Rest of subsidies or taxes": 410}
        self.edited_df = None
        self.editable_columns = ["Baseline"] + [str(year) for year in range(2021, 2051)]
    
    def get_technoeconomic_inputs(self):
        try:
            url = f"{self.get_url}/{self.model}"
            res = requests.get(url)
            if res.status_code != 200:
                st.error("The file 'technoeconomic-inputs.xlsx' was not found.")
                return []

            file_data = BytesIO(res.content)
            with pd.ExcelFile(file_data) as xls:
                return xls.sheet_names

        except Exception as e:
            st.error(f"Error fetching techno-economic inputs: {e}")
            return []

    def fetch_and_load(self, fuel_market: bool):
        
        url = self.fuel_market_get_url if fuel_market else f"{self.get_url}/{self.model}"
        res = requests.get(url)
        if res.status_code != 200:
            st.error("Could not load 'technoeconomic-inputs.xlsx'")
            return False
        
        if not self.fuel_market:
            st.warning("No sheet found in file for selected technology market.")
            return False
        
        file_data = BytesIO(res.content)
        if fuel_market:
            if not self.fuel_market == "C02":
                self.df_fuel_market_inputs = pd.read_excel(file_data, sheet_name=self.fuel_market, engine="openpyxl")
            else:
                self.df_fuel_market_inputs = pd.read_excel(file_data, sheet_name="Carbon", engine="openpyxl")
        else:
            self.df = pd.read_excel(file_data, sheet_name=self.fuel_market, engine="openpyxl")

        if not fuel_market:
            for col in self.df.columns:
                if col not in ["Inputs", "Type", "Units"]:
                    self.df[col] = pd.to_numeric(self.df[col].replace("-", pd.NA), errors="coerce")
            
            self.df = self.df.mask(self.df == "-", np.nan)

        return True

    def show_excel_editor(self, fuel_market: bool):
        df = self.df_fuel_market_inputs.copy() if fuel_market else self.df.copy()
        df.columns = df.columns.astype(str)

        if fuel_market and self.fuel_market == "LPG":
            df["Inputs"] = df["Inputs"].astype(str)
            df = df[~df["Inputs"].str.contains("EBITDA", na=False)]
            df["Inputs"] = df["Inputs"].str.replace("OPEX", "Tariff", regex=False)

        gb = GridOptionsBuilder.from_dataframe(df)

        if not fuel_market:
            for col in df.columns:
                if col in self.editable_columns:
                    gb.configure_column(col, editable=True)
        else:
            gb.configure_columns(df.columns, editable=False)

        if fuel_market: 
            height = self.df_heights_fuel_market_inputs.get(self.fuel_market, self.df_heights_fuel_market_inputs["Electricity"])
        else:
            height = self.df_heights.get(self.fuel_market, self.df_heights["Electricity"])

        grid_options = gb.build()

        grid_response = AgGrid(
            df,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.VALUE_CHANGED if not fuel_market else GridUpdateMode.NO_UPDATE,
            allow_unsafe_jscode=True,
            enable_enterprise_modules=False,
            height=height
        )

        if not fuel_market:
            self.edited_df = pd.DataFrame(grid_response["data"])

    def save_changes(self):
        df = self.edited_df.copy()
        df["Inputs"] = df["Inputs"].astype(str).str.strip()

        for i, row in df.iterrows():
            input_val = row["Inputs"].lower()

            if "output" in input_val:
                for col in df.columns:
                    if col not in ["Inputs", "Type", "Units"]:
                        df.at[i, col] = np.nan

            elif "depreciation" in input_val:
                for col in df.columns:
                    if col not in ["Inputs", "Type", "Units", "Baseline"]:
                        df.at[i, col] = np.nan

        df.columns = df.columns.map(str)
        self.df.columns = self.df.columns.map(str)
        df = df[self.df.columns]
        
        for col in df.columns:
            if col in self.editable_columns:
                df[col] = df[col].fillna("-")

        invalid_cells = self.cell_validator.cell_validations(df, self.editable_columns)
        if invalid_cells:
            for _, input_name, col, value, error in invalid_cells:
                st.warning(f"Invalid value '{value}' in row '{input_name}' (column '{col}'): {error}")
            return False

        data_json = df.reset_index(drop=True).to_dict(orient="records")
        payload = {
            "model": self.model,
            "sheet_name": self.fuel_market,
            "data": data_json
        }
        res = requests.post(self.save_url, json=payload)
        if res.status_code == 200:
            st.success(f"Changes in '{self.fuel_market}' saved successfully.")
        else:
            st.error("Error saving the changes, try again later.")
            return False
        
        return True

    def reset_sheet(self):
        payload = {
            "model": self.model,
            "sheet_name": self.fuel_market,
            "data": []
        }
        response = requests.post(self.reset_url, json=payload)
        if response.status_code == 200:
            st.success(f"File '{self.fuel_market}' reset to template version.")
        else:
            st.error(response.json().get("error", "Something went wrong"))

    def __call__(self):
        
        st.subheader(f"{self.fuel_market} Inputs")
        if self.fuel_market == "Rest of subsidies or taxes":
            if not self.fetch_and_load(fuel_market=False):
                return
            self.show_excel_editor(fuel_market=False)
            if st.button("Save"):
                saved = self.save_changes()
                if saved:
                    time.sleep(2)
                    st.rerun()

            if st.button("Reset"):
                self.reset_sheet()
                time.sleep(2)
                st.rerun()
            return

        
        if self.fuel_market == "C02":
            if not self.fetch_and_load(fuel_market=True):
                return
            self.show_excel_editor(fuel_market=True)
            return
    
        if not self.fetch_and_load(fuel_market=True):
            return
        
        self.show_excel_editor(fuel_market=True)

        if not self.fetch_and_load(fuel_market=False):
            return
        
        self.show_excel_editor(fuel_market=False)

        if st.button("Save"):
            saved = self.save_changes()
            if saved:
                time.sleep(2)
                st.rerun()

        if st.button("Reset"):
            self.reset_sheet()
            time.sleep(1)
            st.rerun()

"""
get
fetch and load
show excel
save reset
"""