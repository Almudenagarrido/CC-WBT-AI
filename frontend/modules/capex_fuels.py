import requests
import numpy as np
import pandas as pd
from io import BytesIO
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

class CapexFuelMarket:
    
    def __init__(self, api_base, subsection, model, fuel_market):
        self.api_base = api_base
        self.subsection = subsection
        self.model = model
        self.fuel_market = fuel_market
        self.get_url = f"{self.api_base}/capex-fuel-market"
        self.df = None
        self.subtables = {
            "Electricity": {"Grid": None, "Off-Grid": None},
            "LPG": {"Local Processing": None, "Local Transport": None, "Upstream": None},
        }
        self.section_starts = {
            "Grid": 0, 
            "Off-Grid": 9, 
            "Local Processing": 0, 
            "Local Transport": 9, 
            "Upstream": 18
        }
    
    def get_capex_markets(self):
        try:
            url = f"{self.get_url}/{self.model}"
            res = requests.get(url)
            if res.status_code != 200:
                st.error(f"The file 'capex-market-{self.model}.xlsx' was not found.")
                return []

            file_data = BytesIO(res.content)
            xls = pd.ExcelFile(file_data)
            return xls.sheet_names

        except Exception as e:
            st.error(f"Error fetching capital structure: {e}")
            return []

    def get_active_subtables(self):
        if self.fuel_market == "Electricity":
            return ["Grid", "Off-Grid"]
        else:
            return ["Local Processing", "Local Transport", "Upstream"]

    def fetch_and_load(self):
        url = f"{self.get_url}/{self.model}"
        res = requests.get(url)
        if res.status_code != 200:
            st.error(f"Could not load 'capex-market-{self.model}.xlsx'")
            return False

        if not self.subsection:
            st.warning("No sheet found in file for selected subsection.")
            return False
        
        file_data = BytesIO(res.content)
        self.df = pd.read_excel(file_data, sheet_name=self.
        fuel_market, engine="openpyxl", header=None, index_col=None)
        self.split_into_subtables()
        return True
    
    def split_into_subtables(self):
        df = self.df
        active_keys = self.get_active_subtables()

        if self.fuel_market not in self.subtables:
            self.subtables[self.fuel_market] = {key: None for key in active_keys}

        active_sections = {k: self.section_starts[k] for k in active_keys}
        sorted_sections = sorted(active_sections.items(), key=lambda x: x[1])

        for i, (key, start_idx) in enumerate(sorted_sections):
            if key not in active_keys:
                continue

            end_idx = sorted_sections[i + 1][1] if i + 1 < len(sorted_sections) else len(df)

            subdf = df.iloc[start_idx:end_idx].reset_index(drop=True)

            subdf = subdf.mask(subdf == "-", np.nan)
            subdf.dropna(axis=0, how="all", inplace=True)
            subdf.dropna(axis=1, how="all", inplace=True)

            if not subdf.empty:
                header_row = subdf.iloc[0]
                subdf.columns = [str(int(x)) if isinstance(x, float) and x.is_integer() else str(x) for x in header_row]
                subdf = subdf[1:].reset_index(drop=True)
                subdf = subdf.loc[:, subdf.columns.notna()]
                subdf = subdf.loc[:, subdf.columns.str.strip() != '']
                subdf = subdf.loc[:, ~subdf.columns.duplicated()]
                subdf = subdf.loc[:, ~subdf.columns.str.contains("^Unnamed", case=False)]

            self.subtables[self.fuel_market][key] = subdf

    def show_excel_editor(self):
        st.subheader(f"{self.fuel_market} - CAPEX")

        if self.fuel_market not in self.subtables:
            st.warning("No subtables found for this fuel market.")
            return

        for key, df in self.subtables[self.fuel_market].items():
            st.markdown(f"##### {key}")
            if df is not None and not df.empty:
                df.columns = df.columns.astype(str)

                gb = GridOptionsBuilder.from_dataframe(df)
                for col in df.columns:
                    if pd.api.types.is_numeric_dtype(df[col]):
                        gb.configure_column(col, type=["numericColumn", "numberColumnFilter"])
                    else:
                        gb.configure_column(col)

                grid_options = gb.build()
                AgGrid(
                    df,
                    gridOptions=grid_options,
                    update_mode=GridUpdateMode.VALUE_CHANGED,
                    allow_unsafe_jscode=True,
                    enable_enterprise_modules=False,
                    height=290,
                    reload_data=False
            )
                
    def __call__(self):
        if not self.fetch_and_load():
            return
        
        self.show_excel_editor()

