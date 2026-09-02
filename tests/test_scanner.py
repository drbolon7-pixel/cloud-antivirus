import pytest
import json
from backend.app import app
from backend.scanner import AntivirusScanner

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    response = client.get('/api/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'

def test_scanner_initialization():
    scanner = AntivirusScanner()
    assert scanner is not None

def test_file_upload_requires_auth(client):
    with open('test.txt', 'wb') as f:
        f.write(b'test content')
    
    with open('test.txt', 'rb') as f:
        response = client.post('/api/scan', data={'file': f})
        assert response.status_code == 401
