"""Public demo boundary tests; transport doubles only for the upstream API."""
import base64
from pathlib import Path
import httpx
import pytest
from fastapi.testclient import TestClient
from backend.app.demo_gateway import create_gateway

PASSWORD='SYNTHETIC_GATEWAY_PASSWORD_123'

@pytest.fixture
def gateway(tmp_path):
    (tmp_path/'index.html').write_text('<html>SYNTHETIC BUILT FRONTEND</html>')
    observed=[]
    def handler(request):
        observed.append(request)
        return httpx.Response(201 if request.method=='POST' else 200,json={'synthetic_transport_fixture':True})
    app=create_gateway(password=PASSWORD,dist=tmp_path,transport=httpx.MockTransport(handler))
    with TestClient(app) as client:yield client,observed

def test_gate_requires_credentials_and_never_proxies_unauthorized_calls(gateway):
    client,observed=gateway
    assert client.get('/').status_code==401
    assert client.post('/api/v2/mas/runs',json={'question':'SYNTHETIC'}).status_code==401
    assert not observed
    for value in ['Basic broken!','Bearer SYNTHETIC','Basic '+base64.b64encode(b'demo:wrong').decode()]:
        assert client.get('/',headers={'Authorization':value}).status_code==401

def test_gate_serves_build_and_allows_only_current_demo_routes(gateway):
    client,observed=gateway
    auth=('demo',PASSWORD)
    assert 'SYNTHETIC BUILT FRONTEND' in client.get('/',auth=auth).text
    assert client.get('/api/v2/system/readiness',auth=auth).status_code==200
    assert client.post('/api/v2/mas/runs',json={'question':'SYNTHETIC'},auth=auth).status_code==201
    assert 'authorization' not in observed[-1].headers
    assert client.post('/api/v1/mas/runs',auth=auth).status_code==404
    assert client.get('/api/v2/knowledge/search',auth=auth).status_code==404
    assert client.get('/missing.js',auth=auth).status_code==404

def test_gate_limits_workflow_requests_and_body_size(gateway):
    client,_=gateway
    for _ in range(6):assert client.post('/api/v2/mas/runs',json={},auth=('demo',PASSWORD)).status_code==201
    assert client.post('/api/v2/mas/runs',json={},auth=('demo',PASSWORD)).status_code==429
    assert client.post('/api/v2/mas/runs',content='x'*16385,auth=('demo',PASSWORD)).status_code==413

def test_gate_fails_closed_for_missing_password_or_external_upstream(tmp_path):
    with pytest.raises(ValueError):create_gateway(password='')
    with pytest.raises(ValueError):create_gateway(password=PASSWORD,upstream='https://external.invalid',dist=tmp_path)
