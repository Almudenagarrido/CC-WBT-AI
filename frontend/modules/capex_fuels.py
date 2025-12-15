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
        self.key_fuels = "normal"
        self.route = os.path.join(country, f"capex-fuels-{model}.xlsx")
        self.template_route = os.path.join(country, "capex-fuels-{model}.xlsx")
        self.df = None
        self.edited_df = None
        self.df_heights = {"LPG": 320}
        self.subtables = {}
        self.empty_rows = {
            "LPG":{"col": "Type", "partial": ["Total Depreciation"], "full": []},
            "Electricity":{"Grid": {"col": "Grid", "partial": ["Total Depreciation"], "full": []}, "Off-Grid": {"col": "Off-Grid", "partial": ["Total Depreciation"], "full": []}}  
        }
        

    def split_into_subtables(self):
        df = self.df.reset_index(drop=True)
        self.subtables[self.fuel] = {}

        if self.fuel == "Electricity":
            self._process_electricity_structure(df)
        else:
            self.subtables[self.fuel][None] = df

    def _process_electricity_structure(self, df):
        
        first_col = df.iloc[:, 0].astype(str).str.strip().str.lower()
        header_rows = first_col[first_col == "type"].index.tolist()
        
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

        for key, df in self.subtables[self.fuel].items():
            if key != None:
                st.markdown(f"##### {key}")

            height = self.df_heights.get(self.fuel, self.df_heights["LPG"])

            editable_cols = [col for col in df.columns if col not in ['Type', 'Units']]
            
            if self.fuel == "Electricity" and key in ["Grid", "Off-Grid"]:
                empty_rows = self.empty_rows.get(self.fuel, {}).get(key, {})
            else:
                empty_rows = self.empty_rows.get(self.fuel, {})

            self.excel_editor.load_data(df, height, editable_cols, empty_rows)
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
