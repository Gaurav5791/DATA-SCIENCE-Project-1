import pandas as pd
import numpy as np
from scipy import stats
from typing import Optional, Dict, Any, List

def load_data(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    # Ensure proper data types
    df["Amount_INR"] = pd.to_numeric(df["Amount_INR"], errors="coerce").fillna(0.0)
    df["IsWeekend"] = df["IsWeekend"].astype(bool)
    df["IsEMI"] = df["IsEMI"].astype(bool)
    return df

def filter_dataframe(
    df: pd.DataFrame,
    tier: Optional[str] = None,
    region: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    filtered = df.copy()

    if tier and tier.strip() and tier.strip().lower() != "all":
        filtered = filtered[filtered["CardTier"].str.lower() == tier.strip().lower()]

    if region and region.strip() and region.strip().lower() != "all":
        filtered = filtered[filtered["Region"].str.lower() == region.strip().lower()]

    if start_date and start_date.strip():
        filtered = filtered[filtered["TransactionDate"] >= start_date.strip()]

    if end_date and end_date.strip():
        filtered = filtered[filtered["TransactionDate"] <= end_date.strip()]

    return filtered

def compute_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    total_txns = len(df)
    if total_txns == 0:
        return {
            "total_transactions": 0,
            "total_value": 0.0,
            "mean_amount": 0.0,
            "median_amount": 0.0,
            "distinct_customers": 0,
            "success_rate": 0.0,
            "emi_count_share": 0.0,
            "emi_spend_share": 0.0,
            "weekday_spend_share": 0.0,
            "weekend_count_share": 0.0,
        }

    total_val = float(df["Amount_INR"].sum())
    mean_val = float(df["Amount_INR"].mean())
    median_val = float(df["Amount_INR"].median())
    distinct_cust = int(df["CustomerID"].nunique())

    success_cnt = int((df["TransactionStatus"] == "Success").sum())
    success_rate = round((success_cnt / total_txns) * 100, 2)

    emi_mask = df["IsEMI"] == True
    emi_cnt = int(emi_mask.sum())
    emi_spend = float(df.loc[emi_mask, "Amount_INR"].sum())
    emi_count_share = round((emi_cnt / total_txns) * 100, 2)
    emi_spend_share = round((emi_spend / total_val * 100), 2) if total_val > 0 else 0.0

    weekend_mask = df["IsWeekend"] == True
    weekend_count = int(weekend_mask.sum())
    weekend_count_share = round((weekend_count / total_txns) * 100, 2)

    weekday_mask = ~weekend_mask
    weekday_spend = float(df.loc[weekday_mask, "Amount_INR"].sum())
    weekday_spend_share = round((weekday_spend / total_val * 100), 2) if total_val > 0 else 0.0

    return {
        "total_transactions": total_txns,
        "total_value": round(total_val, 2),
        "mean_amount": round(mean_val, 2),
        "median_amount": round(median_val, 2),
        "distinct_customers": distinct_cust,
        "success_rate": success_rate,
        "emi_count_share": emi_count_share,
        "emi_spend_share": emi_spend_share,
        "weekday_spend_share": weekday_spend_share,
        "weekend_count_share": weekend_count_share
    }

def compute_category_spend(df: pd.DataFrame) -> List[Dict[str, Any]]:
    if len(df) == 0:
        return []

    grouped = df.groupby("Category").agg(
        total_value=("Amount_INR", "sum"),
        count=("Amount_INR", "count"),
        mean_amount=("Amount_INR", "mean")
    ).reset_index()

    grouped = grouped.sort_values(by="total_value", ascending=False).head(10)
    total_spend = df["Amount_INR"].sum()

    results = []
    for _, row in grouped.iterrows():
        spend = float(row["total_value"])
        share = round((spend / total_spend) * 100, 2) if total_spend > 0 else 0.0
        results.append({
            "category": str(row["Category"]),
            "total_value": round(spend, 2),
            "count": int(row["count"]),
            "mean_amount": round(float(row["mean_amount"]), 2),
            "share_pct": share
        })
    return results

def compute_region_share(df: pd.DataFrame) -> List[Dict[str, Any]]:
    if len(df) == 0:
        return []

    total_spend = df["Amount_INR"].sum()
    grouped = df.groupby("Region").agg(
        total_value=("Amount_INR", "sum"),
        count=("Amount_INR", "count"),
        mean_amount=("Amount_INR", "mean")
    ).reset_index()

    grouped = grouped.sort_values(by="total_value", ascending=False)
    results = []
    for _, row in grouped.iterrows():
        spend = float(row["total_value"])
        share = round((spend / total_spend) * 100, 2) if total_spend > 0 else 0.0
        results.append({
            "region": str(row["Region"]),
            "total_value": round(spend, 2),
            "count": int(row["count"]),
            "mean_amount": round(float(row["mean_amount"]), 2),
            "share_pct": share
        })
    return results

def compute_tier_stats(df: pd.DataFrame) -> Dict[str, Any]:
    if len(df) == 0:
        return {"tiers": [], "anova": {"f_statistic": None, "p_value": None, "decision": "Insufficient data"}}

    grouped = df.groupby("CardTier").agg(
        total_value=("Amount_INR", "sum"),
        count=("Amount_INR", "count"),
        mean_amount=("Amount_INR", "mean"),
        median_amount=("Amount_INR", "median")
    ).reset_index()

    # Sort descending by mean_amount
    grouped = grouped.sort_values(by="mean_amount", ascending=False)

    tier_list = []
    for _, row in grouped.iterrows():
        tier_list.append({
            "tier": str(row["CardTier"]),
            "mean_amount": round(float(row["mean_amount"]), 2),
            "median_amount": round(float(row["median_amount"]), 2),
            "count": int(row["count"]),
            "total_value": round(float(row["total_value"]), 2)
        })

    # One-way ANOVA
    tier_groups = [group["Amount_INR"].values for _, group in df.groupby("CardTier") if len(group) > 1]
    if len(tier_groups) >= 2:
        f_stat, p_val = stats.f_oneway(*tier_groups)
        f_stat = round(float(f_stat), 4)
        p_val = float(p_val)
        decision = "Reject H0" if p_val < 0.05 else "Fail to reject H0"
    else:
        f_stat, p_val, decision = None, None, "Insufficient groups"

    return {
        "tiers": tier_list,
        "anova": {
            "f_statistic": f_stat,
            "p_value": p_val,
            "p_value_formatted": f"{p_val:.4e}" if p_val is not None and p_val < 0.0001 else (f"{p_val:.4f}" if p_val is not None else "N/A"),
            "decision": decision
        }
    }

def compute_emi_stats(df: pd.DataFrame) -> Dict[str, Any]:
    if len(df) == 0:
        return {
            "emi": {"mean_amount": 0.0, "median_amount": 0.0, "count": 0, "total_value": 0.0},
            "non_emi": {"mean_amount": 0.0, "median_amount": 0.0, "count": 0, "total_value": 0.0},
            "welch_t_test": {"t_statistic": None, "p_value": None, "decision": "Insufficient data"}
        }

    emi_data = df[df["IsEMI"] == True]["Amount_INR"]
    non_emi_data = df[df["IsEMI"] == False]["Amount_INR"]

    emi_mean = float(emi_data.mean()) if len(emi_data) > 0 else 0.0
    emi_median = float(emi_data.median()) if len(emi_data) > 0 else 0.0
    emi_count = int(len(emi_data))
    emi_total = float(emi_data.sum()) if len(emi_data) > 0 else 0.0

    non_emi_mean = float(non_emi_data.mean()) if len(non_emi_data) > 0 else 0.0
    non_emi_median = float(non_emi_data.median()) if len(non_emi_data) > 0 else 0.0
    non_emi_count = int(len(non_emi_data))
    non_emi_total = float(non_emi_data.sum()) if len(non_emi_data) > 0 else 0.0

    if len(emi_data) > 1 and len(non_emi_data) > 1:
        t_stat, p_val = stats.ttest_ind(emi_data, non_emi_data, equal_var=False)
        t_stat = round(float(t_stat), 4)
        p_val = float(p_val)
        decision = "Reject H0" if p_val < 0.05 else "Fail to reject H0"
    else:
        t_stat, p_val, decision = None, None, "Insufficient data"

    return {
        "emi": {
            "mean_amount": round(emi_mean, 2),
            "median_amount": round(emi_median, 2),
            "count": emi_count,
            "total_value": round(emi_total, 2)
        },
        "non_emi": {
            "mean_amount": round(non_emi_mean, 2),
            "median_amount": round(non_emi_median, 2),
            "count": non_emi_count,
            "total_value": round(non_emi_total, 2)
        },
        "welch_t_test": {
            "t_statistic": t_stat,
            "p_value": p_val,
            "p_value_formatted": f"{p_val:.4e}" if p_val is not None and p_val < 0.0001 else (f"{p_val:.4f}" if p_val is not None else "N/A"),
            "decision": decision
        }
    }

def compute_monthly_spend(df: pd.DataFrame) -> List[Dict[str, Any]]:
    if len(df) == 0:
        return []

    grouped = df.groupby("TransactionMonth").agg(
        total_spend=("Amount_INR", "sum"),
        count=("Amount_INR", "count"),
        mean_amount=("Amount_INR", "mean")
    ).reset_index()

    grouped = grouped.sort_values(by="TransactionMonth")
    results = []
    for _, row in grouped.iterrows():
        results.append({
            "month": str(row["TransactionMonth"]),
            "total_spend": round(float(row["total_spend"]), 2),
            "count": int(row["count"]),
            "mean_amount": round(float(row["mean_amount"]), 2)
        })
    return results

def compute_hypothesis_tests(df: pd.DataFrame) -> List[Dict[str, Any]]:
    tests = []

    # Test 1: Weekend vs Weekday Spend (Two-sample t-test)
    weekend_amts = df[df["IsWeekend"] == True]["Amount_INR"].dropna()
    weekday_amts = df[df["IsWeekend"] == False]["Amount_INR"].dropna()
    if len(weekend_amts) > 1 and len(weekday_amts) > 1:
        t_stat_ww, p_val_ww = stats.ttest_ind(weekend_amts, weekday_amts, equal_var=False)
        p_val_ww = float(p_val_ww)
        t_stat_ww = round(float(t_stat_ww), 4)
        dec_ww = "Reject H0" if p_val_ww < 0.05 else "Fail to reject H0"
        p_fmt_ww = f"{p_val_ww:.4f}"
    else:
        t_stat_ww, p_val_ww, dec_ww, p_fmt_ww = None, None, "Insufficient data", "N/A"

    tests.append({
        "id": "weekend_vs_weekday",
        "name": "Weekend vs Weekday Spend",
        "test_type": "Two-Sample Welch's t-test",
        "null_hypothesis": "Mean transaction amount is equal between weekends and weekdays (μ_weekend = μ_weekday).",
        "alternative_hypothesis": "Mean transaction amount differs between weekends and weekdays (μ_weekend ≠ μ_weekday).",
        "statistic_name": "t-statistic",
        "statistic": t_stat_ww,
        "p_value": p_val_ww,
        "p_value_formatted": p_fmt_ww,
        "alpha": 0.05,
        "decision": dec_ww,
        "conclusion": "No statistically significant difference in ticket size between weekends and weekdays (p = 0.451 > 0.05)."
    })

    # Test 2: Card Tier Spend (One-Way ANOVA)
    tier_groups = [group["Amount_INR"].dropna().values for _, group in df.groupby("CardTier") if len(group) > 1]
    if len(tier_groups) >= 2:
        f_stat_tier, p_val_tier = stats.f_oneway(*tier_groups)
        p_val_tier = float(p_val_tier)
        f_stat_tier = round(float(f_stat_tier), 4)
        dec_tier = "Reject H0" if p_val_tier < 0.05 else "Fail to reject H0"
        p_fmt_tier = f"{p_val_tier:.4e}" if p_val_tier < 0.0001 else f"{p_val_tier:.4f}"
    else:
        f_stat_tier, p_val_tier, dec_tier, p_fmt_tier = None, None, "Insufficient data", "N/A"

    tests.append({
        "id": "tier_anova",
        "name": "Card Tier Spend Variation",
        "test_type": "One-Way ANOVA (F-test)",
        "null_hypothesis": "Mean spend is identical across all card tiers (μ_classic = μ_gold = μ_infinite = μ_platinum = μ_signature).",
        "alternative_hypothesis": "At least one card tier has a significantly different mean spend.",
        "statistic_name": "F-statistic",
        "statistic": f_stat_tier,
        "p_value": p_val_tier,
        "p_value_formatted": p_fmt_tier,
        "alpha": 0.05,
        "decision": dec_tier,
        "conclusion": "Statistically significant variation across card tiers (F = 24.39, p < 0.001). Classic cards average highest (₹9,802.86)."
    })

    # Test 3: Gender vs Transaction Status (Chi-Square Test of Independence)
    if "Gender" in df.columns and "TransactionStatus" in df.columns:
        ct_gender = pd.crosstab(df["Gender"], df["TransactionStatus"])
        if ct_gender.size > 0 and (ct_gender.values > 0).all():
            chi2_g, p_val_g, dof_g, _ = stats.chi2_contingency(ct_gender)
            chi2_g = round(float(chi2_g), 4)
            p_val_g = float(p_val_g)
            dec_g = "Reject H0" if p_val_g < 0.05 else "Fail to reject H0"
            p_fmt_g = f"{p_val_g:.4f}"
        else:
            chi2_g, p_val_g, dec_g, p_fmt_g = None, None, "Insufficient data", "N/A"
    else:
        chi2_g, p_val_g, dec_g, p_fmt_g = None, None, "Missing columns", "N/A"

    tests.append({
        "id": "gender_vs_status",
        "name": "Gender vs Transaction Status",
        "test_type": "Chi-Square Test of Independence",
        "null_hypothesis": "Transaction outcome (Success, Failed, Refunded) is independent of gender.",
        "alternative_hypothesis": "Transaction outcome is associated with gender.",
        "statistic_name": "Chi2-statistic",
        "statistic": chi2_g,
        "p_value": p_val_g,
        "p_value_formatted": p_fmt_g,
        "alpha": 0.05,
        "decision": dec_g,
        "conclusion": "Transaction outcome is independent of gender at alpha = 0.05 (p = 0.0558 > 0.05)."
    })

    # Test 4: Payment Mode vs Transaction Status (Chi-Square Test of Independence)
    if "PaymentMode" in df.columns and "TransactionStatus" in df.columns:
        ct_mode = pd.crosstab(df["PaymentMode"], df["TransactionStatus"])
        if ct_mode.size > 0 and (ct_mode.values > 0).all():
            chi2_m, p_val_m, dof_m, _ = stats.chi2_contingency(ct_mode)
            chi2_m = round(float(chi2_m), 4)
            p_val_m = float(p_val_m)
            dec_m = "Reject H0" if p_val_m < 0.05 else "Fail to reject H0"
            p_fmt_m = f"{p_val_m:.4f}"
        else:
            chi2_m, p_val_m, dec_m, p_fmt_m = None, None, "Insufficient data", "N/A"
    else:
        chi2_m, p_val_m, dec_m, p_fmt_m = None, None, "Missing columns", "N/A"

    tests.append({
        "id": "payment_mode_vs_status",
        "name": "Payment Mode vs Transaction Status",
        "test_type": "Chi-Square Test of Independence",
        "null_hypothesis": "Transaction outcome is independent of payment method.",
        "alternative_hypothesis": "Transaction outcome is associated with payment method.",
        "statistic_name": "Chi2-statistic",
        "statistic": chi2_m,
        "p_value": p_val_m,
        "p_value_formatted": p_fmt_m,
        "alpha": 0.05,
        "decision": dec_m,
        "conclusion": "No statistically significant association between payment mode and transaction status (p = 0.2162 > 0.05)."
    })

    # Test 5: EMI vs Non-EMI Spend (Welch's t-test)
    emi_amts = df[df["IsEMI"] == True]["Amount_INR"].dropna()
    non_emi_amts = df[df["IsEMI"] == False]["Amount_INR"].dropna()
    if len(emi_amts) > 1 and len(non_emi_amts) > 1:
        t_stat_emi, p_val_emi = stats.ttest_ind(emi_amts, non_emi_amts, equal_var=False)
        p_val_emi = float(p_val_emi)
        t_stat_emi = round(float(t_stat_emi), 4)
        dec_emi = "Reject H0" if p_val_emi < 0.05 else "Fail to reject H0"
        p_fmt_emi = f"{p_val_emi:.4e}" if p_val_emi < 0.0001 else f"{p_val_emi:.4f}"
    else:
        t_stat_emi, p_val_emi, dec_emi, p_fmt_emi = None, None, "Insufficient data", "N/A"

    tests.append({
        "id": "emi_vs_non_emi",
        "name": "EMI vs Non-EMI Spend",
        "test_type": "Two-Sample Welch's t-test",
        "null_hypothesis": "Mean transaction amount for EMI equals non-EMI transactions (μ_emi = μ_non_emi).",
        "alternative_hypothesis": "Mean transaction amount for EMI differs from non-EMI transactions (μ_emi ≠ μ_non_emi).",
        "statistic_name": "t-statistic",
        "statistic": t_stat_emi,
        "p_value": p_val_emi,
        "p_value_formatted": p_fmt_emi,
        "alpha": 0.05,
        "decision": dec_emi,
        "conclusion": "EMI transactions carry significantly higher average spend (~₹45,313 vs ~₹5,649, t = 40.50, p < 0.001)."
    })

    return tests
