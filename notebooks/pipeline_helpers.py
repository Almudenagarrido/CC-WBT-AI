from platform import processor
import os, sys, json, copy, shutil, openpyxl, pandas as pd, matplotlib.pyplot as plt


class PipelineIO:

    def __init__(self, backend: str, country: str, model: str, techs: list, start_year: int = None, end_year: int = None):
        self.backend  = backend
        self.country  = country
        self.model    = model
        self.techs    = techs
        self.start_year = start_year
        self.end_year   = end_year

        self.scenario_dir        = os.path.join(backend, country)
        self.config_path         = os.path.join(backend, 'config.json')
        self.design_cap_path     = os.path.join(self.scenario_dir, f'design-capital-{model}.xlsx')
        self.fuel_fin_path       = os.path.join(self.scenario_dir, 'fuel-financial-inputs.xlsx')
        self.techno_path         = os.path.join(self.scenario_dir, f'technoeconomic-inputs-{model}.xlsx')
        self.carbon_credits_path = os.path.join(self.scenario_dir, 'carbon-credits.xlsx')
        self.fin_statements_path = os.path.join(self.scenario_dir, f'financial-statements-{model}.xlsx')
        self._templates_dir      = os.path.join(backend, '{templates}')

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _load_config(self):
        with open(self.config_path) as f:
            return json.load(f)

    def _save_config(self, cfg):
        with open(self.config_path, 'w') as f:
            json.dump(cfg, f, indent=4)

    def _strip_cell_strings(self, wb):
        for ws in wb.worksheets:
            for row in ws.iter_rows():
                for cell in row:
                    if isinstance(cell.value, str):
                        cell.value = cell.value.strip()

    def _fill_design_capital_dashes(self, wb):
        for ws in wb.worksheets:
            year_start_col = None
            for row in ws.iter_rows():
                for cell in row:
                    val = cell.value
                    year_int = None
                    if isinstance(val, int):
                        year_int = val
                    elif isinstance(val, str) and val.strip().isdigit():
                        year_int = int(val.strip())
                    if year_int is not None and 1900 <= year_int <= 2100:
                        year_start_col = cell.column
                        break
                if year_start_col:
                    break
            if not year_start_col:
                continue
            for row in ws.iter_rows():
                row_num = row[0].row
                all_none = all(
                    ws.cell(row=row_num, column=col).value is None
                    for col in range(year_start_col, ws.max_column + 1)
                )
                if all_none:
                    for col in range(year_start_col, ws.max_column + 1):
                        ws.cell(row=row_num, column=col).value = '-'

    def _year_cols(self, ws):
        for row in ws.iter_rows():
            result = []
            for i, c in enumerate(row):
                h = c.value
                year_int = None
                if isinstance(h, int):
                    year_int = h
                elif isinstance(h, str) and h.strip().isdigit():
                    year_int = int(h.strip())
                if year_int is not None and 1900 <= year_int <= 2100:
                    result.append(i)
            if result:
                return result
        return []
    
    def _trim_year_columns(self, wb):
        if not self.start_year or not self.end_year:
            return
        for ws in wb.worksheets:
            year_columns = {}
            for row in range(1, ws.max_row + 1):
                for col in range(1, ws.max_column + 1):
                    val = ws.cell(row=row, column=col).value
                    if val is None:
                        continue
                    year_int = None
                    if isinstance(val, int):
                        year_int = val
                    elif isinstance(val, str):
                        v = val.strip()
                        if v.isdigit():
                            year_int = int(v)
                    if year_int is not None and 1900 <= year_int <= 2100:
                        year_columns[col] = year_int
                if year_columns:
                    break
            cols_to_delete = [col for col, year in year_columns.items()
                            if year < self.start_year or year > self.end_year]
            for col in sorted(cols_to_delete, reverse=True):
                ws.delete_cols(col)

    # ── Config ────────────────────────────────────────────────────────────────

    def write_config_scalar(self, key, value):
        cfg = self._load_config()
        cfg[key][self.country] = value
        self._save_config(cfg)
        print(f'  config.json -> {key} = {value}')

    def write_config_timeseries(self, key, tech, years, values):
        cfg = self._load_config()
        (cfg.setdefault(key, {})
              .setdefault(self.country, {})
              .setdefault(self.model, {})
              .setdefault(tech, {}))
        for year, val in zip(years, values):
            cfg[key][self.country][self.model][tech][str(year)] = val
        self._save_config(cfg)
        print(f'  config.json -> {key}.{self.model}.{tech}')

    # ── Excel scalar ──────────────────────────────────────────────────────────

    def write_excel_scalar(self, filepath, sheet, param, value):
        wb = openpyxl.load_workbook(filepath)
        for row in wb[sheet].iter_rows(max_col=3):
            if row[0].value == param:
                row[2].value = value; break
        wb.save(filepath); wb.close()
        print(f'  {os.path.basename(filepath)} / {sheet} -> {param} = {value}')

    # ── Time series (fuel-financial-inputs format) ────────────────────────────

    def write_timeseries_list(self, filepath, sheet, param, values):
        wb = openpyxl.load_workbook(filepath)
        ws = wb[sheet]
        yc = self._year_cols(ws)
        for row in ws.iter_rows():
            if row[0].value == param:
                for idx, ci in enumerate(yc):
                    if idx < len(values): row[ci].value = values[idx]
                break
        wb.save(filepath); wb.close()
        print(f'  {os.path.basename(filepath)} / {sheet} -> {param}')

    def write_timeseries_first_year(self, filepath, sheet, param, value):
        wb = openpyxl.load_workbook(filepath)
        ws = wb[sheet]
        yc = self._year_cols(ws)
        for row in ws.iter_rows():
            if row[0].value == param and yc:
                row[yc[0]].value = value; break
        wb.save(filepath); wb.close()
        print(f'  {os.path.basename(filepath)} / {sheet} -> {param} (first year)')

    # ── Technoeconomic with System column (electricity sheets) ────────────────

    def write_techno_list(self, sheet, system, param, values):
        wb = openpyxl.load_workbook(self.techno_path)
        ws = wb[sheet]
        yc = self._year_cols(ws)
        for row in ws.iter_rows():
            if row[0].value == system and row[1].value == param:
                for idx, ci in enumerate(yc):
                    if idx < len(values): row[ci].value = values[idx]
                break
        wb.save(self.techno_path); wb.close()
        print(f'  technoeconomic / {sheet} -> {system}/{param}')

    def write_techno_da(self, sheet, system, value):
        wb = openpyxl.load_workbook(self.techno_path)
        ws = wb[sheet]
        yc = self._year_cols(ws)
        for row in ws.iter_rows():
            if row[0].value == system and row[1].value == 'D&A' and yc:
                row[yc[0]].value = value; break
        wb.save(self.techno_path); wb.close()
        print(f'  technoeconomic / {sheet} -> {system}/D&A (first year)')

    # ── Technoeconomic without System column (LPG sheet) ─────────────────────

    def write_techno_nosystem_list(self, sheet, param, values):
        wb = openpyxl.load_workbook(self.techno_path)
        ws = wb[sheet]
        yc = self._year_cols(ws)
        for row in ws.iter_rows():
            if row[0].value == param:
                for idx, ci in enumerate(yc):
                    if idx < len(values): row[ci].value = values[idx]
                break
        wb.save(self.techno_path); wb.close()
        print(f'  technoeconomic / {sheet} -> {param}')

    def write_techno_nosystem_da(self, sheet, value):
        wb = openpyxl.load_workbook(self.techno_path)
        ws = wb[sheet]
        yc = self._year_cols(ws)
        for row in ws.iter_rows():
            if row[0].value == 'D&A' and yc:
                row[yc[0]].value = value; break
        wb.save(self.techno_path); wb.close()
        print(f'  technoeconomic / {sheet} -> D&A (first year)')

    # ── Design capital — debt ─────────────────────────────────────────────────

    def write_design_debt_list(self, sheet, values):
        wb = openpyxl.load_workbook(self.design_cap_path)
        ws = wb[sheet]
        yc = self._year_cols(ws)
        for row in ws.iter_rows():
            if row[0].value == 'User-defined debt increase' and row[1].value == 'Debt increase':
                for idx, ci in enumerate(yc):
                    if idx < len(values): row[ci].value = values[idx]
                break
        wb.save(self.design_cap_path); wb.close()
        print(f'  design-capital / {sheet} -> User-defined debt increase')

    # ── Carbon credits ────────────────────────────────────────────────────────

    def write_carbon_row(self, param, values):
        wb = openpyxl.load_workbook(self.carbon_credits_path)
        ws = wb['Carbon Credits']
        yc = self._year_cols(ws)
        for row in ws.iter_rows():
            if row[0].value == param:
                for idx, ci in enumerate(yc):
                    if idx < len(values): row[ci].value = values[idx]
                break
        wb.save(self.carbon_credits_path); wb.close()
        print(f'  carbon-credits.xlsx -> {param}')

    def write_carbon_co2_emitted(self, values, years):
        param = f'CO2 emited - {self.model} scenario'
        wb = openpyxl.load_workbook(self.carbon_credits_path)
        ws = wb['Carbon Credits']
        yc = self._year_cols(ws)
        for row in ws.iter_rows():
            if row[0].value == param:
                for idx, ci in enumerate(yc):
                    if idx < len(values): row[ci].value = values[idx]
                break
        wb.save(self.carbon_credits_path); wb.close()
        print(f'  carbon-credits.xlsx -> {param}')

    # ── Model management ──────────────────────────────────────────────────────

    def get_expanded_sheets(self):
        cfg           = self._load_config()
        elec_variants = set(cfg.get('ELECTRICITY_VARIANTS', []))
        all_expanded  = cfg.get('FUELS', {}).get(self.country, {}).get('expanded', [])
        return [s for s in all_expanded
                if (s in elec_variants     and 'Electricity' in self.techs)
                or (s not in elec_variants and s in self.techs)]

    def ensure_model_exists(self):
        cfg           = self._load_config()
        elec_variants = set(cfg.get('ELECTRICITY_VARIANTS', []))
        if self.country not in cfg.get('FUELS', {}):
            template_fuels = cfg.get('FUELS', {}).get('template', {})
            cfg.setdefault('FUELS',              {})[self.country] = copy.deepcopy(template_fuels)
            cfg.setdefault('COUNTRY_YEAR_RANGES',{})[self.country] = {
                'start': self.start_year, 'end': self.end_year
            }
            cfg.setdefault('MODELS',             {})[self.country] = []
            cfg.setdefault('TARIFFS',            {})[self.country] = {}
            cfg.setdefault('UPSTREAMS',          {})[self.country] = {}
            self._save_config(cfg)
            print(f'  New country "{self.country}" initialised in config.json')

        fuels_cfg = cfg.get('FUELS', {}).get(self.country, {})

        # Copy country-level files
        for country_file in ['fuel-financial-inputs.xlsx', 'carbon-credits.xlsx']:
            dst = os.path.join(self.scenario_dir, country_file)
            src = os.path.join(self._templates_dir, country_file.replace('.xlsx', '-{template}.xlsx'))
            if not os.path.exists(dst):
                os.makedirs(self.scenario_dir, exist_ok=True)
                if os.path.exists(src):
                    shutil.copy(src, dst)
                    wb_c = openpyxl.load_workbook(dst)
                    self._strip_cell_strings(wb_c)
                    self._trim_year_columns(wb_c)
                    if country_file == 'carbon-credits.xlsx' and 'Carbon Credits' in wb_c.sheetnames:
                        ws_cc = wb_c['Carbon Credits']
                        for row in ws_cc.iter_rows():
                            for cell in row:
                                if isinstance(cell.value, str) and '{model}' in cell.value:
                                    cell.value = cell.value.replace('{model}', self.model)
                    wb_c.save(dst); wb_c.close()
                    print(f'  Copied {country_file} from template')
                else:
                    print(f'  WARNING: template not found for {country_file}')

        def _sheets(level):
            return [s for s in fuels_cfg.get(level, [])
                    if (s in elec_variants     and 'Electricity' in self.techs)
                    or (s not in elec_variants and s in self.techs)]

        file_level = {
            f'design-capital-{self.model}.xlsx':        'expanded',
            f'technoeconomic-inputs-{self.model}.xlsx': 'expanded',
            f'financial-statements-{self.model}.xlsx':  'more_expanded',
            f'capex-fuels-{self.model}.xlsx':           'expanded',
        }
        needs_create = []
        for fname, level in file_level.items():
            fpath    = os.path.join(self.scenario_dir, fname)
            expected = _sheets(level)
            if not os.path.exists(fpath):
                needs_create.append((fname, level, expected, 'does not exist'))
            else:
                try:
                    wb = openpyxl.load_workbook(fpath, read_only=True)
                    actual = set(wb.sheetnames); wb.close()
                    if actual != set(expected):
                        needs_create.append((fname, level, expected,
                                            f'current sheets={actual}, expected={set(expected)}'))
                except Exception:
                    needs_create.append((fname, level, expected, 'corrupted file — will recreate'))

        if not needs_create:
            print(f'Model {self.model} exists with the correct technologies.'); return

        print('Files to recreate from templates:')
        for fname, _, _, reason in needs_create:
            print(f'  {fname}: {reason}')
        if input('Continue? (y/n): ').lower() != 'y':
            print('Cancelled.'); return

        for fname, level, expected, _ in needs_create:
            fpath = os.path.join(self.scenario_dir, fname)
            tpath = os.path.join(self._templates_dir, fname.replace(self.model, '{model}'))
            os.makedirs(self.scenario_dir, exist_ok=True)
            if os.path.exists(tpath):
                shutil.copy(tpath, fpath)
            else:
                openpyxl.Workbook().save(fpath)
            wb   = openpyxl.load_workbook(fpath)
            wb_t = openpyxl.load_workbook(tpath) if os.path.exists(tpath) else None
            for sheet in expected:
                if sheet not in wb.sheetnames:
                    src = (wb_t[sheet]              if wb_t and sheet in wb_t.sheetnames else
                           wb_t[wb_t.sheetnames[0]] if wb_t else None)
                    new = wb.create_sheet(sheet)
                    if src:
                        for row in src.iter_rows():
                            for cell in row:
                                new[cell.coordinate].value = cell.value
            for s in [s for s in wb.sheetnames if s not in expected]:
                wb.remove(wb[s])
            self._strip_cell_strings(wb)
            self._trim_year_columns(wb)
            if 'design-capital' in fname:
                self._fill_design_capital_dashes(wb)
            wb.save(fpath); wb.close()
            if wb_t: wb_t.close()
            print(f'  {fname}')

        cfg.setdefault('MODELS', {}).setdefault(self.country, [])
        if self.model not in cfg['MODELS'][self.country]:
            cfg['MODELS'][self.country].append(self.model)
        self._save_config(cfg)
        print(f'Model {self.model} ready.')

    # ── Engine ────────────────────────────────────────────────────────────────

    def run_engine(self):
        sys.path.insert(0, self.backend)
        from excel_formula_engine import ExcelFormulaProcessor # type: ignore
        cfg = self._load_config()

        elec_variants = set(cfg.get('ELECTRICITY_VARIANTS', []))
        fuels_cfg     = cfg.get('FUELS', {}).get(self.country, {})

        def _filtered(level):
            return [s for s in fuels_cfg.get(level, [])
                    if (s in elec_variants     and 'Electricity' in self.techs)
                    or (s not in elec_variants and s in self.techs)]

        expanded      = _filtered('expanded')
        more_expanded = _filtered('more_expanded')
        normal        = cfg['FUELS'][self.country].get('normal', [])

        processor = ExcelFormulaProcessor()
        orig = os.getcwd(); os.chdir(self.backend)
        try:
            for _ in range(2):
                processor.clear_workbook_cache()
                processor.apply_formulas(
                    file_path=f'{self.country}/capex-fuels-{self.model}.xlsx',
                    formulas_json_path='formulas_map.json',
                    country=self.country, models=[self.model],
                    fuels=normal, expected_sheets=expanded,
                )
            processor.clear_workbook_cache()
            processor.apply_formulas(
                file_path=f'{self.country}/design-capital-{self.model}.xlsx',
                formulas_json_path='formulas_map.json',
                country=self.country, models=[self.model],
                fuels=normal, expected_sheets=expanded,
            )
            processor.clear_workbook_cache()
            processor.apply_formulas(
                file_path=f'{self.country}/financial-statements-{self.model}.xlsx',
                formulas_json_path='formulas_map.json',
                country=self.country, models=[self.model],
                fuels=normal, expected_sheets=more_expanded,
            )
        finally:
            os.chdir(orig)

    def run_engine_until_convergence(self, max_iter=30, tol=1e-4):
        design_scalars = [
            'How much to be financed', 'Equity', 'Grants', 'Debt', 'WACC'
        ]
        fin_rows = [
            'Annual Cost of Service', 'Long term subsidies',
            'Cash Flow from Assets', 'Operating Cash Flow'
        ]

        def _read_tracked_values():
            vals = {}

            # design-capital scalars (column C)
            wb = openpyxl.load_workbook(self.design_cap_path, data_only=True)
            for ws in wb.worksheets:
                for row in ws.iter_rows(max_col=3):
                    if row[0].value in design_scalars:
                        key = f"DC::{ws.title}::{row[0].value}"
                        v = row[2].value
                        vals[key] = float(v) if isinstance(v, (int, float)) else 0.0
            wb.close()

            # financial-statements time-series (sum across years as scalar proxy)
            wb = openpyxl.load_workbook(self.fin_statements_path, data_only=True)
            for ws in wb.worksheets:
                for row in ws.iter_rows():
                    if row[0].value in fin_rows:
                        year_vals = [
                            float(c.value) for c in row[3:]
                            if isinstance(c.value, (int, float))
                        ]
                        if year_vals:
                            key = f"FS::{ws.title}::{row[0].value}"
                            vals[key] = sum(year_vals)
            wb.close()

            return vals

        records = []
        prev_vals = None

        for i in range(max_iter):
            self.run_engine()
            curr_vals = _read_tracked_values()
            record = {'iteration': i + 1, **curr_vals}

            if prev_vals is not None:
                max_delta = max(
                    abs(curr_vals.get(k, 0) - prev_vals.get(k, 0))
                    for k in curr_vals
                )
                record['max_delta'] = max_delta
                if max_delta <= tol:
                    records.append(record)
                    df = pd.DataFrame(records)
                    print(f"  Converged in {i+1} iterations.")
                    return df
            else:
                record['max_delta'] = None

            records.append(record)
            prev_vals = curr_vals

        print(f"  Warning: did not converge after {max_iter} iterations.")
        return pd.DataFrame(records)
    
    # ── Outputs ───────────────────────────────────────────────────────────────

    def plot_convergence(self, df):

        sheet_colors = {
            'Electricity & E-Cooking':  '#D85A30',
            'Electricity (Low access)': '#378ADD',
            'LPG':                      '#1D9E75',
        }
        sheet_labels = {
            'Electricity & E-Cooking':  'E-Cooking',
            'Electricity (Low access)': 'Low Access',
            'LPG':                      'LPG',
        }

        dc_metrics = ['How much to be financed', 'WACC', 'Equity']
        fs_metrics = ['Cash Flow from Assets', 'Long term subsidies', 'Annual Cost of Service']

        fig, axes = plt.subplots(2, 3, figsize=(15, 7))
        fig.suptitle('Convergence by iteration', fontsize=13, y=1.01)
        iters = df['iteration']

        for row, (metrics, prefix) in enumerate([(dc_metrics, 'DC'), (fs_metrics, 'FS')]):
            for ax, metric in zip(axes[row], metrics):
                for sheet, color in sheet_colors.items():
                    col = f'{prefix}::{sheet}::{metric}'
                    if col in df.columns:
                        ax.plot(iters, df[col], color=color,
                                label=sheet_labels[sheet], marker='o', markersize=3, linewidth=1.5)
                ax.set_title(f'{prefix} — {metric}', fontsize=10)
                ax.set_xlabel('Iteration', fontsize=8)
                ax.legend(fontsize=7)
                ax.grid(True, alpha=0.25)

        plt.tight_layout()
        plt.show()

        # max_delta en log
        fig2, ax2 = plt.subplots(figsize=(10, 3.5))
        valid = df['max_delta'].notna()
        ax2.plot(iters[valid], df.loc[valid, 'max_delta'], 'k-o', markersize=4, linewidth=1.5)
        ax2.set_yscale('log')
        ax2.axhline(1e-4, color='#E24B4A', linestyle='--', linewidth=1, label='Tolerance 1e-4')
        ax2.set_title('Max Δ per iteration (log scale)', fontsize=11)
        ax2.set_xlabel('Iteration')
        ax2.set_ylabel('Max Δ')
        ax2.legend(fontsize=9)
        ax2.grid(True, alpha=0.25, which='both')
        plt.tight_layout()
        plt.show()

    def read_outputs(self, sheet):
        wb = openpyxl.load_workbook(self.fin_statements_path, data_only=True)
        ws = wb[sheet]
        single_rows = ['Long term subsidies', 'Operating Cash Flow',
                       'Financial Expense', 'Debt repayment', 'Equity - EoP']
        double_rows = {
            ('GRANTS', '- Realisation'): 'GRANTS:- Realisation',
            ('GRANTS', '+ Increase')   : 'GRANTS:+ Increase',
            ('GRANTS', 'EoP')          : 'GRANTS:EoP',
            ('DEBT',   '+ Increase')   : 'DEBT:+ Increase',
            ('DEBT',   '- Repayment')  : 'DEBT:- Repayment',
            ('DEBT',   'EoP')          : 'DEBT:EoP',
        }
        out = {}
        for row in ws.iter_rows(values_only=True):
            if row[0] in single_rows:
                out[row[0]] = [v if v is not None else 0 for v in row[3:3+12]]
            if (row[0], row[1]) in double_rows:
                out[double_rows[(row[0], row[1])]] = [v if v is not None else 0 for v in row[3:3+12]]
        wb.close()
        return out