# FinanCCe

FinanCCe is a Streamlit-based application with a Python API backend designed to evaluate and compare financing strategies for previously defined techno-economic plans. The tool supports the analysis of alternative financial structures by allowing users to configure tariffs, capital and debt structures, grants, and other financing mechanisms, and to assess their impacts on overall project viability. While originally centered on electricity-based systems, FinanCCe also enables the definition and evaluation of alternative market fuels such as LPG, ethanol, and advanced cookstoves, allowing consistent comparison across different energy carriers.

FinanCCe enables side-by-side comparison of different financing strategies applied to the same techno-economic configuration, helping users understand trade-offs across cost recovery, capital allocation, and long-term financial performance. The Streamlit frontend provides an interactive user interface, while the backend (served with Uvicorn) handles calculations and supporting services.

-- 

## Key Capabilities

- **Financing strategy evaluation**  
  Analyze multiple financing approaches for a given techno-economic design, including variations in tariffs, grants, equity, and debt structures.

- **Capital structure definition**  
  Configure debt-to-equity ratios, financing terms, and capital allocation assumptions to reflect different investment strategies.

- **Tariff and revenue modeling across energy carriers**  
  Define and compare tariff schemes and revenue mechanisms not only for electricity-based systems, but also for alternative market fuels such as LPG, ethanol, and advanced cookstoves.

- **Multi-fuel market representation**  
  Pivot from electricity-centric analyses to model different fuel markets, enabling the evaluation of financing strategies for diverse energy access and clean cooking solutions.

- **Grant and subsidy analysis**  
  Incorporate grants and other non-repayable funding sources to assess their impact on capital requirements and financial performance.

- **Scenario comparison**  
  Compare alternative financing strategies side by side under consistent techno-economic assumptions.

- **Interactive exploration**  
  Use an intuitive Streamlit interface to explore assumptions, update parameters, and immediately visualize results.

---

## System Prerequisites

Before installing FinanCCe, ensure that the following requirements are met on your system:

- **Python 3.9 or newer**  
  Python must be installed and accessible from the command line.
  You can check your Python version with:

```bash
python --version
```

- **Git** (optional but recommended)  
  Required only if you choose to clone the repository instead of downloading it as a ZIP.

---

## Quickstart

This section describes the fastest ways to get FinanCCe running locally. You can either clone the repository using Git (recommended) or download the source code directly from GitHub.

### Option A: Clone the repository (recommended)

Cloning the repository ensures you can easily pull updates and track changes over time.

```bash
git clone https://github.com/<organization-or-username>/CC-WBT.git
cd CC-WBT
```
### Option B: Download the source code

If you prefer not to use Git, you can download the repository as a ZIP file:

1. Go to the **CC-WBT** GitHub repository.
2. Click **Code → Download ZIP**.
3. Extract the ZIP file to a local directory.
4. Open a terminal and navigate to the extracted folder:

```bash
cd CC-WBT
```

Once the source code is available locally (via cloning or download), you can proceed with environment setup and installation.

---

## Installation

### 1) Create a virtual environment

It is strongly recommended to install FinanCCe inside a virtual environment to avoid dependency conflicts.

From the project root directory (`CC-WBT`), run:

```bash
python -m venv venv
```

Activate the virtual environment:

**Windows (PowerShell):**
```bash
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```bash
.\venv\Scripts\activate.bat
```

***macOS / Linux:**
```bash
source venv/bin/activate
```

Once activated, your terminal prompt should indicate that the venv environment is active.

### 2) Install dependencies

With the virtual environment activated, install the required Python packages:

```bash
pip install -r requirements.txt
```

This will install all dependencies needed to run both the backend API and the Streamlit frontend.

## Running the Application

Running FinanCCe requires **two terminals** to be open at the same time:
- one for the backend API (Uvicorn), and
- one for the Streamlit frontend.

Make sure the virtual environment is activated in **both** terminals.

---

### Terminal 1: Start the backend API

From the project root directory, run:

```bash
cd backend
uvicorn main:app --reload --port 8001
```

This will start the backend service on `http://localhost:8001`.  
Keep this terminal open while using the application.

---

### Terminal 2: Start the Streamlit frontend

Open a second terminal, activate the virtual environment, and run:

```bash
cd frontend
streamlit run app.py --server.port 8501
```

Streamlit will automatically open your default web browser at http://localhost:8501

---

## First-Time User Walkthrough

When the Streamlit interface opens in your browser:

1. **Cover screen**  
   The application opens on a cover screen. Click **Select scenario** to enter the main application.

2. **Select or create a country/context**  
   Choose one of the previously created countries/contexts from the selector, or create a new one.  
   When creating a new country, you will be prompted to define: **country name**, **corporate tax rate**, and **estimated inflation rate**.

3. **Start modeling**  
   Once a country has been selected or created, click **Start modeling** to proceed to the main modeling interface.

