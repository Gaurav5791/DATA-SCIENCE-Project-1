from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any

ALLOWED_TIERS = ["Classic", "Gold", "Infinite", "Platinum", "Signature"]
ALLOWED_REGIONS = ["Central", "East", "North", "South", "West"]

class TransactionCreate(BaseModel):
    Amount_INR: float = Field(..., gt=0, description="Transaction amount in INR, must be strictly greater than 0")
    CardTier: str = Field(..., description="Card tier")
    Region: str = Field(..., description="Geographical region in India")
    CustomerID: Optional[str] = "CUST00999"
    CustomerName: Optional[str] = "New Customer"
    Gender: Optional[str] = "Male"
    Age: Optional[float] = 30.0
    TransactionDate: Optional[str] = None
    TransactionTime: Optional[str] = "12:00"
    Category: Optional[str] = "Groceries"
    Merchant: Optional[str] = "Store"
    PaymentMode: Optional[str] = "Online"
    CardType: Optional[str] = "Visa"
    IsEMI: Optional[bool] = False
    TransactionStatus: Optional[str] = "Success"
    City: Optional[str] = "Mumbai"
    State: Optional[str] = "Maharashtra"
    MonthlyIncomeINR: Optional[float] = 60000.0

    @field_validator("CardTier")
    @classmethod
    def validate_card_tier(cls, v: str) -> str:
        cleaned = v.strip().title()
        if cleaned not in ALLOWED_TIERS:
            raise ValueError(f"CardTier must be one of {ALLOWED_TIERS}, received: {v}")
        return cleaned

    @field_validator("Region")
    @classmethod
    def validate_region(cls, v: str) -> str:
        cleaned = v.strip().title()
        if cleaned not in ALLOWED_REGIONS:
            raise ValueError(f"Region must be one of {ALLOWED_REGIONS}, received: {v}")
        return cleaned

class FilterParams(BaseModel):
    tier: Optional[str] = None
    region: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
