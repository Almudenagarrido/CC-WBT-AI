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
        self.df = df.copy().replace("-", np.nan).infer_objects(copy=False)
        self.height = height
        self.editable_columns = editable_columns
        self.empty_rows = empty_rows

    def show(self):
        df = self.df.copy()
        gb = GridOptionsBuilder.from_dataframe(df)
        
        for col in df.columns:
            gb.configure_column(col, editable=(col in self.editable_columns))
        
        for col in df.columns:
            if (col.isdigit() and len(col) == 4) or col == "Baseline":
                gb.configure_column(
                    col,
                    width=50,
                    sortable=False,
                    filter=False,
                    suppressMovable=True
                )

        grid_options = gb.build()
        grid_response = AgGrid(
            df,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.VALUE_CHANGED,
            allow_unsafe_jscode=True,
            enable_enterprise_modules=False,
            height=self.height,
            fit_columns_on_grid_load=False
        )
        edited_df = pd.DataFrame(grid_response["data"])
        if not edited_df.index.equals(df.index):
            edited_df.index = df.index

        for col in self.editable_columns:
            if col in edited_df.columns:
                df[col] = edited_df[col]

        if self.empty_rows["col"] and self.empty_rows["rows"]:
            for row_key in self.empty_rows["rows"]:
                matching_rows = df[df[self.empty_rows["col"]] == row_key].index
                for idx in matching_rows:
                    for col in self.editable_columns:
                        if col != "Baseline":
                            df.loc[idx, col] = np.nan

        self.df = df.copy()
        return df

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

        for index, row in df.iterrows():
            units = str(row[unit_col]).lower() if unit_col else ""
            input_name = row["Inputs"] if "Inputs" in df.columns else int(index) + 1

            for col in self.editable_columns:
                value = row[col]
                error = self.validate_cell(value, units)
                if error:
                    invalid_cells.append((input_name, col, value, error))

        return invalid_cells