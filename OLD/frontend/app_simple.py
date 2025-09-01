#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""
Versão simplificada do Flask para testar a comunicação com o FastAPI.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import requests
import os

app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-in-production'

API_BASE_URL = 'http://localhost:8000'

# Função auxiliar para fazer requisições à API
def api_request(endpoint, method='GET', data=None, files=None):
    url = f"{API_BASE_URL}/api/v1{endpoint}"
    print(f"Fazendo requisição: {method} {url}")
    
    try:
        if method == 'GET':
            response = requests.get(url, timeout=10)
        elif method == 'POST':
            response = requests.post(url, data=data, files=files, timeout=10)
        elif method == 'PUT':
            if files:
                response = requests.put(url, data=data, files=files, timeout=10)
            else:
                response = requests.put(url, data=data, timeout=10)
        elif method == 'DELETE':
            response = requests.delete(url, timeout=10)
        
        print(f"Status: {response.status_code}")
        return response
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição: {e}")
        return None

@app.route('/')
def index():
    return "<h1>Flask Simples</h1><a href='/alunos'>Ver Alunos</a>"

@app.route('/alunos')
def alunos_list():
    print("Acessando /alunos")
    response = api_request('/alunos')
    alunos = []
    if response and response.status_code == 200:
        alunos = response.json()
        print(f"Encontrados {len(alunos)} alunos")
    else:
        print("Erro ao buscar alunos")
    
    # Retornar JSON simples para teste
    return jsonify({"alunos": alunos, "total": len(alunos)})

@app.route('/test-post')
def test_post():
    print("Testando POST")
    data = {
        'nome': 'Teste Flask Simples',
        'email': 'teste.simples@example.com',
        'cpf': '22222222222',
        'telefone': '11987654321',
        'data_nascimento': '1988-12-10',
        'endereco': 'Rua Simples, 123',
        'observacoes': 'Teste via Flask simples'
    }
    
    response = api_request('/alunos', method='POST', data=data)
    if response and response.status_code == 201:
        return jsonify({"status": "success", "data": response.json()})
    else:
        return jsonify({"status": "error", "message": response.text if response else "Sem resposta"})

if __name__ == '__main__':
    print("Iniciando Flask simples...")
    app.run(debug=True, host='0.0.0.0', port=5001)

