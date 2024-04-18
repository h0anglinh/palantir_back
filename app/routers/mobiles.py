from fastapi import APIRouter, HTTPException, Depends, Query
from ..services.webwatcher.main import Watch

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os
from asyncpg import Connection
from ..services import database
from enum import StrEnum
from pydantic import BaseModel, HttpUrl, validator
from ..services.database import get_db_connection


db_connection = None
router = APIRouter(prefix='/mobiles')
# Načte proměnné prostředí z .env souboru
load_dotenv()
user = os.getenv("O2_NAME")
password = os.getenv("O2_PASSWORD")
instance = Watch(uid=user, pwd=password)

@router.get("/invoices", tags=["o2 family"])
async def get_available_invoices(conn: Connection = Depends(get_db_connection)):
    user = os.getenv("O2_NAME")
    password = os.getenv("O2_PASSWORD")
    if not user or not password:
        raise HTTPException(status_code=500, detail="02_NAME and/or O2_PASSWORD values are not set up")
    try:
        instance = Watch(uid=user, pwd=password)
        scraped_invoices = instance.login().scrape_invoicelist()
    except Exception as e:
        # Ostatní chyby
        raise HTTPException(status_code=500, detail=f"Neznámá chyba: {str(e)}")
    
    db_invoices = []
    try:
        db_invoices  = await conn.fetch("SELECT * FROM mobile_services.invoices")
    except:
        return {'error': 'error'}

    missing_invoices = database.find_missing_invoices(scraped_invoices, db_invoices)
    await database.insert_new_invoice(conn, missing_invoices)

    return  jsonable_encoder({'new': missing_invoices,"found_invoices": scraped_invoices})



@router.get("/invoice", tags=["o2 family"])
async def get_invoice(conn: Connection = Depends(get_db_connection), href: str = Query(..., description="The invoice detail URL")):
    user = os.getenv("O2_NAME")
    password = os.getenv("O2_PASSWORD")
    
    if not user or not password:
        raise HTTPException(status_code=500, detail="O2_NAME and/or O2_PASSWORD values are not set up")
    
    instance = Watch(uid=user, pwd=password)
    scraped_invoice = instance.login().get_invoice_details(href)

    errors = await database.insert_new_invoice_details(conn, scraped_invoice)
    if errors:
        # Možné vrácení chyb s odpovědí, nebo jen logování chyb.
        return JSONResponse(status_code=207, content={"success": "Partial success", "errors": errors, 'founds': scraped_invoice})

    response = jsonable_encoder(scraped_invoice)
    return JSONResponse(content=response)



# Contractrs

class CONTRACT_ACTION(StrEnum):
    INFO = 'info',
    SYNC = 'sync'

@router.get("/contracts", tags=["o2 family"])
async def get_contracts(action: CONTRACT_ACTION = 'info', conn: Connection = Depends(get_db_connection)):
    if not user or not password:
        raise HTTPException(status_code=500, detail="02_NAME and/or O2_PASSWORD values are not set up")
    db_contracts = []
    try:
         query = "SELECT * FROM mobile_services.phone_numbers"
         db_contracts = await conn.fetch(query)
    except:
        return {'error': 'error'}
    scraped = []
    try:
        scraped =  instance.login().scrape_contracts()
    except:
        raise HTTPException(status_code=500, detail="contracts are not available")
    missing = []
    missing = database.find_unstored_phone_numbers(scraped,db_contracts)
    if action == 'sync':
        await database.insert_new_phone_numbers(conn,missing)
    return {'found_contracts': scraped, 'new_contracts': missing, 'action': action}


from pydantic import BaseModel

class PostTarif(BaseModel):
    name: str
    fee: int

class Tariff(BaseModel):
    name: str
    fee: float
    



@router.post('/tariff', tags=['o2 family'])
async def create_tariff(tariff: Tariff, conn: Connection = Depends(get_db_connection)):

    await database.insert_new_tariff(conn,new_tarif=tariff)

    return tariff