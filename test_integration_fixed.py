#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""
Script de teste de integração completa entre Flask e FastAPI.
Simula o fluxo completo de cadastro de aluno.
"""

import requests
import json
import sys
import random
import time

def generate_unique_cpf():
    """Gera um CPF único para testes."""
    return str(int(time.time() * 1000000) % 100000000000).zfill(11)

def test_fastapi_direct():
    """Testa o FastAPI diretamente."""
    print("=== Teste 1: FastAPI Direto ===")
    
    try:
        # GET /alunos
        response = requests.get("http://localhost:8000/api/v1/alunos", timeout=10)
        print(f"GET /alunos - Status: {response.status_code}")
        if response.status_code == 200:
            alunos = response.json()
            print(f"Total de alunos: {len(alunos)}")
        
        # POST /alunos
        unique_cpf = generate_unique_cpf()
        data = {
            "nome": "Teste Integração",
            "email": f"teste.integracao_{unique_cpf}@example.com",
            "cpf": unique_cpf,
            "telefone": "11987654321",
            "data_nascimento": "1992-08-15",
            "endereco": "Rua Integração, 999",
            "observacoes": "Teste de integração completa"
        }
        
        response = requests.post("http://localhost:8000/api/v1/alunos", data=data, timeout=10)
        print(f"POST /alunos - Status: {response.status_code}")
        if response.status_code == 201:
            aluno = response.json()
            print(f"Aluno criado: ID {aluno['id']}, Nome: {aluno['nome']}")
            return aluno['id']
        else:
            print(f"Erro: {response.text}")
            return None
            
    except Exception as e:
        print(f"Erro no teste FastAPI: {e}")
        return None

def test_flask_simulation():
    """Simula o que o Flask faria."""
    print("\n=== Teste 2: Simulação Flask ===")
    
    try:
        # Simular função api_request do Flask
        def api_request(endpoint, method='GET', data=None, files=None):
            url = f"http://localhost:8000/api/v1{endpoint}"
            
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
            
            return response
        
        # Simular alunos_list()
        print("Simulando alunos_list()...")
        response = api_request('/alunos')
        if response and response.status_code == 200:
            alunos = response.json()
            print(f"✓ Lista de alunos carregada: {len(alunos)} alunos")
        else:
            print(f"✗ Erro ao carregar alunos: {response.status_code if response else 'Sem resposta'}")
        
        # Simular alunos_salvar()
        print("Simulando alunos_salvar()...")
        unique_cpf = generate_unique_cpf()
        data = {
            'nome': 'Teste Flask Sim',
            'email': f'teste.flask.sim_{unique_cpf}@example.com',
            'cpf': unique_cpf,
            'telefone': '11987654321',
            'data_nascimento': '1988-03-25',
            'endereco': 'Rua Flask Sim, 777',
            'observacoes': 'Teste simulação Flask'
        }
        
        # Remover campos vazios (como o Flask faz)
        data = {k: v for k, v in data.items() if v}
        
        files = {}  # Sem arquivo de foto
        
        response = api_request('/alunos', method='POST', data=data, files=files)
        if response and response.status_code == 201:
            aluno = response.json()
            print(f"✓ Aluno criado via simulação: ID {aluno['id']}, Nome: {aluno['nome']}")
            return aluno['id']
        else:
            print(f"✗ Erro ao criar aluno: {response.status_code if response else 'Sem resposta'}")
            if response:
                print(f"Resposta: {response.text}")
            return None
            
    except Exception as e:
        print(f"Erro na simulação Flask: {e}")
        return None

def test_form_data():
    """Testa envio de dados como formulário."""
    print("\n=== Teste 3: Dados de Formulário ===")
    
    try:
        # Simular dados de formulário HTML
        unique_cpf = generate_unique_cpf()
        form_data = {
            "nome": "Teste Form Data",
            "email": f"teste.form_{unique_cpf}@example.com",
            "cpf": unique_cpf,
            "telefone": "11987654321",
            "data_nascimento": "1985-12-05",
            "endereco": "Rua Form Data, 555",
            "observacoes": "Teste dados de formulário"
        }
        
        # Enviar como application/x-www-form-urlencoded
        response = requests.post(
            "http://localhost:8000/api/v1/alunos",
            data=form_data,
            timeout=10
        )
        
        print(f"POST form-data - Status: {response.status_code}")
        if response.status_code == 201:
            aluno = response.json()
            print(f"✓ Aluno criado via form-data: ID {aluno['id']}, Nome: {aluno['nome']}")
            return aluno['id']
        else:
            print(f"✗ Erro: {response.text}")
            return None
            
    except Exception as e:
        print(f"Erro no teste form-data: {e}")
        return None

def main():
    print("Iniciando testes de integração Flask <-> FastAPI\n")
    
    # Teste 1: FastAPI direto
    aluno_id_1 = test_fastapi_direct()
    
    # Teste 2: Simulação Flask
    aluno_id_2 = test_flask_simulation()
    
    # Teste 3: Form data
    aluno_id_3 = test_form_data()
    
    # Resumo
    print("\n=== RESUMO DOS TESTES ===")
    print(f"FastAPI Direto: {'✓ PASSOU' if aluno_id_1 else '✗ FALHOU'}")
    print(f"Simulação Flask: {'✓ PASSOU' if aluno_id_2 else '✗ FALHOU'}")
    print(f"Form Data: {'✓ PASSOU' if aluno_id_3 else '✗ FALHOU'}")
    
    if all([aluno_id_1, aluno_id_2, aluno_id_3]):
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("A integração Flask <-> FastAPI está funcionando corretamente.")
        return True
    else:
        print("\n❌ ALGUNS TESTES FALHARAM!")
        print("Há problemas na integração Flask <-> FastAPI.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

