from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class FreeUnitsItem(BaseModel):
    title: str
    unit_from_last_period: Optional[str] = None
    unit_from_current_period: Optional[int] = None
    unit_transferred: Optional[str] = None

class ServiceChargedItem(BaseModel):
    label: str
    unit_used: str
    price: float

class FoundsDetail(BaseModel):
    invoice_number: int
    free_units: Dict[str, FreeUnitsItem]
    service_charged: Dict[str, ServiceChargedItem]
    phone_number: str
    total_sum: float
    total_sum_raw: str

class InvoiceResponseModel(BaseModel):
    success: str
    errors: List[str]
    founds: Dict[str, FoundsDetail]
