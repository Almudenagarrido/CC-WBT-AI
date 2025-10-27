import os
import json
import traceback
from copy import deepcopy
from itertools import product
from functools import lru_cache
from openpyxl import load_workbook


OPS_MAP = {
    "addition": lambda *args: sum(args),
    "subtraction": lambda x, y: x - y,
    "multiply": lambda x, y: x * y,
    "multiply_per": lambda x, y: (x * y)/100,
    "divide": lambda x, y: x / y,
    "gt": lambda x, y: x > y,
    "if": lambda condition, true_val, false_val: true_val if condition else false_val,
    "copy": lambda x: x,
    "min": lambda x, y: min(x, y),
    "max": lambda x, y: max(x, y),
    "abs": lambda x: abs(x),
}


class ExcelFormulaProcessor:
    
    def __init__(self):
        pass
    
    @lru_cache(maxsize=10)
    def _get_workbook(self, file_path, read_only=False, data_only=False):
        return load_workbook(file_path, read_only=read_only, data_only=data_only)
    
    def clear_workbook_cache(self):
        self._get_workbook.cache_clear()

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
    
    def _apply_number_formatting(self, file_path):
        
        try:
            
            wb = load_workbook(file_path)
            
            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                
                for row in ws.iter_rows():
                    for cell in row:
                        if isinstance(cell.value, (int, float)):
                            cell.number_format = '0.0000'
                
            wb.save(file_path)
            wb.close()
            
        except Exception as e:
            raise RuntimeError(f"Error applying number formatting: {str(e)}")

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
            traceback.print_exc()
            raise RuntimeError(f"Error applying formulas: {str(e)}")

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

    def _process_formulas_sheet_file(self, file_path, formulas_sheet_file):
        
        self.clear_workbook_cache()
        
        wb = load_workbook(file_path)
        
        try:
            changes_made = False
            for sheet_name, formulas in formulas_sheet_file.items():
                if sheet_name not in wb.sheetnames:
                    continue
                
                ws = wb[sheet_name]
                
                for formula_idx, formula in enumerate(formulas):
                    try:
                        formula_changed = self._execute_single_formula(ws, formula)
                        if formula_changed:
                            changes_made = True
                    except Exception as e:
                        continue
            
            if changes_made:
                wb.save(file_path)
                
                self._apply_number_formatting(file_path)
            
        except Exception as e:
            traceback.print_exc()
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
                return False
            
            source_cells_list = []
            for source_label in source_labels:
                cell_refs = self._get_cell_refs_from_source_label(source_label, ws)
                if not cell_refs:
                    return False
                source_cells_list.append(cell_refs)
            
            changes_made = False
            for cell_index in range(len(target_cells)):
                
                current_values = []
                for cell_refs in source_cells_list:
                    if cell_index < len(cell_refs):
                        value = self._get_cell_value_from_ref(cell_refs[cell_index], ws)
                        current_values.append(value)
                    else:
                        current_values.append(0)
                
                final_value = self._execute_formula_for_cell(
                    formula_steps, current_values, source_cells_list, cell_index, ws
                )
                
                target_cell = target_cells[cell_index]
                current_target_value = ws[target_cell].value
                
                if current_target_value != final_value:
                    ws[target_cell] = final_value
                    changes_made = True
                    
            return changes_made
                    
        except Exception as e:
            traceback.print_exc()
            return False

    def _get_cell_value_from_ref(self, cell_ref, default_ws):
        
        try:
            if "::" in cell_ref and "!" in cell_ref:
                file_part, rest = cell_ref.split("::")
                sheet_part, coord = rest.split("!")
                file_path = os.path.normpath(file_part)
                wb = self._get_workbook(file_path, data_only=True)
                ws = wb[sheet_part]
                value = ws[coord].value
            else:
                value = default_ws[cell_ref].value
            
            return self._convert_to_numeric(value) if self._is_numeric_value(value) else 0
        except Exception as e:
            return 0

    def _get_operand_value(self, operand, current_values, current_results):

        if isinstance(operand, list):
            if operand[0] == "index":
                key = operand[1]
                if isinstance(key, int):
                    return current_values[key] if key < len(current_values) else 0
                else:
                    return current_results.get(key, 0)
            elif operand[0] in ["literal", "range"]:
                return operand[1]
        elif isinstance(operand, str):
            return current_results.get(operand, 0)
        elif isinstance(operand, (int, float)):
            return operand
        else:
            return 0
    
    def _get_cell_refs_from_source_label(self, source_label, default_ws):
        
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
        label_parts = label_part.split(":")
        
        target_row = None
        for row in range(1, ws.max_row + 1):
            match = True
            for col_idx, expected_value in enumerate(label_parts, start=1):
                cell_value = ws.cell(row=row, column=col_idx).value
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
        
        baseline_col = None
        header_row = 1

        for col in range(1, ws.max_column + 1):
            cell_value = ws.cell(row=header_row, column=col).value
            if cell_value and "baseline" in str(cell_value).lower():
                baseline_col = col
                break

        if baseline_col is None:
            baseline_col = len(label_parts) + 1

        start_col = baseline_col
        cell_refs = []
        for col in range(start_col, ws.max_column + 1):
            cell = ws.cell(row=target_row, column=col)
            cell_value = cell.value
            
            if cell_value is None:
                break
                
            if file_part:
                ref = f"{file_path}::{sheet_part}!{cell.coordinate}"
            else:
                ref = cell.coordinate
                
            cell_refs.append(ref)
        
        return cell_refs

    def _execute_formula_for_cell(self, formula_steps, current_values, source_cells_list, cell_index, default_ws):
        
        results = {}
        
        for step in formula_steps:
            op = step["op"]
            operands = step["operands"]
            result_key = step["result"]
            
            if op == "offset":
                result = self._execute_offset_operation(
                    operands, current_values, results, source_cells_list, cell_index, default_ws
                )
            elif op == "sum_range":
                result = self._execute_sum_range_operation(
                    operands, current_values, results, source_cells_list, cell_index, default_ws, step
                )
            elif op == "range":
                result = cell_index + operands[0][1]
                
            elif op == "value":
                source_index = operands[0][1]
                cell_index_to_get = operands[1][1] 
                
                if 0 <= source_index < len(source_cells_list):
                    cell_refs = source_cells_list[source_index]
                    if 0 <= cell_index_to_get < len(cell_refs):
                        result = self._get_cell_value_from_ref(cell_refs[cell_index_to_get], default_ws)  
                    else:
                        result = 0
                else:
                    result = 0
            else:
                ops_args = []
                for operand in operands:
                    if isinstance(operand, list):
                        if operand[0] == "index":
                            index = operand[1]
                            if isinstance(index, int) and index < len(current_values):
                                ops_args.append(current_values[index])
                            elif index in results:
                                ops_args.append(results[index])
                            else:
                                ops_args.append(0)
                        elif operand[0] == "literal":
                            ops_args.append(operand[1])
                    else:
                        ops_args.append(0)
                
                if op in OPS_MAP:
                    result = OPS_MAP[op](*ops_args)
                else:
                    result = 0
            
            results[result_key] = result
        
        return results.get("final", 0)
    
    def _execute_sum_range_operation(self, operands, current_values, current_results, source_cells_list, current_index, default_ws, step=None):
        
        if isinstance(operands[0], list) and operands[0][0] == "index":
            source_index = operands[0][1]
        else:
            source_index = self._get_operand_value(operands[0], current_values, current_results)
        
        if isinstance(operands[1], list) and operands[1][0] == "literal":
            width = operands[1][1]
        else:
            width = self._get_operand_value(operands[1], current_values, current_results)
        
        direction = step.get("direction", "forward") if step else "forward"
        
        if 0 <= source_index < len(source_cells_list):
            cell_refs = source_cells_list[source_index]
            total = 0
            
            if direction == "backward":
                
                if width == 0:
                    start_index = 0
                    end_index = current_index + 1
                    
                    for i in range(start_index, end_index):
                        if i < len(cell_refs):
                            value = self._get_cell_value_from_ref(cell_refs[i], default_ws)
                            total += value

                else:
                    
                    start_index = max(0, current_index - width + 1)
                    end_index = current_index + 1
                    
                    for i in range(start_index, end_index):
                        if i < len(cell_refs):
                            value = self._get_cell_value_from_ref(cell_refs[i], default_ws)
                            total += value
                            
            else:
                start_index = current_index
                end_index = min(len(cell_refs), current_index + width)
                
                for i in range(start_index, end_index):
                    if i < len(cell_refs):
                        value = self._get_cell_value_from_ref(cell_refs[i], default_ws)
                        total += value
                        
            return total
        else:
            return 0
    
    def _execute_offset_operation(self, operands, current_values, current_results, source_cells_list, current_index, default_ws):
        
        if isinstance(operands[0], list) and operands[0][0] == "index":
            source_index = operands[0][1]
        else:
            source_index = self._get_operand_value(operands[0], current_values, current_results)
        
        if isinstance(operands[1], list) and operands[1][0] == "literal":
            offset = operands[1][1]
        else:
            offset = self._get_operand_value(operands[1], current_values, current_results)
        
        if 0 <= source_index < len(source_cells_list):
            cell_refs = source_cells_list[source_index]
            target_index = current_index - int(offset)
            
            if target_index < 0:
                return 0
            elif target_index < len(cell_refs):
                value = self._get_cell_value_from_ref(cell_refs[target_index], default_ws)
                return value
            else:
                return 0
        else:
            return 0
    
    def _find_cells_from_target_label(self, target_label, worksheet):
        
        label_parts = target_label.split(":")        
        target_row = None
        for row in range(1, worksheet.max_row + 1):
            type_value = str(worksheet.cell(row=row, column=1).value or "").strip()
            sub_value = str(worksheet.cell(row=row, column=2).value or "").strip()
            expected_type = label_parts[0].strip()
            expected_sub = label_parts[1].strip() if len(label_parts) > 1 else ""

            if expected_type.lower() in type_value.lower() and expected_sub.lower() in sub_value.lower():
                target_row = row
                break

        if target_row is None:
            return []
        
        baseline_col = None
        header_row = 1
        
        for col in range(1, worksheet.max_column + 1):
            cell_value = worksheet.cell(row=header_row, column=col).value
            if cell_value:
                cell_str = str(cell_value).strip()
                if "baseline" in cell_str.lower():
                    baseline_col = col
                    break
        
        if baseline_col is not None:
            baseline_value = worksheet.cell(row=target_row, column=baseline_col).value
            
            if not self._is_numeric_value(baseline_value):
                baseline_col = None
        
        if baseline_col is None:
            start_search_col = len(label_parts) + 1
            for col in range(start_search_col, worksheet.max_column + 1):
                cell_value = worksheet.cell(row=target_row, column=col).value
                if self._is_numeric_value(cell_value):
                    baseline_col = col
                    break
        
        if baseline_col is None:
            baseline_col = len(label_parts) + 1
        
        numeric_cells = []        
        for col in range(baseline_col, worksheet.max_column + 1):
            cell = worksheet.cell(row=target_row, column=col)
            cell_value = cell.value
            
            if cell_value is None:
                break
                
            is_numeric = self._is_numeric_value(cell_value)
            if is_numeric:
                numeric_cells.append(cell.coordinate)
            else:
                break
        
        return numeric_cells

