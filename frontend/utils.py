# frontend/utils.py

import requests
from flask import session, current_app

# frontend/utils.py

import requests
from flask import session, current_app

def api_request(endpoint, method='GET', data=None, files=None, json=None, params=None, headers=None):
    """
    Função auxiliar para fazer requisições à API FastAPI, incluindo o token de autenticação.
    """
    api_base_url = current_app.config.get('API_BASE_URL', 'http://localhost:8000')
    url = f"{api_base_url}{endpoint}"

    request_headers = headers if headers is not None else {}
    if 'access_token' in session and 'Authorization' not in request_headers:
        request_headers['Authorization'] = f"Bearer {session['access_token']}"

    try:
        if method == 'GET':
            response = requests.get(url, timeout=10, params=params, headers=request_headers)
        elif method == 'POST':
            response = requests.post(url, data=data, files=files, json=json, timeout=10, headers=request_headers)
        elif method == 'PUT':
            response = requests.put(url, data=data, files=files, json=json, timeout=10, headers=request_headers)
        elif method == 'DELETE':
            response = requests.delete(url, timeout=10, headers=request_headers)
        else:
            return None

        if response.status_code == 401:
            session.clear()
        
        current_app.logger.info(f"API Request: {method} {url} - Status: {response.status_code}")
        return response
        
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Erro na requisição {method} {url}: {e}")
        return None