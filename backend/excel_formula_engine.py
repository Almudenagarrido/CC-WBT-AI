import os
import json
import traceback
from copy import deepcopy
from itertools import product
from functools import lru_cache
from openpyxl import load_workbook


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

OPS_MAP = {
    "addition": lambda *args: sum(args),
    "subtraction": lambda x, y: x - y,
    "multiply": lambda x, y: x * y,
    "multiply_per": lambda x, y: (x * y)/100,
    "divide": lambda x, y: x / y,
    "safe_divide": lambda x, y: (x / y) if y != 0 else 0,
    "safe_divide_minus": lambda x, y, z: (x / y - z) if y != 0 else 0,
    "gt": lambda x, y: x > y,
    "gt_eq": lambda x, y: x >= y,
    "lt": lambda x, y: x < y,
    "equal": lambda x, y: x == y,
    "if": lambda condition, true_val, false_val: true_val if condition else false_val,
    "copy": lambda x: x,
    "min": lambda x, y: min(x, y),
    "max": lambda x, y: max(x, y),
    "abs": lambda x: abs(x),
    "negative": lambda x: - x,
    "percentage": lambda x: x*100,
    "int": lambda x: int(x)
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

    def _manage_upload_flag(self, file_path, action="read", value=None):

        try:
            flag_path = file_path + ".upload_flag"
            
            if action == "read":
                if os.path.exists(flag_path):
                    with open(flag_path, 'r') as f:
                        return f.read().strip() == "True"
                return False
                
            elif action == "write":
                if value is None:
                    raise ValueError()
                with open(flag_path, 'w') as f:
                    f.write(str(value))
                return None
                
            elif action == "clear":
                if os.path.exists(flag_path):
                    os.remove(flag_path)
                return None
                
            else:
                raise ValueError(f"Not a valid action.")
                
        except Exception as e:
            if action == "read":
                return False
            return None

    def apply_formulas(self, file_path, formulas_json_path, country, models, fuels, expected_sheets, just_uploaded=False):

        just_uploaded = self._manage_upload_flag(file_path, "read")
        print(f"🔧 APPLY FORMULAS - just_uploaded: {just_uploaded}")
    
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
                formulas_sheet_file, country, models, fuels, expected_sheets, specific_values, just_uploaded
            )
            
            self._process_formulas_sheet_file(file_path_norm, expanded_formulas, just_uploaded)
                
            if just_uploaded:
                self._manage_upload_flag(file_path, "clear")
                print(f"🧹 Flag de upload limpiado para: {file_path}")
                    
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
    
    def _expand_single_formulas(self, formulas_sheet_file, country, models, fuels, expected_sheets, specific_values=None, just_uploaded=False):
    
        expanded_formulas = {}
        if specific_values is None:
            specific_values = {'model': None, 'fuel': None, 'sheet': None}
        
        print(f"🔧 EXPANDIENDO FÓRMULAS - Archivo tiene {len(formulas_sheet_file)} secciones: {list(formulas_sheet_file.keys())}")
        print(f"🔧 EXPANDIENDO FÓRMULAS - just_uploaded: {just_uploaded}")
    
        print(f"   Models disponibles: {models}")
        print(f"   Specific model: {specific_values['model']}")
        
        for sheet_name, formulas in formulas_sheet_file.items():
            print(f"📑 PROCESANDO SECCIÓN: '{sheet_name}'")
            
            # Expandir nombre de hoja si es {fuel}
            if sheet_name == "{fuel}":
                print(f"   🔥 EXPANDIENDO {{fuel}} → {fuels}")
                sheets_to_expand = fuels
            elif sheet_name == "{sheet}":
                sheets_to_expand = expected_sheets
            else:
                sheets_to_expand = [sheet_name]
                print(f"   ✅ HOJA ESPECÍFICA: {sheet_name}")
            
            for expanded_sheet_name in sheets_to_expand:
                print(f"   🎯 HOJA FINAL: '{expanded_sheet_name}'")
                
                if expanded_sheet_name not in expanded_formulas:
                    expanded_formulas[expanded_sheet_name] = []
                
                # Para cada fórmula, determinar si necesita expansión de model
                for formula in formulas:
                    target = formula.get("target", "")
                    sources = formula.get("sources", [])

                    uses_upload_file = any("upload-" in source for source in sources)
                
                    if uses_upload_file and not just_uploaded:
                        print(f"   ⏭️  Saltando fórmula (no just_uploaded): {formula['target']}")
                        continue
                    
                    # Verificar si esta fórmula necesita expansión de model
                    needs_model = any("{model}" in s for s in [target] + sources)
                    
                    if needs_model:
                        # Si necesita model y hay un valor específico, usar solo ese
                        if specific_values['model']:
                            models_to_use = [specific_values['model']]
                        else:
                            # Si no hay valor específico, expandir para todos los modelos
                            models_to_use = models
                    else:
                        models_to_use = [None]
                    
                    print(f"   📝 Fórmula target: '{target}' -> necesita model: {needs_model}, models a usar: {models_to_use}")
                    
                    # Expandir para cada modelo necesario
                    for model_val in models_to_use:
                        new_formula = deepcopy(formula)
                        target = new_formula.get("target", "")
                        sources = new_formula.get("sources", [])
                        
                        # Reemplazar placeholders en target
                        if "{country}" in target:
                            new_formula["target"] = target.replace("{country}", country)
                        if "{model}" in target and model_val:
                            new_formula["target"] = target.replace("{model}", model_val)
                        if "{fuel}" in target:
                            new_formula["target"] = target.replace("{fuel}", expanded_sheet_name)
                        if "{sheet}" in target:
                            new_formula["target"] = target.replace("{sheet}", expanded_sheet_name)
                        
                        # Reemplazar placeholders en sources
                        new_sources = []
                        for source in sources:
                            if "{country}" in source:
                                source = source.replace("{country}", country)
                            if "{model}" in source and model_val:
                                source = source.replace("{model}", model_val)
                            if "{fuel}" in source:
                                source = source.replace("{fuel}", expanded_sheet_name)
                            if "{sheet}" in source:
                                source = source.replace("{sheet}", expanded_sheet_name)
                            new_sources.append(source)
                        
                        new_formula["sources"] = new_sources
                        
                        expanded_formulas[expanded_sheet_name].append(new_formula)
                        print(f"   ✅ Fórmula expandida: {new_formula['target']}")
        
        print(f"📊 RESULTADO - Hojas expandidas: {list(expanded_formulas.keys())}")
        for sheet_name, formulas in expanded_formulas.items():
            print(f"   📑 {sheet_name}: {len(formulas)} fórmulas")
        
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

    def _process_formulas_sheet_file(self, file_path, formulas_sheet_file, just_uploaded=False):
    
        self.clear_workbook_cache()
    
        wb = load_workbook(file_path)
        
        try:
            changes_made = False
            for sheet_name, formulas in formulas_sheet_file.items():
                print(wb.sheetnames)
                if sheet_name not in wb.sheetnames:
                    print(f"⚠️ Hoja '{sheet_name}' no encontrada en el archivo")
                    continue
                
                ws = wb[sheet_name]
                print(f"🔧 PROCESANDO HOJA: '{sheet_name}' con {len(formulas)} fórmulas")
                
                for formula in formulas:
                    try:
                        formula_changed = self._execute_single_formula(ws, formula)
                        if formula_changed:
                            changes_made = True
                            print(f"✅ Cambios realizados en hoja '{sheet_name}'")
                    except Exception as e:
                        print(f"❌ Error en fórmula de hoja '{sheet_name}': {str(e)}")
                        continue
            
            if changes_made:
                wb.save(file_path)
                self._apply_number_formatting(file_path)
                print("💾 Archivo guardado con cambios")
            #else:
                print("ℹ️ No hubo cambios para guardar")
            
        except Exception as e:
            traceback.print_exc()
        finally:
            if hasattr(wb, 'close'):
                wb.close()
    
    def _get_cell_value_from_ref(self, cell_ref, default_ws):
    
        try:
            # DETECTAR SI ES UNA REFERENCIA A CONFIG.JSON
            if "config.json" in cell_ref:
                # Formato: "config.json::{country}::TAX_RATES"
                parts = cell_ref.split("::")
                if len(parts) == 3:
                    _, country, config_key = parts
                    return self._get_config_value(country, config_key)
                else:
                    print(f"   ❌ Formato de referencia JSON incorrecto: {cell_ref}")
                    return 0
                
            # PROCESAMIENTO NORMAL DE EXCEL
            elif "::" in cell_ref and "!" in cell_ref:
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
            print(f"   ❌ Error obteniendo valor de referencia: {e}")
            return 0
    
    def _execute_single_formula(self, ws, formula):
    
        try:
            print(f"📄 EJECUTANDO FÓRMULA EN HOJA: '{ws.title}'")
            print(f"   TARGET: '{formula['target']}'")
            print(f"   SOURCES: {formula['sources']}")
            print(f"   STEPS: {formula.get('formula_steps', [])}")

            target_label = formula["target"]
            source_labels = formula["sources"]
            formula_steps = formula.get("formula_steps", [])
            
            target_cells = self._find_cells_from_target_label(target_label, ws)
            if not target_cells:
                print(f"   ❌ NO SE ENCONTRARON CELDAS TARGET")
                return False
            
            print(f"   ✅ Celdas target encontradas: {len(target_cells)}")
            
            source_cells_list = []
            for i, source_label in enumerate(source_labels):
                print(f"   🔍 Obteniendo fuente {i}: '{source_label}'")
                cell_refs = self._get_cell_refs_from_source_label(source_label, ws)
                if not cell_refs:
                    print(f"   ❌ No se encontraron referencias para fuente: '{source_label}'")
                    return False
                print(f"   ✅ Fuente {i} tiene {len(cell_refs)} referencias")
                source_cells_list.append(cell_refs)
            
            changes_made = False
            for cell_index in range(len(target_cells)):
                print(f"   🔄 Procesando celda {cell_index + 1}/{len(target_cells)}")
                
                current_values = []
                for i, cell_refs in enumerate(source_cells_list):
                    if cell_index < len(cell_refs):
                        value = self._get_cell_value_from_ref(cell_refs[cell_index], ws)
                        current_values.append(value)
                        print(f"      Fuente {i} valor: {value}")
                    else:
                        current_values.append(0)
                        print(f"      Fuente {i} valor: 0 (fuera de rango)")
                
                final_value = self._execute_formula_for_cell(
                    formula_steps, current_values, source_cells_list, cell_index, ws
                )
                
                print(f"      Valor calculado: {final_value}")
                
                target_cell = target_cells[cell_index]
                current_target_value = ws[target_cell].value
                
                if current_target_value != final_value:
                    ws[target_cell] = final_value
                    changes_made = True
                    print(f"      ✅ ACTUALIZADO {target_cell}: {current_target_value} -> {final_value}")
                #else:
                    print(f"      ⏭️  Sin cambios en {target_cell}")
                    
            return changes_made
                
        except Exception as e:
            print(f"   ❌ ERROR en fórmula: {str(e)}")
            traceback.print_exc()
            return False
    
    def _get_config_value(self, country, config_key):
        try:
            if not os.path.exists(CONFIG_FILE):
                print(f"   ❌ Archivo config.json no encontrado en: {CONFIG_FILE}")
                return 0
            
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            
            # Manejar claves anidadas como "COUNTRY_YEAR_RANGES:start"
            if ":" in config_key:
                main_key, sub_key = config_key.split(":", 1)
                if main_key in config:
                    country_data = config[main_key].get(country, {})
                    value = country_data.get(sub_key)
                    if value is not None:
                        print(f"   ✅ Valor de config.json: {country} -> {main_key}.{sub_key} = {value}")
                        return float(value)
                    else:
                        print(f"   ❌ {sub_key} no encontrado en {main_key} para país: {country}")
                        return 0
                else:
                    print(f"   ❌ Clave principal no encontrada: {main_key}")
                    return 0
            else:
                # Manejo original para claves simples
                if config_key in config:
                    value = config.get(config_key, {}).get(country)
                    if value is not None:
                        print(f"   ✅ Valor de config.json: {country} -> {config_key} = {value}")
                        return float(value)
                    else:
                        print(f"   ❌ {config_key} no encontrado para país: {country}")
                        return 0
                else:
                    print(f"   ❌ Clave de config no encontrada: {config_key}")
                    return 0
                    
        except Exception as e:
            print(f"   ❌ Error leyendo config.json: {e}")
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
                    # Convertir a número
                    return float(value) if value is not None else 0
                elif operand[0] in ["literal", "range"]:
                    value = operand[1]
                    # Convertir a número
                    return float(value) if value is not None else 0
            elif isinstance(operand, str):
                value = current_results.get(operand, 0)
                # Convertir a número
                return float(value) if value is not None else 0
            elif isinstance(operand, (int, float)):
                return float(operand)
            else:
                return 0
        except (ValueError, TypeError) as e:
            print(f"      ❌ Error convirtiendo operando a número: {e} para {operand}")
            return 0
    
    def _get_cell_refs_from_source_label(self, source_label, default_ws):
    
        print(f"   🔍 BUSCANDO FUENTE: '{source_label}'")
        
        # DETECTAR SI ES UNA REFERENCIA A CONFIG.JSON
        if "config.json" in source_label:
            print(f"   ✅ Es una referencia a config.json")
            # Para config.json, devolvemos una lista con una referencia especial
            # que será manejada por _get_cell_value_from_ref
            return [source_label]  # ← Devuelve la misma referencia como "celda"
        
        if "::" in source_label:
            parts = source_label.split("::")
            if len(parts) == 3:
                file_part, sheet_part, label_part = parts
            else:
                print(f"   ❌ Formato de fuente incorrecto: {source_label}")
                return []
        else:
            file_part = None
            sheet_part = default_ws.title
            label_part = source_label
        
        print(f"      Archivo: {file_part}")
        print(f"      Hoja: {sheet_part}") 
        print(f"      Label: {label_part}")
        
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
        print(f"      🧮 Ejecutando fórmula para celda {cell_index}")
        print(f"      Valores actuales: {current_values}")

        for step in formula_steps:
            op = step["op"]
            operands = step["operands"]
            result_key = step["result"]

            print(f"      Paso: {op} {operands} -> {result_key}")
        
            if op == "offset":
                result = self._execute_offset_operation(
                    operands, current_values, results, source_cells_list, cell_index, default_ws
                )
            elif op == "sum_range":
                result = self._execute_sum_range_operation(
                    operands, current_values, results, source_cells_list, cell_index, default_ws, step
                )
            elif op == "range":
                range_value = self._get_operand_value(operands[0], current_values, results)
                result = cell_index + range_value
                    
            elif op == "value":
                result = self._execute_value_operation(
                    operands, current_values, results, source_cells_list, cell_index, default_ws
                )
            
            elif op == "index_match":
                result = self._execute_index_match_operation(
                    operands, current_values, results, source_cells_list, cell_index, default_ws
                )
            
            else:
                # Para otras operaciones, usar el método existente
                ops_args = []
                for operand in operands:
                    ops_args.append(self._get_operand_value(operand, current_values, results))
                
                if op in OPS_MAP:
                    result = OPS_MAP[op](*ops_args)
                else:
                    result = 0
            
            results[result_key] = result
            print(f"      Resultado intermedio {result_key}: {result}")
        
        final_result = results.get("final", 0)
        print(f"      ✅ Resultado final: {final_result}")
        return final_result

    def _execute_value_operation(self, operands, current_values, current_results, source_cells_list, current_index, default_ws):
        """Operación value: obtiene un valor específico de una fuente"""
        if len(operands) >= 2:
            if isinstance(operands[0], list) and operands[0][0] == "index":
                source_index = operands[0][1]
            else:
                source_index = self._get_operand_value(operands[0], current_values, current_results)
            
            if isinstance(operands[1], list) and operands[1][0] == "literal":
                cell_index_to_get = operands[1][1]
            else:
                cell_index_to_get = self._get_operand_value(operands[1], current_values, current_results)
            
            source_index = int(source_index)
            cell_index_to_get = int(cell_index_to_get)
            
            if 0 <= source_index < len(source_cells_list):
                cell_refs = source_cells_list[source_index]
                if 0 <= cell_index_to_get < len(cell_refs):
                    return self._get_cell_value_from_ref(cell_refs[cell_index_to_get], default_ws)  
        
        return 0

    def _execute_index_match_operation(self, operands, current_values, current_results, source_cells_list, current_index, default_ws):
        """
        Operación index_match: INDICE + COINCIDIR
        Busca el primer valor ≠ 0 en el rango inferior y devuelve el valor de arriba
        """
        if len(operands) >= 2:
            # Obtener índices de los rangos (fuente superior e inferior)
            if isinstance(operands[0], list) and operands[0][0] == "index":
                top_source_index = operands[0][1]
            else:
                top_source_index = self._get_operand_value(operands[0], current_values, current_results)
            
            if isinstance(operands[1], list) and operands[1][0] == "index":
                bottom_source_index = operands[1][1]
            else:
                bottom_source_index = self._get_operand_value(operands[1], current_values, current_results)
            
            top_source_index = int(top_source_index)
            bottom_source_index = int(bottom_source_index)
            
            print(f"         INDEX_MATCH: top_index={top_source_index}, bottom_index={bottom_source_index}")
            
            # Verificar que los índices son válidos
            if (0 <= top_source_index < len(source_cells_list) and 
                0 <= bottom_source_index < len(source_cells_list)):
                
                top_cell_refs = source_cells_list[top_source_index]
                bottom_cell_refs = source_cells_list[bottom_source_index]
                
                # Buscar el primer valor ≠ 0 en el rango inferior
                found_index = -1
                for i in range(min(len(bottom_cell_refs), len(top_cell_refs))):
                    value = self._get_cell_value_from_ref(bottom_cell_refs[i], default_ws)
                    print(f"         INDEX_MATCH: celda {i} valor={value}")
                    if value != 0:
                        found_index = i
                        break
                
                # Si se encontró, devolver el valor del rango superior
                if found_index >= 0 and found_index < len(top_cell_refs):
                    result = self._get_cell_value_from_ref(top_cell_refs[found_index], default_ws)
                    print(f"         INDEX_MATCH: encontrado en índice {found_index}, resultado={result}")
                    return result
            
        return 0
    
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
        condition = step.get("condition") if step else None
        
        if 0 <= source_index < len(source_cells_list):
            cell_refs = source_cells_list[source_index]
            
            if width == "all":
                # COMPORTAMIENTO ORIGINAL: Suma TODAS las celdas
                total = 0
                for ref in cell_refs:
                    value = self._get_cell_value_from_ref(ref, default_ws)
                    if self._meets_condition(value, condition):
                        total += value
                print(f"         SUM_RANGE ALL: sumando {len(cell_refs)} celdas = {total}")
                return total
            
            total = 0
            
            if direction == "backward":
                # NUEVO: Si width es 0, suma desde inicio hasta actual
                if width == 0:
                    start_index = 0
                    end_index = current_index + 1
                    
                    for i in range(start_index, end_index):
                        if i < len(cell_refs):
                            value = self._get_cell_value_from_ref(cell_refs[i], default_ws)
                            if self._meets_condition(value, condition):
                                total += value
                    print(f"         SUM_RANGE BACKWARD+0: sumando celdas 0 a {current_index} = {total}")
                
                else:
                    # Comportamiento existente para backward con width > 0
                    start_index = max(0, current_index - width + 1)
                    end_index = current_index + 1
                    
                    for i in range(start_index, end_index):
                        if i < len(cell_refs):
                            value = self._get_cell_value_from_ref(cell_refs[i], default_ws)
                            if self._meets_condition(value, condition):
                                total += value
                    print(f"         SUM_RANGE BACKWARD+{width}: sumando celdas {start_index} a {current_index} = {total}")
                                    
            else:
                # Comportamiento forward
                start_index = current_index
                end_index = min(len(cell_refs), current_index + width)
                
                for i in range(start_index, end_index):
                    if i < len(cell_refs):
                        value = self._get_cell_value_from_ref(cell_refs[i], default_ws)
                        if self._meets_condition(value, condition):
                            total += value
                print(f"         SUM_RANGE FORWARD+{width}: sumando celdas {start_index} a {end_index-1} = {total}")
                            
            return total
        else:
            return 0
    
    def _meets_condition(self, value, condition):
        """
        Evalúa si un valor cumple con una condición dada
        """
        if condition is None:
            return True  # Sin condición, incluir todos los valores
        
        try:
            if condition == "<0":
                return value < 0
            elif condition == ">0":
                return value > 0
            elif condition == "<=0":
                return value <= 0
            elif condition == ">=0":
                return value >= 0
            elif condition == "==0":
                return value == 0
            elif condition == "!=0":
                return value != 0
            else:
                # Para condiciones más complejas, podrías usar eval (con precaución)
                return True  # Por defecto, incluir todos
        except:
            return True  # En caso de error, incluir el valor

    def _execute_offset_operation(self, operands, current_values, current_results, source_cells_list, current_index, default_ws):
    
        # PRIMERO obtener source_index
        if isinstance(operands[0], list) and operands[0][0] == "index":
            source_index = operands[0][1]
        else:
            source_index = self._get_operand_value(operands[0], current_values, current_results)
        
        # LUEGO obtener offset  
        if isinstance(operands[1], list) and operands[1][0] == "literal":
            offset = operands[1][1]
        else:
            offset = self._get_operand_value(operands[1], current_values, current_results)
        
        # AHORA SÍ usar offset en el print
        print(f"         OFFSET: source_index={source_index}, offset={offset}, current_index={current_index}")
        
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
        
        print(f"🎯 BUSCANDO TARGET: '{target_label}'")
        print(f"   Partes del label: {label_parts}")
        print(f"   En hoja: '{worksheet.title}'")
        
        # PRINT ESPECIAL PARA EBIT
        if "EBIT" in target_label.upper():
            print(f"   🔍🔍🔍 BÚSQUEDA ESPECIAL PARA EBIT - Buscando coincidencia EXACTA")
        
        target_row = None
        for row in range(1, worksheet.max_row + 1):
            type_value = str(worksheet.cell(row=row, column=1).value or "").strip()
            sub_value = str(worksheet.cell(row=row, column=2).value or "").strip()
            expected_type = label_parts[0].strip()
            expected_sub = label_parts[1].strip() if len(label_parts) > 1 else ""

            print(f"   🔍 Fila {row}: C1='{type_value}', C2='{sub_value}'")

            # PRINT ESPECIAL PARA EBIT EN CADA FILA
            if "EBIT" in target_label.upper():
                print(f"   🔍🔍🔍 COMPARANDO EBIT: '{expected_type}' vs '{type_value}' - ¿Coincidencia exacta? {expected_type.lower() == type_value.lower()}")

            type_match = (expected_type.lower() in type_value.lower())
            sub_match = (expected_sub == "") or (sub_value.lower() == expected_sub.lower())
            
            if type_match and sub_match:
                target_row = row
                # PRINT ESPECIAL PARA EBIT CUANDO ENCUENTRA
                if "EBIT" in target_label.upper():
                    print(f"   ✅✅✅ EBIT ENCONTRADO en fila {row} (COINCIDENCIA EXACTA)")
                    print(f"      ✅ Buscaba EXACTAMENTE: '{expected_type}'")
                    print(f"      ✅ Encontró EXACTAMENTE: '{type_value}'")
                    if expected_sub:
                        print(f"      ✅ Sub-búsqueda: '{expected_sub}' vs '{sub_value}'")
                else:
                    print(f"   ✅ ENCONTRADO en fila {row} (COINCIDENCIA EXACTA)")
                    print(f"      Buscaba: '{expected_type}' vs Encontrado: '{type_value}'")
                    if expected_sub:
                        print(f"      Buscaba: '{expected_sub}' vs Encontrado: '{sub_value}'")
                break

        if target_row is None:
            # PRINT ESPECIAL PARA EBIT CUANDO NO ENCUENTRA
            if "EBIT" in target_label.upper():
                print(f"   ❌❌❌ EBIT NO ENCONTRADO: No se encontró coincidencia exacta para '{target_label}'")
            else:
                print(f"   ❌ NO ENCONTRADO: '{target_label}'")
            return []
        
        print(f"   ✅ Target encontrado en fila {target_row}")
        
        # ... el resto del código igual ...

        if target_row is None:
            print(f"   ❌ NO ENCONTRADO: '{target_label}'")
            return []
        
        print(f"   ✅ Target encontrado en fila {target_row}")
        
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
    
