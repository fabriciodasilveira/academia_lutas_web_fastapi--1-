#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""
Script de teste para reproduzir o problema de comunicação entre Flask e FastAPI.
"""

import requests
import sys
import traceback

def test_api_request(endpoint, method='GET', data=None, files=None):
    """Função que simula exatamente o que o Flask está fazendo."""
    api_base_url = 'http://localhost:8000'
    url = f"{api_base_url}/api/v1{endpoint}"
    
    print(f"Testando: {method} {url}")
    if data:
        print(f"Data: {data}")
    if files:
        print(f"Files: {files}")
    
    try:
        if method == 'GET':
            response = requests.get(url)
        elif method == 'POST':
            response = requests.post(url, data=data, files=files)
        elif method == 'PUT':
            if files:
                response = requests.put(url, data=data, files=files)
            else:
                response = requests.put(url, data=data)
        elif method == 'DELETE':
            response = requests.delete(url)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        return response
    except Exception as e:
        print(f"Erro na requisição: {e}")
        traceback.print_exc()
        return None

def main():
    print("=== Teste de Comunicação Flask -> FastAPI ===\n")
    
    # Teste 1: GET /alunos
    print("1. Testando GET /alunos")
    response = test_api_request('/alunos')
    print(f"Sucesso: {response is not None and response.status_code == 200}\n")
    
    # Teste 2: POST /alunos (simulando o que o Flask faz)
    print("2. Testando POST /alunos")
    data = {
        'nome': 'Teste Script',
        'email': 'teste.script@example.com',
        'cpf': '11111111111',
        'telefone': '11987654321',
        'data_nascimento': '1995-03-20',
        'endereco': 'Rua Script, 789',
        'observacoes': 'Teste via script'
    }
    
    # Remover campos vazios (como o Flask faz)
    data = {k: v for k, v in data.items() if v}
    
    response = test_api_request('/alunos', method='POST', data=data)
    print(f"Sucesso: {response is not None and response.status_code == 201}\n")
    
    # Teste 3: POST com arquivo (simulando upload)
    print("3. Testando POST /alunos com arquivo")
    files = {}
    # Simular um arquivo vazio (como quando não há upload)
    response = test_api_request('/alunos', method='POST', data=data, files=files)
    print(f"Sucesso: {response is not None and response.status_code == 201}\n")

if __name__ == "__main__":
    main()

