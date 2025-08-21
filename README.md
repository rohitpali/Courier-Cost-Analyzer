# Courier Cost Analyzer

**Automated Courier Invoice Reconciliation, Cost Analysis, and Predictive Insights**

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Key Features](#key-features)
3. [System Architecture](#system-architecture)
4. [Installation & Setup](#installation--setup)
5. [Configuration](#configuration)
6. [Usage — Workflow](#usage---workflow)
7. [Core Modules & File Structure](#core-modules--file-structure)
8. [Visualizations & Reports](#visualizations--reports)
9. [Prediction Engine (ML)](#prediction-engine-ml)
10. [Deployment Guide](#deployment-guide)
11. [Future Enhancements](#future-enhancements)
12. [License & Contact](#license--contact)

---

## Project Overview
**Courier Cost Analyzer** is a Python Flask application that automates the reconciliation of courier invoices against expected charges. It helps finance and operations teams:

Detect overcharges and undercharges
Generate summary tables with counts and amounts
Visualize trends by courier, delivery zone, and weight slab
Forecast courier costs and detect anomalies using ML


## Key Features
- Multi-file upload (Excel/CSV) and merge
- Column standardization and validation
- Row-level reconciliation (Expected vs Billed charges)
- Classification of orders: Correct, Overcharged, Undercharged
- Summary tables and aggregated metrics
- Charts and dashboard visualizations
- Optional ML-based predictions for charges and anomalies
- Exportable reports (CSV/Excel/PDF)


## System Architecture
flowchart TD
    A["Web Application - Flask UI"] --> B["File Upload System"]
    B --> C["Data Processing Engine"]
    C --> D["Summarizer"]
    C --> E["Visualizer"]
    C --> F["Prediction Engine (optional)"]
    G["Auth & User Management"] --> A
    H["Storage: uploads, processed, models, reports"] --> C
    F --> H
    D --> E
    E --> A

## Data Model & Expected Columns
All input columns are case-insensitive and auto-cleaned. If an input file misses required columns, the app will reject it with a descriptive error message.

## Installation & Setup
**Prerequisites**
- Python 3.12+
- Git
- 4GB+ RAM recommended

**Quickstart**
```bash
# clone
git clone <repo-url>
cd courier-cost-analyzer

# create venv
python -m venv .venv
# activate
# windows: .venv\Scripts\activate
# mac/linux: source .venv/bin/activate

pip install -r requirements.txt

# run
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
```

On Windows, set environment variables using `set` or use a `.env` file with `python-dotenv`.


## Configuration
Place application settings in `config/config.py` or use environment variables.

Example `.env` keys (recommended):
```
SECRET_KEY=your_secret_key_here
MODEL_PATH=models/courier_model.pkl
UPLOAD_FOLDER=uploads/
PROCESSED_FOLDER=processed/
REPORTS_FOLDER=reports/
MAX_UPLOAD_SIZE=50MB
```

**Column mappings** are verified in `src/data_processor.py` — edit the mapping if your files use different header names.


## Usage — Workflow
1. Login
2. Upload Excel/CSV files
3. Validate and merge files
4. Run analysis → reconciled results
5. View dashboard: summaries, charts, downloadable reports
6. Optional: Run ML predictions


## Core Modules & File Map
```
.
Courier Cost Analyzer/
├── Simple Analysis/
│   ├── Analysis.ipynb
│   ├── Analysis Overview.pdf
│   ├── sampletest.csv
│   ├── SummaryTable.xlsx
├── static/
│   └── style.css
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── login.html
│   └── signup.html
├── models/
│   └── charge_predictor.pkl
├── instance/
│   ├── database.db
│   ├── result_output.xlsx
├── app.py
├── utils.py
├── models.py
├── requirements.txt
├── README.md
├── Order_Level_Report.csv
├── Courier_Charge_Analysis.xlsx
├── Courier_Charge_Outputs.xlsx
├── P1_Courier_Cost_Analyzer.ipynb
└── venv/
```

## Visualizations & Reports
Typical visualizations produced by `visualizer.py`:
- File-wise order distribution (bar)
- Zone-wise charge analysis (stacked bars or heatmap)
- Overcharge vs Undercharge breakdown (pie / donut)
- Weight-slab based trends (line chart)
- Time-series of monthly billed vs expected (if invoice_date present)

Reports available:
- Order-level reconciliation CSV/Excel
- Summary table CSV/Excel
- Dashboard with embedded charts (exportable to PDF)


## Prediction Engine (ML)
The project ships with an optional prediction engine to:
- Forecast typical courier charges given weight, zone, and courier
- Detect anomalous billed amounts using an isolation-forest or one-class SVM

**Modeling approach**
- Feature engineering: weight, weight_slab, zone, courier, service_type, COD_flag, distance_estimate
- Model candidates: Linear Regression / RandomForestRegressor for forecasting; IsolationForest / LocalOutlierFactor for anomaly detection
- Save models as `models/courier_model.pkl` (use `joblib` or `pickle`)

**predictor.py** exposes two main functions:
- `predict_expected_charge(features_df)` → returns predicted charge
- `detect_anomalies(df)` → returns anomaly scores and flags


## Deployment Guide
**Local (development)**
- Run with Flask built-in server (not for production)


## Future Enhancements
- API endpoints for integration with ERP/CRM systems
- Automated PDF invoice parsing & reconciliation using OCR (Tesseract / commercial OCR)
- Deep-learning-based anomaly detection
- Multi-language dashboard support
- Role-based analytics and scheduled email reports
  
## License
This project is proprietary and confidential. All rights reserved.





