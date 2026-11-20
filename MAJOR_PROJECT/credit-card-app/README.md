# Credit Card Transaction Analytics App

A full-stack credit card analytics dashboard and inferential hypothesis testing engine built on an Indian credit card portfolio dataset containing **10,059 cleaned transactions** across 2024 and 2025.

---

## Architecture & Technology Stack

- **Backend**: Python 3.13, [FastAPI](https://fastapi.tiangolo.com/), [pandas](https://pandas.pydata.org/), [SciPy](https://scipy.org/) (inferential statistics), SQLite (`sqlite3` stdlib)
- **Frontend**: Plain HTML5, CSS3 with custom variables & dark theme support, Vanilla JavaScript (ES6+), and [Chart.js 4.4.1](https://www.chartjs.org/) via cdnjs.
- **Data Persistence**:
  - Analytics are computed dynamically at runtime from `credit_card_transactions_cleaned.csv` (10,059 rows, 27 columns).
  - On startup, the dataset is loaded into an embedded SQLite database (`transactions.db`) for operational ledger queries and `POST` transaction additions.
- **Single-Server Deployment**: FastAPI serves the REST API under `/api/*` and the static single-page app via `StaticFiles` on port `8000`.

---

## Key Analytics & Verified Metrics (Full Dataset)

| Metric | Acceptance Benchmark | Computed Value |
|---|---|---|
| **Total Transactions** | 10,059 | 10,059 |
| **Total Portfolio Value** | ~77.17M INR | ₹77,168,781.81 |
| **Mean Ticket Size** | 7,671.62 INR | ₹7,671.62 |
| **Median Ticket Size** | 1,428.01 INR | ₹1,428.01 |
| **Distinct Cardholders** | 850 | 850 |
| **Transaction Success Rate** | ~90.61% | 90.61% |
| **EMI Mean Ticket** | ~45,313 INR | ₹45,313.15 |
| **Non-EMI Mean Ticket** | ~5,649 INR | ₹5,648.77 |
| **Top Card Tier by Spend** | Classic (~9,802.86 INR) | ₹9,802.86 |
| **North Region Spend Share** | ~26.09% | 26.09% |
| **Weekday Spend Share** | 71.73% | 71.73% |
| **Weekend Volume Share** | 29.04% | 29.04% |
| **Annual Seasonal Peak** | October | October (₹7,406,494.58) |

---

## Statistical Hypothesis Testing Engine (Threshold α = 0.05)

1. **Weekend vs Weekday Spend (Two-Sample Welch's t-test)**
   - **H0**: Mean transaction spend on weekends equals weekdays.
   - **Result**: $t = -0.7539$, $p = 0.4509$.
   - **Decision**: **Fail to reject H0**. No statistically significant difference in ticket size between weekdays and weekends.
2. **Card Tier Spend (One-Way ANOVA F-test)**
   - **H0**: Average spend is identical across Classic, Gold, Infinite, Platinum, and Signature tiers.
   - **Result**: $F = 24.3895$, $p = 4.08 \times 10^{-20}$.
   - **Decision**: **Reject H0**. Statistically significant variation across tiers (Classic cards display the highest average ticket).
3. **Gender vs Transaction Status (Chi-Square Test of Independence)**
   - **H0**: Transaction status (Success, Failed, Refunded) is independent of gender.
   - **Result**: $\chi^2 = 5.7715$, $p = 0.0558$.
   - **Decision**: **Fail to reject H0** at $\alpha = 0.05$. Outcome is independent of gender.
4. **Payment Mode vs Transaction Status (Chi-Square Test of Independence)**
   - **H0**: Transaction status is independent of payment mode.
   - **Result**: $\chi^2 = 10.7515$, $p = 0.2162$.
   - **Decision**: **Fail to reject H0**. Transaction status is independent of payment method.
5. **EMI vs Non-EMI Spend (Two-Sample Welch's t-test)**
   - **H0**: Average spend for EMI equals non-EMI transactions.
   - **Result**: $t = 40.5012$, $p = 2.81 \times 10^{-165}$.
   - **Decision**: **Reject H0**. EMI transactions carry significantly higher average spend (~₹45,313 vs ~₹5,649).

---

## Project Structure

```
credit-card-app/
├── .venv/                         # Python virtual environment
├── requirements.txt               # Dependencies
├── README.md                      # Documentation & execution guide
├── transactions.db                # SQLite database (auto-generated on first run)
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application & endpoints
│   ├── database.py                # SQLite loader, queries, and POST insertion
│   ├── analytics.py               # KPI, aggregations, and SciPy statistical tests
│   └── models.py                  # Pydantic schemas and input validators
├── static/
│   ├── index.html                 # Single-page dashboard interface
│   ├── styles.css                 # CSS custom properties, responsive grid, dark mode
│   └── app.js                     # Chart.js rendering, filtering, pagination, modal
└── tests/
    ├── __init__.py
    └── test_api.py                # Pytest suite validating endpoints & acceptance checks
```

---

## Setup & Running Instructions

### 1. Open PowerShell and Navigate to App Directory
```powershell
cd "DATA-SCIENCE-Project-1\MAJOR_PROJECT\credit-card-app"
```

### 2. Activate the Virtual Environment
```powershell
.\.venv\Scripts\Activate.ps1
```
*(If execution policies prevent script execution, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

### 3. (Optional) Re-install Dependencies
If setting up in a fresh environment:
```powershell
pip install -r requirements.txt
```

### 4. Run the Test Suite
Verify that all 9 endpoint and statistical checks pass:
```powershell
python -m pytest tests -v
```

### 5. Launch the Application (One-Click Auto-Open)
Simply run `run.py`. This starts the server and **automatically opens the dashboard in your default web browser**:
```powershell
python run.py
```

*(Alternatively, you can run directly with Uvicorn: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`)*

### 6. Dashboard URL
If your browser does not open automatically, click or paste:
👉 **[http://localhost:8000](http://localhost:8000)** or **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

*(Note on Windows: Do not type `0.0.0.0:8000` into your browser. `0.0.0.0` is an internal binding address and Windows browsers will show `ERR_ADDRESS_INVALID`. Always use `localhost:8000` or `127.0.0.1:8000`.)*

---

## API Endpoints Reference

All endpoints return JSON and are located under `/api/`:

| Method | Endpoint | Query Parameters | Description |
|---|---|---|---|
| `GET` | `/api/kpis` | `tier`, `region`, `start_date`, `end_date` | Summary KPIs (total spend, transaction count, mean, median, distinct customers, success rate, EMI share). |
| `GET` | `/api/category-spend` | `tier`, `region`, `start_date`, `end_date` | Top 10 categories ranked by spend volume with transaction counts. |
| `GET` | `/api/region-share` | `tier`, `region`, `start_date`, `end_date` | Regional spend distribution and average ticket per region. |
| `GET` | `/api/tier-stats` | `tier`, `region`, `start_date`, `end_date` | Mean and median spend across card tiers with one-way ANOVA test. |
| `GET` | `/api/emi` | `tier`, `region`, `start_date`, `end_date` | EMI vs non-EMI mean comparison with Welch's t-test. |
| `GET` | `/api/monthly` | `tier`, `region`, `start_date`, `end_date` | 24-month spend trend in chronological order. |
| `GET` | `/api/hypothesis-tests` | `tier`, `region`, `start_date`, `end_date` | All 5 inferential tests with statistics, p-values, and decisions. |
| `GET` | `/api/transactions` | `limit`, `offset`, `tier`, `region`, `start_date`, `end_date` | Paginated transactions ledger from SQLite. |
| `POST` | `/api/transactions` | *(Request body JSON)* | Add new transaction to SQLite (validates amount > 0, CardTier, Region). Returns created record. |
| `GET` | `/api/filter-options` | None | Returns distinct values for dropdown selectors and valid date bounds. |
