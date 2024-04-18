from dotenv import load_dotenv
import os
from typing import List, Optional
import asyncpg
from asyncpg import Connection

from .webwatcher.main import INVCE_item_contract
load_dotenv('./.env')

DATABASE_URL = os.getenv("DATABASE_URL")




from pydantic import BaseModel

class Contract(BaseModel):
    tariff: str
    uuid: str
    data: str

class Phone_number(BaseModel):
    phone_number: str
    status: str
   

class Tariff(BaseModel):
    name: str
    monthly_fee: float

class Invoice(BaseModel):
    title: str
    href: str
    issue_date: str
    due_date: str
    amount: float
    is_paid: Optional[bool] = False
    payment_date: Optional[str] = None
    invoice_number: int


class scrapped_Invoice(BaseModel):
    invoice_number: int
    title: str
    href: str
    created: str
    due_date: str
    amount_CZK: int
    status: str
    paid: bool






async def get_db_connection():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        await conn.close()



# Funkce pro porovnání a vytvoření nových Phone_number objektů
def find_unstored_phone_numbers(original: List[Contract], stored: List[Phone_number]) -> List[Phone_number]:
    stored_phone_numbers = {contract['phone_number'] for contract in stored}
    missing_phone_numbers: List[Phone_number] = [{'phone_number': contract['uuid'], 'status': 'NEW'} for contract in original if contract['uuid'] not in stored_phone_numbers]
    return missing_phone_numbers

def find_missing_invoices(original: List[scrapped_Invoice], stored: List[Invoice]) -> List[Invoice]:
    stored_invoices = {invoice['invoice_number'] for invoice in stored}
    missing_invoices: List[Invoice] = [ invoice   for invoice in original if invoice['invoice_number'] not in stored_invoices]
    return missing_invoices

# def find_missing_invoices(original: List[Invoice], scrapped: List[scrapped_Invoice]) -> List[Invoice]:
#     scrapped_numbers = {inv.invoice_number for inv in scrapped}
#     missing_invoices = [inv for inv in original if inv.invoice_number not in scrapped_numbers]
#     return missing_invoices



async def insert_new_phone_numbers(conn: Connection, phone_numbers: List[Phone_number]):
    # Vytvoření příkazu pro vložení
    insert_query = """
    INSERT INTO mobile_services.phone_numbers(phone_number, status)
    VALUES($1, $2)
    """
    for item in phone_numbers:
        await conn.execute(insert_query, item['phone_number'], item['status'])


async def insert_new_tariff(conn: Connection, new_tarif: Tariff):
    insert_query = """
    INSERT INTO mobile_services.tariff(name,monthly_fee)
    VALUES($1,$2)
    """

    await conn.execute(insert_query, new_tarif['name'], new_tarif['monthly_fee'] )



async def insert_new_invoice(conn: Connection, new_invoices: List[Invoice]):
    insert_query = """
    INSERT INTO mobile_services.invoices (title, href, issue_date, due_date, amount, is_paid, invoice_number)
    VALUES ($1, $2, $3, $4, $5, $6, $7);
    """

    for new_invoice in new_invoices:
        await conn.execute(insert_query, new_invoice['title'], new_invoice['href'], new_invoice['issue_date'], new_invoice['due_date'], new_invoice['amount'], new_invoice['is_paid'], new_invoice['invoice_number'])


async def insert_new_invoice_details(conn: Connection, invoiceItem: dict[str, INVCE_item_contract]):
    import json
    insert_query = """
    INSERT INTO mobile_services.invoice_items (invoice_number, phone_number, amount, details)
    VALUES ($1, $2, $3, $4);
    """

    errors = []
    for contract, value in invoiceItem.items():
        details = json.dumps(value)
        try:
            await conn.execute(insert_query, int(value['invoice_number']), contract, value['total_sum'], details)
        except asyncpg.exceptions.UniqueViolationError:
            # Přidání selhání do seznamu chyb pro pozdější zpracování nebo záznam.
            errors.append(f"Failed to insert item with invoice number {value['invoice_number']} and contract {contract} due to duplication.")
        except asyncpg.exceptions.ForeignKeyViolationError as e:
            errors.append(str(e))
            
    return errors