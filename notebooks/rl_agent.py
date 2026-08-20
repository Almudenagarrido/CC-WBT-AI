import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

# ── Constants ────────────────────────────────────────────────────────────────────
PARAM_KEYS = [
    'pct_equity', 'pct_grants', 'cost_equity', 'cost_debt',
    'years_realisation', 'grace_period', 'amortization_period',
]

PARAM_SCALE = {
    'pct_equity':          (0.0, 1.0),
    'pct_grants':          (0.0, 1.0),
    'cost_equity':         (0.0, 0.3),
    'cost_debt':           (0.0, 0.2),
    'years_realisation':   (1,   15),
    'grace_period':        (0,   5),
    'amortization_period': (5,   30),
}

MAX_SHIFT = 0.2
MAX_SCALE = 0.3


# ── State encoding ───────────────────────────────────────────────────────────────
def normalize_params(params: dict) -> list:
    result = []
    for key in PARAM_KEYS:
        val = params.get(key, 0)
        lo, hi = PARAM_SCALE[key]
        result.append((val - lo) / (hi - lo + 1e-8))
    return result


def encode_state(best_params, best_obj, pattern_labels, iteration, max_iter=10):
    """
    State vector (12 features):
        7 normalized params + 1 objective + 3 pattern labels + 1 iteration
    """
    param_vec = normalize_params(best_params)
    obj_norm  = min(best_obj, 1.0)
    labels    = list(pattern_labels.values())
    iter_norm = iteration / max_iter
    features  = param_vec + [obj_norm] + labels + [iter_norm]
    return torch.tensor(features, dtype=torch.float32).unsqueeze(0)


# ── Policy network ───────────────────────────────────────────────────────────────
class RLAgent(nn.Module):
    """
    Takes state (12 features) and outputs adjustments to search range
    centers and widths for each of the 7 params.
    Output: (shift, scale) per param, both in [-1, 1].
    """
    def __init__(self, state_dim=12, hidden_dim=64, n_params=7):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, n_params * 2), nn.Tanh(),
        )
        self.n_params = n_params

    def forward(self, x):
        return self.net(x).view(-1, self.n_params, 2)


# ── Range adjustment ─────────────────────────────────────────────────────────────
def adjust_ranges(action, current_ranges):
    """Apply agent's action to SEARCH_RANGES."""
    action_np  = action.squeeze(0).detach().numpy()
    new_ranges = {}

    for i, key in enumerate(PARAM_KEYS):
        lo, hi     = current_ranges[key]
        width      = hi - lo
        center     = (lo + hi) / 2

        shift      = action_np[i, 0] * MAX_SHIFT * width
        scale      = 1.0 + action_np[i, 1] * MAX_SCALE

        new_center = center + shift
        new_width  = max(width * scale, (PARAM_SCALE[key][1] - PARAM_SCALE[key][0]) * 0.05)

        new_lo = max(new_center - new_width / 2, PARAM_SCALE[key][0])
        new_hi = min(new_center + new_width / 2, PARAM_SCALE[key][1])

        if key in ('years_realisation', 'grace_period', 'amortization_period'):
            new_ranges[key] = (int(round(new_lo)), max(int(round(new_hi)), int(round(new_lo)) + 1))
        else:
            new_ranges[key] = (round(new_lo, 4), round(new_hi, 4))

    return new_ranges


# ── REINFORCE update ─────────────────────────────────────────────────────────────
def update_policy(agent, optimizer, log_prob, reward):
    loss = -log_prob * reward
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    return loss.item()


# ── Main RL loop ─────────────────────────────────────────────────────────────────
def run_rl_optimization(
    tech_dict, tax_rate, years, initial_ranges,
    pattern_model,
    fuel_fin=None, fuel_key='Electricity',
    objective='debt',
    n_rounds=5, n_trials_per_round=50,
    lr=1e-3,
):
    from optimizer import run_optimization
    from pattern_recognizer import LABELS

    agent      = RLAgent()
    optimizer_ = optim.Adam(agent.parameters(), lr=lr)

    ranges       = dict(initial_ranges)
    best_overall = None
    best_obj     = float('inf')
    history      = []

    for round_idx in range(n_rounds):
        print(f"\n── RL Round {round_idx + 1}/{n_rounds} ──")

        # Step 1: run optuna with current ranges
        result = run_optimization(
            tech_dict=tech_dict, tax_rate=tax_rate, years=years,
            search_ranges=ranges, fuel_fin=fuel_fin, fuel_key=fuel_key,
            objective=objective, n_trials=n_trials_per_round,
        )

        # objective proxy: pct_debt (lower = better)
        pct_debt = 1 - result['PCT_EQUITY'] / 100 - result['PCT_GRANTS'] / 100
        obj_val  = max(pct_debt, 0.0)

        # Step 2: pattern labels (dummy until pipeline is wired in layer 3)
        pattern_labels = {label: 0.5 for label in LABELS}

        # Step 3: encode state
        best_params_norm = {
            'pct_equity':          result['PCT_EQUITY'] / 100,
            'pct_grants':          result['PCT_GRANTS'] / 100,
            'cost_equity':         result['COST_OF_EQUITY'] / 100,
            'cost_debt':           result['COST_OF_DEBT'] / 100,
            'years_realisation':   result['YEARS_REALISATION'],
            'grace_period':        result['GRACE_PERIOD'],
            'amortization_period': result['AMORTIZATION'],
        }
        state = encode_state(best_params_norm, obj_val, pattern_labels, round_idx, n_rounds)

        # Step 4: agent action + exploration noise
        action_mean = agent(state)
        dist        = torch.distributions.Normal(action_mean, 0.1)
        action      = dist.sample()
        log_prob    = dist.log_prob(action).sum()

        # Step 5: reward = improvement
        reward = best_obj - obj_val
        if obj_val < best_obj:
            best_obj     = obj_val
            best_overall = result

        # Step 6: update policy
        loss = update_policy(agent, optimizer_, log_prob, reward)

        # Step 7: adjust ranges for next round
        ranges = adjust_ranges(action, ranges)

        history.append({'round': round_idx + 1, 'obj': obj_val, 'reward': reward})
        print(f"  pct_debt={obj_val:.3f}  reward={reward:.4f}  loss={loss:.4f}")
        print(f"  → {result}")

    print(f"\n✓ RL done — best pct_debt: {best_obj:.3f}")
    return best_overall, history