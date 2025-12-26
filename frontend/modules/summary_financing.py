import os
import json
from itertools import product
from copy import deepcopy
from openpyxl import load_workbook

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.dirname(BASE_DIR)
PROJECT_ROOT = os.path.dirname(FRONTEND_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
CONFIG_FILE = os.path.join(BACKEND_DIR, "config.json")
VISUALIZATIONS_JSON = os.path.join(BASE_DIR, "visualizations_map.json")

OPS_MAP = {
    "copy": lambda x: x,
    "addition": lambda x, y: x + y,
    "subtraction": lambda x, y: x - y,
    "multiply": lambda x, y: x * y,
    "multiply_per": lambda x, y: (x * y) / 100,
    "divide": lambda x, y: x / y if y != 0 else 0,
    "safe_divide": lambda x, y: (x / y) if y != 0 else 0,
    "safe_divide_minus": lambda x, y, z: (x / y - z) if y != 0 else 0,
    "gt": lambda x, y: x > y,
    "gt_eq": lambda x, y: x >= y,
    "lt": lambda x, y: x < y,
    "lt_eq": lambda x, y: x <= y,
    "equal": lambda x, y: x == y,
    "if": lambda condition, true_val, false_val: true_val if condition else false_val,
    "min": lambda x, y: min(x, y),
    "max": lambda x, y: max(x, y),
    "abs": lambda x: abs(x),
    "negative": lambda x: -x,
    "percentage": lambda x: x * 100,
    "int": lambda x: int(x)
}


class SummaryFinancing:
    
    def __init__(self, country):
        self.country = country
        self.formulas_json_path = VISUALIZATIONS_JSON
        self.config = self._load_config()
        self.year_range = self._get_year_range()
        self.previously_calculated = {}
        self._workbook_cache = {}
    
    def _load_config(self):
        with open(CONFIG_FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    
    def _get_year_range(self):
        year_ranges = self.config.get("COUNTRY_YEAR_RANGES", {})
        country_range = year_ranges.get(self.country, {})
        return {
            "start": country_range.get("start", 2020),
            "end": country_range.get("end", 2050)
        }
    
    def _get_workbook(self, file_path, data_only=True):
        if file_path not in self._workbook_cache:
            try:
                self._workbook_cache[file_path] = load_workbook(file_path, data_only=data_only)
            except Exception:
                return None
        return self._workbook_cache[file_path]
    
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
    
    def _expand_visualizations_json(self, visualizations_json):
        expanded_graphs = {}
        models = self.config.get("MODELS", {}).get(self.country, [])
        fuels = self.config.get("FUELS", {}).get(self.country, {}).get("normal", [])
        
        for graph_raw_name, graph_data in visualizations_json.items():
            has_country = "{country}" in graph_raw_name
            has_model = "{model}" in graph_raw_name
            has_fuel = "{fuel}" in graph_raw_name
            
            if not (has_country or has_model or has_fuel):
                expanded_graphs[graph_raw_name] = deepcopy(graph_data)
                continue
            
            country_values = [self.country] if has_country else [""]
            model_values = models if has_model else [""]
            fuel_values = fuels if has_fuel else [""]
            
            for country_val, model_val, fuel_val in product(country_values, model_values, fuel_values):
                expanded_name = graph_raw_name
                
                if has_country:
                    expanded_name = expanded_name.replace("{country}", country_val)
                if has_model:
                    expanded_name = expanded_name.replace("{model}", model_val)
                if has_fuel:
                    expanded_name = expanded_name.replace("{fuel}", fuel_val)
                
                if expanded_name != graph_raw_name:
                    expanded_graph_data = deepcopy(graph_data)
                    expansion_info = {
                        'country': country_val,
                        'model': model_val,
                        'fuel': fuel_val
                    }
                    expanded_graph_data['_expansion_info'] = expansion_info
                    expanded_graphs[expanded_name] = expanded_graph_data
        
        return expanded_graphs

    def _expand_sources_paths(self, expanded_graphs):
        for _, graph_data in expanded_graphs.items():
            if "sources" not in graph_data:
                continue
            
            sources = graph_data["sources"]
            expansion_info = graph_data.get('_expansion_info', {})
            country_val = expansion_info.get('country', self.country)
            model_val = expansion_info.get('model', '')
            fuel_val = expansion_info.get('fuel', '')
            
            for _, source_info in sources.items():
                if "sources" not in source_info:
                    continue
                
                original_paths = source_info["sources"]
                expanded_paths = []
                
                for source_path in original_paths:
                    expanded_path = source_path
                    if "{country}" in expanded_path:
                        expanded_path = expanded_path.replace("{country}", country_val)
                    if "{model}" in expanded_path:
                        expanded_path = expanded_path.replace("{model}", model_val)
                    if "{fuel}" in expanded_path:
                        expanded_path = expanded_path.replace("{fuel}", fuel_val)
                    
                    if "\\" in expanded_path:
                        parts = expanded_path.split("\\", 1)
                        if len(parts) == 2:
                            country_dir, rest_path = parts
                            full_path = os.path.join(BACKEND_DIR, country_dir, rest_path)
                        else:
                            full_path = os.path.join(BACKEND_DIR, country_val, expanded_path.lstrip("\\"))
                    else:
                        full_path = os.path.join(BACKEND_DIR, country_val, expanded_path)
                    
                    full_path = os.path.normpath(full_path)
                    expanded_paths.append(full_path)
                
                source_info["sources"] = expanded_paths
        
        return expanded_graphs
    
    def _find_year_column(self, ws, year_range):
        try:
            start_year = year_range.get('start', 0)
            if not start_year:
                return None
            
            next_year = start_year + 1
            
            for row in range(1, ws.max_row + 1):
                for col in range(1, ws.max_column + 1):
                    cell_value = ws.cell(row=row, column=col).value
                    
                    if cell_value is None:
                        continue
                    
                    is_start_year = False
                    if str(cell_value) == str(start_year):
                        is_start_year = True
                    elif isinstance(cell_value, (int, float)) and int(cell_value) == start_year:
                        is_start_year = True
                    
                    if is_start_year:
                        if col + 1 <= ws.max_column:
                            next_cell = ws.cell(row=row, column=col + 1).value
                            if next_cell is not None:
                                if str(next_cell) == str(next_year):
                                    return col
                                elif isinstance(next_cell, (int, float)) and int(next_cell) == next_year:
                                    return col
            
            return None
        except Exception:
            return None
    
    def _get_cell_refs_from_source_label(self, source_path, year_range):
        try:
            if "::" not in source_path:
                return []
            
            file_part, sheet_part, label_part = source_path.split("::", 2)
            
            if not os.path.exists(file_part):
                return []
            
            wb = self._get_workbook(file_part)
            if wb is None:
                return []
            
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
                    
                    if "vs. BAU" not in expected_str:
                        if cell_str != expected_str:
                            match = False
                            break
                    else:
                        if expected_str not in cell_str:
                            match = False
                            break
                
                if match:
                    target_row = row
                    break
            
            if target_row is None:
                return []
            
            start_col = self._find_year_column(ws, year_range)
            if not start_col:
                for col in range(1, ws.max_column + 1):
                    val = ws.cell(row=1, column=col).value
                    if val == year_range['start']:
                        start_col = col
                        break
            
            if not start_col:
                return []
            
            num_years = year_range['end'] - year_range['start'] + 1
            cell_refs = []
            
            for offset in range(num_years):
                col = start_col + offset
                if col > ws.max_column:
                    break
                
                cell_coord = ws.cell(row=target_row, column=col).coordinate
                cell_refs.append(f"{file_part}::{sheet_part}!{cell_coord}")
            
            return cell_refs
            
        except Exception:
            return []
    
    def _get_cell_value_from_ref(self, cell_ref):
        try:
            if "::" in cell_ref and "!" in cell_ref:
                file_part, rest = cell_ref.split("::", 1)
                sheet_part, coord = rest.split("!", 1)
                
                if not os.path.exists(file_part):
                    return 0
                
                wb = self._get_workbook(file_part)
                if wb is None or sheet_part not in wb.sheetnames:
                    return 0
                
                ws = wb[sheet_part]
                value = ws[coord].value
                
                if self._is_numeric_value(value):
                    num_value = self._convert_to_numeric(value)
                    return num_value
                else:
                    return 0
            else:
                return 0
                
        except Exception:
            return 0
    
    def _get_operand_value(self, operand, current_values, current_results):
        try:
            if isinstance(operand, list):
                if operand[0] == "index":
                    key = operand[1]
                    if isinstance(key, int):
                        value = current_values[key] if key < len(current_values) else 0
                    else:
                        value = current_results.get(key, 0)
                    return float(value) if value is not None else 0
                elif operand[0] in ["literal", "range"]:
                    value = operand[1]
                    return float(value) if value is not None else 0
                elif operand[0] == "str":
                    value = operand[1]
                    return str(value) if value is not None else ""
            elif isinstance(operand, str):
                value = current_results.get(operand, 0)
                return float(value) if value is not None else 0
            elif isinstance(operand, (int, float)):
                return float(operand)
            else:
                return 0
        except (ValueError, TypeError):
            return 0
    
    def _execute_formula_steps(self, formula_steps, current_values, source_cells_list, cell_index):
        if not formula_steps:
            return current_values[0] if current_values else 0
        
        results = {}
        
        for step in formula_steps:
            op = step["op"]
            operands = step["operands"]
            result_key = step["result"]
            
            if op == "copy":
                ops_args = []
                for operand in operands:
                    arg_value = self._get_operand_value(operand, current_values, results)
                    ops_args.append(arg_value)
                
                result = OPS_MAP[op](*ops_args)
                results[result_key] = result
                
            elif op == "offset":
                source_index = self._get_operand_value(operands[0], current_values, results)
                offset = self._get_operand_value(operands[1], current_values, results)
                
                source_index = int(source_index)
                offset = int(offset)
                
                if not (0 <= source_index < len(source_cells_list)):
                    results[result_key] = 0
                    continue
                
                cell_refs = source_cells_list[source_index]
                target_index = cell_index - offset
                
                if target_index < 0 or target_index >= len(cell_refs):
                    results[result_key] = 0
                    continue
                
                if isinstance(cell_refs[0], str) and cell_refs[0].startswith("CACHED::"):
                    label = cell_refs[0].split("::")[-1]
                    if label in self.previously_calculated:
                        cached_values = self.previously_calculated[label]
                        results[result_key] = cached_values[target_index] if target_index < len(cached_values) else 0
                    else:
                        results[result_key] = 0
                else:
                    results[result_key] = self._get_cell_value_from_ref(cell_refs[target_index])
                    
            elif op == "value":
                source_index = self._get_operand_value(operands[0], current_values, results)
                cell_index_to_get = self._get_operand_value(operands[1], current_values, results)
                
                source_index = int(source_index)
                cell_index_to_get = int(cell_index_to_get)
                
                if not (0 <= source_index < len(source_cells_list)):
                    results[result_key] = 0
                    continue
                
                cell_refs = source_cells_list[source_index]
                
                if cell_index_to_get < 0 or cell_index_to_get >= len(cell_refs):
                    results[result_key] = 0
                    continue
                
                results[result_key] = self._get_cell_value_from_ref(cell_refs[cell_index_to_get])
                
            elif op == "sum_range":
                results[result_key] = 0
                
            else:
                ops_args = []
                for operand in operands:
                    arg_value = self._get_operand_value(operand, current_values, results)
                    ops_args.append(arg_value)
                
                if op in OPS_MAP:
                    try:
                        result = OPS_MAP[op](*ops_args)
                        results[result_key] = result
                    except Exception:
                        results[result_key] = 0
                else:
                    results[result_key] = 0
        
        return results.get("final", 0)
    
    def _process_source_data(self, source_info):
        formula_steps = source_info.get("formula_steps", [])
        source_paths = source_info.get("sources", [])
        
        if not source_paths:
            return None
        
        source_cells_list = []
        for source_path in source_paths:
            cell_refs = self._get_cell_refs_from_source_label(source_path, self.year_range)
            if not cell_refs:
                return None
            
            source_cells_list.append(cell_refs)
        
        num_years = self.year_range['end'] - self.year_range['start'] + 1
        calculated_values = []
        
        for cell_index in range(num_years):
            current_values = []
            for cell_refs in source_cells_list:
                if cell_index < len(cell_refs):
                    value = self._get_cell_value_from_ref(cell_refs[cell_index])
                    current_values.append(value)
                else:
                    current_values.append(0)
            
            final_value = self._execute_formula_steps(
                formula_steps, 
                current_values, 
                source_cells_list, 
                cell_index
            )
            
            calculated_values.append(final_value)
        
        return calculated_values
    
    def _calculate_graph_values(self, graph_data):
        source_values = {}
        
        if "sources" in graph_data:
            sources = graph_data["sources"]
            
            for source_name, source_info in sources.items():
                values = self._process_source_data(source_info)
                if values:
                    source_values[source_name] = values
        
        return source_values
    
    def _calculate_values(self):
        
        with open(self.formulas_json_path, "r", encoding='utf-8') as f:
            visualizations_json = json.load(f)
        
        expanded_graphs = self._expand_visualizations_json(visualizations_json)
        final_graphs = self._expand_sources_paths(expanded_graphs)
        
        resultados = {}
        
        for graph_name, graph_data in final_graphs.items():
            source_values = self._calculate_graph_values(graph_data)
            
            resultados[graph_name] = {
                "chart_type": graph_data.get("chart_type"),
                "source_values": source_values,
                "years": list(range(self.year_range['start'], self.year_range['end'] + 1))
            }
        
        for wb in self._workbook_cache.values():
            if hasattr(wb, 'close'):
                wb.close()
        self._workbook_cache.clear()
        
        return resultados
    
    def __call__(self):

        data_values = self._calculate_values()