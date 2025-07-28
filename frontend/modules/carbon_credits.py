import time
import requests
import pandas as pd
from io import BytesIO
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

class CarbonCredits:
    def __init__(self, api_base, subsection, model, cell_validator):
        self.api_base = api_base
        self.subsection = subsection
        self.model = model
        self.cell_validator = cell_validator
        self.get_url = f"{self.api_base}/carbon-credits"
        self.save_url = f"{self.api_base}/save-carbon-credits"
        self.reset_url = f"{self.api_base}/reset-carbon-credits"
        self.df = None
        self.edited_df = None
        self.editable_columns = ["Baseline"] + [str(year) for year in range(2020, 2051)]

    def get_carbon_credits(self):
        try:
            res = requests.get(self.get_url)
            if res.status_code != 200:
                st.error("The file 'carbon-credits.xlsx' was not found.")
                return []
            file_data = BytesIO(res.content)
            xls = pd.ExcelFile(file_data)
            return xls.sheet_names
        except Exception as e:
            st.error(f"Error fetching 'carbon-credits' file: {e}")
            return []
    
    def fetch_and_load(self):
        res = requests.get(self.get_url)
        if res.status_code != 200:
            st.error("Could not load 'carbon-credits.xlsx'")
            return False

        file_data = BytesIO(res.content)
        self.df = pd.read_excel(file_data, sheet_name="Carbon Credits", engine="openpyxl")

        for col in self.df.columns:
            if col in self.editable_columns:
                self.df[col] = pd.to_numeric(self.df[col].replace("-", pd.NA), errors="coerce")
        
        self.df.dropna(how="all", inplace=True)
        self.df.dropna(axis=1, how="all", inplace=True)

        return True
    
    def show_excel_editor(self):

        st.subheader(f"Carbon Credits")
        df = self.df.copy()

        df_filtered = df[~df.apply(lambda row: row.astype(str).str.contains(r"\{model\}", regex=True).any(), axis=1)]

        gb = GridOptionsBuilder.from_dataframe(df_filtered)
        
        for col in df_filtered.columns:
            col_str = str(col)
            if col_str in self.editable_columns:
                gb.configure_column(col_str, editable=True)
            else:
                gb.configure_column(col_str, editable=False)

        grid_options = gb.build()
        grid_response = AgGrid(
            df_filtered,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.VALUE_CHANGED,
            allow_unsafe_jscode=True,
            enable_enterprise_modules=False,
            height=220
        )
        self.edited_df = pd.DataFrame(grid_response["data"])
    
    def save_changes(self):
        self.df.columns = self.df.columns.map(str)
        df = self.edited_df.copy()
        df = df[self.df.columns]

        for col in df.columns:
            col_str = str(col)
            if col_str in self.editable_columns:
                df[col_str] = df[col_str].fillna(0)
                
        invalid_cells = self.cell_validator.cell_validations(df, self.editable_columns)

        if invalid_cells:
            for _, input_name, col, value, error in invalid_cells:
                st.warning(f"Invalid value '{value}' in row '{input_name}' (column '{col}'): {error}")
            return False

        data_json = df.reset_index(drop=True).to_dict(orient="records")
        payload = {
            "model": "",
            "sheet_name": "Carbon Credits",
            "data": data_json
        }
        res = requests.post(self.save_url, json=payload)
        if res.status_code == 200:
            st.success(f"Changes saved successfully in 'carbon-credits.xlsx'.")
        else:
            st.error("Error saving the changes, try again later.")

        return True
    
    def reset_sheet(self):
        response = requests.post(self.reset_url, json={"model": "", "sheet_name": "Carbon Credits", "data": []})
        if response.status_code == 200:
            st.success(f"File 'carbon-credits' reset to template version.")
        else:
            st.error(response.json().get("error", "Something went wrong"))

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

