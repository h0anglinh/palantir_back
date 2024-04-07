from fastapi import APIRouter, HTTPException
from .webwatcher.main import Watch

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from dotenv import load_dotenv
import os


router = APIRouter(prefix='/mobiles')
# Načte proměnné prostředí z .env souboru
load_dotenv()

class Invoice(BaseModel):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Foo",
                    "description": "A very nice Item",
                    "price": 35.4,
                    "tax": 3.2,
                }
            ]
        }
    }



@router.get("/invoices", tags=["o2 family"])
def get_available_invoices():
    user = os.getenv("O2_NAME")
    password = os.getenv("O2_PASSWORD")
    if not user or not password:
        raise HTTPException(status_code=500, detail="02_NAME and/or O2_PASSWORD values are not set up")

    try:
        instance = Watch(uid=user, pwd=password)
        invoices = instance.login().scrape_invoicelist()

        amount = [invoice['amount_CZK'] for invoice in invoices]

        if len(amount) % 2 == 1:
            median = amount[len(amount) // 2]
        else:
            mid_1 = amount[len(amount) // 2 - 1]
            mid_2 = amount[len(amount) // 2]
            median = (mid_1 + mid_2) / 2 


        average_amount = round(sum(amount) / len(amount), 1)
        min_amount = min(amount)
        max_amount = max(amount)
        response = jsonable_encoder({"invoices": invoices, "stats": {'length': len(invoices), "average": average_amount, 'min_amount': min_amount, 'max_amount': max_amount, 'median': median}})
    except:
        raise HTTPException(status_code=401, detail="invoices are not available")


    return JSONResponse(content=response) 



@router.get("/contracts", tags=["o2 family"])
def get_contracts():
    user = os.getenv("O2_NAME")
    password = os.getenv("O2_PASSWORD")
    if not user or not password:
        raise HTTPException(status_code=500, detail="02_NAME and/or O2_PASSWORD values are not set up")

    try:
        instance = Watch(uid=user, pwd=password)
        contracts = instance.login().scrape_contracts()
        response = jsonable_encoder(contracts)
    except:
        raise HTTPException(status_code=500, detail="contracts are not available")
    return JSONResponse(content=response)

@router.get("/invoice", tags=["o2 family"])
def get_invoice(href: str):
    user = os.getenv("O2_NAME")
    password = os.getenv("O2_PASSWORD")
    if not user or not password:
        raise HTTPException(status_code=500, detail="02_NAME and/or O2_PASSWORD values are not set up")

    instance = Watch(uid=user, pwd=password)
    invoice = instance.login().get_invoice_details(href)
    response = jsonable_encoder(invoice)

   
    return JSONResponse(content=response)