4. **Application layout and navigation**

   Once the modeling interface loads, the application is organized into two main areas:

   - **Left navigation bar**  
     The left sidebar is used to navigate across the different sections of the application. From here, you can:
     - go back to country selection,
     - access financial inputs,
     - manage techno-economic models, and
     - navigate to output sections.

   - **Central workspace**  
     The central window is the main working area of the application. Depending on the selected section from the left navigation bar, this area is used to:
     - input and edit techno-economic or financial data, or
     - visualize results, summaries, and outputs generated by the model.  

5. **Define techno-economic inputs**

   After entering the modeling interface, you can define and manage the techno-economic inputs associated with the selected country.

   - **Set the year range**  
     First, define the modeling year range.If you attempt to change the year range after inputs have already been defined, the application will prompt you with a confirmation message to ensure that existing inputs are ready to be updated or reset.

   - **Manage existing techno-economic models**  
     Any previously created or loaded techno-economic models will appear in the list. For each model, you can:
     - **Download current inputs** as Excel files,
     - **Download an Excel template** to populate inputs offline and upload them back into the application,
     - **Upload template inputs** from Excel files, or
     - **Delete the model** if it is no longer needed.

   - **Create a new techno-economic model**  
     To define a new model, provide a **model name** and click **Create**.  
     The new model will then be available for input definition, editing, and comparison.

   This workflow allows users to either define inputs directly through the interface or manage them efficiently using Excel-based templates, while maintaining consistency across modeling years and scenarios.

6. **Define financing assumptions (common across strategies)**

   After (or before) creating the techno-economic models, you can configure the **financing assumptions**. These assumptions are **common to all techno-economic models** and are managed through the **left navigation bar** under *Financial Inputs*.

   Financing inputs are organized by market and revenue stream, and are defined over the selected modeling year range.

   - **Electricity financial inputs**  
     When selecting *Electricity* from the left navigation bar, the central workspace displays a table where you can define electricity-related financial parameters, including:
     - expected **non-technical losses**,
     - **trade receivables** (days of revenues),
     - **trade payables** (days of OPEX costs).

     These parameters are specified on a yearly basis and apply consistently across all financing strategies.

   - **Fuel market financial inputs (e.g. LPG, ethanol, advanced cookstoves)**  
     Additional fuel markets can be selected from the left navigation bar or created using the *Add new fuel market* option. For each fuel market, the user can define the corresponding financial assumptions in a similar year-by-year format. Fuel markets can also be removed if they are no longer part of the analysis.

   - **Carbon credits financial inputs**  
     Selecting *Carbon Credits Financial Inputs* allows you to define assumptions related to carbon revenues, including:
     - the share of **CO₂ certified** from total avoided emissions,
     - **liquidity** assumptions,
     - **price per ton of CO₂**, and
     - the **number of years** during which

