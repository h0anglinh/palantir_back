from fastapi import APIRouter,HTTPException, Query, Depends
import os
import httpx
from dotenv import load_dotenv
from asyncpg import Connection
from ..services.database import get_db_connection
from ..services import database
from ..services.dependencies import get_bank_data
load_dotenv()
TOKEN = os.getenv("FIO_TOKEN")
FIO_ACCOUNT = os.getenv("FIO_ACCOUNT_PERSONAL")

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
from pydantic import BaseModel
from typing import List
router = APIRouter(prefix='/fio')

from ..models.fio import BankData
import httpx

from datetime import date
from dateutil.relativedelta import relativedelta
format_time = "%Y-%m-%d" 

now = date.today()
today = now.strftime(format_time)
current_year = now.year
two_month_ago = (now - relativedelta(months=2)).strftime(format_time)






# def two_month_ago():
#     return (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")

# def today():
#     return datetime.now().strftime("%Y-%m-%d")

    
@router.get('/period', tags=['FIO'], summary='Get balance history', response_model=BankData)
async def get_status(bank_data=Depends(get_bank_data)):
    return bank_data




@router.get('/store', tags=['FIO'], summary='save transaction to DB')
async def save_transaction(conn: Connection = Depends(get_db_connection)):
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/fio/period")
        data: BankData = response.json()

        transactionList = data['accountStatement']['transactionList']['transaction']

        res  = await database.insert_new_bank_record(conn,transactionList=transactionList)



        # Zpracování dat
        return res
     
    #  res  = await database.insert_new_bank_record(conn=conn)

class PaymentOrder(BaseModel):
    accountTo: str
    accountCodeTo: str
    amount: float = 0.0
    date: str = today
    currency: str = "CZK"

@router.post("/create_payment/" , tags=['FIO'])
async def create_payment(order: PaymentOrder):
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Import>
      <Orders>
        <DomesticTransaction>
          <accountFrom>{FIO_ACCOUNT}</accountFrom>
          <currency>{order.currency}</currency>
          <amount>{order.amount}</amount>
          <accountTo>{order.accountTo}</accountTo>
          <bankCode>{order.accountCodeTo}</bankCode>
          <date>{order.date}</date>
        </DomesticTransaction>
      </Orders>
    </Import>"""

    # Příprava dat pro odeslání
    data = {
        'token': TOKEN,  # Token získaný od uživatele
        'type': 'xml',   # Předpokládáme, že typ je 'xml'
    }
    files = {
        'file': ('payment_orders.xml', xml_content, 'application/xml')
    }

    # Zde bys odeslal XML do banky pomocí HTTP klienta, například:
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.post('/import/', data=data, files=files)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Nepodařilo se odeslat platbu.")
    
    return {"message": "Platba byla úspěšně odeslána.", "response": response.text}


