# CC-WBT — Country-Configurable Web-Based Tool

CC-WBT is an open-source web-based platform for financial viability analysis of clean cooking electrification projects. Built on a declarative computation engine, it automates multi-scenario financial modelling across countries, techno-economic models and fuel markets — replacing manual Excel workflows with auditable, reproducible financial statements.

Developed in collaboration with the IIT (Comillas) and SE4All, CC-WBT has been validated against Rwanda's National Integrated Clean Cooking Plan and is actively used for financial planning across multiple countries.

---

## Key Capabilities

- **Financing strategy evaluation**  
  Analyze multiple financing approaches for a given techno-economic design, including variations in tariffs, grants, equity, and debt structures.

- **Capital structure definition**  
  Configure debt-to-equity ratios, financing terms, and capital allocation assumptions to reflect different investment strategies.

- **Tariff and revenue modeling across energy carriers**  
  Define and compare tariff schemes and revenue mechanisms for electricity-based systems and alternative market fuels such as LPG, ethanol, and advanced cookstoves.

- **Multi-fuel market representation**  
  Model different fuel markets and evaluate financing strategies for diverse energy access and clean cooking solutions.

- **Grant and subsidy analysis**  
  Incorporate grants and other non-repayable funding sources to assess their impact on capital requirements and financial performance.

- **Scenario comparison**  
  Compare alternative financing strategies side by side under consistent techno-economic assumptions.

- **Interactive exploration**  
  Use an intuitive Streamlit interface to explore assumptions, update parameters, and immediately visualize results.

---

## System Prerequisites

- **Python 3.9 or newer**
- **Git** (optional but recommended)

---

## Quickstart

### Option A: Clone the repository (recommended)

```bash
git clone https://github.com/SEforALL-IEAP/CC-WBT-AI.git
cd CC-WBT-AI
```

### Option B: Download the source code

1. Click **Code → Download ZIP** on the repository page.
2. Extract and navigate to the folder.

---

## Installation

### 1) Create a virtual environment

```bash
python -m venv venv
```

Activate:

**Windows (PowerShell):**
```bash
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```bash
.\venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
source venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

---

## Running the Application

Running CC-WBT requires **two terminals** open simultaneously.

### Terminal 1: Start the backend API

```bash
cd backend
uvicorn main:app --reload --port 8001
```

### Terminal 2: Start the Streamlit frontend

```bash
cd frontend
streamlit run app.py --server.port 8501
```

The application will open at `http://localhost:8501`.

To stop, press `Ctrl + C` in both terminals.

---

## User Guide

A brief walkthrough of the platform — from country setup to financial outputs — is available on request. For a quick overview of the full workflow, refer to the demo video in the repository.

---

## AI Lab

The `notebooks/` folder contains an exploratory AI lab for sensitivity analysis and Monte Carlo simulation of financial planning parameters, built directly on top of the CC-WBT computation engine.

---

## Acknowledgments

CC-WBT has been developed by researchers at the [Instituto de Investigación Tecnológica](https://www.iit.comillas.edu/). Key contributors include [Almudena Garrido](https://www.linkedin.com/in/almudena-garridogp), [Santos Diaz](https://www.linkedin.com/in/santos-diazpastor), and [Pablo Duenas](https://www.linkedin.com/in/pablo-duenas-martinez).

CC-WBT has also benefited from the support and collaboration of [Sustainable Energy for All (SE4All)](https://www.seforall.org/), whose engagement has been instrumental in the development of this work.