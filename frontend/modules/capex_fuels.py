import os
import utils as u
import pandas as pd
import streamlit as st


class CapexFuelMarket:
    
    def __init__(self, excel_editor, country, subsection, model, fuel):
        self.excel_editor = excel_editor
        self.country = country
        self.subsection = subsection
        self.model = model
        self.fuel = fuel
        self.key_fuels = "expanded"
        self.route = os.path.join(country, f"capex-fuels-{model}.xlsx")
        self.template_route = os.path.join(country, "capex-fuels-{model}.xlsx")
        self.df = None
        self.edited_df = None
        self.df_heights = {"LPG": 320}
        self.subtables = {}
        self.empty_rows = {
            "LPG":{"col": "Type", "partial": ["Total Depreciation"], "full": []},
            "Electricity & E-Cooking":{"Grid": {"col": "Grid", "partial": ["Total Depreciation"], "full": []}, "Off-Grid": {"col": "Off-Grid", "partial": ["Total Depreciation"], "full": []}},
            "Electricity (Low access)":{"Grid": {"col": "Grid", "partial": ["Total Depreciation"], "full": []}, "Off-Grid": {"col": "Off-Grid", "partial": ["Total Depreciation"], "full": []}}
        }
        
    def split_into_subtables(self):
        df = self.df.reset_index(drop=True)
        self.subtables[self.fuel] = {}

        if self.fuel in ["Electricity & E-Cooking", "Electricity (Low access)"]:
            self._process_electricity_structure(df)
        else:
            self.subtables[self.fuel][None] = df

    def _process_electricity_structure(self, df):
        
        first_col = df.iloc[:, 0].astype(str).str.strip()
        header_rows = []
        for idx, value in enumerate(first_col):
            if "type" in value.lower():
                header_rows.append(idx)
                
        if not header_rows:
            unique_values = first_col.unique()
            
            if len(unique_values) <= 3:
                for value in unique_values:
                    if pd.notna(value) and str(value).strip():
                        subdf = df[df.iloc[:, 0] == value].reset_index(drop=True)
                        key = str(value).strip()
                        self.subtables[self.fuel][key] = subdf
                return
        
        if header_rows and header_rows[0] > 0:
            first_block = df.iloc[:header_rows[0]].reset_index(drop=True)
            
            if len(first_block.columns) > 1:
                key = first_block.columns.tolist()[1]
                self.subtables[self.fuel][key] = first_block
                
        for i, start_idx in enumerate(header_rows):
            end_idx = header_rows[i + 1] if i + 1 < len(header_rows) else len(df)
            subdf = df.iloc[start_idx:end_idx].reset_index(drop=True)
            
            if len(subdf) > 0:
                header_row = subdf.iloc[0]
                new_columns = []
                for x in header_row:
                    if isinstance(x, float) and x.is_integer():
                        new_columns.append(str(int(x)))
                    else:
                        new_columns.append(str(x))
                subdf.columns = new_columns
                subdf = subdf.iloc[1:].reset_index(drop=True)
                
                if len(subdf.columns) > 1:
                    key = subdf.columns.tolist()[1]
                    self.subtables[self.fuel][key] = subdf
    
    def show_excel_editor(self):
        st.subheader(f"{self.fuel} - CAPEX")

        for idx, (key, df) in enumerate(self.subtables[self.fuel].items()):
            if key != None:
                st.markdown(f"##### {key}")

            height = self.df_heights.get(self.fuel, self.df_heights["LPG"])
            
            if self.fuel == "Electricity" and key in ["Grid", "Off-Grid"]:
                empty_rows = self.empty_rows.get(self.fuel, {}).get(key, {})
            else:
                empty_rows = self.empty_rows.get(self.fuel, {})

            self.excel_editor.load_data(df, f"{self.fuel}_{idx}", height, [], empty_rows)
            self.edited_df = self.excel_editor.show()
                
    def __call__(self):

        sheet = u.get_sheet_from_backend(
            self.country,
            self.route,
            self.template_route,
            self.fuel,
            self.key_fuels
        )

        self.df = pd.DataFrame(sheet)
        self.split_into_subtables()
        self.show_excel_editor()
