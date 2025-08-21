# Courier Cost Analyzer

**Automated courier invoice reconciliation, cost analysis, and predictive insights**

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Key Features](#key-features)
3. [System Architecture](#system-architecture)
   - High-level diagram
   - Component descriptions
4. [Data Model & Expected Columns](#data-model--expected-columns)
5. [Installation & Setup](#installation--setup)
6. [Configuration](#configuration)
7. [Usage — Workflow](#usage---workflow)
8. [Core Modules & File Map](#core-modules--file-map)
9. [Processing Rules & Business Logic](#processing-rules--business-logic)
10. [Visualizations & Reports](#visualizations--reports)
11. [Prediction Engine (ML)](#prediction-engine-ml)
12. [Error Handling & Logging](#error-handling--logging)
13. [Security Considerations](#security-considerations)
14. [Performance & Scalability](#performance--scalability)
15. [Testing & QA](#testing--qa)
16. [Deployment Guide](#deployment-guide)
17. [Maintenance & Re-training](#maintenance--re-training)
18. [Future Enhancements](#future-enhancements)
19. [License & Contact](#license--contact)

---

## Project Overview
**Courier Cost Analyzer** is a Python-based web application (Flask) that automates reconciliation of courier invoices against expected internal charge calculations. It helps operations and finance teams detect overcharges and undercharges, generate summaries, visualize trends (zonewise/weightslab/filewise), and provide ML-powered forecasts and anomaly detection.

The application is optimized for batch uploads of Excel/CSV files, robust preprocessing, and transparent reporting so teams can reconcile invoices faster and with fewer errors.


## Key Features
- Multi-file upload (Excel / CSV) and merging
- Column standardization and input validation (case-insensitive mapping)
- Row-level reconciliation: `Expected Charge` vs `Billed Charge`
- Classification of orders: Correctly charged, Overcharged, Undercharged
- Summary tables with counts & aggregated amounts
- Rich visualizations: zone-wise, weight-slab trends, over/undercharge breakdown
- ML-based prediction engine for forecasting courier costs and detecting anomalies
- Role-based access control, secure authentication
- Exportable reports (CSV/Excel/PDF)


## System Architecture

### High-level diagram (Mermaid)

```mermaid
flowchart TD
  A[Web Application (Flask UI)] --> B[File Upload System]
  B --> C[Data Processing Engine]
  C --> D[Summarizer]
  C --> E[Visualizer]
  C --> F[Prediction Engine (optional)]
  G[Auth & User Management] --> A
  H[Storage: /uploads, /processed, /models, /reports] --> C
  F --> H
  D --> E
  E --> A
  subgraph Users
    U1[Ops User]
    U2[Finance User]
    U3[Management]
  end
  U1 --> A
  U2 --> A
  U3 --> A
```

**Component descriptions**
- **Web Application (Flask UI)**: Frontend endpoints for login, file upload, dashboard, reports, and model settings.
- **File Upload System**: Handles multiple file selection, sanitization, and initial parsing (CSV & Excel). Stores raw uploads in a quarantine area.
- **Data Processing Engine**: Cleans data, normalizes column names, merges multiple files into a unified dataframe, applies business rules, computes `difference = billed - expected` and tags rows.
- **Summarizer**: Produces summary tables such as counts and amounts for correctly charged / overcharged / undercharged orders.
- **Visualizer**: Generates charts for dashboards and downloadable images via Matplotlib (or Plotly on the frontend).
- **Prediction Engine**: Optional component to load pre-trained models for forecasting costs and detecting anomalies. Uses scikit-learn for classical models; extendable to deep learning.
- **Auth & User Management**: Role-based access: Admin, Finance, Ops, Viewer. Passwords hashed; sessions managed securely.
- **Storage**: Organized file storage for raw, processed, models, and generated reports.


## Data Model & Expected Columns
All input columns are case-insensitive and auto-cleaned. If an input file misses required columns, the app will reject it with a descriptive error message.

**Required / Recommended columns**
- `order_id` (string)
- `awb_number` (string)
- `total_weight_as_per_x_kg` (float)
- `weight_slab_as_per_x_kg` (string/label)
- `total_weight_as_per_courier_kg` (float)
- `weight_slab_charged_by_courier_kg` (string/label)
- `delivery_zone_as_per_x` (string)
- `delivery_zone_charged_by_courier` (string)
- `expected_charge_as_per_x_rs` (float)
- `charges_billed_by_courier_rs` (float)
- `invoice_date` (date) — optional but recommended
- `courier_name` (string) — optional but recommended

The processor will create these additional columns:
- `difference_rs` = `charges_billed_by_courier_rs` - `expected_charge_as_per_x_rs`
- `reconciliation_status` = [`Correct`, `Overcharged`, `Undercharged`]
- `overcharge_amount_rs` (if overcharged)
- `undercharge_amount_rs` (if undercharged)


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
1. Login (or use demo account)
2. Navigate to Upload page
3. Select multiple Excel/CSV files and Submit
4. System validates and parses files; displays preview
5. Click `Run Analysis` to merge and reconcile
6. View results on dashboard: summaries, charts, downloadable CSV/Excel
7. (Optional) Run `Predict` to get forecasting and anomaly detection


## Core Modules & File Map
```
.
├── config/
│   ├── config.py
│   └── path_config.py
├── src/
│   ├── app_routes.py  # flask routes
│   ├── data_processor.py  # read/clean/merge
│   ├── summarizer.py  # generate summary tables
│   ├── predictor.py  # ML wrapper
│   ├── visualizer.py  # create charts
│   └── utils.py  # helpers: logging, file io, mapping
├── templates/
│   ├── dashboard.html
│   └── login.html
├── static/  # css/js/images
├── models/  # saved ML models
├── uploads/  # raw uploads
├── processed/  # processed csv/xlsx
├── reports/  # generated reports
├── app.py
├── requirements.txt
└── README.md
```


## Processing Rules & Business Logic
- **Column normalization**: headers are stripped, lowercased, and non-alphanumeric replaced with underscores.
- **Type casting**: weights and charges are coerced to numeric; non-convertible rows flagged for manual review.
- **Merging**: files merged on `order_id`/`awb_number` (preferred) — fallback to concatenation if no common key present.
- **Reconciliation**:
  - `difference_rs = charges_billed_by_courier_rs - expected_charge_as_per_x_rs`
  - If `abs(difference_rs) < tolerance` → `Correct` (tolerance configurable, default ₹1)
  - If `difference_rs > tolerance` → `Overcharged`
  - If `difference_rs < -tolerance` → `Undercharged`
- **Aggregation**: summary tables by file, by courier, by delivery zone, and by weight slab.
- **Business rule hooks**: `rules.py` (or a DB table) can define special-case logic (free pickup, extra COD fee, insurance, etc.).


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


## Error Handling & Logging
- Centralized logger in `src/utils.py` using Python `logging` module; logs saved to `/logs/
- Input validation errors return human-friendly messages and recommend corrective actions
- Files failing parse are quarantined with a CSV containing `row_number` and `error_reason`
- Try/Except blocks around critical I/O and model loading with graceful fallbacks


## Security Considerations
- Passwords hashed with `bcrypt` or `argon2`
- File uploads sanitized and stored outside webroot
- No sensitive data (PII) written to logs
- Rate-limiting and session timeout for multi-user deployment
- HTTPS enforcement in production


## Performance & Scalability
- Efficient merges using chunked Pandas reads for very large files
- Caching of intermediate aggregated results to speed up dashboard re-renders
- Offload ML model scoring to worker processes for large batches (Celery/RQ)
- Consider using a relational DB (Postgres) or data warehouse for heavy usage


## Testing & QA
- Unit tests for `data_processor`, `summarizer`, and `predictor` using `pytest`
- Test fixtures for sample CSV/Excel input
- Integration tests for end-to-end flow: upload → process → visualize
- CI pipeline: linting (flake8), unit tests, build checks


## Deployment Guide
**Local (development)**
- Run with Flask built-in server (not for production)

**Production (example with Gunicorn + Nginx)**
1. Create virtualenv and install requirements
2. Configure environment variables and file paths
3. Use Gunicorn to serve Flask app: `gunicorn -w 4 -b 0.0.0.0:8000 app:app`
4. Nginx as reverse proxy for SSL termination and static file serving
5. Use systemd unit file for service management
6. Configure periodic backups of `uploads/`, `processed/`, and `models/`


## Maintenance & Re-training
- Retrain prediction models periodically (monthly/quarterly) or whenever courier rate structure changes
- Keep a changelog of rate updates and retraining metadata
- Monitor model drift via held-out validation sets and A/B checks


## Future Enhancements
- API endpoints for integration with ERP/CRM systems
- Automated PDF invoice parsing & reconciliation using OCR (Tesseract / commercial OCR)
- Deep-learning-based anomaly detection
- Multi-language dashboard support
- Role-based analytics and scheduled email reports


## Example: Reconciliation Logic (Pseudo)
```python
# simplified
expected = df['expected_charge_as_per_x_rs'].astype(float)
billed = df['charges_billed_by_courier_rs'].astype(float)
diff = billed - expected
tolerance = config.TOLERANCE_RUPEES # e.g. 1.0

status = np.where(np.abs(diff) <= tolerance, 'Correct', np.where(diff > tolerance, 'Overcharged','Undercharged'))

df['difference_rs'] = diff
df['reconciliation_status'] = status
```


## Project Structure Diagram (detailed)

```mermaid
flowchart LR
  subgraph Frontend
    UI[Flask Templates / JS] --> UploadEndpoint[/upload]
    UI --> DashboardEndpoint[/dashboard]
  end
  subgraph Backend
    UploadEndpoint --> UploadHandler[src/data_processor.py]
    UploadHandler --> QuarantineStore[uploads/quarantine]
    UploadHandler --> Cleaner[DataCleaner]
    Cleaner --> Merger[Merger]
    Merger --> Reconciler[src/summarizer.py]
    Reconciler --> Summaries[summary CSV/XLSX]
    Reconciler --> VisualGenerator[src/visualizer.py]
    VisualGenerator --> ReportStore[reports/]
    Merger --> Predictor[src/predictor.py]
    Predictor --> ModelStore[models/]
  end
  Auth[Auth System] --> UploadEndpoint
  Auth --> DashboardEndpoint
  ReportingUser[User Roles] --> UI
```


## Example Input & Output (sample)
**Input (CSV columns)**
```
Order ID,AWB Number,Total weight as per X (KG),Weight slab as per X (KG),Total weight as per Courier Company (KG),Weight slab charged by Courier Company (KG),Delivery Zone as per X,Delivery Zone charged by Courier Company,Expected Charge as per X (Rs.),Charges Billed by Courier Company (Rs.)
```

**Output (reconciliation row sample)**
```
order_id,awb_number,expected_charge_as_per_x_rs,charges_billed_by_courier_rs,difference_rs,reconciliation_status,overcharge_amount_rs,undercharge_amount_rs
ORD001,AWB0001,150.0,160.0,10.0,Overcharged,10.0,0.0
```


## Contact & Support
For questions, improvements, or bug reports, contact the project owner or open an issue in the repository.


## License
This project is proprietary and confidential. All rights reserved.

---

*Generated README for Courier Cost Analyzer — customize the column mappings, business rules, and ML model paths to fit your environment.*

