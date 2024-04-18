from fastapi import APIRouter,HTTPException, Query
import os
import httpx
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("FIO_TOKEN")
FIO_ACCOUNT = os.getenv("FIO_ACCOUNT_PERSONAL")
from pydantic import BaseModel
from typing import List
router = APIRouter(prefix='/fio')



from datetime import date
from dateutil.relativedelta import relativedelta
format_time = "%Y-%m-%d" 

now = date.today()
today = now.strftime(format_time)
current_year = now.year
two_month_ago = (now - relativedelta(months=2)).strftime(format_time)





BASE_URL = 'https://www.fio.cz/ib_api/rest'

@router.get('/period', tags=['FIO'], summary='Get balance history' )
async def get_status(date_from: str = Query(default=two_month_ago, description=f'earliest date is 180 days from now, if you want earlier date, api must be authorized, format [yyyy-mm-dd]'), date_to: str = Query(default=today, description=f'date to value, format [yyyy-mm-dd]')):
    try:
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get(f'/periods/{TOKEN}/{date_from}/{date_to}/transactions.json')
            response.raise_for_status()  # Vyvolá výjimku pro chybné HTTP kódy
            return response.json()
    except httpx.HTTPStatusError as e:
        detail = {"error": f"Chyba HTTP stavového kódu: {e.response.status_code}", "detail": str(e)}
        raise HTTPException(status_code=e.response.status_code, detail=detail)
    except httpx.RequestError as e:
        # Chyba spojení, např. problémy sítě
        detail = {"error": "Chyba spojení s externím API", "detail": str(e)}
        raise HTTPException(status_code=503, detail=detail)
    except Exception as e:
        # Ostatní chyby
        raise HTTPException(status_code=500, detail=f"Neznámá chyba: {str(e)}")
    

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
