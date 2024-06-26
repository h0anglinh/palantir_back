from dotenv import load_dotenv
from fastapi import Depends
from .dependencies import get_bank_data
import os
from typing import List, Optional
import asyncpg
from asyncpg import Connection
from ..models.fio import TransactionList
from datetime import datetime
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
    title: Optional[str]
    href: Optional[str]
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

class transaction(BaseModel):
    amount: float
    transaction_date: str
    sender_name: str
    execution_date: str
    sender_account: str
    receiver_account: str
    description_account: str
    message_for_receiver: str
    variable_symbol: str
    constant_symbol: str
    currency: str
    transaction_id: int




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

def find_updated_invoices(original: List[scrapped_Invoice], stored: List[Invoice]) -> List[Invoice]:
    results = []
    # Mapa pro rychlý přístup k invoice podle invoice_number
    invoice_dict = {invoice.invoice_number: invoice for invoice in stored}

    for scrapped in original:
        if scrapped.invoice_number in invoice_dict:
            invoice = invoice_dict[scrapped.invoice_number]
            # Porovnání is_paid a paid
            if invoice.is_paid != scrapped.paid:
                results.append(invoice)  # Přidáváme pouze relevantní Invoice objekty

    return results





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

def parse_payment_date(input_string):
    try:
        # Pokud řetězec začíná "Zaplaceno", parsovat datum
        if input_string.startswith("Zaplaceno"):
            date_str = input_string.split(" ")[1:]  # odstraní "Zaplaceno" a vezme zbytek
            date_str = " ".join(date_str)
            # Převede string na datetime objekt
            payment_date = datetime.strptime(date_str, '%d. %m. %Y')
            # Vrátí date objekt místo stringu
            return payment_date.date()
        else:
            # Jinak vrací None
            return None
    except ValueError:
        # Pro jistotu, pokud parsování selže
        return None


async def insert_new_invoice(conn: Connection, new_invoices: List[Invoice]):
    insert_query = """
    INSERT INTO mobile_services.invoices (title, href, issue_date, due_date, amount, is_paid, invoice_number, payment_date)
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    ON CONFLICT (invoice_number) DO UPDATE 
    SET is_paid = EXCLUDED.is_paid,
    payment_date = EXCLUDED.payment_date
    WHERE mobile_services.invoices.invoice_number = EXCLUDED.invoice_number;
    """
    for new_invoice in new_invoices:
        payment_date = parse_payment_date(new_invoice['status'])
        await conn.execute(insert_query, new_invoice['title'], new_invoice['href'], new_invoice['issue_date'], new_invoice['due_date'], new_invoice['amount'], new_invoice['is_paid'], new_invoice['invoice_number'], payment_date)




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


async def insert_new_bank_record( conn: Connection, transactionList:TransactionList ): # type: ignore
    insert_query = """
        INSERT INTO finance.payments (amount, transaction_date, sender_name, sender_account, message_for_receiver, constant_symbol, sender_bank_code, sender_bank_name, transaction_id)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """
    error = []
    success = []



    for inv in transactionList:
        transaction_id = inv['column22']['value']
        try:
            date_str = inv['column0']['value']
            date_str = date_str[:10] + 'T00:00:00' + date_str[10:]
            transaction_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z")

            msg_for_reciever = inv['column16']['value']
            ks = inv['column4']['value']
            currency = inv['column14']['value']
            sender_account = inv['column2']['value']
            bank_code = inv['column3']['value']
            bank_name = inv['column12']['value']
            transaction_id = inv['column22']['value']
            amount = inv['column1']['value']
            sender_name = inv['column10']['value']
            await conn.execute(insert_query, amount, transaction_date, sender_name, sender_account, msg_for_reciever, ks, bank_code, bank_name, transaction_id )
            success.append(f'transaction {transaction_id} ({amount} {currency}) added')
        except asyncpg.exceptions.UniqueViolationError as e:
            error.append(f'{transaction_id} already added')

       
    
    return {"error": error, "success": success}