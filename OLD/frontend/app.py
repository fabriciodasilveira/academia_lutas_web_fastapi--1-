from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import requests
import os
from config import Config
import logging
from datetime import datetime

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
        'cpf': '932193219',
        'telefone': request.form.get('telefone'),
        'data_nascimento': request.form.get('data_nascimento'),
        'endereco': request.form.get('endereco'),
        'observacoes': request.form.get('observacoes')
    }
    
    # Remover campos vazios
    data = {k: v for k, v in data.items() if v}
    
    aluno_id = request.form.get('id')
    
    if aluno_id:
        # Atualizar aluno existente
        response = api_request(f'/alunos/{aluno_id}', method='PUT', data=data)
    else:
        # Criar novo aluno
        response = api_request('/alunos', method='POST', data=data)
    
    if response and response.status_code in [200, 201]:
        flash('Aluno salvo com sucesso!', 'success')
        logging.info(f"Aluno salvo com sucesso: {data['nome']}")
    else:
        flash('Erro ao salvar aluno.', 'error')
        logging.error(f"Erro ao salvar aluno: {response.text if response else 'Sem resposta'}")
    
    return redirect(url_for('alunos_list'))

@app.route('/alunos/<int:id>/deletar', methods=['POST'])
def alunos_deletar(id):
    response = api_request(f'/alunos/{id}', method='DELETE')
    if response and response.status_code == 200:
        flash('Aluno excluído com sucesso!', 'success')
    else:
        flash('Erro ao excluir aluno.', 'error')
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
        'salario': float(request.form.get('salario', 0)) if request.form.get('salario') else None
    }
    
    # Remover campos vazios
    data = {k: v for k, v in data.items() if v is not None and v != ''}
    
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

@app.route('/professores/<int:id>/deletar', methods=['POST'])
def professores_deletar(id):
    response = api_request(f'/professores/{id}', method='DELETE')
    if response and response.status_code == 200:
        flash('Professor excluído com sucesso!', 'success')
    else:
        flash('Erro ao excluir professor.', 'error')
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

@app.route('/turmas/<int:id>/editar')
def turmas_editar(id):
    response = api_request(f'/turmas/{id}')
    turma = None
    if response and response.status_code == 200:
        turma = response.json()
    
    # Buscar professores para o select
    professores_response = api_request('/professores')
    professores = []
    if professores_response and professores_response.status_code == 200:
        professores = professores_response.json()
    
    return render_template('turmas/form.html', turma=turma, professores=professores)

@app.route('/turmas/salvar', methods=['POST'])
def turmas_salvar():
    data = {
        'nome': request.form.get('nome'),
        'modalidade': request.form.get('modalidade'),
        'professor_id': int(request.form.get('professor_id')) if request.form.get('professor_id') else None,
        'nivel': request.form.get('nivel'),
        'horario': request.form.get('horario'),
        'capacidade_maxima': int(request.form.get('capacidade_maxima')) if request.form.get('capacidade_maxima') else None,
        'valor_mensalidade': float(request.form.get('valor_mensalidade')) if request.form.get('valor_mensalidade') else None,
        'idade_minima': int(request.form.get('idade_minima')) if request.form.get('idade_minima') else None,
        'ativa': bool(int(request.form.get('ativa', 1))),
        'descricao': request.form.get('descricao'),
        'observacoes': request.form.get('observacoes')
    }
    
    # Remover campos vazios
    data = {k: v for k, v in data.items() if v is not None and v != ''}
    
    turma_id = request.form.get('id')
    
    if turma_id:
        response = api_request(f'/turmas/{turma_id}', method='PUT', data=data)
    else:
        response = api_request('/turmas', method='POST', data=data)
    
    if response and response.status_code in [200, 201]:
        flash('Turma salva com sucesso!', 'success')
    else:
        flash('Erro ao salvar turma.', 'error')
    
    return redirect(url_for('turmas_list'))

@app.route('/turmas/<int:id>/deletar', methods=['POST'])
def turmas_deletar(id):
    response = api_request(f'/turmas/{id}', method='DELETE')
    if response and response.status_code == 200:
        flash('Turma excluída com sucesso!', 'success')
    else:
        flash('Erro ao excluir turma.', 'error')
    return redirect(url_for('turmas_list'))

