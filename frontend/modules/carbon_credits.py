import os
import openpyxl
import utils as u
import pandas as pd
import streamlit as st
from openpyxl.utils.dataframe import dataframe_to_rows


class CarbonCredits:
    def __init__(self, excel_editor, country, subsection, model):
        self.excel_editor = excel_editor
        self.country = country
        self.subsection = subsection
        self.model = model
        self.fuel = "Carbon Credits"
        self.key_fuels = "carbon"
        self.route = os.path.join(country, "carbon-credits-general.xlsx")
        self.template_route = os.path.join(country, "carbon-credits-{template}.xlsx")
        self.df = None
        self.edited_df = None
        self.df_heights = {"Electricity": 80}
        self.empty_rows = {
            "Electricity": {"col": "Inputs", "partial": [], "full": []}
        }
        self.last_models = []

    def needs_expansion(self):
        current_models = [m for m in st.session_state.models if m.lower() != "bau"]
        if not current_models or current_models == self.last_models:
            return False, current_models, []
        
        first_col = self.df.columns[0]
        mask_expand = self.df[first_col].astype(str).str.contains(r"\{model\}", regex=True, na=False)
        needs_expand = mask_expand.any()
        
        existing_models = set()
        for cell_value in self.df[first_col].dropna():
            if isinstance(cell_value, str) and "CO2 equivalent avoided in" in cell_value:
                if "{model}" not in cell_value:
                    model_name = cell_value.replace("CO2 equivalent avoided in the", "").strip()
                    if model_name:
                        existing_models.add(model_name)
        
        models_to_remove = [model for model in existing_models if model not in current_models]
        
        return needs_expand or bool(models_to_remove), current_models, models_to_remove
    
    def remove_old_models(self, models_to_remove):
        if not models_to_remove:
            return False
        
        response = u.remove_models_from_backend(
            country=self.country,
            route=self.route,
            sheet_name=self.fuel,
            models=models_to_remove
        )
        
        return response and response.get("removed", False)
    
    def expand_model_rows(self):
        needs_expansion, current_models, models_to_remove = self.needs_expansion()
        
        if models_to_remove:
            success = self.remove_old_models(models_to_remove)

            if success:
                sheet = u.get_sheet_from_backend(
                    self.country,
                    self.route,
                    self.template_route,
                    self.fuel,
                    self.key_fuels
                )
                if sheet:
                    self.df = pd.DataFrame(sheet)
        
        if needs_expansion:
            success = u.expand_sheet_in_backend(
                country=self.country,
                route=self.route,
                sheet_name=self.fuel,
                models=current_models
            )
            
            if success:
                if success.get("expanded", False):
                    sheet = u.get_sheet_from_backend(
                        self.country,
                        self.route,
                        self.template_route,
                        self.fuel,
                        self.key_fuels
                    )
                    if sheet:
                        self.df = pd.DataFrame(sheet)
                        self.last_models = current_models
    
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
        