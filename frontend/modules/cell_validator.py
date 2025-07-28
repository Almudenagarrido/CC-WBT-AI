
class CellValidator:
    
    def __init__(self):
        self.validators = {
            "%": self.validate_percentage,
            "days": self.validate_positive_integer,
            "years": self.validate_positive_integer,
            "$ / ton": self.validate_positive_value,
            # "m$": self.validate_positive_value,
        }

    def validate_percentage(self, value):
        try:
            if pd.isna(value) or value == "-":
                return None
            val = float(value)
            if not (0 <= val <= 100):
                return "Value must be between 0 and 100 (percentage)"
        except:
            return "Not a valid number"
        return None

    def validate_positive_integer(self, value):
        try:
            if pd.isna(value) or value == "-":
                return None
            val = float(value)
            if val < 0 or not float(val).is_integer():
                return "Value must be a positive integer"
        except:
            return "Not a valid number"
        return None

    def validate_positive_value(self, value):
        try:
            if pd.isna(value) or value == "-":
                return None
            val = float(value)
            if val < 0:
                return "Value must be positive"
        except:
            return "Not a valid number"
        return None

    def validate_cell(self, value, unit):
        validator = self.validators.get(unit.strip().lower())
        if validator:
            return validator(value)
        return None
    
    def cell_validations(self, df, editable_columns):
        invalid_cells = []

        unit_col = next((col for col in df.columns if "units" in col.lower()), None)

        for index, row in df.iterrows():
            units = str(row[unit_col]).lower() if unit_col else ""
            input_name = row["Inputs"] if "Inputs" in df.columns else int(index) + 1

            for col in df.columns:
                if col not in editable_columns:
                    continue

                value = row[col]
                error = self.validate_cell(value, units)
                if error:
                    invalid_cells.append((index, input_name, col, value, error))

        return invalid_cells
    