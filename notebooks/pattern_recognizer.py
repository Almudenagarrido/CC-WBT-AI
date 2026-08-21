import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split


# 1. SYNTHETIC DATA GENERATOR
def generate_dataset(n_samples=5000, seed=42):
    np.random.seed(seed)
    n_years = 12

    X, y = [], []

    for _ in range(n_samples):
        lts          = np.random.uniform(-60, 5,   n_years)
        debt_eop     = np.random.uniform(0,   200, n_years)
        ocf          = np.random.uniform(-50, 700, n_years)
        equity_eop   = np.random.uniform(0,   5000, n_years)
        n_iterations = np.random.randint(1, 30)

        features = [
            float(np.mean(lts)),
            float(np.min(lts)),
            float(np.sum(lts < -10)),
            float(np.mean(debt_eop)),
            float(np.max(debt_eop)),
            float(np.sum(debt_eop > 0)),
            float(np.mean(ocf)),
            float(np.mean(equity_eop)),
            float(n_iterations),
        ]

        label_subsidy  = 1 if np.mean(lts) < -15 and np.sum(lts < -10) > 6 else 0
        label_fragile  = 1 if np.max(debt_eop) > 50 and np.sum(debt_eop > 0) > 6 else 0
        label_circular = 1 if n_iterations > 15 else 0

        X.append(features)
        y.append([label_subsidy, label_fragile, label_circular])

    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)


# 2. NEURAL NETWORK
class PatternRecognizer(nn.Module):
    def __init__(self, input_dim=9, hidden_dim=32, n_labels=3):
        super().__init__()
        self.bn = nn.BatchNorm1d(input_dim)
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, n_labels),
            nn.Sigmoid(),
        )

    def forward(self, x):
        return self.net(self.bn(x))


# 3. TRAINING
def train(n_samples=5000, epochs=50, batch_size=64, lr=1e-3):
    X, y = generate_dataset(n_samples)
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    train_loader = DataLoader(TensorDataset(torch.tensor(X_train), torch.tensor(y_train)), batch_size=batch_size, shuffle=True)

    model   = PatternRecognizer()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.BCELoss()

    for epoch in range(epochs):
        model.train()
        for xb, yb in train_loader:
            optimizer.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            optimizer.step()

        if (epoch + 1) % 10 == 0:
            model.eval()
            with torch.no_grad():
                val_loss = criterion(model(torch.tensor(X_val)), torch.tensor(y_val))
            print(f"Epoch {epoch+1}/{epochs} — val loss: {val_loss:.4f}")

    return model


# 4. INFERENCE
LABELS = ['subsidy_dependent', 'fragile_structure', 'high_circularity']

def predict(model, lts, debt_eop, ocf, equity_eop, n_iterations):
    features = [
        float(np.mean(lts)),
        float(np.min(lts)),
        float(np.sum(np.array(lts) < -10)),
        float(np.mean(debt_eop)),
        float(np.max(debt_eop)),
        float(np.sum(np.array(debt_eop) > 0)),
        float(np.mean(ocf)),
        float(np.mean(equity_eop)),
        float(n_iterations),
    ]
    x = torch.tensor([features], dtype=torch.float32)
    with torch.no_grad():
        probs = model(x).squeeze().numpy()
    return {label: round(float(p), 3) for label, p in zip(LABELS, probs)}