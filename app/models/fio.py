from typing import List, Optional
from pydantic import BaseModel, Field

class ColumnDetail(BaseModel):
    value: Optional[object]  # 'object' type used for mixed types (int, str, etc.)
    name: str
    id: int

class Transaction(BaseModel):
    column22: ColumnDetail # ID pohybu
    column0: ColumnDetail # Datum
    column1: ColumnDetail # Objem / castka
    column14: ColumnDetail # Mena
    column2: ColumnDetail #Protiucet
    column10: ColumnDetail #Nazev protiuctu
    column3: ColumnDetail #Kod banky
    column12: ColumnDetail #Nazev Banky
    column4: ColumnDetail #KS Konstantni symbol
    column5: Optional[ColumnDetail] 
    column6: Optional[ColumnDetail]
    column7: Optional[ColumnDetail] #uzivatelska identifikace
    column16: ColumnDetail #zprava pro prijemnce
    column8: ColumnDetail # Typ
    column9: Optional[ColumnDetail] 
    column18: Optional[ColumnDetail]
    column25: Optional[ColumnDetail] #Komentar
    column26: Optional[ColumnDetail]
    column17: ColumnDetail #ID pokynu
    column27: Optional[ColumnDetail]

class TransactionList(BaseModel):
    transaction: List[Transaction]

class Info(BaseModel):
    accountId: str
    bankId: str
    currency: str
    iban: str
    bic: str
    openingBalance: float
    closingBalance: float
    dateStart: str
    dateEnd: str
    yearList: Optional[list]
    idList: Optional[list]
    idFrom: int
    idTo: int
    idLastDownload: Optional[int]

class AccountStatement(BaseModel):
    info: Info
    transactionList: TransactionList

class BankData(BaseModel):
    accountStatement: AccountStatement