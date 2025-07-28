import requests
import numpy as np
import pandas as pd
from io import BytesIO
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode


class FinancialStatements:
    
    def __init__(self, api_base, subsection, model, fuel_market):
        self.api_base = api_base
        self.subsection = subsection
        self.model = model
        self.fuel_market = fuel_market
        self.get_url = f"{self.api_base}/financial-statements"
        self.df = None
        self.subtables = {"Profit & Loss": None, "Balance Sheet": None, "Cash Flow Statement": None, "PP&E - Capex": None, "Working Capital Calculations": None, "Equity Schedule": None, "Capital Structure": None}
        self.section_starts = {
            "Profit & Loss": 0,
            "Balance Sheet": 36,
            "Cash Flow Statement": 65,
            "PP&E - Capex": 84,
            "Working Capital Calculations": 92,
            "Equity Schedule": 102,
            "Capital Structure": 108
        }
        self.subtable_heights = {"Profit & Loss": 1070, "Balance Sheet": 870, "Cash Flow Statement": 580, "PP&E - Capex": 260, "Working Capital Calculations": 320, "Equity Schedule": 200, "Capital Structure": 400}
        if self.fuel_market == "Electricity (Low access)":
            self.subtables["Transferred Capex"] = None
            self.section_starts["Transferred Capex"] = 121
            self.subtable_heights["Transferred Capex"] = 170
    
    def get_financial_statements(self):
        try:
            url = f"{self.get_url}/{self.model}"
            res = requests.get(url)
            if res.status_code != 200:
                st.error(f"The file 'financial-statements-{self.model}.xlsx' was not found.")
                return []

            file_data = BytesIO(res.content)
            xls = pd.ExcelFile(file_data)
            return xls.sheet_names

        except Exception as e:
            st.error(f"Error fetching capital structure: {e}")
            return []

    def fetch_and_load(self):
        url = f"{self.get_url}/{self.model}"
        res = requests.get(url)
        if res.status_code != 200:
            st.error(f"Could not load 'financial-statements-{self.model}.xlsx'")
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
        sorted_sections = sorted(self.section_starts.items(), key=lambda x: x[1])

        for i, (key, start_idx) in enumerate(sorted_sections):
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
            
            self.subtables[key] = subdf

    def show_excel_editor(self):
        st.subheader(f"{self.fuel_market} - FFSS")

        for key, df in self.subtables.items():
            st.markdown(f"##### {key}")
            if df is not None and not df.empty:
                df.columns = df.columns.astype(str)
                
                gb = GridOptionsBuilder.from_dataframe(df)
                for col in df.columns:
                
                    if pd.api.types.is_numeric_dtype(df[col]):
                        gb.configure_column(
                            col,
                            type=["numericColumn", "numberColumnFilter"]
                        )
                    else:
                        gb.configure_column(
                            col,
                        )
                
                grid_options = gb.build()
                grid_response = AgGrid(
                    df,
                    gridOptions=grid_options,
                    update_mode=GridUpdateMode.VALUE_CHANGED,
                    allow_unsafe_jscode=True,
                    enable_enterprise_modules=False,
                    height=self.subtable_heights[key],
                    reload_data=False
                )

    def __call__(self):
        if not self.fetch_and_load():
            return
        
        self.show_excel_editor()

