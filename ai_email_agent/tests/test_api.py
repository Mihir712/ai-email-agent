import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure the project root is on sys.path so `backend` can be imported
sys.path.append(str(Path(__file__).resolve().parents[1]))

from backend.main import app

client = TestClient(app)


@pytest.mark.skipif(
    not os.environ.get('OPENAI_API_KEY'),
    reason='Skipping integration test when OPENAI_API_KEY is not set',
)
def test_generate_endpoint():
    payload = {"email": "Can we schedule a call next week?"}
    resp = client.post('/generate', json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert 'classification' in data
    assert 'draft_reply' in data
    assert isinstance(data['draft_reply'], str)
