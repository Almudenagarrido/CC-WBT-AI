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
        if self.fuel and "e-cooking" in self.fuel.lower():
            self.section_headers = ["Division - GRID", "Division - OFF-GRID", "Type", "Financiation", "Total - GRID", "Total - OFF-GRID",]
            self.subtable_heights = {
                "Division - GRID": 270,
                "Division - OFF-GRID": 270,
                "Type": 140,
                "Financiation": 70,
                "Total - GRID": 130,
                "Total - OFF-GRID": 130,
            }
            self.editable_columns = {
                "Division - GRID": ["Amount"],
                "Division - OFF-GRID": ["Amount"],
                "Type": ["Baseline"] + [str(year) for year in range(2021, 2061)],
                "Financiation": [],
                "Total - GRID": ["Amount"],
                "Total - OFF-GRID": ["Amount"]
            }
            self.empty_rows = {
                "Division - GRID": {"col": "Division - GRID", "partial": [], "full": ["3. Debt - GRID"]},
                "Division - OFF-GRID": {"col": "Division - OFF-GRID", "partial": [], "full": ["3. Debt - OFF-GRID"]},
                "Type": {"col": "Type", "partial": [], "full": ["Annual debt needs"]},
                "Financiation": {"col": "", "partial": [], "full": []},
                "Total - GRID": {"col": "", "partial": [], "full": []},
                "Total - OFF-GRID": {"col": "", "partial": [], "full": []}
            }
        else:
            self.section_headers = ["Division", "Type", "Financiation", "Total"]
            self.subtable_heights = {
                "Division": 270,
                "Type": 140,
                "Financiation": 70,
                "Total": 130
            }
            self.editable_columns = {
                "Division": ["Amount"],
                "Type": ["Baseline"] + [str(year) for year in range(2021, 2061)],
                "Financiation": [],
                "Total": ["Amount"]
            }
            self.empty_rows = {
                "Division": {"col": "Division", "partial": [], "full": ["3. Debt"]},
                "Type": {"col": "Type", "partial": [], "full": ["Annual debt needs"]},
                "Financiation": {"col": "", "partial": [], "full": []},
                "Total": {"col": "", "partial": [], "full": []}
            }

    def split_into_subtables(self):
        
        df = self.df.reset_index(drop=True)
        self.subtables[self.fuel] = {}
        
        first_col = df.iloc[:, 0].astype(str).str.strip().str.lower()
        
        first_header = self.section_headers[0] if self.section_headers else "Division"
        other_sections = [h for h in self.section_headers if h != first_header]
        
        for header in other_sections:
            matches = first_col[first_col == header.lower()]
            if not matches.empty:
                break
        
        sections = {}
        sections[first_header] = 0
        
        for header in other_sections:
            matches = first_col[first_col == header.lower()]
            if not matches.empty:
                sections[header] = matches.index[0]
        
        sorted_sections = sorted(sections.items(), key=lambda x: x[1])
        
        for i, (section, start_idx) in enumerate(sorted_sections):
            
            end_idx = sorted_sections[i+1][1] - 1 if i + 1 < len(sorted_sections) else len(df)
            subdf = df.iloc[start_idx:end_idx+1].copy()
            
            if not subdf.empty and str(subdf.iloc[0, 0]).strip().lower() == section.lower():

                new_columns = []
                for col in subdf.iloc[0]:
                    if pd.isna(col) or str(col).strip() in ['', 'None', 'NaN']:
                        new_columns.append('')
                    else:
                        new_columns.append(str(col))
                subdf.columns = new_columns
                subdf = subdf.iloc[1:]
            
            subdf = subdf.dropna(axis=1, how='all')
            subdf = subdf.dropna(how='all')
            
            if not subdf.empty:
                subdf = subdf.reset_index(drop=True)
                self.subtables[self.fuel][section] = subdf

    def combine_subtables(self):
        combined_df = self.df.copy()
        
        for section in self.section_headers:
            if section in self.subtables[self.fuel]:
                edited_data = self.subtables[self.fuel][section]
                
                mask = combined_df.iloc[:, 0].astype(str).str.strip().str.lower() == section.lower()
                if not mask.any():
                    continue
                    
                start_idx = mask.idxmax()
                combined_df.iloc[start_idx] = self.df.iloc[start_idx]
                
                if not edited_data.empty:
                    rows_to_fill = min(len(edited_data), len(combined_df) - start_idx - 1)
                    cols_to_fill = min(len(edited_data.columns), len(combined_df.columns))
                    
                    for i in range(rows_to_fill):
                        for j in range(cols_to_fill):
                            val = edited_data.iloc[i, j]
                            if pd.isna(val) or val == '-':
                                combined_df.iloc[start_idx+1+i, j] = np.nan
                            else:
                                combined_df.iloc[start_idx+1+i, j] = val
        
        return combined_df

    def show_section_editor(self, section, is_calculated=False):
        if section in self.subtables[self.fuel] and not self.subtables[self.fuel][section].empty:
            df = self.subtables[self.fuel][section]
            height = self.subtable_heights.get(section, self.subtable_heights[self.section_headers[0]])
            editable_cols = [] if is_calculated else self.editable_columns.get(section, self.editable_columns[self.section_headers[0]])
            empty_rows = self.empty_rows.get(section, self.empty_rows[self.section_headers[0]])
            
            self.excel_editor.load_data(df, height, editable_cols, empty_rows)
            edited_df = self.excel_editor.show()
            self.subtables[self.fuel][section] = edited_df

    def validate_input_sections(self):
        input_sections = [section for section in self.section_headers if any(keyword in section for keyword in ["Division", "Type"])]
        
        invalid_cells = []
        for section in input_sections:
            if section in self.subtables[self.fuel]:
                df = self.subtables[self.fuel][section]
                height = self.subtable_heights.get(section, self.subtable_heights[self.section_headers[0]])
                editable_cols = self.editable_columns.get(section, self.editable_columns[self.section_headers[0]])
                self.excel_editor.load_data(df, height, editable_cols, empty_rows={})
                section_invalid_cells = self.excel_editor.validate()
                for error in section_invalid_cells:
                    input_name, col, value, msg = error
                    invalid_cells.append((section, input_name, col, value, msg))
        return invalid_cells

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

        st.subheader(f"Capital Structure for {self.fuel}")
        input_sections = [section for section in self.section_headers  if any(keyword in section for keyword in ["Division", "Type"])]
        for section in input_sections:
            self.show_section_editor(section, is_calculated=False)
        
        self.edited_df = self.combine_subtables()

        invalid_cells = self.validate_input_sections()
        save_disabled = bool(invalid_cells)
        
        if st.button("Save", disabled=save_disabled, key="save_input"):
            saved = u.save_sheet_in_backend(self.edited_df, self.route, self.fuel)
            if saved:
                st.success(f"Changes in '{self.fuel}' Design Capital saved successfully.")
                time.sleep(2)
                st.rerun()

        if st.button("Reset", key="reset_input"):
            reset = u.reset_sheet_in_backend(self.route, self.template_route, self.fuel)
            if reset:
                st.success(f"'{self.fuel}' Design Capital reset to template successfully.")
                time.sleep(2)
                st.rerun()
        
        if save_disabled:
            for section, input_name, col, value, error in invalid_cells:
                st.warning(f"Section '{section}' - Row '{input_name}' - Column '{col}': {error} (Current value: {value})")

        st.markdown("---")
        
        if st.button("Calculate Financiation & Totals", type="secondary", key="calculate_financial"):
            calculated_sections = [section for section in self.section_headers if any(keyword in section for keyword in ["Financiation", "Total"])]
            
            for section in calculated_sections:
                self.show_section_editor(section, is_calculated=True)