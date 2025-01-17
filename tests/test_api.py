# tests/test_api.py
import json
import pytest
from flask import url_for

def test_voices_endpoint(test_client, mock_loaded_models):
    """Test /api/voices endpoint"""
    response = test_client.get('/api/voices')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'rmz' in data
    assert 'en' in data

def test_tts_endpoint_empty_text(test_client):
    """Test TTS endpoint with empty text"""
    response = test_client.post('/api/short', json={
        'text': '',
        'voice': 'test-mms'
    })
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'message' in data
    assert data['message'] == 'Text must not be empty'


def test_tts_endpoint_missing_text(test_client):
    """Test TTS endpoint with missing text field"""
    response = test_client.post('/api/short', json={
        'voice': 'test-mms'
    })
    assert response.status_code == 400

def test_tts_endpoint_invalid_voice(test_client):
    """Test TTS endpoint with invalid voice"""
    response = test_client.post('/api/short', json={
        'text': 'Hello',
        'voice': 'nonexistent-voice'
    })
    assert response.status_code == 404