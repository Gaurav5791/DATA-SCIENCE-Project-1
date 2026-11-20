import os
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .models import TransactionCreate, ALLOWED_TIERS, ALLOWED_REGIONS
from .database import init_db, insert_transaction, get_transactions_paginated
from .analytics import (
    load_data,
    filter_dataframe,
    compute_kpis,
    compute_category_spend,
    compute_region_share,
    compute_tier_stats,
    compute_emi_stats,
    compute_monthly_spend,
    compute_hypothesis_tests,
)

# Locate CSV
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANDIDATE_PATHS = [
    os.path.abspath(os.path.join(BASE_DIR, "..", "credit_card_transactions_cleaned.csv")),
    os.path.abspath(os.path.join(BASE_DIR, "credit_card_transactions_cleaned.csv")),
    os.path.abspath(os.path.join(os.getcwd(), "DATA-SCIENCE-Project-1", "MAJOR_PROJECT", "credit_card_transactions_cleaned.csv")),
    os.path.abspath(os.path.join(os.getcwd(), "MAJOR_PROJECT", "credit_card_transactions_cleaned.csv")),
]

CSV_PATH = None
for p in CANDIDATE_PATHS:
    if os.path.exists(p):
        CSV_PATH = p
        break

if not CSV_PATH:
    raise FileNotFoundError("Could not locate credit_card_transactions_cleaned.csv in expected locations.")

# In-memory dataframe for runtime analytics
DATA_DF = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global DATA_DF
    # 1. Initialize SQLite DB with CSV if needed
    init_db(CSV_PATH)
    # 2. Load dataset into pandas
    DATA_DF = load_data(CSV_PATH)
    yield

app = FastAPI(
    title="Credit Card Transaction Analytics API",
    description="Analytics and transaction intelligence for Indian credit card transaction dataset",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_filtered_df(
    tier: Optional[str] = None,
    region: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    global DATA_DF
    if DATA_DF is None:
        DATA_DF = load_data(CSV_PATH)
    return filter_dataframe(DATA_DF, tier, region, start_date, end_date)

@app.get("/api/filter-options")
def get_filter_options():
    global DATA_DF
    if DATA_DF is None:
        DATA_DF = load_data(CSV_PATH)
    return {
        "tiers": ALLOWED_TIERS,
        "regions": ALLOWED_REGIONS,
        "categories": sorted(DATA_DF["Category"].unique().tolist()),
        "payment_modes": sorted(DATA_DF["PaymentMode"].unique().tolist()),
        "card_types": sorted(DATA_DF["CardType"].unique().tolist()),
        "min_date": str(DATA_DF["TransactionDate"].min()),
        "max_date": str(DATA_DF["TransactionDate"].max()),
    }

@app.get("/api/kpis")
def get_kpis(
    tier: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    df = get_filtered_df(tier, region, start_date, end_date)
    return compute_kpis(df)

@app.get("/api/category-spend")
def get_category_spend(
    tier: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    df = get_filtered_df(tier, region, start_date, end_date)
    return compute_category_spend(df)

@app.get("/api/region-share")
def get_region_share(
    tier: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    df = get_filtered_df(tier, region, start_date, end_date)
    return compute_region_share(df)

@app.get("/api/tier-stats")
def get_tier_stats(
    tier: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    df = get_filtered_df(tier, region, start_date, end_date)
    return compute_tier_stats(df)

@app.get("/api/emi")
def get_emi_stats(
    tier: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    df = get_filtered_df(tier, region, start_date, end_date)
    return compute_emi_stats(df)

@app.get("/api/monthly")
def get_monthly_spend(
    tier: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    df = get_filtered_df(tier, region, start_date, end_date)
    return compute_monthly_spend(df)

@app.get("/api/hypothesis-tests")
def get_hypothesis_tests(
    tier: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    df = get_filtered_df(tier, region, start_date, end_date)
    return compute_hypothesis_tests(df)

@app.get("/api/transactions")
def get_transactions(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tier: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    total, rows = get_transactions_paginated(
        limit=limit,
        offset=offset,
        tier=tier,
        region=region,
        start_date=start_date,
        end_date=end_date,
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": rows,
    }

@app.post("/api/transactions", status_code=status.HTTP_201_CREATED)
def create_transaction(payload: TransactionCreate):
    # Validation is enforced by Pydantic: amount > 0, CardTier in ALLOWED_TIERS, Region in ALLOWED_REGIONS
    try:
        created_row = insert_transaction(payload.model_dump())
        return created_row
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record transaction: {str(e)}")

# Mount static files
STATIC_DIR = os.path.join(BASE_DIR, "static")
if os.path.exists(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
