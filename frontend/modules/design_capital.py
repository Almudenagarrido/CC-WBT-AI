import os
import time
import utils as u
import numpy as np
import pandas as pd
import streamlit as st


class DesignCapitalStructure:
    
    def __init__(self, excel_editor, country, subsection, model, fuel):
        self.excel_editor = excel_editor
        self.country = country
        self.subsection = subsection
        self.model = model
        self.fuel = fuel
        self.key_fuels = "expanded"
        self.route = os.path.join(country, f"design-capital-{model}.xlsx")
        self.template_route = os.path.join(country, "design-capital-{model}.xlsx")
        self.df = None
        self.edited_df = None
        self.subtables = {}
        self.important_cols = ["Division", "Units", "Amount", "FFSS - Outputs", "FFSS - Inputs", "Type", "Financiation", "Total", "Category"]
        if self.fuel and "electricity" in self.fuel.lower():
            self.section_headers = ["Division - GRID", "Division - OFF-GRID", "FFSS - Outputs", "FFSS - Inputs", "Financiation", "Total - GRID", "Total - OFF-GRID",]
            self.subtable_heights = {
                "Division - GRID": 240,
                "Division - OFF-GRID": 240,
                "FFSS - Outputs": 120,
                "FFSS - Inputs": 90,
                "Financiation": 70,
                "Total - GRID": 155,
                "Total - OFF-GRID": 155,
            }
            self.editable_columns = {
                "Division - GRID": ["Amount"],
                "Division - OFF-GRID": ["Amount"],
                "FFSS - Outputs": [],
                "FFSS - Inputs": [str(year) for year in range(2021, 2061)],
                "Financiation": [],
                "Total - GRID": ["Amount"],
                "Total - OFF-GRID": ["Amount"]
            }
            self.empty_rows = {
                "Division - GRID": {"col": "Division - GRID", "partial": [], "full": ["3. Debt - GRID"], "target_columns": ["Amount"]},
                "Division - OFF-GRID": {"col": "Division - OFF-GRID", "partial": [], "full": ["3. Debt - OFF-GRID"], "target_columns": ["Amount"]},
                "FFSS - Outputs": {"col": "", "partial": [], "full": []},
                "FFSS - Inputs": {"col": "", "partial": [], "full": []},
                "Financiation": {"col": "", "partial": [], "full": []},
                "Total - GRID": {"col": "", "partial": [], "full": []},
                "Total - OFF-GRID": {"col": "", "partial": [], "full": []}
            }
        else:
            self.section_headers = ["Division", "FFSS - Outputs", "FFSS - Inputs", "Financiation", "Total"]
            self.subtable_heights = {
                "Division": 240,
                "FFSS - Outputs": 120,
                "FFSS - Inputs": 90,
                "Financiation": 70,
                "Total": 155
            }
            self.editable_columns = {
                "Division": ["Amount"],
                "FFSS - Outputs": [],
                "FFSS - Inputs": [str(year) for year in range(2021, 2061)],
                "Financiation": [],
                "Total": ["Amount"]
            }
            self.empty_rows = {
                "Division": {"col": "Division", "partial": [], "full": ["3. Debt"], "target_columns": ["Amount"]},
                "FFSS - Outputs": {"col": "", "partial": [], "full": []},
                "FFSS - Inputs": {"col": "", "partial": [], "full": []},
                "Financiation": {"col": "", "partial": [], "full": []},
                "Total": {"col": "", "partial": [], "full": []}
            }

    def split_into_subtables(self):
    
        df = self.df.reset_index(drop=True)
        self.subtables[self.fuel] = {}
        
        first_section = self.section_headers[0]
        first_col = df.iloc[:, 0].astype(str).str.strip().str.lower()
        
        sections = {}
        sections[first_section] = 0 
        for header in self.section_headers[1:]:
            matches = first_col[first_col == header.lower()]
            if not matches.empty:
                sections[header] = matches.index[0]
            else:
                for idx, val in enumerate(first_col):
                    if header.lower() in val or val in header.lower():
                        sections[header] = idx
                        break
        
        sorted_sections = sorted(sections.items(), key=lambda x: x[1])
        
        for i, (section, start_idx) in enumerate(sorted_sections):
            
            end_idx = sorted_sections[i+1][1] - 1 if i + 1 < len(sorted_sections) else len(df)
            subdf = df.iloc[start_idx:end_idx+1].copy()
            
            if section != first_section and not subdf.empty and str(subdf.iloc[0, 0]).strip().lower() == section.lower():
                new_columns = []
                for col in subdf.iloc[0]:
                    if pd.isna(col) or str(col).strip() in ['', '-', 'None', 'NaN']:
                        new_columns.append('')
                    else:
                        new_columns.append(str(col))
                subdf.columns = new_columns
                subdf = subdf.iloc[1:]
            
            subdf = subdf.dropna(axis=1, how='all')
            cols_to_remove = []
            for col in subdf.columns:
                all_dash_or_empty = True
                for val in subdf[col]:
                    if not (pd.isna(val) or str(val).strip() in ['', '-']):
                        all_dash_or_empty = False
                        break
                
                is_important = any(important in str(col) for important in self.important_cols)
                if all_dash_or_empty and not is_important:
                    cols_to_remove.append(col)
            
            if cols_to_remove:
                subdf = subdf.drop(columns=cols_to_remove)
            
            subdf = subdf.dropna(how='all')
            if not subdf.empty:
                subdf = subdf.reset_index(drop=True)
                self.subtables[self.fuel][section] = subdf

    def combine_subtables(self):
    
        combined_df = self.df.copy()
        first_section = self.section_headers[0]
        
        for section in self.section_headers:
            if section in self.subtables[self.fuel]:
                edited_data = self.subtables[self.fuel][section]
                
                if section == first_section:
                    start_idx = 0
                    
                    if not edited_data.empty:
                        for i in range(min(len(edited_data), len(combined_df))):
                            for j in range(min(len(edited_data.columns), len(combined_df.columns))):
                                val = edited_data.iloc[i, j]
                                if not pd.isna(val) and str(val).strip() not in ['', '-']:
                                    combined_df.iloc[i, j] = val
                else:
                    mask = combined_df.iloc[:, 0].astype(str).str.strip().str.lower() == section.lower()
                    if not mask.any():
                        for idx, val in enumerate(combined_df.iloc[:, 0].astype(str).str.strip().str.lower()):
                            if section.lower() in val:
                                start_idx = idx
                                break
                        else:
                            continue
                    else:
                        start_idx = mask.idxmax()
                    
                    if start_idx < len(combined_df):
                        combined_df.iloc[start_idx] = self.df.iloc[start_idx]
                    
                    if not edited_data.empty:
                        for i in range(min(len(edited_data), len(combined_df) - start_idx - 1)):
                            for j in range(min(len(edited_data.columns), len(combined_df.columns))):
                                val = edited_data.iloc[i, j]
                                if not pd.isna(val) and str(val).strip() not in ['', '-']:
                                    combined_df.iloc[start_idx+1+i, j] = val
        
        return combined_df

    def show_input_tables(self):
        st.subheader(f"Capital Structure for {self.fuel} - Input Tables")
        
        input_sections = [section for section in self.section_headers if any(keyword in section for keyword in ["Division", "FFSS - Outputs", "FFSS - Inputs"])]
        
        for section in input_sections:
            self.show_section_editor(section)
        
        self.edited_df = self.combine_subtables()

    def show_section_editor(self, section):
        
        if section in self.subtables[self.fuel] and not self.subtables[self.fuel][section].empty:
            df = self.subtables[self.fuel][section]
            height = self.subtable_heights.get(section, self.subtable_heights[self.section_headers[0]])
            editable_cols = self.editable_columns.get(section, self.editable_columns[self.section_headers[0]])
            empty_rows = self.empty_rows.get(section, self.empty_rows[self.section_headers[0]])
            
            self.excel_editor.load_data(df, f"{self.fuel}_{section}_editor",height, editable_cols, empty_rows)
            edited_df = self.excel_editor.show()
            self.subtables[self.fuel][section] = edited_df
    
    def show_action_buttons(self):
        invalid_cells = self.validate_input_sections()
        save_disabled = bool(invalid_cells)

        if st.button("Save", disabled=save_disabled):
            saved = u.save_sheet_in_backend(self.edited_df, self.route, self.fuel)
            if saved:
                st.success(f"Changes in '{self.fuel}' Design Capital saved successfully.")
                time.sleep(2)
                st.rerun()

        if save_disabled:
            for section, input_name, col, value, error in invalid_cells:
                st.warning(f"Section '{section}' - Row '{input_name}' - Column '{col}': {error} (Current value: {value})")

        # Botón Reset (igual que TechnoEconomicInputs)
        if st.button("Reset"):
            reset = u.reset_sheet_in_backend(self.route, self.template_route, self.fuel)
            if reset:
                st.success(f"'{self.fuel}' Design Capital reset to template successfully.")
                time.sleep(2)
                st.rerun()
    
    def validate_input_sections(self):
        input_sections = [section for section in self.section_headers if any(keyword in section for keyword in ["Division", "FFSS - Inputs"])]
        
        invalid_cells = []
        for section in input_sections:
            if section in self.subtables[self.fuel]:
                df = self.subtables[self.fuel][section]
                height = self.subtable_heights.get(section, self.subtable_heights[self.section_headers[0]])
                editable_cols = self.editable_columns.get(section, self.editable_columns[self.section_headers[0]])
                self.excel_editor.load_data(df, f"{self.fuel}_{section}_validator", height, editable_cols, empty_rows={})
                section_invalid_cells = self.excel_editor.validate()
                for error in section_invalid_cells:
                    input_name, col, value, msg = error
                    invalid_cells.append((section, input_name, col, value, msg))
        return invalid_cells

    def show_validation_errors(self, invalid_cells):
        for section, input_name, col, value, error in invalid_cells:
            st.warning(f"Section '{section}' - Row '{input_name}' - Column '{col}': {error} (Current value: {value})")

    def show_calculation_section(self):
        st.markdown("---")
        
        if st.button("Calculate Financial Tables", type="secondary", key="calculate_financial"):
            st.subheader("Calculated Financial Tables")
            
            calculated_sections = [section for section in self.section_headers 
                                  if any(keyword in section for keyword in ["Financiation", "Total"])]
            
            for section in calculated_sections:
                self.show_calculated_section(section)

    def show_calculated_section(self, section):
        if section in self.subtables[self.fuel] and not self.subtables[self.fuel][section].empty:
            df = self.subtables[self.fuel][section]
            height = self.subtable_heights.get(section, self.subtable_heights[self.section_headers[0]])
            editable_cols = self.editable_columns.get(section, self.editable_columns[self.section_headers[0]])
            empty_rows = self.empty_rows.get(section, self.empty_rows[self.section_headers[0]])
            
            self.excel_editor.load_data(df, self.fuel, height, editable_cols, empty_rows)
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
        
        self.split_into_subtables()        
        self.show_input_tables()        
        self.show_action_buttons()
        self.show_calculation_section()