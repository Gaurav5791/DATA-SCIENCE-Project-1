# Data Science Project 1

A collection of data science coursework, exploratory data analysis (EDA) mini-projects, and one end-to-end major project, built while practicing the core data analytics workflow: cleaning, univariate/bivariate/multivariate analysis, correlation, and reporting.

## Repository Structure

```
DATA-SCIENCE-Project-1/
├── ASSIGNMENT/
│   ├── Assignment_1.ipynb      # NumPy fundamentals (arrays, reshaping, indexing)
│   ├── Assignment_2.ipynb      # Pandas fundamentals (Series, DataFrames, filtering)
│   ├── Assignment_3.ipynb      # Matplotlib plotting practice
│   ├── Assignment_4.ipynb      # Guided EDA on the Superstore sales dataset
│   └── train.csv               # Superstore sales data used in Assignment_4
│
├── MINI_PROJECT/
│   ├── Hotel.ipynb              # 11-phase guided EDA lab manual (Hotel Booking data)
│   ├── Titanic.ipynb            # Data cleaning exercise (Titanic dataset via seaborn)
│   ├── netflix_titles.ipynb     # EDA on the Netflix titles catalog
│   ├── hotel_booking.csv
│   ├── titanic.csv
│   ├── netflix_titles.csv
│   └── chart4_countplot_survival.png
│
└── MAJOR_PROJECT/
    ├── Credit_Card_Analysis (1).ipynb        # End-to-end credit card transaction analytics
    ├── credit_card_transactions_INDIA.csv    # Raw dataset
    ├── credit_card_transactions_cleaned.csv  # Cleaned output
    ├── Credit_Card_Analytics_Presentation.pptx
    ├── Power BI Report.pbit                  # Power BI dashboard template
    └── Power BI Report.pdf                   # Exported dashboard view
```

## Contents

### ASSIGNMENT — Core Library Practice
| Notebook | Topic |
|---|---|
| `Assignment_1.ipynb` | NumPy: array creation, reshaping, indexing/slicing |
| `Assignment_2.ipynb` | Pandas: Series, DataFrames, selection, filtering |
| `Assignment_3.ipynb` | Matplotlib: line plots, styling, labels, multi-series charts |
| `Assignment_4.ipynb` | Full EDA workflow on the Superstore dataset — business understanding, data quality checks, univariate analysis (sales distribution, ship mode, segment, category) |

### MINI_PROJECT — Applied EDA
| Notebook | Dataset | Description |
|---|---|---|
| `Hotel.ipynb` | Hotel booking demand | Structured as an 11-phase lab manual: business understanding → data quality assessment → cleaning → univariate/bivariate/multivariate analysis → outlier detection → feature engineering → final report |
| `Titanic.ipynb` | Titanic (seaborn built-in) | Data cleaning pass: missing value imputation, duplicate removal, dropping the `deck` column, type casting |
| `netflix_titles.ipynb` | Netflix titles catalog (8,807 rows) | Cleaning, univariate/bivariate/correlation analysis, feature engineering (genre count, age-when-added), business insights and a one-page summary brief |

### MAJOR_PROJECT — Credit Card Transaction Analytics (India)
An end-to-end analytics project on 10,658 transaction records across 850 customers, 21 spending categories, and 16 states:
- **Data cleaning:** consolidating inconsistent category/brand spellings, normalizing mixed boolean and date formats, fixing sign errors and data-entry outliers, removing duplicate transactions
- **EDA:** univariate distributions, bivariate/multivariate breakdowns (region × card tier, gender × spend)
- **Deliverables:** a cleaned CSV, a slide presentation (`.pptx`), and an interactive Power BI dashboard (`.pbit` + exported `.pdf`)

## Tech Stack

- **Language:** Python 3
- **Core libraries:** `pandas`, `numpy`, `matplotlib`, `seaborn`, `scipy`
- **Environment:** Jupyter Notebook
- **Dashboarding:** Power BI Desktop

## Getting Started

```bash
git clone https://github.com/Gaurav5791/DATA-SCIENCE-Project-1.git
cd DATA-SCIENCE-Project-1
pip install pandas numpy matplotlib seaborn scipy jupyter
jupyter notebook
```

Then open any `.ipynb` file from the `ASSIGNMENT`, `MINI_PROJECT`, or `MAJOR_PROJECT` folders. Each notebook reads its CSV from the same folder it lives in, so run them from that folder (or adjust the file path in the first cell).

To view the Power BI dashboard, open `MAJOR_PROJECT/Power BI Report.pbit` in [Power BI Desktop](https://www.microsoft.com/en-us/power-platform/products/power-bi/desktop) (free), or view the static export in `Power BI Report.pdf`.

## Notes

- These datasets are used for practice/learning purposes.
- No `requirements.txt` is currently included — the library list above covers everything imported across the notebooks.
