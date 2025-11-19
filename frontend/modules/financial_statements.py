import os
import utils as u
import pandas as pd
import streamlit as st


class FinancialStatements:
    
    def __init__(self, excel_editor, country, subsection, model, fuel):
        self.excel_editor = excel_editor
        self.country = country
        self.subsection = subsection
        self.model = model
        self.fuel = fuel
        self.key_fuels = "more_expanded"
        self.route = os.path.join(country, f"financial-statements-{model}.xlsx")
        self.template_route = os.path.join(country, "financial-statements-{model}.xlsx")
        self.df = None
        self.edited_df = None
        self.subtables = {}
        self.section_headers = ["P&L", "BS", "CFS", "PP&E - Capex", "WCC", "ES", "CS"]
        self.subtable_heights = {"P&L": 1070, "BS": 870, "CFS": 580, "PP&E - Capex": 230, "WCC": 320, "ES": 200, "CS": 410}
        self.empty_rows = {
            "P&L": {"col": "", "partial": [], "full": []}
        }
    
    def split_into_subtables(self):
        df = self.df.reset_index(drop=True)
        self.subtables[self.fuel] = {}
        first_col = df.iloc[:, 0].astype(str).str.strip().str.lower()
        sections = {
            h: first_col[first_col == h.lower()].index[0] 
            for h in self.section_headers 
            if h.lower() in first_col.values
        }
        
        if "P&L" not in sections and "BS" in sections:
            sections["P&L"] = 0
        
        sorted_sections = sorted(sections.items(), key=lambda x: x[1])
        for i, (section, start_idx) in enumerate(sorted_sections):
            if i + 1 < len(sorted_sections):
                end_idx = sorted_sections[i+1][1] - 1
            else:
                end_idx = len(df)
            
            subdf = df.iloc[start_idx:end_idx+1].copy()
            
            if not subdf.empty and str(subdf.iloc[0, 0]).strip().lower() == section.lower():
                subdf.columns = [str(int(x)) if isinstance(x, float) and x.is_integer() else str(x) for x in subdf.iloc[0]]
                subdf = subdf.iloc[1:]
            
            invalid_cols = {'Unnamed', 'None', '-'}
            valid_cols = [
                col for col in subdf.columns 
                if str(col) not in invalid_cols 
                and not str(col).startswith('Unnamed:') 
                and not pd.isna(col)
            ]
            
            subdf = subdf[valid_cols].dropna(how='all')
            self.subtables[self.fuel][section] = subdf.reset_index(drop=True)

    def show_excel_editor(self):
        st.subheader(f"{self.fuel} - FFSS")

        for section, df in self.subtables[self.fuel].items():
            if df.empty:
                continue

            height = self.subtable_heights.get(section, self.subtable_heights["P&L"])
            empty_rows = self.empty_rows.get(section, self.empty_rows["P&L"])
            self.excel_editor.load_data(df, height, [], empty_rows)
            edited_df = self.excel_editor.show()
            self.subtables[self.fuel][section] = edited_df

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

