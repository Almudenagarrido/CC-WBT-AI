# CC-WBT-AI

CC-WBT-AI is an AI-powered lab for financial planning analysis of clean cooking electrification projects. Built on top of the CC-WBT computation engine, it enables sensitivity analysis and Monte Carlo simulation of key financial parameters — helping energy planners and researchers understand the drivers of project viability and explore optimal financing structures.

---

## What is this?

Energy planners working on clean cooking transitions need to answer questions like: how sensitive is the required subsidy to the cost of debt? what happens to cash flow if tariffs grow 15% slower than expected? what financing structure minimises the public subsidy while keeping the project solvent?

CC-WBT-AI addresses these questions by running the CC-WBT financial engine programmatically — varying input parameters, executing the computation, and analysing outputs — without going through the web interface.

---

## Key Capabilities

- **Sensitivity analysis** — vary one parameter at a time and observe the impact on financial outputs
- **Monte Carlo simulation** — jointly sample uncertain parameters and obtain distributions of financial outcomes
- **Direct engine access** — calls the CC-WBT computation engine directly, no API or frontend required
- **Project finance metrics** — tracks Long-Term Subsidies, Cash Flow, DSCR and WACC across scenarios

---

## Repository Structure

```
CC-WBT-AI/
  backend/         # CC-WBT computation engine and Rwanda scenario data
  frontend/        # CC-WBT web interface (Streamlit)
  notebooks/       # AI lab — sensitivity analysis and Monte Carlo
  requirements.txt
```

---

## Getting Started

### 1) Clone the repository

```bash
git clone https://github.com/Almudenagarrido/CC-WBT-AI.git
cd CC-WBT-AI
```

### 2) Create and activate a virtual environment

```bash
python -m venv venv
```

**Windows (Command Prompt):**
```bash
.\venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
source venv/bin/activate
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

---

## Running the Platform (optional)

The CC-WBT web interface can be launched independently. Open two terminals with the virtual environment activated:

**Terminal 1 — backend:**
```bash
cd backend
uvicorn main:app --reload --port 8001
```

**Terminal 2 — frontend:**
```bash
cd frontend
streamlit run app.py --server.port 8501
```

The platform will be available at `http://localhost:8501`.

---

## AI Lab

The `notebooks/` folder is the core of this repository. It contains Jupyter notebooks for:

- Exploring the CC-WBT computation engine directly
- Running sensitivity analysis on capital structure parameters
- Monte Carlo simulation of financial outcomes under uncertainty

> **Note:** The AI lab is under active development. Usage guides and detailed documentation will be added as the project evolves.

---

## Acknowledgments

CC-WBT-AI builds on [CC-WBT](https://github.com/SEforALL-IEAP/CC-WBT), developed by researchers at the [Instituto de Investigación Tecnológica](https://www.iit.comillas.edu/). Key contributors include [Almudena Garrido](https://www.linkedin.com/in/almudena-garridogp), [Santos Diaz](https://www.linkedin.com/in/santos-diazpastor), and [Pablo Duenas](https://www.linkedin.com/in/pablo-duenas-martinez).

This work has been developed in collaboration with [Sustainable Energy for All (SE4All)](https://www.seforall.org/).