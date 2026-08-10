from pyomo.environ import (
    ConcreteModel, Set, Param, Var, Objective, Constraint,
    NonNegativeReals, Reals, minimize, SolverFactory
)
 
N_PERIODS = 10
 
 
def build_model(
    pct_debt: float,
    pct_equity: float,
    cost_debt: float,
    cost_equity: float,
    grace_period: int,        # T1
    amortization_period: int,  # T2
    capex_data=None,
    cost_upstream_data=None,
    years_realisation: int = 8,
    K1: float = 0.5,
    K2: float = 0.3,
    NTLOSSES: float = 0.1,
    TAXRATE: float = 0.25,
    pct_grants: float = 0.2,
    DAYS_PAYABLE: float = 45,
    DAYS_RECEIVABLE: float = 30,
    N_DEPREC: int = 20,
    N_PERIODS: int = 10,
):
 
    assert abs((pct_debt + pct_equity + pct_grants) - 1.0) < 1e-9, (
        "pct_debt + pct_equity + pct_grants must equal 1"
    )
 
    capex_data = capex_data or {t: 0.0 for t in range(N_PERIODS)}
    cost_upstream_data = cost_upstream_data or {t: 0.0 for t in range(N_PERIODS)}
    realisation_periods = set(range(years_realisation))
 
    model = ConcreteModel()
 
    # ------------------ SETS -----------------------
    model.T = Set(initialize=range(N_PERIODS), ordered=True)
    first_t = min(model.T)
 
    # ------------------ PARAMETERS -----------------------
    # ----------------- model inputs ----------------------
    model.capex_data = Param(model.T, initialize=capex_data, mutable=True)
    model.cost_upstream_data = Param(model.T, initialize=cost_upstream_data, mutable=True)
 
    model.K1 = Param(initialize=K1, mutable=True)
    model.K2 = Param(initialize=K2, mutable=True)
    model.NTLOSSES = Param(initialize=NTLOSSES, mutable=True)
    model.TAXRATE = Param(initialize=TAXRATE, mutable=True)
    model.pct_grants = Param(initialize=pct_grants, mutable=True)
    model.DAYS_PAYABLE = Param(initialize=DAYS_PAYABLE, mutable=True)
    model.DAYS_RECEIVABLE = Param(initialize=DAYS_RECEIVABLE, mutable=True)
    model.N_DEPREC = Param(initialize=N_DEPREC, mutable=True)
    model.T2 = Param(initialize=amortization_period, mutable=True)
    model.COST_OF_DEBT = Param(initialize=cost_debt, mutable=True)
 
    wacc_value = cost_equity * pct_equity + cost_debt * pct_debt
    model.WACC = Param(initialize=wacc_value, mutable=True)
 
    # ------------------ VARIABLES -----------------------
    model.tariff_income = Var(model.T, within=NonNegativeReals)
    model.grants = Var(model.T, within=NonNegativeReals)
    model.lt_subsidies = Var(model.T, within=NonNegativeReals)
    model.revenues = Var(model.T, within=Reals)
 
    model.upstream = Var(model.T, within=NonNegativeReals)
    model.opex = Var(model.T, within=NonNegativeReals)
    model.provisions = Var(model.T, within=NonNegativeReals)
    model.costs = Var(model.T, within=Reals)
 
    model.rab = Var(model.T, within=Reals)
    model.wc = Var(model.T, within=Reals)
    model.dwc = Var(model.T, within=Reals)
    model.treceivables = Var(model.T, within=NonNegativeReals)
    model.tpayables = Var(model.T, within=NonNegativeReals)
    model.da = Var(model.T, within=NonNegativeReals)
    model.taxes = Var(model.T, within=NonNegativeReals)
    model.cum = Var(model.T, within=NonNegativeReals)
 
    model.acofservice = Var(model.T, within=Reals)
 
    model.ebitda = Var(model.T, within=Reals)
    model.ebit = Var(model.T, within=Reals)
    model.ebt = Var(model.T, within=Reals)
    model.financial_expenses = Var(model.T, within=Reals)
 
    model.cash_flow_assets = Var(model.T, within=Reals)
    model.debt = Var(model.T, within=NonNegativeReals)
 
    # -------------- OBJECTIVE FUNCTION -------------------
    def obj_rule(m):
        return sum(m.debt[t] for t in m.T)
    model.obj = Objective(rule=obj_rule, sense=minimize)
 
    # ----------------- CONSTRAINTS ----------------------
 
    def tariff_income_rule(m, t):
        return m.tariff_income[t] == m.K1 * m.capex_data[t]
    model.c_tariff_income = Constraint(model.T, rule=tariff_income_rule)
 
    def grants_rule(m, t):
        if t == first_t or t in realisation_periods:
            return m.grants[t] == m.pct_grants * m.capex_data[t]
        return m.grants[t] == 0
    model.c_grants = Constraint(model.T, rule=grants_rule)
 
    def revenues_rule(m, t):
        return m.tariff_income[t] + m.grants[t] + m.lt_subsidies[t] == m.revenues[t]
    model.c_revenues = Constraint(model.T, rule=revenues_rule)
 
    def lt_subsidies_rule(m, t):
        return m.lt_subsidies[t] <= m.acofservice[t] - m.tariff_income[t]
    model.c_lt_subsidies = Constraint(model.T, rule=lt_subsidies_rule)
 
    # upstream_t = COST_UPSTREAM_t * K2 * capex_t
    def upstream_rule(m, t):
        return m.upstream[t] == m.cost_upstream_data[t] * m.K2 * m.capex_data[t]
    model.c_upstream = Constraint(model.T, rule=upstream_rule)
 
    # opex_t = K2 * capex_t
    def opex_rule(m, t):
        return m.opex[t] == m.K2 * m.capex_data[t]
    model.c_opex = Constraint(model.T, rule=opex_rule)
 
    # provisions_t = NTLOSSES * K1 * capex_t
    def provisions_rule(m, t):
        return m.provisions[t] == m.NTLOSSES * m.K1 * m.capex_data[t]
    model.c_provisions = Constraint(model.T, rule=provisions_rule)
 
    def costs_rule(m, t):
        return m.upstream[t] + m.opex[t] + m.provisions[t] == m.costs[t]
    model.c_costs = Constraint(model.T, rule=costs_rule)
 
    def rab_rule(m, t):
        if t == first_t:
            return m.rab[t] == 0
        return m.rab[t] == m.capex_data[t] - m.da[t] + m.rab[t - 1]
    model.c_rab = Constraint(model.T, rule=rab_rule)
 
    def treceivables_rule(m, t):
        return m.treceivables[t] == m.K1 * m.capex_data[t] * m.DAYS_RECEIVABLE / 365
    model.c_treceivables = Constraint(model.T, rule=treceivables_rule)
 
    def tpayables_rule(m, t):
        return m.tpayables[t] == (m.opex[t] + m.upstream[t]) * m.DAYS_PAYABLE / 365
    model.c_tpayables = Constraint(model.T, rule=tpayables_rule)
 
    def wc_rule(m, t):
        return m.wc[t] == m.treceivables[t] - m.tpayables[t]
    model.c_wc = Constraint(model.T, rule=wc_rule)
 
    def dwc_rule(m, t):
        if t == first_t:
            return m.dwc[t] == 0
        return m.dwc[t] == m.wc[t] - m.wc[t - 1]
    model.c_dwc = Constraint(model.T, rule=dwc_rule)
 
    def da_rule(m, t):
        return m.da[t] == (1 / m.N_DEPREC) * sum(m.capex_data[s] for s in m.T if s <= t)
    model.c_da = Constraint(model.T, rule=da_rule)
 
    def acofservice_rule(m, t):
        return m.acofservice[t] == (
            m.WACC * m.rab[t] + m.upstream[t] + m.opex[t] + m.provisions[t]
            + m.dwc[t] + m.da[t] + m.taxes[t]
        )
    model.c_acofservice = Constraint(model.T, rule=acofservice_rule)
 
    def taxes_rule(m, t):
        if t == first_t:
            return m.taxes[t] == 0
        return m.taxes[t] >= (m.ebt[t] - m.cum[t - 1]) * m.TAXRATE
    model.c_taxes = Constraint(model.T, rule=taxes_rule)

    def cum_rule(m, t):
        if t == first_t:
            return m.cum[t] == 0
        return m.cum[t] >= m.cum[t - 1] - m.ebt[t]
    model.c_cum = Constraint(model.T, rule=cum_rule)
 
    def ebitda_rule(m, t):
        return m.ebitda[t] == m.revenues[t] - m.costs[t]
    model.c_ebitda = Constraint(model.T, rule=ebitda_rule)
 
    def ebit_rule(m, t):
        return m.ebit[t] == m.ebitda[t] - m.da[t]
    model.c_ebit = Constraint(model.T, rule=ebit_rule)
 
    def ebt_rule(m, t):
        return m.ebt[t] == m.ebit[t] - m.financial_expenses[t]
    model.c_ebt = Constraint(model.T, rule=ebt_rule)

    def financial_expenses_rule(m, t):
        return m.financial_expenses[t] == (
            (1 / m.T2) * sum(m.debt[s] for s in m.T if s <= t) * m.COST_OF_DEBT
        )
    model.c_financial_expenses = Constraint(model.T, rule=financial_expenses_rule)
 
    def cash_flow_assets_rule(m, t):
        return m.cash_flow_assets[t] == -(
            m.ebitda[t] - m.taxes[t] - m.dwc[t] - m.capex_data[t]
        )
    model.c_cash_flow_assets = Constraint(model.T, rule=cash_flow_assets_rule)
 
    def debt_rule(m, t):
        return m.debt[t] >= m.cash_flow_assets[t]
    model.c_debt = Constraint(model.T, rule=debt_rule)
 
    return model

# ----------------- HELPER FUNCTIONS ----------------------
def make_capex_data(tech_dict, n_periods):
    grid    = tech_dict.get('GRID',     {}).get('CAPEX - Growth', [])
    offgrid = tech_dict.get('OFF-GRID', {}).get('CAPEX - Growth', [])
    return {t: (grid[t] if t < len(grid) else 0) + (offgrid[t] if t < len(offgrid) else 0)
            for t in range(n_periods)}


def make_k1_k2(tech_dict):
    grid   = tech_dict.get('GRID', {})
    capex  = grid.get('CAPEX - Growth', [])
    demand = grid.get('Demand', [])
    opex   = grid.get('OPEX',   [])
    k1 = [c / d for c, d in zip(capex, demand) if d]
    k2 = [c / o for c, o in zip(capex, opex)   if o]
    return (sum(k1) / len(k1) if k1 else 0.5,
            sum(k2) / len(k2) if k2 else 0.3)