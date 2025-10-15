import os
import json
import logging
import traceback
from copy import deepcopy
from itertools import product
from functools import lru_cache
from openpyxl import load_workbook

logger = logging.getLogger(__name__)

OPS_MAP = {
    "addition": lambda *args: sum(args),
    "subtract": lambda x, y: x - y,
    "subtract_one": lambda x: x - 1,
    "multiply": lambda x, y: x * y,
    "multiply_per": lambda x, y: (x * y)/100,
    "divide": lambda x, y: x / y,
    "safe_divide": lambda x, y: x / y if y != 0 else 0,
    "safe_divide_subtract_one": lambda x, y: x / y - 1 if y != 0 else 0,
    "gt": lambda x, y: x > y,
    "gt_eq": lambda x, y: x > y,
    "lt": lambda x, y: x < y,
    "pos_or_cero": lambda x: max(x, 0),
    "equal": lambda x, y: x == y,
    "if": lambda condition, true_val, false_val: true_val if condition else false_val,
    "copy": lambda x: x,
    "negative": lambda x: -x,
    "percentage": lambda x: x*100,
    "min": lambda x, y: min(x, y),
    "max": lambda x, y: max(x, y),
    "abs": lambda x: abs(x),
}


class ExcelFormulaProcessor:
    
    def __init__(self):
        self.workbook_cache = {}
    
    def clear_workbook_cache(self):
        self._get_workbook.cache_clear()
        self.workbook_cache.clear()

    def apply_formulas(self, file_path, formulas_json_path, country, models, fuels, expected_sheets):
        try:            
            with open(formulas_json_path) as f:
                formulas_json = json.load(f)

            expanded_main_json = self._expand_main_keys_json(formulas_json, country, models, fuels, expected_sheets)

            file_path_norm = os.path.normpath(file_path)
            if file_path_norm not in expanded_main_json:
                return
            
            formulas_sheet_file = expanded_main_json[file_path_norm]
            
            specific_values = self._extract_specific_values(file_path_norm, models, fuels, expected_sheets)
            
            expanded_formulas = self._expand_single_formulas(
                formulas_sheet_file, country, models, fuels, expected_sheets, specific_values
            )
            
            self._process_formulas_sheet_file(file_path_norm, expanded_formulas)
                
        except Exception as e:
            raise RuntimeError(f"Error applying formulas: {str(e)}")

    def _extract_specific_values(self, file_path, models, fuels, expected_sheets):
        specific_values = {
            'model': None,
            'fuel': None, 
            'sheet': None
        }
        
        for model in models:
            if model in file_path:
                specific_values['model'] = model
                break
        
        for fuel in fuels:
            if fuel in file_path:
                specific_values['fuel'] = fuel
                break
        
        for sheet in expected_sheets:
            if sheet in file_path:
                specific_values['sheet'] = sheet
                break
        
        return specific_values

    def _expand_single_formulas(self, formulas_sheet_file, country, models, fuels, expected_sheets, specific_values=None):
        expanded_formulas = {}
        
        if specific_values is None:
            specific_values = {'model': None, 'fuel': None, 'sheet': None}
        
        for sheet_name, formulas in formulas_sheet_file.items():
            fuels_to_expand = []
            
            if sheet_name == "{fuel}":
                if specific_values['fuel']:
                    fuels_to_expand = [specific_values['fuel']]
                else:
                    fuels_to_expand = fuels
            else:
                expanded_formulas[sheet_name] = []
                fuels_to_expand = [None]
            
            for fuel_val in fuels_to_expand:
                if sheet_name == "{fuel}" and fuel_val:
                    expanded_sheet_name = fuel_val
                else:
                    expanded_sheet_name = sheet_name
                
                expanded_formulas[expanded_sheet_name] = []
                
                for formula in formulas:
                    target = formula.get("target", "")
                    source_labels = formula.get("sources", [])
                    
                    needs_country = any("{country}" in s for s in [target] + source_labels)
                    needs_model = any("{model}" in s for s in [target] + source_labels)
                    needs_fuel = any("{fuel}" in s for s in [target] + source_labels)
                    needs_sheet = any("{sheet}" in s for s in [target] + source_labels)
                    
                    models_to_use = [specific_values['model']] if (needs_model and specific_values['model']) else (models if needs_model else [None])
                    
                    fuels_to_use = [fuel_val] if (needs_fuel and fuel_val) else ([specific_values['fuel']] if (needs_fuel and specific_values['fuel']) else (fuels if needs_fuel else [None]))
                    
                    sheets_to_use = [specific_values['sheet']] if (needs_sheet and specific_values['sheet']) else (expected_sheets if needs_sheet else [None])
                    
                    combinations = product(
                        [country] if needs_country else [None],
                        models_to_use if needs_model else [None],
                        fuels_to_use if needs_fuel else [None],
                        sheets_to_use if needs_sheet else [None]
                    )
                    
                    for country_val, model_val, formula_fuel_val, sheet_val in combinations:
                        final_fuel_val = fuel_val if fuel_val else formula_fuel_val
                        
                        new_formula = deepcopy(formula)
                        if country_val: new_formula["target"] = new_formula["target"].replace("{country}", country_val)
                        if model_val: new_formula["target"] = new_formula["target"].replace("{model}", model_val)
                        if final_fuel_val: new_formula["target"] = new_formula["target"].replace("{fuel}", final_fuel_val)
                        if sheet_val: new_formula["target"] = new_formula["target"].replace("{sheet}", sheet_val)
                        
                        new_source_labels = []
                        for label in new_formula["sources"]:
                            if country_val: label = label.replace("{country}", country_val)
                            if model_val: label = label.replace("{model}", model_val)
                            if final_fuel_val: label = label.replace("{fuel}", final_fuel_val)
                            if sheet_val: label = label.replace("{sheet}", sheet_val)
                            new_source_labels.append(label)
                        new_formula["sources"] = new_source_labels
                        
                        expanded_formulas[expanded_sheet_name].append(new_formula)
                        
        return expanded_formulas
    
    def _expand_main_keys_json(self, formulas_json, country, models, fuels, expected_sheets):    
        expanded_json = {}
        
        for file_raw_key, file_formulas in formulas_json.items():
            
            needs_country = "{country}" in file_raw_key
            needs_model = "{model}" in file_raw_key
            needs_fuel = "{fuel}" in file_raw_key
            needs_sheet = "{sheet}" in file_raw_key
            
           
            combinations = product(
                [country] if needs_country else [None],
                models if needs_model else [None],
                fuels if needs_fuel else [None],
                expected_sheets if needs_sheet else [None]
            )
            
            expanded_count = 0
            for country_val, model_val, fuel_val, sheet_val in combinations:
                expanded_key = file_raw_key
                if country_val: expanded_key = expanded_key.replace("{country}", country_val)
                if model_val: expanded_key = expanded_key.replace("{model}", model_val)
                if fuel_val: expanded_key = expanded_key.replace("{fuel}", fuel_val)
                if sheet_val: expanded_key = expanded_key.replace("{sheet}", sheet_val)
                
                expanded_json[expanded_key] = file_formulas
                expanded_count += 1
            
            if expanded_count == 0:
                expanded_json[file_raw_key] = file_formulas
        
        return expanded_json
    
    @lru_cache(maxsize=10)
    def _get_workbook(self, file_path, read_only=False, data_only=False):
        return load_workbook(file_path, read_only=read_only, data_only=data_only)
    
    def _process_formulas_sheet_file(self, file_path, formulas_sheet_file):
        wb = self._get_workbook(file_path, read_only=False)
        try:
            for sheet_name, formulas in formulas_sheet_file.items():
                if sheet_name not in wb.sheetnames:
                    continue
                
                ws = wb[sheet_name]
                for formula in formulas:
                    try:
                        self._execute_single_formula(ws, formula)
                    except Exception as e:
                        continue
            
            wb.save(file_path)
            
        finally:
            if hasattr(wb, 'close'):
                wb.close()
    
    def _execute_single_formula(self, ws, formula):
        try:
            target_label = formula["target"]
            source_labels = formula["sources"]
            formula_steps = formula.get("formula_steps", [])
            
            target_cells = self._find_cells_from_target_label(target_label, ws)
            if not target_cells:
                return
            
            source_values_list = []
            for i, source_label in enumerate(source_labels):
                source_values = self._get_values_from_source_label(source_label, ws)
                if not source_values:
                    return
                
                source_values_list.append(source_values)

            final_result = self._execute_formula_steps(formula_steps, source_values_list)

            self._validate_results(ws, target_cells, final_result)

        except Exception as e:
            traceback.print_exc()

    def _is_numeric_value(self, value):
        if value is None:
            return False
        if isinstance(value, (int, float)):
            return True
        if isinstance(value, str):
            try:
                float(value.replace(",", ".").strip())
                return True
            except ValueError:
                return False
        return False

    def _convert_to_numeric(self, value):
        if value is None:
            return 0
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.replace(",", ".").strip())
            except ValueError:
                return 0
        return 0
    
    def _find_cells_from_target_label(self, target_label, worksheet):
        label_parts = target_label.split(":")
        
        for row in range(1, worksheet.max_row + 1):
            row_data = []
            for col in range(1, min(worksheet.max_column + 1, 10)):
                cell = worksheet.cell(row=row, column=col)
                cell_value = cell.value
                if cell_value is None:
                    display_value = "None"
                elif isinstance(cell_value, str):
                    display_value = f"'{cell_value.strip()}'"
                else:
                    display_value = str(cell_value)
                row_data.append(f"C{col}:{display_value}")
            
        target_row = None
        for row in range(1, worksheet.max_row + 1):
            match = True
            row_debug = []
            
            for col_idx, expected_value in enumerate(label_parts, start=1):
                cell_value = worksheet.cell(row=row, column=col_idx).value
                cell_str = str(cell_value).strip() if cell_value is not None else ""
                expected_str = expected_value.strip()
                
                if expected_str not in cell_str:
                    match = False
                    break
            
            if match:
                target_row = row
                break
        
        if target_row is None:
            return []
        
        start_col = len(label_parts) + 1
        numeric_cells = []
        for col in range(start_col, worksheet.max_column + 1):
            cell = worksheet.cell(row=target_row, column=col)
            cell_value = cell.value
            is_numeric = self._is_numeric_value(cell_value)
            
            if is_numeric:
                numeric_cells.append(cell.coordinate)
        
        return numeric_cells

    def _get_values_from_source_label(self, source_label, default_ws):
        if "::" in source_label:
            parts = source_label.split("::")
            if len(parts) == 3:
                file_part, sheet_part, label_part = parts
            else:
                return []
        else:
            file_part = None
            sheet_part = default_ws.title
            label_part = source_label
        
        if file_part:
            file_path = os.path.normpath(file_part)
            try:
                wb = self._get_workbook(file_path, data_only=True)
            except Exception as e:
                return []
        else:
            wb = self._get_workbook(default_ws.parent.path, data_only=True)
        
        if sheet_part not in wb.sheetnames:
            return []
        
        ws = wb[sheet_part]
        target_row = None
        label_parts = label_part.split(":")
        
        for row in range(1, ws.max_row + 1):
            match = True
            for col_idx, expected_value in enumerate(label_parts, start=1):
                cell_value = ws.cell(row=row, column=col_idx).value
                cell_str = str(cell_value).strip() if cell_value is not None else ""
                expected_str = expected_value.strip()
                
                if cell_str != expected_str:
                    match = False
                    break
            
            if match:
                target_row = row
                break
        
        if target_row is None:
            return []
        
        start_col = len(label_parts) + 2  # ATENTION
        values = []
        for col in range(start_col, ws.max_column + 1):
            cell = ws.cell(row=target_row, column=col)
            cell_value = cell.value
            
            if cell_value is None:
                break
                
            numeric_value = self._convert_to_numeric(cell.value)
            
            if self._is_numeric_value(cell_value):
                numeric_value = self._convert_to_numeric(cell_value)
                values.append(numeric_value)
            else:
                break
        
        return values
    
    def _execute_formula_steps(self, formula_steps, source_values_list):
        results = {}
        
        for step in formula_steps:
            op = step["op"]
            operands = step["operands"]
            result_key = step["result"]
            
            operand_lists = []
            for operand in operands:
                if operand[0] == "index":
                    index = operand[1]
                    
                    if index in results:
                        operand_lists.append(results[index])
        
                    elif isinstance(index, int) and index < len(source_values_list):
                        operand_lists.append(source_values_list[index])

                    else:
                        operand_lists.append([0])
                    
                elif operand[0] == "literal":
                    literal_value = operand[1]
                    list_length = len(source_values_list[0]) if source_values_list else 0
                    operand_lists.append([literal_value] * list_length)
            
            max_length = max(len(lst) for lst in operand_lists) if operand_lists else 0
            for i in range(len(operand_lists)):
                if len(operand_lists[i]) < max_length:
                    operand_lists[i] = operand_lists[i] + [0] * (max_length - len(operand_lists[i]))
            
            result_list = []
            for i in range(max_length):
                current_values = [lst[i] for lst in operand_lists]
                
                if op in OPS_MAP:
                    try:
                        result_value = OPS_MAP[op](*current_values)
                        result_list.append(result_value)
                    except Exception as e:
                        result_list.append(0)
                else:
                    result_list.append(0)
            
            results[result_key] = result_list
        
        final_result = results.get("final", [0])
        return final_result
    
    def _validate_results(self, ws, target_cells, final_result):
        if len(final_result) != len(target_cells):
            return

        for i, target_cell in enumerate(target_cells):
            try:
                ws[target_cell] = final_result[i]
            except Exception as e:
                traceback.print_exc()
        