# Rotas para Eventos
# @app.route('/eventos')
# def eventos_list():
#     response = api_request('/eventos')
#     eventos = []
#     if response and response.status_code == 200:
#         eventos = response.json()
#     return render_template('eventos/list.html', eventos=eventos)
@app.route('/eventos')
def eventos_list():
    response = api_request('/eventos')
    eventos = []
    
    if response and response.status_code == 200:
        eventos = response.json()
        # Converter strings de data para objetos datetime
        for evento in eventos:
            try:
                # Tenta parsear o formato ISO
                evento['data_evento'] = datetime.fromisoformat(evento['data_evento'])
            except ValueError:
                try:
                    # Tenta outros formatos comuns
                    evento['data_evento'] = datetime.strptime(evento['data_evento'], '%Y-%m-%d %H:%M:%S')
                except:
                    # Mantém como string se não conseguir converter
                    pass
    
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

@app.route('/eventos/<int:id>/editar')
def eventos_editar(id):
    response = api_request(f'/eventos/{id}')
    evento = None
    if response and response.status_code == 200:
        evento = response.json()
    return render_template('eventos/form.html', evento=evento)

@app.route('/eventos/salvar', methods=['POST'])
def eventos_salvar():
    data = {
        'nome': request.form.get('nome'),
        'tipo': request.form.get('tipo'),
        'data_evento': request.form.get('data_evento'),
        'horario': request.form.get('horario'),
        'status': request.form.get('status', 'agendado'),
        'local': request.form.get('local'),
        'capacidade_maxima': int(request.form.get('capacidade_maxima')) if request.form.get('capacidade_maxima') else None,
        'valor_inscricao': float(request.form.get('valor_inscricao')) if request.form.get('valor_inscricao') else None,
        'idade_minima': int(request.form.get('idade_minima')) if request.form.get('idade_minima') else None,
        'descricao': request.form.get('descricao'),
        'requisitos': request.form.get('requisitos'),
        'observacoes': request.form.get('observacoes')
    }
    
    # Remover campos vazios
    data = {k: v for k, v in data.items() if v is not None and v != ''}
    
    evento_id = request.form.get('id')
    
    if evento_id:
        response = api_request(f'/eventos/{evento_id}', method='PUT', data=data)
    else:
        response = api_request('/eventos', method='POST', data=data)
    
    if response and response.status_code in [200, 201]:
        flash('Evento salvo com sucesso!', 'success')
    else:
        flash('Erro ao salvar evento.', 'error')
    
    return redirect(url_for('eventos_list'))

@app.route('/eventos/<int:id>/deletar', methods=['POST'])
def eventos_deletar(id):
    response = api_request(f'/eventos/{id}', method='DELETE')
    if response and response.status_code == 200:
        flash('Evento excluído com sucesso!', 'success')
    else:
        flash('Erro ao excluir evento.', 'error')
    return redirect(url_for('eventos_list'))

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

@app.route('/financeiro/transacoes/salvar', methods=['POST'])
def financeiro_transacoes_salvar():
    data = {
        'tipo': request.form.get('tipo'),
        'categoria': request.form.get('categoria'),
        'descricao': request.form.get('descricao'),
        'valor': float(request.form.get('valor')) if request.form.get('valor') else 0,
        'data': request.form.get('data'),
        'status': request.form.get('status', 'confirmado'),
        'observacoes': request.form.get('observacoes')
    }
    
    # Remover campos vazios
    data = {k: v for k, v in data.items() if v is not None and v != ''}
    
    transacao_id = request.form.get('id')
    
    if transacao_id:
        response = api_request(f'/financeiro/transacoes/{transacao_id}', method='PUT', data=data)
    else:
        response = api_request('/financeiro/transacoes', method='POST', data=data)
    
    if response and response.status_code in [200, 201]:
        flash('Transação salva com sucesso!', 'success')
    else:
        flash('Erro ao salvar transação.', 'error')
    
    return redirect(url_for('financeiro_transacoes'))

@app.route('/financeiro/transacoes/<int:id>/deletar', methods=['POST'])
def financeiro_transacoes_deletar(id):
    response = api_request(f'/financeiro/transacoes/{id}', method='DELETE')
    if response and response.status_code == 200:
        flash('Transação excluída com sucesso!', 'success')
    else:
        flash('Erro ao excluir transação.', 'error')
    return redirect(url_for('financeiro_transacoes'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5500)

