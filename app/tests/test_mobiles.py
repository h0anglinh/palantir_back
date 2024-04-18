from app.main import app

import pytest
from fastapi.testclient import TestClient

client = TestClient(app)

def test_contracts():
    response = client.get('/mobiles/contracts')
    assert response.status_code == 200
    data = response.json()
    assert "action" in data
    assert "new_contracts" in data
    assert "found_contracts" in data
    assert data['action'] == 'info'



def test_invoices():
    response = client.get('/mobiles/invoices')
    data = response.json()
    assert 'new' in data
    assert 'found_invoices' in data
    assert response.status_code == 200



def test_invoice_detail():

    response = client.get('/mobiles/invoice', params={'href': 'https://moje.o2family.cz/vyuctovani-a-prehledy/detail-faktury/7412810571'})
    data = response.json()
    assert 'contracts' in data
    assert response.status_code == 200
    
    response = client.get('/mobiles/invoice', params={'href': 'https://moje.o2family.cz/vyuctovani-a-prehledy/detail-faktury/7412810571'})
    data = response.json()
    assert 'contracts' in data
    assert response.status_code == 200