import optuna
from pyomo.environ import SolverFactory
from pyomo_model import build_model, make_capex_data, make_k1_k2


def run_optimization(tech_dict, tax_rate, years, search_ranges, objective='debt', n_trials=100):
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    n_periods  = len(years)
    capex_data = make_capex_data(tech_dict, n_periods)
    K1, K2     = make_k1_k2(tech_dict)
    solver     = SolverFactory('appsi_highs')

    def _trial(trial):
        pct_equity = trial.suggest_float('pct_equity', *search_ranges['pct_equity'])
        pct_grants = trial.suggest_float('pct_grants', *search_ranges['pct_grants'])
        pct_debt   = 1 - pct_equity - pct_grants
        if pct_debt < 0:
            return float('inf')

        cost_equity  = trial.suggest_float('cost_equity',  *search_ranges['cost_equity'])
        cost_debt    = trial.suggest_float('cost_debt',    *search_ranges['cost_debt'])
        years_real   = trial.suggest_int('years_realisation',   *search_ranges['years_realisation'])
        grace        = trial.suggest_int('grace_period',        *search_ranges['grace_period'])
        amortization = trial.suggest_int('amortization_period', *search_ranges['amortization_period'])

        try:
            model = build_model(
                pct_debt=pct_debt,
                pct_equity=pct_equity,
                pct_grants=pct_grants,
                cost_equity=cost_equity,
                cost_debt=cost_debt,
                grace_period=grace,
                amortization_period=amortization,
                years_realisation=years_real,
                capex_data=capex_data,
                K1=K1, K2=K2,
                TAXRATE=tax_rate / 100,
                N_PERIODS=n_periods,
            )
            solver.solve(model)

            if objective == 'lts':
                return sum(model.lt_subsidies[t].value or 0 for t in model.T)
            else:
                return model.obj()
        except Exception:
            return float('inf')

    study = optuna.create_study(direction='minimize')
    study.optimize(_trial, n_trials=n_trials)

    p = study.best_params
    return {
        'PCT_EQUITY':        round(p['pct_equity']  * 100),
        'COST_OF_EQUITY':    round(p['cost_equity'] * 100),
        'PCT_GRANTS':        round(p['pct_grants']  * 100),
        'YEARS_REALISATION': p['years_realisation'],
        'COST_OF_DEBT':      round(p['cost_debt']   * 100),
        'GRACE_PERIOD':      p['grace_period'],
        'AMORTIZATION':      p['amortization_period'],
        'DEBT_INCREASE':     [0] * n_periods,
    }