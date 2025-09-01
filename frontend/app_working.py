#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""
Versão funcional do Flask para o sistema de gerenciamento da academia.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import requests
import os
import logging
from werkzeug.utils import secure_filename

# Configuração da aplicação
app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-in-production'

# Configurações
API_BASE_URL = 'http://localhost:8000'
UPLOAD_FOLDER = 'static/uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

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
    stats = {
        'total_alunos': 0,
        'total_professores': 0,
        'total_turmas': 0,
        'total_eventos': 0
    }
    
    try:
        # Buscar apenas alunos para evitar travamento
        alunos_response = api_request('/alunos')
        if alunos_response and alunos_response.status_code == 200:
            stats['total_alunos'] = len(alunos_response.json())
    except Exception as e:
        app.logger.error(f"Erro ao buscar estatísticas: {e}")
    
    try:
        return render_template('index.html', stats=stats)
    except Exception as e:
        app.logger.error(f"Erro ao renderizar template: {e}")
        return f"""
        <h1>Sistema de Gestão Escolar</h1>
        <p>Total de Alunos: {stats['total_alunos']}</p>
        <ul>
            <li><a href="/alunos">Gerenciar Alunos</a></li>
            <li><a href="/professores">Gerenciar Professores</a></li>
        </ul>
        """

# === ROTAS PARA ALUNOS ===

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
            flash('Erro ao carregar lista de alunos.', 'error')
            app.logger.error(f"Erro ao carregar alunos: {response.status_code if response else 'Sem resposta'}")
        
        try:
            return render_template('alunos/list.html', alunos=alunos)
        except Exception as e:
            app.logger.error(f"Erro ao renderizar template alunos/list.html: {e}")
            # Fallback para HTML simples
            html = "<h1>Lista de Alunos</h1>"
            html += f"<p>Total: {len(alunos)} alunos</p>"
            html += '<p><a href="/alunos/novo">Novo Aluno</a></p>'
            html += "<ul>"
            for aluno in alunos:
                html += f"<li>ID: {aluno['id']} - Nome: {aluno['nome']} - CPF: {aluno.get('cpf', 'N/A')}</li>"
            html += "</ul>"
            return html
            
    except Exception as e:
        app.logger.error(f"Erro na função alunos_list: {e}")
        return f"<h1>Erro</h1><p>{e}</p><p><a href='/'>Voltar</a></p>"

