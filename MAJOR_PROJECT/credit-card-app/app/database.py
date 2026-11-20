import sqlite3
import os
import pandas as pd
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "transactions.db")

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(csv_path: str):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if table already exists and has records
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transactions';")
    table_exists = cursor.fetchone()
    
    if table_exists:
        cursor.execute("SELECT COUNT(*) FROM transactions;")
        count = cursor.fetchone()[0]
        if count >= 10000:
            conn.close()
            return

    # Load data from CSV
    if not os.path.exists(csv_path):
        conn.close()
        raise FileNotFoundError(f"Source CSV not found at: {csv_path}")

    df = pd.read_csv(csv_path)
    
    # Write to SQLite
    df.to_sql("transactions", conn, if_exists="replace", index=False)
    
    # Create indexes for filtering performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_txn_date ON transactions(TransactionDate);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_txn_tier ON transactions(CardTier);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_txn_region ON transactions(Region);")
    
    conn.commit()
    conn.close()

def get_next_transaction_id() -> str:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(rowid) FROM transactions;")
    res = cursor.fetchone()
    max_id = res[0] if res and res[0] is not None else 10059
    conn.close()
    return f"TXN{max_id + 1:07d}"

def insert_transaction(data: Dict[str, Any]) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()

    # Fill default fields if missing
    txn_id = data.get("TransactionID") or get_next_transaction_id()
    txn_date = data.get("TransactionDate") or datetime.now().strftime("%Y-%m-%d")
    txn_time = data.get("TransactionTime") or datetime.now().strftime("%H:%M")
    
    try:
        dt = datetime.strptime(txn_date, "%Y-%m-%d")
        day_of_week = dt.strftime("%A")
        is_weekend = dt.weekday() >= 5
        txn_month = dt.strftime("%Y-%m")
    except Exception:
        day_of_week = "Monday"
        is_weekend = False
        txn_month = txn_date[:7] if len(txn_date) >= 7 else "2024-01"

    try:
        txn_hour = int(txn_time.split(":")[0])
    except Exception:
        txn_hour = 12

    amount = float(data["Amount_INR"])
    reward_points = round(amount * 0.02, 2)
    age = float(data.get("Age") or 30.0)
    monthly_income = float(data.get("MonthlyIncomeINR") or 60000.0)

    # Age group
    if age < 26:
        age_group = "18-25"
    elif age < 36:
        age_group = "26-35"
    elif age < 46:
        age_group = "36-45"
    elif age < 56:
        age_group = "46-55"
    else:
        age_group = "56+"

    # Income bracket
    if monthly_income < 40000:
        income_bracket = "<40K"
    elif monthly_income <= 60000:
        income_bracket = "40-60K"
    elif monthly_income <= 80000:
        income_bracket = "60-80K"
    elif monthly_income <= 100000:
        income_bracket = "80-100K"
    else:
        income_bracket = "100K+"

    row = {
        "TransactionID": txn_id,
        "CustomerID": data.get("CustomerID") or "CUST00999",
        "CustomerName": data.get("CustomerName") or "New Customer",
        "Gender": data.get("Gender") or "Male",
        "Age": age,
        "TransactionDate": txn_date,
        "TransactionTime": txn_time,
        "DayOfWeek": day_of_week,
        "IsWeekend": 1 if is_weekend else 0,
        "Category": data.get("Category") or "Groceries",
        "Merchant": data.get("Merchant") or "Store",
        "Amount_INR": amount,
        "PaymentMode": data.get("PaymentMode") or "Online",
        "CardType": data.get("CardType") or "Visa",
        "CardTier": data["CardTier"],
        "IsEMI": 1 if data.get("IsEMI") else 0,
        "TransactionStatus": data.get("TransactionStatus") or "Success",
        "RewardPoints": reward_points,
        "City": data.get("City") or "Mumbai",
        "State": data.get("State") or "Maharashtra",
        "Region": data["Region"],
        "MonthlyIncomeINR": monthly_income,
        "TransactionMonth": txn_month,
        "TransactionHour": txn_hour,
        "Amount_IsOutlier": 1 if amount > 50000 else 0,
        "AgeGroup": age_group,
        "IncomeBracket": income_bracket
    }

    cols = list(row.keys())
    placeholders = ", ".join(["?"] * len(cols))
    sql = f"INSERT INTO transactions ({', '.join(cols)}) VALUES ({placeholders})"
    cursor.execute(sql, [row[c] for c in cols])
    conn.commit()
    conn.close()

    return row

def get_transactions_paginated(
    limit: int = 10,
    offset: int = 0,
    tier: Optional[str] = None,
    region: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Tuple[int, List[Dict[str, Any]]]:
    conn = get_connection()
    cursor = conn.cursor()

    conditions = []
    params = []

    if tier and tier.strip() and tier.strip().lower() != "all":
        conditions.append("CardTier = ?")
        params.append(tier.strip())

    if region and region.strip() and region.strip().lower() != "all":
        conditions.append("Region = ?")
        params.append(region.strip())

    if start_date and start_date.strip():
        conditions.append("TransactionDate >= ?")
        params.append(start_date.strip())

    if end_date and end_date.strip():
        conditions.append("TransactionDate <= ?")
        params.append(end_date.strip())

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    # Count query
    count_sql = f"SELECT COUNT(*) FROM transactions {where_clause}"
    cursor.execute(count_sql, params)
    total_count = cursor.fetchone()[0]

    # Paginated select
    select_sql = f"SELECT * FROM transactions {where_clause} ORDER BY rowid DESC LIMIT ? OFFSET ?"
    cursor.execute(select_sql, params + [limit, offset])
    rows = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return total_count, rows
