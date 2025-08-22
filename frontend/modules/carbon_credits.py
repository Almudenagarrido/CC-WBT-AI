import os
import utils as u
import pandas as pd
import streamlit as st


class CarbonCredits:
    def __init__(self, excel_editor, country, subsection, model):
        self.excel_editor = excel_editor
        self.country = country
        self.subsection = subsection
        self.model = model
        self.fuel = "Carbon Credits"
        self.key_fuels = "carbon"
        self.route = os.path.join(country, "carbon-credits.xlsx")
        self.template_route = os.path.join(country, "carbon-credits-{template}.xlsx")
        self.df = None
        self.edited_df = None
        self.df_heights = {"Electricity": 80}
        self.empty_rows = {
            "Electricity": {"col": "Inputs", "partial": [], "full": []}
        }
    
    def expand_model_rows(self):
        
        mask = self.df.apply(lambda row: row.astype(str).str.contains(r"\{model\}", regex=True).any(), axis=1)
        model_rows = self.df[mask].copy()
        rows = self.df[~mask].copy()
        models = [m for m in st.session_state.models if m.lower() != "bau"]
        new_rows = []

        for _, row in model_rows.iterrows():
            for model in models:
                new_row = row.copy()
                for col in new_row.index:
                    val = str(new_row[col])
                    if "{model}" in val:
                        new_row[col] = val.replace("{model}", model)

                df_compare = pd.concat([rows, pd.DataFrame(new_rows)])
                existe = ((df_compare.astype(str) == new_row.astype(str)).all(axis=1)).any()
                if not existe:
                    new_rows.append(new_row)

        self.df = pd.concat([rows, pd.DataFrame(new_rows)], ignore_index=True)

    def show_excel_editor(self):

        st.subheader(f"Carbon Credits")

        models = [m for m in st.session_state.models if m.lower() != "bau"]
        base_height = self.df_heights.get(self.fuel, self.df_heights["Electricity"])
        height = base_height + 120*(len(models))

        empty_rows = self.empty_rows.get(self.fuel, self.empty_rows["Electricity"])
        self.excel_editor.load_data(self.df, height, [], empty_rows)
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
        self.expand_model_rows()
        self.show_excel_editor()
        