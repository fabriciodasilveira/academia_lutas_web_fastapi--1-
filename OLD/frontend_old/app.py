from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import requests
import os
from config import Config
import logging

app = Flask(__name__)
app.config.from_object(Config)


import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log'  # Nome do arquivo de log
)

# Função auxiliar para fazer requisições à API
def api_request(endpoint, method='GET', data=None, files=None):
    url = f"{app.config['API_BASE_URL']}{endpoint}"
    try:
        if method == 'GET':
            response = requests.get(url)
        elif method == 'POST':
            if files:
                response = requests.post(url, data=data, files=files)
            else:
                response = requests.post(url, json=data)
        elif method == 'PUT':
            if files:
                response = requests.put(url, data=data, files=files)
            else:
                response = requests.put(url, json=data)
        elif method == 'DELETE':
            response = requests.delete(url)
        
        return response
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição: {e}")
        return None

# Rota principal - Dashboard
@app.route('/')
def index():
    # Buscar estatísticas da API
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
        print(f"Erro ao buscar estatísticas: {e}")
    
    return render_template('index.html', stats=stats)

# Rotas para Alunos
@app.route('/alunos')
def alunos_list():
    response = api_request('/alunos')
    alunos = []
    if response and response.status_code == 200:
        alunos = response.json()
    return render_template('alunos/list.html', alunos=alunos)

@app.route('/alunos/novo')
def alunos_novo():
    return render_template('alunos/form.html', aluno=None)

@app.route('/alunos/<int:id>')
def alunos_view(id):
    response = api_request(f'/alunos/{id}')
    aluno = None
    if response and response.status_code == 200:
        aluno = response.json()
    return render_template('alunos/view.html', aluno=aluno)

@app.route('/alunos/<int:id>/editar')
def alunos_editar(id):
    response = api_request(f'/alunos/{id}')
    aluno = None
    if response and response.status_code == 200:
        aluno = response.json()
    return render_template('alunos/form.html', aluno=aluno)

@app.route('/alunos/salvar', methods=['POST'])
def alunos_salvar():
    data = {
        'nome': request.form.get('nome'),
        'email': request.form.get('email'),
        'telefone': request.form.get('telefone'),
        'data_nascimento': request.form.get('data_nascimento'),
        'endereco': request.form.get('endereco'),
        'observacoes': request.form.get('observacoes')
    }
    
    aluno_id = request.form.get('id')
    
    if aluno_id:
        # Atualizar aluno existente
        response = api_request(f'/alunos/{aluno_id}', method='PUT', data=data)
    else:
        # Criar novo aluno
        response = api_request('/alunos', method='POST', data=data)
    
    if response and response.status_code in [200, 201]:
        flash('Aluno salvo com sucesso!', 'success')
    else:
        flash('Erro ao salvar aluno.', 'error')
    
    return redirect(url_for('alunos_list'))

# Rotas para Professores
@app.route('/professores')
def professores_list():
    response = api_request('/professores')
    professores = []
    if response and response.status_code == 200:
        professores = response.json()
    return render_template('professores/list.html', professores=professores)

@app.route('/professores/novo')
def professores_novo():
    return render_template('professores/form.html', professor=None)

@app.route('/professores/<int:id>')
def professores_view(id):
    response = api_request(f'/professores/{id}')
    professor = None
    if response and response.status_code == 200:
        professor = response.json()
    return render_template('professores/view.html', professor=professor)

@app.route('/professores/<int:id>/editar')
def professores_editar(id):
    response = api_request(f'/professores/{id}')
    professor = None
    if response and response.status_code == 200:
        professor = response.json()
    return render_template('professores/form.html', professor=professor)

@app.route('/professores/salvar', methods=['POST'])
def professores_salvar():
    data = {
        'nome': request.form.get('nome'),
        'email': request.form.get('email'),
        'telefone': request.form.get('telefone'),
        'especialidade': request.form.get('especialidade'),
        'data_contratacao': request.form.get('data_contratacao'),
        'salario': float(request.form.get('salario', 0))
    }
    
    professor_id = request.form.get('id')
    
    if professor_id:
        response = api_request(f'/professores/{professor_id}', method='PUT', data=data)
    else:
        response = api_request('/professores', method='POST', data=data)
    
    if response and response.status_code in [200, 201]:
        flash('Professor salvo com sucesso!', 'success')
    else:
        flash('Erro ao salvar professor.', 'error')
    
    return redirect(url_for('professores_list'))

# Rotas para Turmas
@app.route('/turmas')
def turmas_list():
    response = api_request('/turmas')
    turmas = []
    if response and response.status_code == 200:
        turmas = response.json()
    return render_template('turmas/list.html', turmas=turmas)

@app.route('/turmas/novo')
def turmas_novo():
    # Buscar professores para o select
    professores_response = api_request('/professores')
    professores = []
    if professores_response and professores_response.status_code == 200:
        professores = professores_response.json()
    return render_template('turmas/form.html', turma=None, professores=professores)

@app.route('/turmas/<int:id>')
def turmas_view(id):
    response = api_request(f'/turmas/{id}')
    turma = None
    if response and response.status_code == 200:
        turma = response.json()
    return render_template('turmas/view.html', turma=turma)

# Rotas para Eventos
@app.route('/eventos')
def eventos_list():
    response = api_request('/eventos')
    eventos = []
    if response and response.status_code == 200:
        eventos = response.json()
    return render_template('eventos/list.html', eventos=eventos)

@app.route('/eventos/novo')
def eventos_novo():
    return render_template('eventos/form.html', evento=None)

@app.route('/eventos/<int:id>')
def eventos_view(id):
    response = api_request(f'/eventos/{id}')
    evento = None
    if response and response.status_code == 200:
        evento = response.json()
    return render_template('eventos/view.html', evento=evento)

# Rotas para Financeiro
@app.route('/financeiro')
def financeiro_dashboard():
    response = api_request('/financeiro/transacoes')
    transacoes = []
    if response and response.status_code == 200:
        transacoes = response.json()
    
    # Calcular estatísticas
    receitas = sum(t.get('valor', 0) for t in transacoes if t.get('tipo') == 'receita')
    despesas = sum(t.get('valor', 0) for t in transacoes if t.get('tipo') == 'despesa')
    saldo = receitas - despesas
    
    stats = {
        'receitas': receitas,
        'despesas': despesas,
        'saldo': saldo,
        'total_transacoes': len(transacoes)
    }
    
    return render_template('financeiro/dashboard.html', stats=stats, transacoes=transacoes[:10])

@app.route('/financeiro/transacoes')
def financeiro_transacoes():
    response = api_request('/financeiro/transacoes')
    transacoes = []
    if response and response.status_code == 200:
        transacoes = response.json()
    return render_template('financeiro/transacoes.html', transacoes=transacoes)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5500)

