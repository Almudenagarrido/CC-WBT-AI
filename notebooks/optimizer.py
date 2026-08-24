import optuna
from pyomo.environ import SolverFactory, TerminationCondition, value
from pyomo_model import build_model, make_capex_data, make_k1_k2


def run_optimization(tech_dict, tax_rate, years, search_ranges, fuel_fin=None, fuel_key='Electricity', objective='debt', n_trials=100, tariffs=None):
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    n_periods = len(years)
    capex_total = make_capex_data(tech_dict, n_periods)
    demand_base,K1, K2 = make_k1_k2(tech_dict, n_periods)
    print(f"K1={K1:.2g}, K2={K2:.2g}")
    ff = (fuel_fin or {}).get(fuel_key, {})
    ntlosses_data        = {t: ff.get('NTL',      [5] *n_periods)[t] / 100  for t in range(n_periods)}
    days_receivable_data = {t: ff.get('DAYS_REC', [30]*n_periods)[t]        for t in range(n_periods)}
    days_payable_data    = {t: ff.get('DAYS_PAY', [30]*n_periods)[t]        for t in range(n_periods)}
    tariff_raw  = (tariffs or {}).get(fuel_key, [0.0]*n_periods)
    tariff_data = {t: tariff_raw[t] if t < len(tariff_raw) else 0.0 for t in range(n_periods)}

    solver     = SolverFactory('appsi_highs')
    if not solver.available(exception_flag=False):
        raise RuntimeError("The appsi_highs solver is unavailable")

    pyomo_runs = []

    def _trial(trial):
        pct_equity = trial.suggest_float('pct_equity', *search_ranges['pct_equity'])
        pct_grants = trial.suggest_float('pct_grants', *search_ranges['pct_grants'])
        pct_debt = 1 - pct_equity

        cost_equity  = trial.suggest_float('cost_equity',  *search_ranges['cost_equity'])
        cost_debt    = trial.suggest_float('cost_debt',    *search_ranges['cost_debt'])
        years_real   = trial.suggest_int('years_realisation',   *search_ranges['years_realisation'])
        grace        = trial.suggest_int('grace_period',        *search_ranges['grace_period'])
        amortization = trial.suggest_int('amortization_period', *search_ranges['amortization_period'])

        model = build_model(
            pct_debt=pct_debt,
            pct_equity=pct_equity,
            pct_grants=pct_grants,
            cost_equity=cost_equity,
            cost_debt=cost_debt,
            grace_period=grace,
            amortization_period=amortization,
            years_realisation=years_real,
            capex_total=capex_total,
            K1=K1, K2=K2,
            TAXRATE=tax_rate / 100,
            ntlosses_data=ntlosses_data,
            days_receivable_data=days_receivable_data,
            days_payable_data=days_payable_data,
            N_PERIODS=n_periods,
            demand_base=demand_base,
            TARIFF=tariff_data
        )
        results = solver.solve(model)
        if results.solver.termination_condition != TerminationCondition.optimal:
            raise RuntimeError(
                f"Trial {trial.number} did not solve to optimality: "
                f"{results.solver.termination_condition}"
            )

        debt_schedule = [value(model.debt[t]) or 0 for t in range(n_periods)]  # pyright: ignore[reportIndexIssue]
        capex_schedule = [value(model.capex_data[t]) or 0 for t in range(n_periods)]  # pyright: ignore[reportIndexIssue]
        lt_subsidy_schedule = [value(model.lt_subsidies[t]) or 0 for t in range(n_periods)]  # pyright: ignore[reportIndexIssue]
        objective_result = value(model.obj)  # pyright: ignore[reportGeneralTypeIssues]
        if objective_result is None:
            raise RuntimeError("The solved model has no objective value")
        objective_value = float(objective_result)
        run = {
            'TRIAL': trial.number,
            'PCT_EQUITY': pct_equity,
            'PCT_DEBT': pct_debt,
            'PCT_GRANTS': pct_grants,
            'COST_OF_EQUITY': cost_equity,
            'COST_OF_DEBT': cost_debt,
            'YEARS_REALISATION': years_real,
            'GRACE_PERIOD': grace,
            'AMORTIZATION': amortization,
            'TOTAL_DEBT': objective_value,
            'DEBT_SCHEDULE': debt_schedule,
            'CAPEX_SCHEDULE': capex_schedule,
            'TOTAL_LT_SUBSIDIES': sum(lt_subsidy_schedule),
            'LT_SUBSIDY_SCHEDULE': lt_subsidy_schedule,
        }
        pyomo_runs.append(run)
        print(
            f"Trial {trial.number}: total debt={objective_value:.1g}, "
            f"debt={debt_schedule}, capex={capex_schedule}, "
            f"lt_subsidies={lt_subsidy_schedule}"
        )
        return objective_value

    study = optuna.create_study(direction='minimize')
    study.optimize(_trial, n_trials=n_trials)
    if not pyomo_runs:
        raise RuntimeError("No feasible Pyomo runs were completed")

    p = study.best_params
    pct_debt_best = 1 - p['pct_equity']

    best_model = build_model(
        pct_debt=pct_debt_best,
        pct_equity=p['pct_equity'],
        pct_grants=p['pct_grants'],
        cost_equity=p['cost_equity'],
        cost_debt=p['cost_debt'],
        grace_period=p['grace_period'],
        amortization_period=p['amortization_period'],
        years_realisation=p['years_realisation'],
        capex_total=capex_total,
        K1=K1, K2=K2,
        TAXRATE=tax_rate / 100,
        ntlosses_data=ntlosses_data,
        days_receivable_data=days_receivable_data,
        days_payable_data=days_payable_data,
        N_PERIODS=n_periods,
        demand_base=demand_base,
        TARIFF=tariff_data
    )
    results = solver.solve(best_model)
    if results.solver.termination_condition != TerminationCondition.optimal:
        raise RuntimeError(
            f'Best model did not solve to optimality: '
            f'{results.solver.termination_condition}'
        )

    debt_schedule = [value(best_model.debt[t]) or 0 for t in range(n_periods)]  # pyright: ignore[reportIndexIssue]
    capex_schedule = [value(best_model.capex_data[t]) or 0 for t in range(n_periods)]  # pyright: ignore[reportIndexIssue]
    lt_subsidy_schedule = [value(best_model.lt_subsidies[t]) or 0 for t in range(n_periods)]  # pyright: ignore[reportIndexIssue]
    tariff_income_schedule      = [value(best_model.tariff_income[t])          or 0 for t in range(n_periods)]
    grants_schedule             = [value(best_model.grants[t])                 or 0 for t in range(n_periods)]
    revenues_schedule           = [value(best_model.revenues[t])               or 0 for t in range(n_periods)]
    costs_schedule              = [value(best_model.costs[t])                  or 0 for t in range(n_periods)]
    ebitda_schedule             = [value(best_model.ebitda[t])                 or 0 for t in range(n_periods)]
    financial_expenses_schedule = [value(best_model.financial_expenses[t])     or 0 for t in range(n_periods)]
    cfa_schedule = [value(best_model.cash_flow[t]) or 0 for t in range(n_periods)]
    acofservice_schedule = [value(best_model.acofservice[t]) or 0 for t in range(n_periods)]

    return {
        'K1': K1,
        'K2': K2,
        'PCT_EQUITY':        round(p['pct_equity']  * 100),
        'PCT_DEBT':          round(pct_debt_best * 100),
        'COST_OF_EQUITY':    round(p['cost_equity'] * 100),
        'PCT_GRANTS':        round(p['pct_grants']  * 100),
        'YEARS_REALISATION': p['years_realisation'],
        'COST_OF_DEBT':      round(p['cost_debt']   * 100),
        'GRACE_PERIOD':      p['grace_period'],
        'AMORTIZATION':      p['amortization_period'],
        'DEBT_INCREASE':     debt_schedule,
        'CAPEX_SCHEDULE':    capex_schedule,
        'TOTAL_LT_SUBSIDIES': sum(lt_subsidy_schedule),
        'LT_SUBSIDY_SCHEDULE': lt_subsidy_schedule,
        'PYOMO_RUNS':        pyomo_runs,
        'TARIFF_INCOME':        tariff_income_schedule,
        'GRANTS_PYOMO':         grants_schedule,
        'REVENUES_PYOMO':       revenues_schedule,
        'COSTS_PYOMO':          costs_schedule,
        'EBITDA_PYOMO':         ebitda_schedule,
        'FINANCIAL_EXP_PYOMO':  financial_expenses_schedule,
        'CFA_PYOMO':            cfa_schedule,
    }