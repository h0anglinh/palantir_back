from fastapi import FastAPI, Depends, HTTPException, Query
import httpx
from datetime import datetime, timedelta
import os
import httpx
from dotenv import load_dotenv

from ..models.fio import BankData
load_dotenv()

TOKEN = os.getenv("FIO_TOKEN")
BASE_URL = 'https://www.fio.cz/ib_api/rest'


def two_month_ago():
    return (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")

def today():
    return datetime.now().strftime("%Y-%m-%d")
# Vytvoříme pomocnou závislost, která vrátí parametry
async def get_date_range(
    date_from: str = Query(default=two_month_ago(), description='earliest date is 180 days from now, if you want earlier date, api must be authorized, format [yyyy-mm-dd]'),
    date_to: str = Query(default=today(), description='date to value, format [yyyy-mm-dd]')
):
    return date_from, date_to

# Použijeme tuto závislost pro získání dat
async def get_bank_data(date_range: tuple = Depends(get_date_range)) -> BankData:
    date_from, date_to = date_range
    try:
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get(f'/periods/{TOKEN}/{date_from}/{date_to}/transactions.json')
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        detail = {"error": f"HTTP status code error: {e.response.status_code}", "detail": str(e)}
        raise HTTPException(status_code=e.response.status_code, detail=detail)
    except httpx.RequestError as e:
        detail = {"error": "Connection error with external API", "detail": str(e)}
        raise HTTPException(status_code=503, detail=detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {str(e)}")
