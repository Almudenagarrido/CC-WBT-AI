import os
import time
import utils as u
import pandas as pd
import streamlit as st


class FuelFinancialInformation:

    def __init__(self, excel_editor, country, subsection, fuel):
        self.excel_editor = excel_editor
        self.country = country
        self.subsection = subsection
        self.fuel = fuel
        self.key_fuels = "normal"
        self.route = os.path.join(country, "fuel-financial-inputs.xlsx")
        self.template_route = os.path.join(country, "fuel-financial-inputs-{template}.xlsx")
        self.df = None
        self.edited_df = None
        self.df_heights = {"Electricity": 170, "LPG": 170, "Carbon": 170}
        self.editable_columns = ["Baseline"] + [str(year) for year in range(2021, 2061)]
        self.empty_rows = {
            "Electricity": {"col": "", "partial": [], "full": []},
            "Carbon Credits": {"col": "Inputs", "partial": ["Number of years that you could sell those carbon credits"], "full": []}
        }

    def show_excel_editor(self):
        st.subheader(f"{self.fuel} Financial Inputs")

        height = self.df_heights.get(self.fuel, self.df_heights["Electricity"])
        empty_rows = self.empty_rows.get(self.fuel, self.empty_rows["Electricity"])

        self.excel_editor.load_data(self.df, height, self.editable_columns, empty_rows)
        self.edited_df = self.excel_editor.show()

    def __call__(self):
        if self.subsection == "add":
            u.add_fuel_to_backend()
            return

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
                st.success(f"Changes in '{self.fuel}' Financial Inputs saved successfully.")
                time.sleep(2)
                st.rerun()

        if save_disabled:
            st.warning("Please fix invalid cells before saving.")
            for input_name, col, value, error in invalid_cells:
                st.error(f"Row '{input_name}' - Column '{col}': {error} (Current value: {value})")

        if st.button("Reset"):
            reset = u.reset_sheet_in_backend(self.route, self.template_route, self.fuel)
            if reset:
                st.success(f"'{self.fuel}' Financial Inputs reset to template successfully.")
                time.sleep(2)
                st.rerun()