7. **Configure a techno-economic model**

   When selecting a techno-economic model from the **Manage Techno-Economic Models** menu, the application opens a dedicated configuration panel in the **left navigation bar**. This panel contains all inputs required to define the selected techno-economic model in detail.

   The inputs are grouped into sections that should typically be completed in the order shown below.

   **7.1 Techno-Economic Inputs**

   This section defines the **explicit techno-economic inputs** of the selected model. Values entered here are provided directly by the user and are **not derived from other inputs**.

   For electricity-based systems, inputs may be defined as:
   - **Electricity (low access)**, and
   - **Electricity & E-Cooking**, where electricity demand is extended to explicitly account for e-cooking use.

   Depending on the modeling context, additional fuel types (e.g. LPG, ethanol, advanced cookstoves) may also appear and follow the same input structure.

   Inputs are specified over the selected year range and include demand, capital expenditures (CAPEX), operating expenditures (OPEX), asset lifetimes, and commercial parameters such as losses and working-capital assumptions.

   The **Save** and **Reset** buttons indicate that these values are treated as **explicit modeling assumptions**.  
   - **Save** stores the user-defined inputs for use in subsequent calculations.  
   - **Reset** restores default values.

   **7.2 Prices and Upstream Energy Costs**

   This section defines both **tariffs (revenues)** and **upstream energy costs (inputs)** for the selected techno-economic model. Configuration is performed **separately for each market fuel** (e.g. electricity, LPG, ethanol).

   For each fuel, prices and costs can be defined using one of two methods:
   - **Initial value + inflation**  
     An initial price or cost is specified and automatically projected forward using the country-level inflation rate.
   - **Annual values**  
     Prices or costs are entered explicitly for each year of the modeling period.

   This unified approach ensures a consistent treatment of revenue and cost trajectories across fuels and simplifies scenario comparison. All values defined in this section are treated as **explicit user inputs** and are applied consistently across all financing strategies associated with the model.

   **7.3 CAPEX Fuel Market**

   This section displays the **capital expenditures associated with each fuel market**.  
   Unlike previous sections, the values shown here are **derived inputs** and **cannot be edited directly by the user**.

   CAPEX is automatically computed based on the techno-economic inputs and configuration defined in earlier sections. The central workspace presents year-by-year capital trajectories, including growth CAPEX, accumulated CAPEX, depreciation, and regulated asset base (RAB) metrics.

   For electricity-based systems, the application distinguishes between:
   - **Electricity (low access)**, and
   - **Electricity & E-Cooking**, where the additional capital requirements associated with e-cooking are explicitly accounted for.

   Similar CAPEX views are available for other fuel markets (e.g. LPG) when they are included in the model.

   The absence of *Save* and *Reset* controls indicates that values in this section are **computed outputs**, provided for transparency and interpretation rather than direct input.

   **7.5 Design Capital Structure**

   This section defines the **financing structure** applied to the selected techno-economic model and is completed **separately for each market fuel** (e.g. Electricity & E-Cooking, Electricity (Low access), LPG).

   The section combines **explicit user inputs** with **calculated financial outputs**, allowing users to both define financing assumptions and immediately evaluate their implications.

   **7.5.1 Financial Plan (Inputs)**

   Users specify the capital structure parameters, including:
   - **Equity share** and **cost of equity**,
   - **Grants share**, and
   - **Debt parameters**, including cost of debt, grace period, and amortization period.

   **7.5.2 Financial Structure Support Scheme (FFSS)**

   Based on the defined capital structure, the application computes intermediate financing requirements, such as:
   - calculated debt needs, and
   - required debt variation over time.

   Users may optionally override calculated debt increases by providing **user-defined debt adjustments**, enabling scenario testing while maintaining consistency with the overall financing logic.

   **7.5.3 Calculated Financial Tables**

   Once inputs are defined, clicking **Calculate Financial Tables** generates the resulting financial outputs, including:
   - total financing requirements,
   - allocation between equity, grants, and debt, and
   - weighted average cost of capital (WACC),

   displayed separately for each system configuration.

   This section links techno-economic design and financing assumptions, providing a transparent view of how capital structure choices translate into financial outcomes.

8. **Model outputs**

   After defining the techno-economic inputs and capital structure, FinanCCe generates a set of **financial outputs** that summarize the economic performance of the selected model. Outputs are accessed from the **Outputs** section in the left navigation bar and are shown **separately for each market fuel** (e.g. Electricity & E-Cooking, Electricity (Low access), LPG).

   **8.1 Financial Statements**

   This section presents the core financial statements derived from the model assumptions and financing structure: **Profit & Loss (P&L)**, **Balance Sheet**, and **Cash Flow Statement**.  

   These statements provide a consistent accounting view of project performance across the modeling horizon.

   **8.2 Capital and Asset Tracking**

   Additional tables detail how capital and assets evolve over time, including: **PP&E (Property, Plant & Equipment)**, **Working capital calculations** and **Equity schedules**

   **8.3 Capital Structure and Financing Breakdown**

   This section summarizes how the project is financed, including: total financing requirements, allocation between **equity, grants, and debt**, grant realization over time, and debt balances, repayments, and financial expenses.

   Key indicators such as **WACC** and financing shares are shown to support comparison across alternative financing strategies.

   Together, these outputs provide a transparent and structured view of how techno-economic assumptions and financing choices translate into financial performance, supporting informed comparison of alternative strategies.

9. **Carbon credits**

   This section provides an **independent carbon credit calculation**, separate from the financial statements and capital structure modules. It is accessed from the **Carbon Credits** entry in the left navigation bar.

   **9.1 Input emissions**

   Users define annual **CO₂ emissions** (in CO₂eq) for different scenarios, including: a **baseline scenario**, and alternative scenarios for each techno-economic model. These inputs are entered explicitly by the user.

   **9.2 Carbon credit calculation**

   By clicking **Calculate Carbon Credits**, the application computes the avoided emissions relative to the baseline, differences between techno-economic models and baseline, CO₂-equivalent avoided emissions, and the **potential income from carbon credits**, based on the defined carbon credit assumptions.

   Results are displayed year by year and are not automatically fed into the core financial statements.

   This modular design allows users to explore carbon impacts and potential revenues independently from the main financing analysis.

10. **Summary financing dashboard**

    The **Summary Financing** dashboard provides a high-level visual overview of the financing outcomes for the modeled strategies. It aggregates results across all configured sectors and scenarios, allowing users to quickly compare how different design and financing choices affect overall funding structure and balance.

    This view is intended for synthesis and comparison, supporting decision-making at a glance without requiring detailed inspection of individual financial tables.

**All input and output tables are also exported as Excel files and stored in the `backend/{country_name}` folder.**

---

## Stopping the Application

To stop FinanCCe, press `Ctrl + C` in **both terminals**.
