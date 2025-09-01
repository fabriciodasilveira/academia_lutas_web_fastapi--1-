#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""
Nova aplicação Flask para o sistema de gerenciamento da academia.
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
    """Página inicial com estatísticas."""
    stats = {
        'total_alunos': 0,
        'total_professores': 0,
        'total_turmas': 0,
        'total_eventos': 0
    }
    
    try:
        # Buscar dados dos endpoints
        alunos_response = api_request('/alunos')
        if alunos_response and alunos_response.status_code == 200:
            stats['total_alunos'] = len(alunos_response.json())
        
        professores_response = api_request('/professores')
        if professores_response and professores_response.status_code == 200:
            stats['total_professores'] = len(professores_response.json())
        
        turmas_response = api_request('/turmas')
        if turmas_response and turmas_response.status_code == 200:
            stats['total_turmas'] = len(turmas_response.json())
        
        eventos_response = api_request('/eventos')
        if eventos_response and eventos_response.status_code == 200:
            stats['total_eventos'] = len(eventos_response.json())
            
    except Exception as e:
        app.logger.error(f"Erro ao buscar estatísticas: {e}")
    
    return render_template('index.html', stats=stats)

# === ROTAS PARA ALUNOS ===

@app.route('/alunos')
def alunos_list():
    """Lista todos os alunos."""
    response = api_request('/alunos')
    alunos = []
    
    if response and response.status_code == 200:
        alunos = response.json()
        app.logger.info(f"Carregados {len(alunos)} alunos")
    else:
        flash('Erro ao carregar lista de alunos.', 'error')
        app.logger.error(f"Erro ao carregar alunos: {response.status_code if response else 'Sem resposta'}")
    
    return render_template('alunos/list.html', alunos=alunos)

@app.route('/alunos/novo')
def alunos_novo():
    """Formulário para novo aluno."""
    return render_template('alunos/form.html', aluno=None)

@app.route('/alunos/<int:id>')
def alunos_view(id):
    """Visualizar detalhes de um aluno."""
    response = api_request(f'/alunos/{id}')
    aluno = None
    
    if response and response.status_code == 200:
        aluno = response.json()
    else:
        flash('Aluno não encontrado.', 'error')
    
    return render_template('alunos/view.html', aluno=aluno)

@app.route('/alunos/<int:id>/editar')
def alunos_editar(id):
    """Formulário para editar aluno."""
    response = api_request(f'/alunos/{id}')
    aluno = None
    
    if response and response.status_code == 200:
        aluno = response.json()
    else:
        flash('Aluno não encontrado.', 'error')
        return redirect(url_for('alunos_list'))
    
    return render_template('alunos/form.html', aluno=aluno)

@app.route('/alunos/salvar', methods=['POST'])
def alunos_salvar():
    """Salvar (criar ou atualizar) aluno."""
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
        
        # Processar arquivo de foto
        files = {}
        if 'foto_perfil' in request.files and request.files['foto_perfil'].filename != '':
            foto = request.files['foto_perfil']
            files['foto'] = (foto.filename, foto.stream, foto.content_type)
        
        # Verificar se é edição ou criação
        aluno_id = request.form.get('id')
        
        if aluno_id:
            # Atualizar aluno existente
            response = api_request(f'/alunos/{aluno_id}', method='PUT', data=data, files=files)
            success_status = 200
            success_message = 'Aluno atualizado com sucesso!'
        else:
            # Criar novo aluno
            response = api_request('/alunos', method='POST', data=data, files=files)
            success_status = 201
            success_message = 'Aluno cadastrado com sucesso!'
        
        if response and response.status_code == success_status:
            flash(success_message, 'success')
            app.logger.info(f"Aluno salvo: {data.get('nome', 'N/A')}")
        else:
            error_msg = 'Erro ao salvar aluno.'
            if response:
                try:
                    error_detail = response.json().get('detail', '')
                    if error_detail:
                        error_msg += f' {error_detail}'
                except:
                    pass
            flash(error_msg, 'error')
            app.logger.error(f"Erro ao salvar aluno: {response.text if response else 'Sem resposta'}")
    
    except Exception as e:
        flash('Erro interno ao salvar aluno.', 'error')
        app.logger.error(f"Erro interno ao salvar aluno: {e}")
    
    return redirect(url_for('alunos_list'))

@app.route('/alunos/<int:id>/deletar', methods=['POST'])
def alunos_deletar(id):
    """Deletar aluno."""
    response = api_request(f'/alunos/{id}', method='DELETE')
    
    if response and response.status_code == 204:
        flash('Aluno excluído com sucesso!', 'success')
        app.logger.info(f"Aluno {id} excluído")
    else:
        flash('Erro ao excluir aluno.', 'error')
        app.logger.error(f"Erro ao excluir aluno {id}")
    
    return redirect(url_for('alunos_list'))

# === TRATAMENTO DE ERROS ===

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    print("Iniciando aplicação Flask...")
    print(f"API Base URL: {API_BASE_URL}")
    app.run(debug=True, host='0.0.0.0', port=5600)

