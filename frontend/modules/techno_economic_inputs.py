import os
import time
import utils as u
import pandas as pd
import streamlit as st


class TechnoEconomicInputs:
    
    def __init__(self, excel_editor, country, subsection, model, fuel):
        self.excel_editor = excel_editor
        self.country = country
        self.subsection = subsection
        self.model = model
        self.fuel = fuel
        self.key_fuels = "rest"
        self.route = os.path.join(country, f"technoeconomic-inputs-{model}.xlsx")
        self.template_route = os.path.join(country, "technoeconomic-inputs-{model}.xlsx")
        self.route_fuels = os.path.join(country, "fuel-financial-inputs.xlsx")
        self.template_route_fuels = os.path.join(country, "fuel-financial-inputs-{template}.xlsx")
        self.df = None
        self.edited_df = None
        self.df_heights = {"Electricity": 580, "LPG": 500, "Rest of subsidies or taxes": 410}
        self.df_fuels = None
        self.edited_df_fuels = None
        self.df_heights_fuels = {"Electricity": 170, "LPG": 170, "C02": 170}
        self.editable_columns = ["Baseline"] + [str(year) for year in range(2021, 2061)]
        self.empty_rows = {
            "Electricity": {"col": "Inputs", "partial": ["GRID", "OFF GRID", "HEAT"], "full": ["Outputs of the GRID techno-economic analysis", "Outputs of the OFF GRID techno-economic analysis", "Outputs of the E-Cooking-Heat fraction techno-economic analysis"]}
        }
    
    def show_excel_editor(self):
        st.subheader(f"{self.fuel} Inputs")

        height_fuels = self.df_heights_fuels.get(self.fuel, self.df_heights_fuels["Electricity"])
        height = self.df_heights.get(self.fuel, self.df_heights["Electricity"])
        empty_rows = self.empty_rows.get(self.fuel, self.empty_rows["Electricity"])

        if self.fuel != "Rest of subsidies or taxes":
            self.excel_editor.load_data(self.df_fuels, height_fuels, [], empty_rows)
            self.edited_df_fuels = self.excel_editor.show()

        self.excel_editor.load_data(self.df, height, self.editable_columns, empty_rows)
        self.edited_df = self.excel_editor.show()

    def __call__(self):
        if self.fuel != "Rest of subsidies or taxes":
            sheet_fuels = u.get_sheet_from_backend(
                self.country,
                self.route_fuels,
                self.template_route_fuels,
                self.fuel,
                self.key_fuels
            )
            self.df_fuels = pd.DataFrame(sheet_fuels)

        sheet = u.get_sheet_from_backend(
            self.country,
            self.route,
            self.template_route,
            self.fuel,
            self.key_fuels
        )
        self.df = pd.DataFrame(sheet)

        self.show_excel_editor()
        invalid_cells = self.excel_editor.validate()
        save_disabled = bool(invalid_cells)

        if st.button("Save", disabled=save_disabled):
            saved = u.save_sheet_in_backend(self.edited_df, self.route, self.fuel)
            if saved:
                st.success(f"Changes in '{self.fuel}' Techno-Economic Inputs saved successfully.")
                time.sleep(2)
                st.rerun()

        if save_disabled:
            st.warning("Please fix invalid cells before saving.")
            for input_name, col, value, error in invalid_cells:
                st.error(f"Row '{input_name}' - Column '{col}': {error} (Current value: {value})")

        if st.button("Reset"):
            reset = u.reset_sheet_in_backend(self.route, self.template_route, self.fuel)
            if reset:
                st.success(f"'{self.fuel}' Techno-Economic Inputs reset to template successfully.")
                time.sleep(2)
                st.rerun()