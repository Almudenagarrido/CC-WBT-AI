import time
import requests
import numpy as np
import pandas as pd
from io import BytesIO
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

class DesignCapitalStructure:
    
    def __init__(self, api_base, subsection, model, fuel_market):
        self.api_base = api_base
        self.subsection = subsection
        self.model = model
        self.fuel_market = fuel_market
        self.get_url = f"{self.api_base}/design-capital-structure"
        self.save_url = f"{self.api_base}/save-design-capital-structure"
        self.reset_url = f"{self.api_base}/reset-design-capital-structure"
        self.df = None
        self.subtables = {"Finance": None, "Total": None, "Division": None, "Debts": None}
        self.subtable_titles = {
            "Finance": "Financiation",
            "Total": "Total",
            "Division": "Division",
            "Debts": "Type"
        }
        self.subtable_heights = {
            "Finance": 100,
            "Total": 130,
            "Division": 230,
            "Debts": 150
        }
        self.editable_columns = {
            "Finance": ["Amount"],
            "Total": ["Amount"],
            "Division": ["Amount"],
            "Debts": ["Baseline"] + [str(year) for year in range(1, 2051)]
        }

    def get_design_capital(self):
        try:
            url = f"{self.get_url}/{self.model}"
            res = requests.get(url)
            if res.status_code != 200:
                st.error("The file 'design-capital-structure.xlsx' was not found.")
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
            st.error(f"Could not load 'design-capital-structure-{self.model}.xlsx'")
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
        section_starts = {}
        
        for idx, row in df.iterrows():
            first_col_val = str(row[0]) if pd.notna(row[0]) else ""
            for key, keyword in self.subtable_titles.items():
                if key not in section_starts and keyword.lower() in first_col_val.lower():
                    section_starts[key] = idx

        sorted_sections = sorted(section_starts.items(), key=lambda x: x[1])
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
        st.subheader(f"{self.fuel_market} Financial Plan")

        for key, df in self.subtables.items():
            if df is not None and not df.empty:
                df.columns = df.columns.astype(str)
                base_columns = {col: col.split('_')[0] for col in df.columns}
                editable_cols = self.editable_columns.get(key, [])
                
                gb = GridOptionsBuilder.from_dataframe(df)
                for col in df.columns:
                    is_editable = base_columns[col] in editable_cols
                
                    if pd.api.types.is_numeric_dtype(df[col]):
                        gb.configure_column(
                            col, 
                            editable=is_editable,
                            type=["numericColumn", "numberColumnFilter"]
                        )
                    else:
                        gb.configure_column(
                            col,
                            editable=is_editable
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
                
                self.subtables[key] = pd.DataFrame(grid_response["data"])

    def save_changes(self):
        full_df = self.df.copy()

        for key, title in self.subtable_titles.items():
            subdf = self.subtables.get(key)
            if subdf is None or subdf.empty:
                continue

            section_start = None
            for idx, row in full_df.iterrows():
                if title in " ".join(str(v) for v in row if pd.notna(v)):
                    section_start = idx
                    break
            if section_start is None:
                continue

            headers = full_df.iloc[section_start].tolist()
            headers = [str(int(h)) if isinstance(h, float) and h.is_integer() else str(h) for h in headers]

            editable_cols = [col for col in subdf.columns if col in headers]

            for i, (_, sub_row) in enumerate(subdf.iterrows()):
                target_idx = section_start + 1 + i
                for col in editable_cols:
                    col_idx = headers.index(col)
                    full_df.iat[target_idx, col_idx] = sub_row[col]

        for i, row in full_df.iterrows():
            if str(row[0]).strip().lower() == "3.- debt":
                for col in full_df.columns:
                    if col != 0:
                        full_df.at[i, col] = pd.NA

        for col in full_df.columns:
            full_df[col] = full_df[col].astype(object)
            full_df[col] = full_df[col].fillna('-')

        for key, title in self.subtable_titles.items():
            subdf = self.subtables.get(key)
            if subdf is None or subdf.empty:
                continue

            editable_cols = self.editable_columns.get(key, [])

            invalid_cells = self.cell_validator.cell_validations(subdf, editable_cols)
            if invalid_cells:
                for _, input_name, col, value, error in invalid_cells:
                    st.warning(f"[Table {key}] Invalid value '{value}' in row '{input_name}' (column '{col}'): {error}")
                return False

        payload = {
            "model": self.model,
            "sheet_name": self.fuel_market,
            "data": full_df.to_dict(orient="records")
        }
        res = requests.post(self.save_url, json=payload)
        if res.status_code == 200:
            st.success(f"Changes in '{self.fuel_market}' saved successfully in '{self.model}'.")
        else:
            st.error(f"Save failed (HTTP {res.status_code}): {res.text}")

        return True

    def reset_sheet(self):
        payload = {
            "model": self.model,
            "sheet_name": self.fuel_market,
            "data": []
        }

        res = requests.post(self.reset_url, json=payload)
        if res.status_code == 200:
            st.success(f"File '{self.fuel_market}' of '{self.model}' was reset to template version.")
        else:
            st.error(res.json().get("error", "Something went wrong"))
    
    def __call__(self):
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

