#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""
Versão simplificada do Flask para testar funcionalidade POST.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import requests
import os
import logging

# Configuração da aplicação
app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-in-production'

# Configurações
API_BASE_URL = 'http://localhost:8000'

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def api_request(endpoint, method='GET', data=None, files=None):
    """Função auxiliar para fazer requisições à API FastAPI."""
    url = f"{API_BASE_URL}/api/v1{endpoint}"
    
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
        
        app.logger.info(f"API Request: {method} {url} - Status: {response.status_code}")
        return response
        
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Erro na requisição {method} {url}: {e}")
        return None

@app.route('/')
def index():
    """Página inicial simplificada."""
    return """
    <h1>Sistema de Gestão Escolar - Teste</h1>
    <ul>
        <li><a href="/alunos">Lista de Alunos</a></li>
        <li><a href="/alunos/novo">Novo Aluno</a></li>
        <li><a href="/test-post">Teste POST Direto</a></li>
    </ul>
    """

@app.route('/alunos')
def alunos_list():
    """Lista todos os alunos."""
    try:
        response = api_request('/alunos')
        alunos = []
        
        if response and response.status_code == 200:
            alunos = response.json()
            app.logger.info(f"Carregados {len(alunos)} alunos")
        else:
            app.logger.error(f"Erro ao carregar alunos: {response.status_code if response else 'Sem resposta'}")
        
        # Retornar HTML simples
        html = "<h1>Lista de Alunos</h1>"
        html += f"<p>Total: {len(alunos)} alunos</p>"
        html += "<ul>"
        for aluno in alunos:
            html += f"<li>ID: {aluno['id']} - Nome: {aluno['nome']} - CPF: {aluno.get('cpf', 'N/A')}</li>"
        html += "</ul>"
        html += '<p><a href="/alunos/novo">Novo Aluno</a> | <a href="/">Voltar</a></p>'
        return html
        
    except Exception as e:
        app.logger.error(f"Erro na função alunos_list: {e}")
        return f"<h1>Erro</h1><p>{e}</p><p><a href='/'>Voltar</a></p>"

@app.route('/alunos/novo')
def alunos_novo():
    """Formulário para novo aluno."""
    return """
    <h1>Novo Aluno</h1>
    <form action="/alunos/salvar" method="POST">
        <p>
            <label>Nome *:</label><br>
            <input type="text" name="nome" required>
        </p>
        <p>
            <label>Email:</label><br>
            <input type="email" name="email">
        </p>
        <p>
            <label>CPF:</label><br>
            <input type="text" name="cpf">
        </p>
        <p>
            <label>Telefone:</label><br>
            <input type="text" name="telefone">
        </p>
        <p>
            <label>Data de Nascimento:</label><br>
            <input type="date" name="data_nascimento">
        </p>
        <p>
            <label>Endereço:</label><br>
            <textarea name="endereco"></textarea>
        </p>
        <p>
            <label>Observações:</label><br>
            <textarea name="observacoes"></textarea>
        </p>
        <p>
            <button type="submit">Cadastrar Aluno</button>
            <a href="/alunos">Cancelar</a>
        </p>
    </form>
    """

@app.route('/alunos/salvar', methods=['POST'])
def alunos_salvar():
    """Salvar (criar) aluno."""
    try:
        # Coletar dados do formulário
        data = {
            'nome': request.form.get('nome'),
            'email': request.form.get('email'),
            'cpf': request.form.get('cpf'),
            'telefone': request.form.get('telefone'),
            'data_nascimento': request.form.get('data_nascimento'),
            'endereco': request.form.get('endereco'),
            'observacoes': request.form.get('observacoes')
        }
        
        # Remover campos vazios
        data = {k: v for k, v in data.items() if v}
        
        app.logger.info(f"Dados recebidos: {data}")
        
        # Criar novo aluno
        response = api_request('/alunos', method='POST', data=data)
        
        if response and response.status_code == 201:
            aluno = response.json()
            app.logger.info(f"Aluno criado: {aluno['nome']}")
            return f"""
            <h1>Sucesso!</h1>
            <p>Aluno cadastrado com sucesso!</p>
            <p>ID: {aluno['id']}</p>
            <p>Nome: {aluno['nome']}</p>
            <p><a href="/alunos">Ver Lista de Alunos</a> | <a href="/alunos/novo">Cadastrar Outro</a></p>
            """
        else:
            error_msg = 'Erro ao salvar aluno.'
            if response:
                try:
                    error_detail = response.json().get('detail', '')
                    if error_detail:
                        error_msg += f' {error_detail}'
                except:
                    error_msg += f' Status: {response.status_code}'
            
            app.logger.error(f"Erro ao salvar aluno: {response.text if response else 'Sem resposta'}")
            return f"""
            <h1>Erro</h1>
            <p>{error_msg}</p>
            <p><a href="/alunos/novo">Tentar Novamente</a> | <a href="/alunos">Ver Lista</a></p>
            """
    
    except Exception as e:
        app.logger.error(f"Erro interno ao salvar aluno: {e}")
        return f"""
        <h1>Erro Interno</h1>
        <p>Erro interno ao salvar aluno: {e}</p>
        <p><a href="/alunos/novo">Tentar Novamente</a></p>
        """

@app.route('/test-post')
def test_post():
    """Teste POST direto."""
    try:
        import time
        unique_cpf = str(int(time.time() * 1000000) % 100000000000).zfill(11)
        
        data = {
            'nome': 'Teste Flask Direto',
            'email': f'teste.flask.direto_{unique_cpf}@example.com',
            'cpf': unique_cpf,
            'telefone': '11987654321',
            'data_nascimento': '1990-01-01',
            'endereco': 'Rua Teste Flask, 123',
            'observacoes': 'Teste POST direto via Flask'
        }
        
        response = api_request('/alunos', method='POST', data=data)
        
        if response and response.status_code == 201:
            aluno = response.json()
            return f"""
            <h1>Teste POST - Sucesso!</h1>
            <p>Aluno criado via teste direto:</p>
            <p>ID: {aluno['id']}</p>
            <p>Nome: {aluno['nome']}</p>
            <p>CPF: {aluno['cpf']}</p>
            <p><a href="/alunos">Ver Lista</a> | <a href="/">Voltar</a></p>
            """
        else:
            return f"""
            <h1>Teste POST - Erro</h1>
            <p>Status: {response.status_code if response else 'Sem resposta'}</p>
            <p>Resposta: {response.text if response else 'N/A'}</p>
            <p><a href="/">Voltar</a></p>
            """
            
    except Exception as e:
        return f"""
        <h1>Teste POST - Erro</h1>
        <p>Erro: {e}</p>
        <p><a href="/">Voltar</a></p>
        """

if __name__ == '__main__':
    print("Iniciando Flask simplificado para teste POST...")
    print(f"API Base URL: {API_BASE_URL}")
    app.run(debug=True, host='0.0.0.0', port=5000)

