import re
import warnings
import numpy as np
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode


warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    message=".*Downcasting behavior in `replace` is deprecated.*"
)


class ExcelEditor:
    def __init__(self):
        self.df = None
        self.editable_columns = []
        self.height = 300
        self.empty_rows = {"rows": [], "col": None}
        self.validators = {
            "%": self.validate_percentage,
            "days": self.validate_positive_integer,
            "years": self.validate_positive_integer,
            "$ / ton": self.validate_positive_value,
        }
        self.expected_years = [str(year) for year in range(2020, 2061)]

    def load_data(self, df, fuel, height, editable_columns, empty_rows):
        
        self.fuel = fuel
        existing_columns = list(df.columns)
        filtered_editable_columns = [col for col in editable_columns if col in existing_columns]
        self.df = df.copy().replace("-", np.nan).infer_objects(copy=False)
        self.df = self.df.dropna(how='all')
        self.df = self.df.dropna(how='all', axis=1)
        self.height = min(height, 500)
        self.editable_columns = filtered_editable_columns
        self.empty_rows = empty_rows
        self.year_columns = self.detect_years()
        self._apply_empty_rows_on_load()
    
    def detect_years(self):
        year_columns_info = []
        
        for col_idx, col_name in enumerate(self.df.columns):
            year = None
            if isinstance(col_name, str) and col_name.isdigit() and len(col_name) == 4:
                year = int(col_name)
            
            elif isinstance(col_name, (int, float)):
                try:
                    year = int(float(col_name))
                except:
                    pass
            
            elif isinstance(col_name, str):
                matches = re.findall(r'\b\d{4}\b', col_name)
                if matches:
                    year = int(matches[0])
            
            if year and 1900 <= year <= 2100:
                year_columns_info.append((col_idx, col_name, year))
        
        year_columns_info.sort(key=lambda x: x[2])                 
        year_column_names = [col_name for _, col_name, _ in year_columns_info]
        
        return year_column_names
    
    def _apply_empty_rows_on_load(self):
        if not self.empty_rows:
            return
        
        if "target_columns" in self.empty_rows and self.empty_rows["target_columns"]:
            columns_to_empty = self.empty_rows["target_columns"]
        else:
            columns_to_empty = [col for col in self.year_columns if col in self.df.columns]
        
        if not columns_to_empty:
            return
        
        if "col" in self.empty_rows and self.empty_rows["col"]:
            target_col = self.empty_rows["col"]
            if target_col in self.df.columns:
                for row_key in self.empty_rows.get("partial", []):
                    if isinstance(row_key, str):
                        matching_rows = self.df[self.df[target_col] == row_key].index
                        for idx in matching_rows:
                            for col in columns_to_empty:
                                if col != columns_to_empty[0]:
                                    self.df.loc[idx, col] = np.nan
                
                for row_key in self.empty_rows.get("full", []):
                    if isinstance(row_key, str):
                        matching_rows = self.df[self.df[target_col] == row_key].index
                        for idx in matching_rows:
                            for col in columns_to_empty:
                                if col != target_col:
                                    self.df.loc[idx, col] = np.nan
        
        for rule in self.empty_rows.get("partial", []):
            if not isinstance(rule, dict):
                continue
            
            col1 = rule.get("col1")
            value1 = rule.get("value1")
            col2 = rule.get("col2")
            value2 = rule.get("value2")
            
            mask = (self.df[col1] == value1) & (self.df[col2] == value2)
            matching_rows = self.df[mask].index
            
            for idx in matching_rows:
                for col in columns_to_empty:
                    if col != columns_to_empty[0]:
                        self.df.loc[idx, col] = np.nan

    def show(self, decimals=1):
        df = self.df.copy()

        df_filtered = df[~df.apply(lambda row: row.astype(str).str.contains(r"\{model\}", regex=True).any(), axis=1)].copy()

        row_name = "Calculated debt variation"
        label_col = df_filtered.columns[0]
        mask = df_filtered[label_col] == row_name
        if mask.any():
            for col in df_filtered.columns:
                if col in self.year_columns:
                    df_filtered.loc[mask, col] = (
                        df_filtered.loc[mask, col].astype(float).round(decimals)
                    )

        for col in df_filtered.columns:
            if pd.api.types.is_numeric_dtype(df_filtered[col]):
                df_filtered[col] = df_filtered[col].round(decimals)
        
        unit_col = None
        for col in df_filtered.columns:
            if "units" in str(col).lower():
                unit_col = col
                break
        
        if unit_col and unit_col in df_filtered.columns:
            percentage_mask = df_filtered[unit_col].astype(str).str.contains('%', na=False)
            
            if percentage_mask.any():
                idx_list = percentage_mask[percentage_mask].index
                
                for idx in idx_list:
                    for col in df_filtered.columns:
                        if pd.api.types.is_numeric_dtype(df_filtered[col]) and col in self.year_columns:
                            if pd.notna(df_filtered.at[idx, col]):
                                df_filtered.at[idx, col] = round(float(df_filtered.at[idx, col]), 0)
        
        
        gb = GridOptionsBuilder.from_dataframe(df_filtered)
        
        for col in df_filtered.columns:
            gb.configure_column(
                col, 
                editable=(col in self.editable_columns),
                suppressMovable=True,
                minWidth=60,
                resizable=True
            )
        
        for col in df_filtered.columns:
            if col in self.year_columns:
                gb.configure_column(
                    col,
                    width=50,
                    sortable=False,
                    filter=False,
                    suppressMovable=True
                )

        grid_response = AgGrid(
            df_filtered,
            gridOptions=gb.build(),
            update_mode=GridUpdateMode.VALUE_CHANGED,
            allow_unsafe_jscode=True,
            enable_enterprise_modules=False,
            height=self.height,
            fit_columns_on_grid_load=False,
            key=f"aggrid_{self.fuel}"
        )
        edited_df = pd.DataFrame(grid_response["data"])

        if not edited_df.index.equals(df_filtered.index):
            edited_df.index = df_filtered.index

        for col in self.editable_columns:
            if col in edited_df.columns:
                df_filtered[col] = edited_df[col]

        self.df = df_filtered.copy()
        return df_filtered
    
    def validate_percentage(self, value):
        try:
            if pd.isna(value) or value == "-":
                return None
            val = float(value)
            if not (0 <= val <= 100):
                return "Value must be between 0 and 100."
        except:
            return "Not a valid number"
        return None

    def validate_positive_integer(self, value):
        try:
            if pd.isna(value) or value == "-":
                return None
            val = float(value)
            if val < 0 or not float(val).is_integer():
                return "Value must be a positive integer."
        except:
            return "Not a valid number"
        return None

    def validate_positive_value(self, value):
        try:
            if pd.isna(value) or value == "-":
                return None
            val = float(value)
            if val < 0:
                return "Value must be positive."
        except:
            return "Not a valid number"
        return None
    
    def validate_cell(self, value, unit):
        validator = self.validators.get(unit.strip().lower())
        if validator:
            return validator(value)
        return None
    
    def validate(self):
        invalid_cells = []
        df = self.df.copy()
        unit_col = next((col for col in df.columns if "units" in col.lower()), None)

        name_cols = ["Inputs", "Financiation", "Total", "Division", "Type"]
        name_col = next((col for col in name_cols if col in df.columns), None)

        for index, row in df.iterrows():
            units = str(row[unit_col]).lower() if unit_col else ""
            input_name = str(row[name_col]) if name_col else int(index + 1)

            for col in self.editable_columns:
                value = row.get(col, None)
                error = self.validate_cell(value, units)
                if error:
                    invalid_cells.append((input_name, col, value, error))

        return invalid_cells