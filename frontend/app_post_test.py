#!/usr/bin/env python3.11
from flask import Flask, request, jsonify
import requests
import time

app = Flask(__name__)

API_BASE_URL = 'http://localhost:8000'

@app.route('/')
def index():
    return """
    <h1>Teste POST - Sistema de Gestão Escolar</h1>
    <h2>Formulário de Teste</h2>
    <form action="/test-post" method="POST">
        <p>
            <label>Nome:</label><br>
            <input type="text" name="nome" value="Teste Usuario" required>
        </p>
        <p>
            <label>Email:</label><br>
            <input type="email" name="email" value="teste@example.com">
        </p>
        <p>
            <label>CPF:</label><br>
            <input type="text" name="cpf" value="">
        </p>
        <p>
            <label>Telefone:</label><br>
            <input type="text" name="telefone" value="11987654321">
        </p>
        <p>
            <button type="submit">Testar POST</button>
        </p>
    </form>
    
    <h2>Teste Direto</h2>
    <p><a href="/direct-test">Teste POST Direto (sem formulário)</a></p>
    """

@app.route('/test-post', methods=['POST'])
def test_post():
    try:
        # Gerar CPF único
        unique_cpf = str(int(time.time() * 1000000) % 100000000000).zfill(11)
        
        # Coletar dados do formulário
        data = {
            'nome': request.form.get('nome', 'Teste Usuario'),
            'email': request.form.get('email', f'teste_{unique_cpf}@example.com'),
            'cpf': unique_cpf,
            'telefone': request.form.get('telefone', '11987654321'),
            'data_nascimento': '1990-01-01',
            'endereco': 'Rua Teste, 123',
            'observacoes': 'Teste POST via formulário'
        }
        
        # Fazer requisição para FastAPI
        url = f"{API_BASE_URL}/api/v1/alunos"
        response = requests.post(url, data=data, timeout=10)
        
        if response.status_code == 201:
            aluno = response.json()
            return f"""
            <h1>✅ SUCESSO!</h1>
            <p><strong>Aluno criado com sucesso via POST!</strong></p>
            <p>ID: {aluno['id']}</p>
            <p>Nome: {aluno['nome']}</p>
            <p>CPF: {aluno['cpf']}</p>
            <p>Email: {aluno['email']}</p>
            <p><a href="/">Voltar</a></p>
            """
        else:
            return f"""
            <h1>❌ ERRO</h1>
            <p>Status: {response.status_code}</p>
            <p>Resposta: {response.text}</p>
            <p><a href="/">Voltar</a></p>
            """
            
    except Exception as e:
        return f"""
        <h1>❌ ERRO DE EXCEÇÃO</h1>
        <p>Erro: {str(e)}</p>
        <p><a href="/">Voltar</a></p>
        """

@app.route('/direct-test')
def direct_test():
    try:
        # Gerar CPF único
        unique_cpf = str(int(time.time() * 1000000) % 100000000000).zfill(11)
        
        # Dados de teste
        data = {
            'nome': 'Teste Direto',
            'email': f'teste.direto_{unique_cpf}@example.com',
            'cpf': unique_cpf,
            'telefone': '11987654321',
            'data_nascimento': '1985-05-15',
            'endereco': 'Rua Teste Direto, 456',
            'observacoes': 'Teste POST direto'
        }
        
        # Fazer requisição para FastAPI
        url = f"{API_BASE_URL}/api/v1/alunos"
        response = requests.post(url, data=data, timeout=10)
        
        if response.status_code == 201:
            aluno = response.json()
            return f"""
            <h1>✅ TESTE DIRETO - SUCESSO!</h1>
            <p><strong>Aluno criado com sucesso!</strong></p>
            <p>ID: {aluno['id']}</p>
            <p>Nome: {aluno['nome']}</p>
            <p>CPF: {aluno['cpf']}</p>
            <p>Email: {aluno['email']}</p>
            <p><a href="/">Voltar</a></p>
            """
        else:
            return f"""
            <h1>❌ TESTE DIRETO - ERRO</h1>
            <p>Status: {response.status_code}</p>
            <p>Resposta: {response.text}</p>
            <p><a href="/">Voltar</a></p>
            """
            
    except Exception as e:
        return f"""
        <h1>❌ TESTE DIRETO - ERRO DE EXCEÇÃO</h1>
        <p>Erro: {str(e)}</p>
        <p><a href="/">Voltar</a></p>
        """

@app.route('/status')
def status():
    try:
        # Testar conexão com FastAPI
        url = f"{API_BASE_URL}/api/v1/alunos"
        response = requests.get(url, timeout=5)
        
        return f"""
        <h1>Status da Conexão</h1>
        <p>FastAPI URL: {API_BASE_URL}</p>
        <p>Status GET /alunos: {response.status_code}</p>
        <p>Resposta: {len(response.json()) if response.status_code == 200 else 'Erro'} alunos</p>
        <p><a href="/">Voltar</a></p>
        """
    except Exception as e:
        return f"""
        <h1>Status da Conexão - ERRO</h1>
        <p>Erro: {str(e)}</p>
        <p><a href="/">Voltar</a></p>
        """

if __name__ == '__main__':
    print("Iniciando Flask para teste POST...")
    print(f"API Base URL: {API_BASE_URL}")
    app.run(debug=False, host='0.0.0.0', port=5000)

