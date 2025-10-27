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

    def load_data(self, df, height, editable_columns, empty_rows):
        
        existing_columns = list(df.columns)
        filtered_editable_columns = [col for col in editable_columns if col in existing_columns]
        self.df = df.copy().replace("-", np.nan).infer_objects(copy=False)
        self.df = self.df.dropna(how='all')
        self.df = self.df.dropna(how='all', axis=1)
        self.height = height
        self.editable_columns = filtered_editable_columns
        self.empty_rows = empty_rows
        self._apply_empty_rows_on_load()
    
    def _apply_empty_rows_on_load(self):
        if not self.empty_rows.get("col") or self.empty_rows["col"] not in self.df.columns:
            return
        
        for row_key in self.empty_rows.get("partial", []):
            matching_rows = self.df[self.df[self.empty_rows["col"]] == row_key].index
            for idx in matching_rows:
                for col in self.editable_columns:
                    if col != "Baseline":
                        self.df.loc[idx, col] = np.nan
        
        for row_key in self.empty_rows.get("full", []):
            matching_rows = self.df[self.df[self.empty_rows["col"]] == row_key].index
            for idx in matching_rows:
                for col in self.editable_columns:
                    if col != self.empty_rows["col"]:
                        self.df.loc[idx, col] = np.nan

    def show(self):

        df = self.df.copy()

        df_filtered = df[~df.apply(lambda row: row.astype(str).str.contains(r"\{model\}", regex=True).any(), axis=1)]

        gb = GridOptionsBuilder.from_dataframe(df_filtered)
        
        for col in df_filtered.columns:
            gb.configure_column(col, editable=(col in self.editable_columns))
        
        for col in df_filtered.columns:
            if ((col).isdigit() and len(col) == 4) or col == "Baseline":
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
            fit_columns_on_grid_load=False
        )
        edited_df = pd.DataFrame(grid_response["data"])

        if not edited_df.index.equals(df_filtered.index):
            edited_df.index = df_filtered.index

        for col in self.editable_columns:
            if col in edited_df.columns:
                df_filtered[col] = edited_df[col]

        if self.empty_rows.get("col"):
            for row_key in self.empty_rows.get("partial", []):
                matching_rows = df_filtered[df_filtered[self.empty_rows["col"]] == row_key].index
                for idx in matching_rows:
                    for col in self.editable_columns:
                        if col != "Baseline":
                            df_filtered.loc[idx, col] = np.nan

            for row_key in self.empty_rows.get("full", []):
                matching_rows = df_filtered[df_filtered[self.empty_rows["col"]] == row_key].index
                for idx in matching_rows:
                    for col in self.editable_columns:
                        if col != self.empty_rows["col"]:
                            df_filtered.loc[idx, col] = np.nan

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