@app.route('/alunos/novo')
def alunos_novo():
    """Formulário para novo aluno."""
    try:
        return render_template('alunos/form.html', aluno=None, action='criar')
    except Exception as e:
        app.logger.error(f"Erro ao renderizar template alunos/form.html: {e}")
        # Fallback para HTML simples
        return """
        <h1>Novo Aluno</h1>
        <form action="/alunos/salvar" method="POST" enctype="multipart/form-data">
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
                <label>Foto:</label><br>
                <input type="file" name="foto" accept="image/*">
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
        
        # Processar arquivo de foto se enviado
        files = {}
        if 'foto' in request.files:
            foto = request.files['foto']
            if foto and foto.filename:
                filename = secure_filename(foto.filename)
                files['foto'] = (filename, foto.read(), foto.content_type)
        
        app.logger.info(f"Dados recebidos: {data}")
        app.logger.info(f"Arquivos: {list(files.keys())}")
        
        # Criar novo aluno
        response = api_request('/alunos', method='POST', data=data, files=files)
        
        if response and response.status_code == 201:
            aluno = response.json()
            flash(f'Aluno {aluno["nome"]} cadastrado com sucesso!', 'success')
            app.logger.info(f"Aluno criado: {aluno['nome']}")
            return redirect(url_for('alunos_list'))
        else:
            error_msg = 'Erro ao salvar aluno.'
            if response:
                try:
                    error_detail = response.json().get('detail', '')
                    if error_detail:
                        error_msg += f' {error_detail}'
                except:
                    error_msg += f' Status: {response.status_code}'
            
            flash(error_msg, 'error')
            app.logger.error(f"Erro ao salvar aluno: {response.text if response else 'Sem resposta'}")
            return redirect(url_for('alunos_novo'))
    
    except Exception as e:
        flash(f'Erro interno ao salvar aluno: {e}', 'error')
        app.logger.error(f"Erro interno ao salvar aluno: {e}")
        return redirect(url_for('alunos_novo'))

# === ROTAS PARA PROFESSORES ===

@app.route('/professores')
def professores_list():
    """Lista todos os professores."""
    try:
        response = api_request('/professores')
        professores = []
        
        if response and response.status_code == 200:
            professores = response.json()
            app.logger.info(f"Carregados {len(professores)} professores")
        else:
            flash('Erro ao carregar lista de professores.', 'error')
            app.logger.error(f"Erro ao carregar professores: {response.status_code if response else 'Sem resposta'}")
        
        try:
            return render_template('professores/list.html', professores=professores)
        except Exception as e:
            app.logger.error(f"Erro ao renderizar template professores/list.html: {e}")
            # Fallback para HTML simples
            html = "<h1>Lista de Professores</h1>"
            html += f"<p>Total: {len(professores)} professores</p>"
            html += '<p><a href="/professores/novo">Novo Professor</a></p>'
            html += "<ul>"
            for professor in professores:
                html += f"<li>ID: {professor['id']} - Nome: {professor['nome']} - CPF: {professor.get('cpf', 'N/A')}</li>"
            html += "</ul>"
            return html
            
    except Exception as e:
        app.logger.error(f"Erro na função professores_list: {e}")
        return f"<h1>Erro</h1><p>{e}</p><p><a href='/'>Voltar</a></p>"

@app.route('/professores/novo')
def professores_novo():
    """Formulário para novo professor."""
    try:
        return render_template('professores/form.html', professor=None, action='criar')
    except Exception as e:
        app.logger.error(f"Erro ao renderizar template professores/form.html: {e}")
        # Fallback para HTML simples
        return """
        <h1>Novo Professor</h1>
        <form action="/professores/salvar" method="POST" enctype="multipart/form-data">
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
                <label>Especialidade:</label><br>
                <input type="text" name="especialidade">
            </p>
            <p>
                <label>Observações:</label><br>
                <textarea name="observacoes"></textarea>
            </p>
            <p>
                <label>Foto:</label><br>
                <input type="file" name="foto" accept="image/*">
            </p>
            <p>
                <button type="submit">Cadastrar Professor</button>
                <a href="/professores">Cancelar</a>
            </p>
        </form>
        """

@app.route('/professores/salvar', methods=['POST'])
def professores_salvar():
    """Salvar (criar) professor."""
    try:
        # Coletar dados do formulário
        data = {
            'nome': request.form.get('nome'),
            'email': request.form.get('email'),
            'cpf': request.form.get('cpf'),
            'telefone': request.form.get('telefone'),
            'data_nascimento': request.form.get('data_nascimento'),
            'especialidade': request.form.get('especialidade'),
            'observacoes': request.form.get('observacoes')
        }
        
        # Remover campos vazios
        data = {k: v for k, v in data.items() if v}
        
        # Processar arquivo de foto se enviado
        files = {}
        if 'foto' in request.files:
            foto = request.files['foto']
            if foto and foto.filename:
                filename = secure_filename(foto.filename)
                files['foto'] = (filename, foto.read(), foto.content_type)
        
        app.logger.info(f"Dados recebidos: {data}")
        app.logger.info(f"Arquivos: {list(files.keys())}")
        
        # Criar novo professor
        response = api_request('/professores', method='POST', data=data, files=files)
        
        if response and response.status_code == 201:
            professor = response.json()
            flash(f'Professor {professor["nome"]} cadastrado com sucesso!', 'success')
            app.logger.info(f"Professor criado: {professor['nome']}")
            return redirect(url_for('professores_list'))
        else:
            error_msg = 'Erro ao salvar professor.'
            if response:
                try:
                    error_detail = response.json().get('detail', '')
                    if error_detail:
                        error_msg += f' {error_detail}'
                except:
                    error_msg += f' Status: {response.status_code}'
            
            flash(error_msg, 'error')
            app.logger.error(f"Erro ao salvar professor: {response.text if response else 'Sem resposta'}")
            return redirect(url_for('professores_novo'))
    
    except Exception as e:
        flash(f'Erro interno ao salvar professor: {e}', 'error')
        app.logger.error(f"Erro interno ao salvar professor: {e}")
        return redirect(url_for('professores_novo'))

if __name__ == '__main__':
    print("Iniciando aplicação Flask funcional...")
    print(f"API Base URL: {API_BASE_URL}")
    app.run(debug=False, host='0.0.0.0', port=5000)

