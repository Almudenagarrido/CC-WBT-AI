import os
import time
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
        self.key_fuels = "only_carbon"
        self.route = os.path.join(country, "carbon-credits.xlsx")
        self.template_route = os.path.join(country, "carbon-credits-{template}.xlsx")
        self.df = None
        self.edited_df = None
        self.subtables = {}
        self.important_cols = []
        self.section_headers = ["CO2 emited", "Carbon Credits"]
        self.subtable_heights = {
            "CO2 emited": 90,
            "Carbon Credits": 60
        }
        self.editable_columns = {
            "CO2 emited": [str(year) for year in range(2020, 2061)],
            "Carbon Credits": [str(year) for year in range(2020, 2061)]
        }
        self.empty_rows = {
            "CO2 emited": {"col": "", "partial": [], "full": []},
            "Carbon Credits": {"col": "", "partial": [], "full": []}
        }
        self.last_models = []

    def needs_expansion(self):

        current_models = [m for m in st.session_state.models if m.lower() != "baseline"]
        if not current_models or current_models == self.last_models:
            return False, current_models, []

        first_col = self.df.columns[0]
        mask_expand = self.df[first_col].astype(str).str.strip().str.contains(r"\{model\}", regex=True, na=False)
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

            if success and success.get("expanded", False):
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

    def split_into_subtables(self):
        
        df = self.df.reset_index(drop=True)
        self.subtables[self.fuel] = {}

        for i, section in enumerate(self.section_headers):
            
            mask = df.iloc[:, 0].astype(str).str.strip().str.contains(section, case=False, na=False)
            
            if mask.any():
                start_idx = mask.idxmax()
                
                if i + 1 < len(self.section_headers):
                    next_section = self.section_headers[i + 1]
                    next_mask = df.iloc[:, 0].astype(str).str.strip().str.contains(next_section, case=False, na=False)
                    end_idx = next_mask.idxmax() - 1 if next_mask.any() else df.index[-1]
                else:
                    end_idx = df.index[-1]

                subdf = df.iloc[start_idx:end_idx + 1].copy()
                subdf = subdf.reset_index(drop=True)

                header_row = None
                
                if section.lower() == "carbon credits":
                    header_row = subdf.iloc[0].copy()
                    new_header = header_row.astype(str).tolist()
                    for i, h in enumerate(new_header):
                        try:
                            if isinstance(h, str) and h.endswith(".0"):
                                new_header[i] = str(int(float(h)))
                            else:
                                new_header[i] = h
                        except:
                            new_header[i] = h

                    subdf = subdf[1:].copy()
                    subdf.columns = new_header

                self.subtables[self.fuel][section] = {
                    "df": subdf,
                    "header_row": header_row
                }

    def combine_subtables(self):

        combined_df = self.df.copy()

        for section in self.section_headers:

            if section not in self.subtables[self.fuel]:
                continue

            edited_data = self.subtables[self.fuel][section]["df"]
            header_row = self.subtables[self.fuel][section]["header_row"]

            if header_row is None:
                edited_with_header = edited_data.copy()
            else:
                edited_with_header = pd.concat(
                    [pd.DataFrame([header_row]), edited_data],
                    ignore_index=True
                )

            mask = (
                combined_df.iloc[:, 0]
                .astype(str)
                .str.strip()
                .str.lower()
                .str.contains(section.lower(), na=False)
            )

            if not mask.any():
                continue

            start_idx = mask.idxmax()

            for i in range(min(len(edited_with_header), len(combined_df) - start_idx)):
                for j in range(min(len(edited_with_header.columns), len(combined_df.columns))):
                    val = edited_with_header.iloc[i, j]

                    if not pd.isna(val) and str(val).strip() not in ['', '-']:
                        combined_df.iloc[start_idx + i, j] = val

        return combined_df

    def show_input_tables(self):
        
        st.subheader("Carbon Credits - Input Emissions")
        input_section = "CO2 emited"
        self.show_section_editor(input_section)
        self.edited_df = self.combine_subtables()
    
    def get_num_models(self):
        return len([m for m in st.session_state.models if m.lower() != "baseline"])
    
    def get_section_height(self, section):
        num_models = self.get_num_models()

        if section == "CO2 emited":
            base = 90
            per_model = 30
            return base + num_models * per_model

        if section == "Carbon Credits":
            base = 60
            per_model = 90
            return base + num_models * per_model

        return 240

    def show_section_editor(self, section):
        
        if section in self.subtables[self.fuel] and not self.subtables[self.fuel][section]["df"].empty:
            df = self.subtables[self.fuel][section]["df"]
            height = self.get_section_height(section)
            editable_cols = self.editable_columns.get(section, [])
            empty_rows = self.empty_rows.get(section, {"col": "", "partial": [], "full": []})
            self.excel_editor.load_data(df, f"{self.fuel}_{section}_editor", height, editable_cols, empty_rows)
            edited_df = self.excel_editor.show()
            self.subtables[self.fuel][section]["df"] = edited_df

    def show_action_buttons(self):
        
        if st.button("Save"):
            saved = u.save_sheet_in_backend(self.edited_df, self.route, self.fuel)
            if saved:
                st.success(f"CO2 inputs saved successfully.")
                time.sleep(2)
                st.rerun()

        if st.button("Reset"):
            reset = u.reset_sheet_in_backend(self.route, self.template_route, self.fuel)
            if reset:
                st.success(f"CO2 inputs reset to template successfully.")
                time.sleep(2)
                st.rerun()

    def show_calculation_section(self):
        
        st.markdown("---")
        if st.button("Calculate Carbon Credits", type="secondary", key="calculate_carbon"):
            calculated_section = "Carbon Credits"
            self.show_calculated_section(calculated_section)

    def show_calculated_section(self, section):
        if section in self.subtables[self.fuel] and not self.subtables[self.fuel][section]["df"].empty:
            df = self.subtables[self.fuel][section]["df"]
            height = self.get_section_height(section)
            editable_cols = []
            empty_rows = self.empty_rows.get(section, {"col": "", "partial": [], "full": []})
            self.excel_editor.load_data(df, f"{self.fuel}_{section}_calc", height, editable_cols, empty_rows)
            _ = self.excel_editor.show()

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
        self.split_into_subtables()

        self.show_input_tables()
        self.show_action_buttons()
        self.show_calculation_section()
