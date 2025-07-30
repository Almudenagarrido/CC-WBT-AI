import time
import requests
import utils as u
import pandas as pd
from io import BytesIO
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from modules.cell_validator import CellValidator


class FuelMarketInformation:

    def __init__(self, api_url, subsection, fuel_market):
        self.api_base = api_url
        self.subsection = subsection
        self.fuel_market = fuel_market
        self.cell_validator = CellValidator()
        self.get_url = f"{self.api_base}/fuel-market-information"
        self.save_url = f"{self.api_base}/save-fuel-market-information"
        self.reset_url = f"{self.api_base}/reset-fuel-market-information"
        self.add_url = f"{self.api_base}/add-fuel-market"
        self.delete_url = f"{self.api_base}/delete-fuel-market"
        self.df = None
        self.edited_df = None
        self.editable_columns = ["Baseline"] + [str(year) for year in range(2020, 2051)]
        self.df_heights = {"Electricity": 170, "LPG": 290, "Carbon": 170}

    def get_fuel_markets(self):
        try:
            res = requests.get(self.get_url)
            if res.status_code != 200:
                st.error("The file 'fuel-market-information.xlsx' was not found.")
                return []
            file_data = BytesIO(res.content)
            xls = pd.ExcelFile(file_data)
            return xls.sheet_names
        except Exception as e:
            st.error(f"Error fetching financial markets: {e}")
            return []

    def fetch_and_load(self):
        res = requests.get(self.get_url)
        if res.status_code != 200:
            st.error("Could not load 'fuel-market-information.xlsx'")
            return False

        if not self.fuel_market:
            st.warning("No sheet found in file for selected technology market.")
            return False

        file_data = BytesIO(res.content)
        self.df = pd.read_excel(file_data, sheet_name=self.fuel_market, engine="openpyxl")

        for col in self.df.columns:
            if col not in ["Inputs", "Units"]:
                self.df[col] = pd.to_numeric(self.df[col].replace("-", pd.NA), errors="coerce")
        
        return True

    def show_excel_editor(self):

        st.subheader(f"{self.fuel_market} Financial Inputs")
        df = self.df.copy()
        gb = GridOptionsBuilder.from_dataframe(df)
        height = self.df_heights[self.fuel_market] if self.fuel_market in self.df_heights else self.df_heights["Electricity"]
        
        for col in df.columns:
            if col in self.editable_columns:
                gb.configure_column(col, editable=True)
            else:
                gb.configure_column(col, editable=False)

        grid_options = gb.build()
        grid_response = AgGrid(
            df,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.VALUE_CHANGED,
            allow_unsafe_jscode=True,
            enable_enterprise_modules=False,
            height=height
        )
        self.edited_df = pd.DataFrame(grid_response["data"])
           
    def save_changes(self):
        df = self.edited_df.copy()
        df = df[self.df.columns]

        for col in df.columns:
            if col in self.editable_columns:
                df[col] = df[col].fillna(0)

        for i, row in df.iterrows():
            if str(row.get("Inputs", "")).strip().lower() == "number of years that you could sell those carbon credits":
                for col in df.columns:
                    if col not in ["Inputs", "Units", "Baseline"]:
                        df.at[i, col] = pd.NA
        
        editable_cols_in_df = [col for col in self.editable_columns if col in df.columns]
        df[editable_cols_in_df] = df[editable_cols_in_df].astype(object)
        df.loc[df.index[-1], editable_cols_in_df] = df.loc[df.index[-1], editable_cols_in_df].fillna("-")

                
        invalid_cells = self.cell_validator.cell_validations(df, self.editable_columns)

        if invalid_cells:
            for _, input_name, col, value, error in invalid_cells:
                st.warning(f"Invalid value '{value}' in row '{input_name}' (column '{col}'): {error}")
            return False

        data_json = df.reset_index(drop=True).to_dict(orient="records")
        payload = {
            "model": "",
            "sheet_name": self.fuel_market,
            "data": data_json
        }
        res = requests.post(self.save_url, json=payload)
        if res.status_code == 200:
            st.success(f"Changes in '{self.fuel_market}' saved successfully.")
        else:
            st.error("Error saving the changes, try again later.")

        return True

    def reset_sheet(self):
        response = requests.post(self.reset_url, json={"model": "", "sheet_name": self.fuel_market, "data": []})
        if response.status_code == 200:
            st.success(f"File '{self.fuel_market}' reset to template version.")
        else:
            st.error(response.json().get("error", "Something went wrong"))

    def __call__(self):

        if self.subsection == "add":
            u.add_fuel_to_backend()
            return
        
        if not self.fetch_and_load():
            return
        
        self.show_excel_editor()
        
        if st.button("Save"):
            saved = self.save_changes()
            if saved:
                time.sleep(2)
                st.rerun()

        if st.button("Reset"):
            self.reset_sheet()
            time.sleep(2)
            st.rerun()

