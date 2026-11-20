import pytest
from fastapi.testclient import TestClient
import math

from app.main import app, CSV_PATH
from app.analytics import load_data
import pandas as pd

client = TestClient(app)

def test_kpis_acceptance_checks():
    response = client.get("/api/kpis")
    assert response.status_code == 200
    data = response.json()

    # Rows: 10,059
    assert data["total_transactions"] == 10059

    # Total value: about 77.17 million INR
    assert pytest.approx(data["total_value"], rel=1e-2) == 77168781.81
    assert 77.0e6 <= data["total_value"] <= 77.3e6

    # Mean amount: 7,671.62; median: 1,428.01
    assert pytest.approx(data["mean_amount"], abs=0.1) == 7671.62
    assert pytest.approx(data["median_amount"], abs=0.1) == 1428.01

    # Distinct customers
    assert data["distinct_customers"] == 850

    # Success rate
    assert pytest.approx(data["success_rate"], abs=0.1) == 90.61

    # Weekday spend share: 71.73%, Weekend count share: 29.04%
    assert pytest.approx(data["weekday_spend_share"], abs=0.1) == 71.73
    assert pytest.approx(data["weekend_count_share"], abs=0.1) == 29.04

def test_tier_stats_acceptance_checks():
    response = client.get("/api/tier-stats")
    assert response.status_code == 200
    data = response.json()

    tiers = {t["tier"]: t for t in data["tiers"]}
    assert "Classic" in tiers
    # Classic tier mean: about 9,802.86 (highest tier mean)
    assert pytest.approx(tiers["Classic"]["mean_amount"], abs=0.5) == 9802.86

    for tier_name, tier_data in tiers.items():
        if tier_name != "Classic":
            assert tier_data["mean_amount"] < tiers["Classic"]["mean_amount"]

    # Tier ANOVA F: about 24.39
    anova = data["anova"]
    assert pytest.approx(anova["f_statistic"], abs=0.1) == 24.39
    assert anova["decision"] == "Reject H0"

def test_emi_stats_acceptance_checks():
    response = client.get("/api/emi")
    assert response.status_code == 200
    data = response.json()

    # EMI mean: about 45,313 vs non-EMI about 5,649
    assert pytest.approx(data["emi"]["mean_amount"], abs=5.0) == 45313.15
    assert pytest.approx(data["non_emi"]["mean_amount"], abs=5.0) == 5648.77

    # Welch t-test
    welch = data["welch_t_test"]
    assert pytest.approx(welch["t_statistic"], abs=0.2) == 40.50
    assert welch["decision"] == "Reject H0"

def test_region_share_acceptance_checks():
    response = client.get("/api/region-share")
    assert response.status_code == 200
    data = response.json()

    regions = {r["region"]: r for r in data}
    assert "North" in regions
    # North region share: about 26.09%
    assert pytest.approx(regions["North"]["share_pct"], abs=0.1) == 26.09

def test_monthly_spend_checks():
    response = client.get("/api/monthly")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 24
    assert data[0]["month"] == "2024-01"
    assert data[-1]["month"] == "2025-12"

def test_hypothesis_tests_acceptance_checks():
    response = client.get("/api/hypothesis-tests")
    assert response.status_code == 200
    tests = {t["id"]: t for t in response.json()}

    assert len(tests) == 5

    # 1. Weekend vs weekday p-value: about 0.451
    assert pytest.approx(tests["weekend_vs_weekday"]["p_value"], abs=0.01) == 0.451
    assert tests["weekend_vs_weekday"]["decision"] == "Fail to reject H0"

    # 2. Tier ANOVA F: about 24.39
    assert pytest.approx(tests["tier_anova"]["statistic"], abs=0.1) == 24.39
    assert tests["tier_anova"]["decision"] == "Reject H0"

    # 3. Gender vs Status
    assert tests["gender_vs_status"]["decision"] == "Fail to reject H0"

    # 4. Payment Mode vs Status
    assert tests["payment_mode_vs_status"]["decision"] == "Fail to reject H0"

    # 5. EMI vs non-EMI
    assert pytest.approx(tests["emi_vs_non_emi"]["statistic"], abs=0.5) == 40.50
    assert tests["emi_vs_non_emi"]["decision"] == "Reject H0"

def test_category_spend():
    response = client.get("/api/category-spend")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 10
    # Sorted descending by total_value
    values = [item["total_value"] for item in data]
    assert values == sorted(values, reverse=True)

def test_transactions_pagination():
    response = client.get("/api/transactions?limit=5&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 5
    assert data["offset"] == 0
    assert len(data["items"]) == 5
    assert data["total"] >= 10059

def test_post_transaction_validation():
    # 1. Invalid amount <= 0
    bad_payload_amount = {
        "Amount_INR": -100,
        "CardTier": "Gold",
        "Region": "North"
    }
    res = client.post("/api/transactions", json=bad_payload_amount)
    assert res.status_code == 422

    # 2. Invalid CardTier
    bad_payload_tier = {
        "Amount_INR": 5000,
        "CardTier": "SuperVIP",
        "Region": "North"
    }
    res = client.post("/api/transactions", json=bad_payload_tier)
    assert res.status_code == 422

    # 3. Invalid Region
    bad_payload_region = {
        "Amount_INR": 5000,
        "CardTier": "Gold",
        "Region": "NorthPole"
    }
    res = client.post("/api/transactions", json=bad_payload_region)
    assert res.status_code == 422

    # 4. Valid transaction
    valid_payload = {
        "Amount_INR": 7500.50,
        "CardTier": "Platinum",
        "Region": "West",
        "Category": "Dining",
        "Merchant": "Taj Hotel",
        "PaymentMode": "Tap & Pay (NFC)",
        "CardType": "Visa"
    }
    res = client.post("/api/transactions", json=valid_payload)
    assert res.status_code == 201
    created = res.json()
    assert created["Amount_INR"] == 7500.50
    assert created["CardTier"] == "Platinum"
    assert created["Region"] == "West"
    assert "TransactionID" in created
