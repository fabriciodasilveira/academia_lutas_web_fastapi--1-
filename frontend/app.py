# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import requests
import os
import logging
from datetime import datetime, date, timedelta
import math
from functools import wraps
from whitenoise import WhiteNoise # Importa WhiteNoise

app = Flask(__name__)

# Configura WhiteNoise para servir arquivos estáticos da pasta 'static'
# O prefixo '/static' é o padrão do Flask e geralmente não precisa ser especificado
app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/')

app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production') # Usa variável de ambiente

# Usa variável de ambiente para a URL da API
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')

# --- NOVO: Context processor para injetar API_BASE_URL ---
@app.context_processor
def inject_global_vars():
    """Injeta variáveis globais em todos os templates."""
    # Adicione outras variáveis globais aqui se necessário
    return dict(API_BASE_URL=API_BASE_URL)
# --- FIM DO BLOCO NOVO ---

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# --- Decorators (login_required, admin_required) ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'access_token' not in session:
            flash("Por favor, faça login para acessar esta página.", "warning")
            return redirect(url_for('login', next=request.url))
        # Opcional: Verificar se o token ainda é válido fazendo uma chamada rápida à API
        # response = api_request("/auth/me")
        # if not response or response.status_code != 200:
        #     session.clear()
        #     flash("Sua sessão expirou. Por favor, faça login novamente.", "info")
        #     return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not login_required(lambda: True)(): # Primeiro verifica se está logado
             return redirect(url_for('login', next=request.url))
        user_info = session.get('user_info')
        # Verifica se user_info existe e se a role é 'administrador'
        if not user_info or user_info.get('role') != 'administrador':
            flash("Acesso restrito a administradores.", "danger")
            return redirect(url_for('index')) # Redireciona para a página inicial logada
        return f(*args, **kwargs)
    return decorated_function

# --- Rotas de Autenticação (login, logout, callback) ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        api_data = {"username": username, "password": password}
        try:
            response = requests.post(f"{API_BASE_URL}/api/v1/auth/token", data=api_data, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Verifica se o usuário tem permissão para acessar o painel
                user_role = data.get('user_info', {}).get('role')
                if user_role in ['administrador', 'gerente']:
                    session['access_token'] = data['access_token']
                    session['user_info'] = data['user_info']
                    # Adiciona a chave pública da Stripe à sessão para uso posterior
                    # session['STRIPE_PUBLIC_KEY'] = os.getenv('STRIPE_PUBLIC_KEY')
                    flash("Login realizado com sucesso!", "success")
                    next_url = request.args.get('next')
                    return redirect(next_url or url_for('index'))
                else:
                    flash("Usuário sem permissão para acessar este painel.", "danger")
            elif response.status_code == 401:
                 flash("Email ou senha inválidos.", "danger")
            else:
                flash(f"Erro inesperado da API ({response.status_code}). Tente novamente.", "danger")
        except requests.exceptions.RequestException as e:
            flash(f"Erro de conexão com a API: {e}", "danger")
            app.logger.error(f"Erro de conexão com a API em /login: {e}")

    # Passa a URL da API para o template poder construir o link do Google Login
    return render_template("login.html", API_BASE_URL=API_BASE_URL)


@app.route("/login/callback")
def login_callback():
    token = request.args.get('token')
    if not token:
        flash("Falha na autenticação via Google (token ausente).", "danger")
        return redirect(url_for('login'))

    # Usa a função api_request para verificar o token e obter dados do usuário
    user_info_resp = api_request("/auth/me", headers={"Authorization": f"Bearer {token}"})

    if user_info_resp and user_info_resp.status_code == 200:
        user_info = user_info_resp.json()
        user_role = user_info.get('role')

        # Verifica permissão ANTES de criar a sessão
        if user_role not in ['administrador', 'gerente']:
            if user_role == 'pendente':
                flash("Sua conta foi criada e está aguardando aprovação de um administrador.", "info")
            elif user_role == 'aluno':
                 flash("Login com Google permitido apenas para administradores e gerentes neste painel.", "warning")
            else:
                 flash("Usuário sem permissão para acessar este painel.", "danger")
            return redirect(url_for('login'))

        # Cria a sessão
        session['access_token'] = token
        session['user_info'] = user_info
        # Adiciona a chave pública da Stripe à sessão
        # session['STRIPE_PUBLIC_KEY'] = os.getenv('STRIPE_PUBLIC_KEY')
        flash("Login com Google realizado com sucesso!", "success")
        return redirect(url_for('index'))
    else:
        status = user_info_resp.status_code if user_info_resp else 'N/A'
        flash(f"Não foi possível obter os dados do usuário da API (Erro: {status}).", "danger")
        return redirect(url_for('login'))


@app.route("/logout")
def logout():
    session.clear()
    flash("Você saiu do sistema.", "success")
    return redirect(url_for('login'))

# --- Função Auxiliar api_request ---
def api_request(endpoint, method='GET', data=None, files=None, json=None, params=None, headers=None, timeout=20):
    """
    Função auxiliar para fazer requisições à API FastAPI, incluindo o token.
    Retorna o objeto Response ou None em caso de erro de conexão.
    """
    url = f"{API_BASE_URL}/api/v1{endpoint}"
    request_headers = headers if headers is not None else {}
    access_token = session.get('access_token')

    if access_token and 'Authorization' not in request_headers:
        request_headers['Authorization'] = f"Bearer {access_token}"

    try:
        if method == 'GET':
            response = requests.get(url, params=params, headers=request_headers, timeout=timeout)
        elif method == 'POST':
            response = requests.post(url, data=data, files=files, json=json, headers=request_headers, timeout=timeout)
        elif method == 'PUT':
            response = requests.put(url, data=data, files=files, json=json, headers=request_headers, timeout=timeout)
        elif method == 'DELETE':
            response = requests.delete(url, headers=request_headers, timeout=timeout)
        else:
            app.logger.error(f"Método HTTP não suportado: {method}")
            return None

        # Log detalhado da requisição e resposta
        # app.logger.info(f"API Request: {method} {url} Params: {params} Data: {data} Json: {json}")
        # app.logger.info(f"API Response Status: {response.status_code}")
        # try:
        #      app.logger.debug(f"API Response Body: {response.text}")
        # except Exception:
        #      app.logger.debug("API Response Body: (não pôde ser lido)")


        # Se a API retornar 401 Unauthorized, limpa a sessão e redireciona para login
        if response.status_code == 401 and request.endpoint != 'login': # Evita loop infinito no login
            session.clear()
            flash("Sua sessão expirou ou é inválida. Por favor, faça login novamente.", "warning")
            # Usa um status code especial para indicar redirecionamento ao JS se necessário
            # Ou retorna um Response especial que o decorator @login_required pode pegar
            # Por simplicidade, vamos apenas retornar None aqui e deixar o @login_required tratar
            return None # Sinaliza que a requisição falhou por autenticação

        return response

    except requests.exceptions.Timeout:
        app.logger.error(f"Timeout na requisição {method} {url}")
        flash("A API demorou muito para responder. Tente novamente.", "danger")
        return None
    except requests.exceptions.ConnectionError as e:
         app.logger.error(f"Erro de conexão com a API {method} {url}: {e}")
         flash(f"Não foi possível conectar à API ({url}). Verifique se ela está online.", "danger")
         return None
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Erro geral na requisição {method} {url}: {e}")
        flash("Ocorreu um erro inesperado ao comunicar com a API.", "danger")
        return None

# --- Filtros de Template ---
@app.template_filter('format_datetime')
def format_datetime_filter(s):
    if not s: return ""
    try:
        dt_obj = datetime.fromisoformat(str(s).replace('Z', '+00:00')) # Trata 'Z' de UTC
        return dt_obj.strftime('%d/%m/%Y %H:%M')
    except (ValueError, TypeError): return s

@app.template_filter('format_date_br')
def format_date_br_filter(value):
    if not value: return ""
    try:
        if isinstance(value, str): dt_obj = date.fromisoformat(value)
        elif isinstance(value, date): dt_obj = value
        else: return value
        return dt_obj.strftime('%d/%m/%Y')
    except (ValueError, TypeError): return value

# --- Rotas Principais ---
@app.route('/')
@login_required
def index():
    stats = { 'total_alunos_ativos': 0, 'total_professores': 0, 'total_turmas': 0, 'total_eventos': 0 }
    chart_data = {"labels": [], "datasets": {"alunos": [], "eventos": []}}
    try:
        alunos_resp = api_request("/alunos?status=ativo&limit=1")
        if alunos_resp and alunos_resp.status_code == 200:
            stats['total_alunos_ativos'] = alunos_resp.json().get('total', 0)
        
        prof_resp = api_request('/professores?limit=1000') # Assume max 1000 prof
        if prof_resp and prof_resp.status_code == 200:
            stats['total_professores'] = len(prof_resp.json())

        turmas_resp = api_request('/turmas?limit=1000') # Assume max 1000 turmas
        if turmas_resp and turmas_resp.status_code == 200:
            stats['total_turmas'] = len(turmas_resp.json())

        eventos_resp = api_request('/eventos?limit=1000') # Assume max 1000 eventos
        if eventos_resp and eventos_resp.status_code == 200:
            stats['total_eventos'] = len(eventos_resp.json())

        chart_response = api_request("/dashboard/atividades-recentes")
        if chart_response and chart_response.status_code == 200:
            chart_data = chart_response.json()
    except Exception as e:
        app.logger.error(f"Erro ao buscar estatísticas do dashboard: {e}")
        flash("Erro ao carregar dados do dashboard.", "warning")

    return render_template('index.html', stats=stats, chart_data=chart_data)


# --- Rotas de Alunos ---
@app.route('/alunos')
@login_required
def alunos_list():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    busca = request.args.get('busca', '')
    status = request.args.get('status', 'ativo') # Padrão 'ativo'
    skip = (page - 1) * limit

    params = { "skip": skip, "limit": limit }
    if busca: params["nome"] = busca
    if status: params["status"] = status

    response = api_request("/alunos", params=params)
    alunos = []
    total_alunos = 0
    total_pages = 0

    if response is None: # Se api_request retornou None (erro de auth ou conexão)
         return redirect(url_for('login', next=request.url)) # Força redirect se sessão expirou

    if response.status_code == 200:
        data = response.json()
        alunos = data.get("alunos", [])
        total_alunos = data.get("total", 0)
        if total_alunos > 0 and limit > 0:
            total_pages = math.ceil(total_alunos / limit)
    elif response.status_code != 401: # Não mostra erro se for só não autorizado (já tratado)
        flash(f"Erro ao carregar alunos da API ({response.status_code}).", "danger")

    return render_template('alunos/list.html', alunos=alunos, page=page, limit=limit,
                           total_pages=total_pages, total_alunos=total_alunos, busca=busca, status=status)

@app.route('/alunos/<int:id>')
@login_required
def alunos_view(id):
    response = api_request(f'/alunos/{id}')
    aluno = None
    historico = []
    status_info = {}

    if response is None: return redirect(url_for('login', next=request.url))

    if response.status_code == 200:
        aluno = response.json()
        if aluno.get('data_nascimento'):
            try:
                data_nasc = date.fromisoformat(aluno['data_nascimento'])
                hoje = date.today()
                idade = hoje.year - data_nasc.year - ((hoje.month, hoje.day) < (data_nasc.month, data_nasc.day))
                aluno['idade'] = idade
            except (ValueError, TypeError): aluno['idade'] = None

        historico_response = api_request(f"/alunos/{id}/historico")
        if historico_response and historico_response.status_code == 200:
             # Formata data no backend para evitar erros no template se a data for inválida
             historico_bruto = historico_response.json()
             for evento in historico_bruto:
                  try:
                     data_obj = datetime.fromisoformat(evento['data'].replace('Z', '+00:00'))
                     evento['data_formatada'] = data_obj.strftime('%d/%m/%Y às %H:%M')
                  except:
                      evento['data_formatada'] = evento['data'] # Usa data original se falhar
             historico = historico_bruto

        status_response = api_request(f"/alunos/{id}/status-detalhado")
        if status_response and status_response.status_code == 200:
            status_info = status_response.json()
    else:
        flash(f"Aluno com ID {id} não encontrado ou erro na API ({response.status_code}).", 'warning')
        return redirect(url_for('alunos_list'))

    return render_template('alunos/view.html', aluno=aluno, historico=historico, status_info=status_info)


@app.route('/alunos/novo')
@login_required
def alunos_novo():
    return render_template('alunos/form.html', aluno=None)

@app.route('/alunos/<int:id>/editar')
@login_required
def alunos_editar(id):
    response = api_request(f'/alunos/{id}')
    if response is None: return redirect(url_for('login', next=request.url))
    aluno = None
    if response.status_code == 200:
        aluno = response.json()
    else:
        flash(f"Aluno com ID {id} não encontrado ou erro na API ({response.status_code}).", "warning")
        return redirect(url_for("alunos_list"))
    return render_template('alunos/form.html', aluno=aluno)

@app.route("/alunos/salvar", methods=["POST"])
@login_required
def alunos_salvar():
    aluno_id = request.form.get("id")
    try:
        data = {
            "nome": request.form.get("nome"),
            "email": request.form.get("email"),
            "cpf": request.form.get("cpf"),
            "telefone": request.form.get("telefone"),
            "data_nascimento": request.form.get("data_nascimento"),
            "endereco": request.form.get("endereco"),
            "observacoes": request.form.get("observacoes"),
            "nome_responsavel": request.form.get("nome_responsavel"),
            "cpf_responsavel": request.form.get("cpf_responsavel"),
            "parentesco_responsavel": request.form.get("parentesco_responsavel"),
            "telefone_responsavel": request.form.get("telefone_responsavel"),
            "email_responsavel": request.form.get("email_responsavel"),
        }
        # Envia apenas campos preenchidos? Decide a política. Enviar None pode ser melhor.
        # data = {k: v for k, v in data.items() if v} # Comentado - envia tudo

        files = {}
        if "foto_perfil" in request.files and request.files["foto_perfil"].filename:
            foto = request.files["foto_perfil"]
            # Envia como multipart/form-data
            files["foto"] = (foto.filename, foto.stream, foto.content_type)

        if aluno_id:
            response = api_request(f"/alunos/{aluno_id}", method="PUT", data=data, files=files)
            success_status = 200
            success_message = "Aluno atualizado com sucesso!"
        else:
            response = api_request("/alunos", method="POST", data=data, files=files)
            success_status = 201
            success_message = "Aluno cadastrado com sucesso!"

        if response and response.status_code == success_status:
            flash(success_message, "success")
            # Redireciona para a view do aluno criado/editado
            new_aluno_id = response.json().get('id', None) if not aluno_id else aluno_id
            if new_aluno_id:
                 return redirect(url_for("alunos_view", id=new_aluno_id))
            else:
                 return redirect(url_for("alunos_list"))
        else:
             # Tenta obter a mensagem de erro da API
            error_msg = "Erro ao salvar aluno."
            detail = "N/A"
            status_code = "N/A"
            if response is not None:
                status_code = response.status_code
                try: detail = response.json().get("detail", response.text)
                except: detail = response.text
            flash(f"{error_msg} (API Status: {status_code}, Detalhe: {detail})", "danger")
            # Retorna ao formulário em caso de erro, mantendo os dados (se possível)
            # Precisaria passar 'data' de volta para o 'form.html' preencher os campos
            return render_template('alunos/form.html', aluno=data, id=aluno_id) # Passa 'id' para saber se é edição

    except Exception as e:
        flash(f"Erro interno inesperado ao salvar aluno: {e}", "danger")
        app.logger.error(f"Erro ao salvar aluno (ID: {aluno_id}): {e}", exc_info=True)
        # Retorna ao formulário em caso de erro interno
        return render_template('alunos/form.html', aluno=request.form, id=aluno_id)

@app.route("/alunos/<int:id>/deletar", methods=["POST"])
@login_required
def alunos_deletar(id):
    response = api_request(f"/alunos/{id}", method="DELETE")
    if response is None: return redirect(url_for('login', next=request.url))

    if response.status_code == 204:
        flash("Aluno excluído com sucesso!", "success")
        app.logger.info(f"Aluno {id} excluído")
    else:
        detail = "N/A"
        try: detail = response.json().get("detail", response.text)
        except: detail = response.text
        flash(f"Erro ao excluir aluno (API Status: {response.status_code}, Detalhe: {detail}).", "danger")
        app.logger.error(f"Erro ao excluir aluno {id}: Status {response.status_code}, Body: {detail}")
    return redirect(url_for("alunos_list"))


# --- Rotas de Professores ---
@app.route('/professores')
@login_required
def professores_list():
    response = api_request('/professores?limit=1000') # Assume limite alto
    if response is None: return redirect(url_for('login', next=request.url))
    professores = []
    if response.status_code == 200:
        professores = response.json()
    else:
        flash(f"Erro ao carregar professores ({response.status_code}).", "warning")
    return render_template('professores/list.html', professores=professores)

@app.route("/professores/novo")
@login_required
def professores_novo():
    return render_template("professores/form.html", professor=None)

@app.route("/professores/<int:id>")
@login_required
def professores_view(id):
    response = api_request(f"/professores/{id}")
    if response is None: return redirect(url_for('login', next=request.url))
    professor = None
    if response.status_code == 200:
        professor = response.json()
    else:
        flash(f"Professor ID {id} não encontrado ({response.status_code}).", "warning")
        return redirect(url_for('professores_list'))
    return render_template("professores/view.html", professor=professor)

@app.route("/professores/<int:id>/editar")
@login_required
def professores_editar(id):
    response = api_request(f"/professores/{id}")
    if response is None: return redirect(url_for('login', next=request.url))
    professor = None
    if response.status_code == 200:
        professor = response.json()
    else:
        flash(f"Professor ID {id} não encontrado ({response.status_code}).", "warning")
        return redirect(url_for("professores_list"))
    return render_template("professores/form.html", professor=professor)

@app.route("/professores/salvar", methods=["POST"])
@login_required
def professores_salvar():
    professor_id = request.form.get("id")
    try:
        data = {
            "nome": request.form.get("nome"),
            "email": request.form.get("email"),
            "cpf": request.form.get("cpf"),
            "telefone": request.form.get("telefone"),
            "data_nascimento": request.form.get("data_nascimento"),
            "especialidade": request.form.get("especialidade"),
            "formacao": request.form.get("formacao"),
            "data_contratacao": request.form.get("data_contratacao"),
            "salario": request.form.get("salario"),
            "observacoes": request.form.get("observacoes")
        }
        # data = {k: v for k, v in data.items() if v} # Decide se envia Nones ou não

        files = {}
        if "foto_perfil" in request.files and request.files["foto_perfil"].filename:
            foto = request.files["foto_perfil"]
            files["foto"] = (foto.filename, foto.stream, foto.content_type)

        if professor_id:
            response = api_request(f"/professores/{professor_id}", method="PUT", data=data, files=files)
            success_status = 200
            success_message = "Professor atualizado com sucesso!"
        else:
            response = api_request("/professores", method="POST", data=data, files=files)
            success_status = 201
            success_message = "Professor cadastrado com sucesso!"

        if response and response.status_code == success_status:
            flash(success_message, "success")
            new_prof_id = response.json().get('id') if not professor_id else professor_id
            if new_prof_id:
                return redirect(url_for('professores_view', id=new_prof_id))
            else:
                return redirect(url_for('professores_list'))
        else:
            error_msg = "Erro ao salvar professor."
            detail = "N/A"; status_code="N/A"
            if response is not None:
                status_code=response.status_code
                try: detail = response.json().get("detail", response.text)
                except: detail = response.text
            flash(f"{error_msg} (API Status: {status_code}, Detalhe: {detail})", "danger")
            return render_template("professores/form.html", professor=data, id=professor_id)

    except Exception as e:
        flash(f"Erro interno inesperado ao salvar professor: {e}", "danger")
        app.logger.error(f"Erro ao salvar professor (ID: {professor_id}): {e}", exc_info=True)
        return render_template("professores/form.html", professor=request.form, id=professor_id)

@app.route("/professores/<int:id>/deletar", methods=["POST"])
@login_required
def professores_deletar(id):
    response = api_request(f"/professores/{id}", method="DELETE")
    if response is None: return redirect(url_for('login', next=request.url))
    if response.status_code == 204:
        flash("Professor excluído com sucesso!", "success")
    else:
        detail = "N/A"; status_code="N/A"
        if response is not None:
            status_code=response.status_code
            try: detail = response.json().get("detail", response.text)
            except: detail = response.text
        flash(f"Erro ao excluir professor (API Status: {status_code}, Detalhe: {detail}).", "danger")
    return redirect(url_for("professores_list"))


# --- Rotas de Turmas ---
@app.route("/turmas")
@login_required
def turmas_list():
    response = api_request("/turmas?limit=1000") # Assume limite alto
    if response is None: return redirect(url_for('login', next=request.url))
    turmas = []
    if response.status_code == 200:
        turmas = response.json()
    else:
         flash(f"Erro ao carregar turmas ({response.status_code}).", "warning")
    return render_template("turmas/list.html", turmas=turmas)

@app.route("/turmas/novo")
@login_required
def turmas_novo():
    prof_resp = api_request("/professores?limit=1000")
    if prof_resp is None: return redirect(url_for('login', next=request.url))
    professores = []
    if prof_resp.status_code == 200:
         professores = prof_resp.json()
    else:
         flash(f"Erro ao carregar professores ({prof_resp.status_code}).", "warning")
    return render_template("turmas/form.html", turma=None, professores=professores)

@app.route("/turmas/<int:id>")
@login_required
def turmas_view(id):
    turma_resp = api_request(f"/turmas/{id}")
    if turma_resp is None: return redirect(url_for('login', next=request.url))
    turma = None
    if turma_resp.status_code == 200:
        turma = turma_resp.json()
    else:
        flash(f"Turma ID {id} não encontrada ({turma_resp.status_code}).", "warning")
        return redirect(url_for('turmas_list'))
    return render_template("turmas/view.html", turma=turma)

@app.route("/turmas/<int:id>/editar")
@login_required
def turmas_editar(id):
    turma_resp = api_request(f"/turmas/{id}")
    if turma_resp is None: return redirect(url_for('login', next=request.url))
    turma = None
    if turma_resp.status_code == 200:
        turma = turma_resp.json()
    else:
        flash(f"Turma ID {id} não encontrada ({turma_resp.status_code}).", "warning")
        return redirect(url_for("turmas_list"))

    prof_resp = api_request("/professores?limit=1000")
    if prof_resp is None: return redirect(url_for('login', next=request.url))
    professores = []
    if prof_resp.status_code == 200:
        professores = prof_resp.json()
    else:
         flash(f"Erro ao carregar professores ({prof_resp.status_code}).", "warning")

    return render_template("turmas/form.html", turma=turma, professores=professores)

@app.route("/turmas/salvar", methods=["POST"])
@login_required
def turmas_salvar():
    turma_id = request.form.get("id")
    try:
        # Tenta converter os campos numéricos, tratando erros
        professor_id_str = request.form.get("professor_id")
        professor_id = int(professor_id_str) if professor_id_str else None

        capacidade_max_str = request.form.get("capacidade_maxima")
        capacidade_maxima = int(capacidade_max_str) if capacidade_max_str else None

        valor_mensal_str = request.form.get("valor_mensalidade", "").replace(',', '.')
        valor_mensalidade = float(valor_mensal_str) if valor_mensal_str else None

        idade_min_str = request.form.get("idade_minima")
        idade_minima = int(idade_min_str) if idade_min_str else None

        turma_data = {
            "nome": request.form.get("nome"),
            "modalidade": request.form.get("modalidade"),
            "horario": request.form.get("horario"),
            "dias_semana": request.form.get("dias_semana"), # Pegar do form
            "professor_id": professor_id,
            "nivel": request.form.get("nivel"),
            "capacidade_maxima": capacidade_maxima,
            "valor_mensalidade": valor_mensalidade,
            "idade_minima": idade_minima,
            "ativa": request.form.get("ativa") == "1", # Checkbox envia '1' ou nada
            "descricao": request.form.get("descricao"),
            "observacoes": request.form.get("observacoes")
        }

        # Não filtra mais Nones para permitir desassociar professor
        final_data = turma_data

        if turma_id:
            response = api_request(f"/turmas/{turma_id}", method="PUT", json=final_data)
            success_status = 200
            success_message = "Turma atualizada com sucesso!"
        else:
            response = api_request("/turmas", method="POST", json=final_data)
            success_status = 201
            success_message = "Turma cadastrada com sucesso!"

        if response and response.status_code == success_status:
            flash(success_message, "success")
            new_turma_id = response.json().get('id') if not turma_id else turma_id
            if new_turma_id:
                return redirect(url_for('turmas_view', id=new_turma_id))
            else:
                 return redirect(url_for('turmas_list'))
        else:
            error_msg = "Erro ao salvar turma."
            detail = "N/A"; status_code="N/A"
            if response is not None:
                status_code=response.status_code
                try: detail = response.json().get("detail", response.text)
                except: detail = response.text
            flash(f"{error_msg} (API Status: {status_code}, Detalhe: {detail})", "danger")
            # Recarrega professores para reenviar ao form
            prof_resp = api_request("/professores?limit=1000")
            professores = prof_resp.json() if prof_resp and prof_resp.status_code == 200 else []
            return render_template("turmas/form.html", turma=turma_data, professores=professores, id=turma_id)

    except ValueError as e:
         flash(f"Erro ao converter valor numérico: {e}. Verifique os campos de capacidade, valor e idade.", "danger")
         prof_resp = api_request("/professores?limit=1000")
         professores = prof_resp.json() if prof_resp and prof_resp.status_code == 200 else []
         return render_template("turmas/form.html", turma=request.form, professores=professores, id=turma_id)
    except Exception as e:
        flash(f"Erro interno inesperado ao salvar turma: {e}", "danger")
        app.logger.error(f"Erro ao salvar turma (ID: {turma_id}): {e}", exc_info=True)
        prof_resp = api_request("/professores?limit=1000")
        professores = prof_resp.json() if prof_resp and prof_resp.status_code == 200 else []
        return render_template("turmas/form.html", turma=request.form, professores=professores, id=turma_id)

@app.route("/turmas/<int:id>/deletar", methods=["POST"])
@login_required
def turmas_deletar(id):
    response = api_request(f"/turmas/{id}", method="DELETE")
    if response is None: return redirect(url_for('login', next=request.url))
    if response.status_code == 204:
        flash("Turma excluída com sucesso!", "success")
    else:
        detail = "N/A"; status_code="N/A"
        if response is not None:
            status_code=response.status_code
            try: detail = response.json().get("detail", response.text)
            except: detail = response.text
        flash(f"Erro ao excluir turma (API Status: {status_code}, Detalhe: {detail}). Pode haver alunos matriculados.", "danger")
    return redirect(url_for("turmas_list"))


# --- Rotas de Matrículas ---
@app.route("/matriculas")
@login_required
def matriculas_list():
    busca = request.args.get('busca', '')
    status = request.args.get('status', '') # Vazio = todos, 'ativa', 'inativa'

    params = {}
    if busca: params["busca"] = busca
    if status: params["status"] = status

    response = api_request("/matriculas", params=params)
    if response is None: return redirect(url_for('login', next=request.url))
    matriculas = []
    if response.status_code == 200:
        matriculas = response.json()
    else:
        flash(f"Erro ao carregar matrículas ({response.status_code}).", "warning")

    return render_template("matriculas/list.html", matriculas=matriculas, busca=busca, status=status)

@app.route("/matriculas/novo")
@login_required
def matriculas_novo():
    # Carrega turmas e planos para os dropdowns
    turmas_resp = api_request("/turmas?limit=1000")
    planos_resp = api_request("/planos?limit=1000")

    if turmas_resp is None or planos_resp is None : return redirect(url_for('login', next=request.url))

    turmas = turmas_resp.json() if turmas_resp.status_code == 200 else []
    planos = planos_resp.json() if planos_resp.status_code == 200 else []

    if not turmas: flash("Erro ao carregar turmas.", "warning")
    if not planos: flash("Erro ao carregar planos.", "warning")

    return render_template("matriculas/form.html", turmas=turmas, planos=planos, matricula=None)

@app.route("/matriculas/<int:id>/editar")
@login_required
def matriculas_editar(id):
    matricula_resp = api_request(f"/matriculas/{id}")
    if matricula_resp is None: return redirect(url_for('login', next=request.url))

    if matricula_resp.status_code != 200:
        flash(f"Matrícula ID {id} não encontrada ({matricula_resp.status_code}).", "warning")
        return redirect(url_for("matriculas_list"))
    matricula = matricula_resp.json()

    turmas_resp = api_request("/turmas?limit=1000")
    planos_resp = api_request("/planos?limit=1000")
    if turmas_resp is None or planos_resp is None : return redirect(url_for('login', next=request.url))

    turmas = turmas_resp.json() if turmas_resp.status_code == 200 else []
    planos = planos_resp.json() if planos_resp.status_code == 200 else []

    if not turmas: flash("Erro ao carregar turmas.", "warning")
    if not planos: flash("Erro ao carregar planos.", "warning")

    return render_template("matriculas/form.html", matricula=matricula, turmas=turmas, planos=planos)

@app.route("/matriculas/salvar", methods=["POST"])
@login_required
def matriculas_salvar():
    # Esta rota é apenas para NOVAS matrículas
    try:
        aluno_id_str = request.form.get("aluno_id")
        turma_id_str = request.form.get("turma_id")
        plano_id_str = request.form.get("plano_id")

        if not all([aluno_id_str, turma_id_str, plano_id_str]):
            flash("Erro: Aluno, Turma e Plano são obrigatórios.", "danger")
            # Recarrega dados para o form
            turmas_resp = api_request("/turmas?limit=1000"); turmas = turmas_resp.json() if turmas_resp and turmas_resp.status_code == 200 else []
            planos_resp = api_request("/planos?limit=1000"); planos = planos_resp.json() if planos_resp and planos_resp.status_code == 200 else []
            return render_template("matriculas/form.html", turmas=turmas, planos=planos, matricula=request.form)

        matricula_data = {
            "aluno_id": int(aluno_id_str),
            "turma_id": int(turma_id_str),
            "plano_id": int(plano_id_str)
        }

        response = api_request("/matriculas", method="POST", json=matricula_data)

        if response and response.status_code == 201:
            flash("Matrícula realizada com sucesso! A primeira mensalidade foi gerada.", "success")
            return redirect(url_for("matriculas_list"))
        else:
            error_msg = "Erro ao realizar matrícula."
            detail = "N/A"; status_code = "N/A"
            if response is not None:
                status_code = response.status_code
                try:
                    error_detail = response.json().get("detail", response.text)
                    if isinstance(error_detail, list): error_msg += " Verifique os dados: " + ", ".join([e.get('msg', '') for e in error_detail])
                    elif error_detail: error_msg += f" Detalhe: {error_detail}"
                except: error_msg += f" Resposta: {response.text}"
            flash(f"{error_msg} (API Status: {status_code})", "danger")
            turmas_resp = api_request("/turmas?limit=1000"); turmas = turmas_resp.json() if turmas_resp and turmas_resp.status_code == 200 else []
            planos_resp = api_request("/planos?limit=1000"); planos = planos_resp.json() if planos_resp and planos_resp.status_code == 200 else []
            return render_template("matriculas/form.html", turmas=turmas, planos=planos, matricula=request.form)

    except ValueError as e:
        flash(f"Erro: Valor inválido fornecido. {e}", "danger")
        turmas_resp = api_request("/turmas?limit=1000"); turmas = turmas_resp.json() if turmas_resp and turmas_resp.status_code == 200 else []
        planos_resp = api_request("/planos?limit=1000"); planos = planos_resp.json() if planos_resp and planos_resp.status_code == 200 else []
        return render_template("matriculas/form.html", turmas=turmas, planos=planos, matricula=request.form)
    except Exception as e:
        flash(f"Erro interno inesperado ao salvar matrícula: {e}", "danger")
        app.logger.error(f"Erro ao salvar nova matrícula: {e}", exc_info=True)
        turmas_resp = api_request("/turmas?limit=1000"); turmas = turmas_resp.json() if turmas_resp and turmas_resp.status_code == 200 else []
        planos_resp = api_request("/planos?limit=1000"); planos = planos_resp.json() if planos_resp and planos_resp.status_code == 200 else []
        return render_template("matriculas/form.html", turmas=turmas, planos=planos, matricula=request.form)


@app.route("/matriculas/salvar_edicao", methods=["POST"])
@login_required
def matriculas_salvar_edicao():
    matricula_id = request.form.get("id")
    if not matricula_id:
        flash("ID da matrícula não fornecido para edição.", "danger")
        return redirect(url_for('matriculas_list'))
    try:
        # Na edição, só permitimos alterar a turma e o status ativo
        matricula_data = {
            "turma_id": int(request.form.get("turma_id")),
             "plano_id": int(request.form.get("plano_id")), # Permite alterar plano
            "ativa": request.form.get("ativa") == 'on' # Checkbox envia 'on' se marcado
        }

        response = api_request(f"/matriculas/{matricula_id}", method="PUT", json=matricula_data)

        if response and response.status_code == 200:
            flash("Matrícula atualizada com sucesso!", "success")
        else:
            error_msg = "Erro ao atualizar matrícula."
            detail = "N/A"; status_code = "N/A"
            if response is not None:
                status_code = response.status_code
                try: detail = response.json().get("detail", response.text)
                except: detail = response.text
            flash(f"{error_msg} (API Status: {status_code}, Detalhe: {detail})", "danger")
            # Em caso de erro, redireciona de volta para a edição
            return redirect(url_for('matriculas_editar', id=matricula_id))

    except ValueError as e:
         flash(f"Erro: Valor inválido fornecido. {e}", "danger")
         return redirect(url_for('matriculas_editar', id=matricula_id))
    except Exception as e:
        flash(f"Erro interno ao salvar edição da matrícula: {e}", "danger")
        app.logger.error(f"Erro ao editar matrícula {matricula_id}: {e}", exc_info=True)
        return redirect(url_for('matriculas_editar', id=matricula_id))

    return redirect(url_for("matriculas_list"))


@app.route("/matriculas/status/<int:id>", methods=["POST"])
@login_required
def matriculas_status(id):
    # Esta rota agora chama a API que faz a lógica de toggle
    response = api_request(f"/matriculas/{id}/toggle-status", method="POST")
    if response is None: return redirect(url_for('login', next=request.url))

    if response.status_code == 200:
        new_status = response.json().get("ativa")
        action = 'ativada' if new_status else 'trancada'
        flash(f"Matrícula {action} com sucesso!", "success")
    else:
        detail = "N/A"; status_code = "N/A"
        if response is not None:
            status_code = response.status_code
            try: detail = response.json().get("detail", response.text)
            except: detail = response.text
        flash(f"Erro ao alterar status (API Status: {status_code}, Detalhe: {detail}).", "danger")

    return redirect(url_for("matriculas_list"))


@app.route("/matriculas/deletar/<int:id>", methods=["POST"])
@login_required
def matriculas_deletar(id):
    response = api_request(f"/matriculas/{id}", method="DELETE")
    if response is None: return redirect(url_for('login', next=request.url))

    if response.status_code == 204:
        flash("Matrícula excluída com sucesso!", "success")
    else:
        detail = "N/A"; status_code = "N/A"
        if response is not None:
            status_code = response.status_code
            try: detail = response.json().get("detail", response.text)
            except: detail = response.text
        flash(f"Erro ao excluir matrícula (API Status: {status_code}, Detalhe: {detail}). Pode haver mensalidades associadas.", "danger")
    return redirect(url_for("matriculas_list"))


# --- Rotas Financeiras ---
@app.route("/financeiro/dashboard")
@login_required
def financeiro_dashboard():
    hoje = date.today()
    primeiro_dia_mes = hoje.replace(day=1)
    
    # Busca balanço do mês atual
    balanco_params = { "data_inicio": primeiro_dia_mes.strftime('%Y-%m-%d'), "data_fim": hoje.strftime('%Y-%m-%d')}
    balanco_resp = api_request("/financeiro/balanco", params=balanco_params)
    if balanco_resp is None: return redirect(url_for('login', next=request.url))
    stats = balanco_resp.json() if balanco_resp.status_code == 200 else {}

    # Busca últimas 5 transações
    trans_resp = api_request("/financeiro/transacoes?limit=5&sort_by=data&order=desc")
    if trans_resp is None: return redirect(url_for('login', next=request.url))
    transacoes = []
    if trans_resp.status_code == 200:
        trans_data = trans_resp.json()
        if isinstance(trans_data, list): # Verifica se a API retornou uma lista
             transacoes = trans_data
             # Tenta converter as datas
             for t in transacoes:
                 if t.get('data'):
                      try: t['data'] = datetime.fromisoformat(t['data'].replace('Z', '+00:00'))
                      except: pass # Ignora se falhar
        else:
            app.logger.error(f"API /financeiro/transacoes retornou tipo inesperado: {type(trans_data)}")

    # Busca categorias
    cat_resp = api_request("/categorias")
    if cat_resp is None: return redirect(url_for('login', next=request.url))
    categorias = cat_resp.json() if cat_resp.status_code == 200 else []

    # Busca mensalidades pendentes
    mens_params = {"status": "pendente", "limit": 1000} # Pega todas pendentes
    mens_resp = api_request("/mensalidades", params=mens_params)
    if mens_resp is None: return redirect(url_for('login', next=request.url))
    mensalidades_pendentes = []
    if mens_resp.status_code == 200:
        # --- CORREÇÃO AQUI ---
        # Extrai a lista de dentro do objeto paginado
        data = mens_resp.json()
        mensalidades_pendentes = data.get("mensalidades", [])
        # ---------------------
    else:
        # Não mostra erro grave, apenas loga
        app.logger.warning(f"Não foi possível buscar mensalidades pendentes ({mens_resp.status_code})")

    if not stats: flash("Erro ao carregar balanço financeiro.", "warning")
    # Não flasheia erro para transações, categorias ou mensalidades, só loga

    return render_template("financeiro/dashboard.html", stats=stats, transacoes=transacoes,
                           categorias=categorias, mensalidades_pendentes=mensalidades_pendentes)


@app.route("/financeiro/transacoes")
@login_required
def financeiro_transacoes():
    # Parâmetros de filtro da URL
    tipo_filtro = request.args.get('tipo', '')
    categoria_filtro = request.args.get('categoria', '')
    busca_filtro = request.args.get('busca', '')
    data_inicio = request.args.get('data_inicio', '')
    data_fim = request.args.get('data_fim', '')
    page = request.args.get('page', 1, type=int)
    limit = 20
    skip = (page - 1) * limit

    # Monta parâmetros para API de transações
    trans_params = {"skip": skip, "limit": limit, "sort_by": "data", "order": "desc"}
    if tipo_filtro: trans_params["tipo"] = tipo_filtro
    if categoria_filtro: trans_params["categoria"] = categoria_filtro
    if busca_filtro: trans_params["busca"] = busca_filtro
    if data_inicio: trans_params["data_inicio"] = data_inicio
    if data_fim: trans_params["data_fim"] = data_fim

    trans_resp = api_request("/financeiro/transacoes", params=trans_params)
    if trans_resp is None: return redirect(url_for('login', next=request.url))

    transacoes = []
    total_transacoes = 0
    total_pages = 0
    if trans_resp.status_code == 200:
         data = trans_resp.json()
         # API retorna lista diretamente ou objeto paginado? Assumindo objeto paginado
         transacoes = data.get("transacoes", [])
         total_transacoes = data.get("total", 0)
         if total_transacoes > 0 and limit > 0:
              total_pages = math.ceil(total_transacoes / limit)
         # Converte datas
         for t in transacoes:
              if t.get('data'):
                  try: t['data'] = datetime.fromisoformat(t['data'].replace('Z', '+00:00'))
                  except: pass
    else:
         flash(f"Erro ao carregar transações ({trans_resp.status_code}).", "warning")

    # Monta parâmetros para API de balanço (apenas datas)
    balanco_params = {}
    if data_inicio: balanco_params["data_inicio"] = data_inicio
    if data_fim: balanco_params["data_fim"] = data_fim

    balanco_resp = api_request("/financeiro/balanco", params=balanco_params)
    if balanco_resp is None: return redirect(url_for('login', next=request.url))
    stats = balanco_resp.json() if balanco_resp.status_code == 200 else {}
    if not stats: flash("Erro ao carregar balanço.", "warning")

    # Busca categorias
    cat_resp = api_request("/categorias")
    if cat_resp is None: return redirect(url_for('login', next=request.url))
    categorias = cat_resp.json() if cat_resp.status_code == 200 else []

    # Cria um dicionário com os filtros atuais para passar ao template
    current_filters = {
        'tipo': tipo_filtro, 'categoria': categoria_filtro, 'busca': busca_filtro,
        'data_inicio': data_inicio, 'data_fim': data_fim
    }

    return render_template("financeiro/transacoes.html", transacoes=transacoes, stats=stats,
                           categorias=categorias, filters=current_filters, page=page,
                           total_pages=total_pages, total_transacoes=total_transacoes)


@app.route("/financeiro/salvar_transacao", methods=["POST"])
@login_required
def financeiro_salvar_transacao():
    transacao_id = request.form.get("id")
    try:
        valor_str = request.form.get("valor", "0").replace(',', '.')
        valor = float(valor_str) if valor_str else 0.0

        transacao_data = {
            "tipo": request.form.get("tipo"),
            "categoria": request.form.get("categoria"),
            "descricao": request.form.get("descricao"),
            "valor": valor,
            "status": request.form.get("status", "pendente"), # Define padrão se não vier
            "observacoes": request.form.get("observacoes"),
            "data": request.form.get("data") or datetime.utcnow().isoformat() # Usa data atual se vazia
        }

        # Remove 'id' antes de enviar para API, a API não espera 'id' no corpo
        # transacao_data.pop('id', None) # Não precisa mais se não está no dict inicial

        if transacao_id:
            response = api_request(f"/financeiro/transacoes/{transacao_id}", method="PUT", json=transacao_data)
            success_status = 200
            success_message = "Transação atualizada com sucesso!"
        else:
            response = api_request("/financeiro/transacoes", method="POST", json=transacao_data)
            success_status = 201
            success_message = "Transação salva com sucesso!"

        if response and response.status_code == success_status:
            flash(success_message, "success")
        else:
            error_msg = "Erro ao salvar transação."
            detail = "N/A"; status_code = "N/A"
            if response is not None:
                status_code = response.status_code
                try: detail = response.json().get("detail", response.text)
                except: detail = response.text
            flash(f"{error_msg} (API Status: {status_code}, Detalhe: {detail})", "danger")

    except ValueError as e:
         flash(f"Erro ao converter valor: {e}. Use apenas números e vírgula/ponto decimal.", "danger")
    except Exception as e:
        flash(f"Erro interno inesperado ao salvar transação: {e}", "danger")
        app.logger.error(f"Erro ao salvar transação (ID: {transacao_id}): {e}", exc_info=True)

    # Redireciona de volta para a lista, mantendo os filtros se possível
    # (precisaria pegar os filtros do request.referrer ou similar)
    return redirect(url_for("financeiro_transacoes"))


@app.route("/financeiro/deletar_transacao/<int:id>", methods=["POST"])
@login_required
def financeiro_deletar_transacao(id):
    response = api_request(f"/financeiro/transacoes/{id}", method="DELETE")
    if response is None: return redirect(url_for('login', next=request.url))

    if response.status_code == 204:
        flash("Transação excluída com sucesso!", "success")
    else:
        detail = "N/A"; status_code = "N/A"
        if response is not None:
            status_code = response.status_code
            try: detail = response.json().get("detail", response.text)
            except: detail = response.text
        flash(f"Erro ao excluir transação (API Status: {status_code}, Detalhe: {detail}).", "danger")
    return redirect(url_for("financeiro_transacoes"))

# --- Rotas de Produtos --- (Simplificado, adicionar validação se necessário)
@app.route("/produtos")
@login_required
def produtos_list():
    resp = api_request("/produtos?limit=1000")
    if resp is None: return redirect(url_for('login', next=request.url))
    produtos = resp.json() if resp.status_code == 200 else []
    if resp.status_code != 200 : flash("Erro ao carregar produtos.", "warning")
    return render_template("produtos/list.html", produtos=produtos)

@app.route("/produtos/novo")
@login_required
def produtos_novo():
    return render_template("produtos/form.html", produto=None)

@app.route("/produtos/<int:id>/editar")
@login_required
def produtos_editar(id):
    resp = api_request(f"/produtos/{id}")
    if resp is None: return redirect(url_for('login', next=request.url))
    produto = None
    if resp.status_code == 200:
        produto = resp.json()
    else:
        flash(f"Produto ID {id} não encontrado ({resp.status_code}).", "warning")
        return redirect(url_for("produtos_list"))
    return render_template("produtos/form.html", produto=produto)

@app.route("/produtos/salvar", methods=["POST"])
@login_required
def produtos_salvar():
    produto_id = request.form.get("id")
    try:
        produto_data = {
            "codigo": request.form.get("codigo"), "nome": request.form.get("nome"),
            "descricao": request.form.get("descricao"),
            "preco_custo": float(request.form.get("preco_custo", "0").replace(',', '.')),
            "preco_venda": float(request.form.get("preco_venda", "0").replace(',', '.')),
            "quantidade_estoque": int(request.form.get("quantidade_estoque", "0"))
        }
        if produto_id:
            response = api_request(f"/produtos/{produto_id}", method="PUT", json=produto_data)
            msg = "Produto atualizado!"; status_ok = 200
        else:
            response = api_request("/produtos", method="POST", json=produto_data)
            msg = "Produto cadastrado!"; status_ok = 201

        if response and response.status_code == status_ok: flash(msg, "success")
        else:
            detail = response.json().get('detail', 'Erro desconhecido') if response else 'Sem resposta da API'
            flash(f"Erro ao salvar produto: {detail}", "danger")
            return render_template("produtos/form.html", produto=produto_data, id=produto_id)

    except ValueError as e:
        flash(f"Erro ao converter valor numérico: {e}", "danger")
        return render_template("produtos/form.html", produto=request.form, id=produto_id)
    except Exception as e:
        flash(f"Erro interno: {e}", "danger")
        app.logger.error(f"Erro ao salvar produto {produto_id}: {e}", exc_info=True)
        return render_template("produtos/form.html", produto=request.form, id=produto_id)
    return redirect(url_for("produtos_list"))

@app.route("/produtos/deletar/<int:id>", methods=["POST"])
@login_required
def produtos_deletar(id):
    response = api_request(f"/produtos/{id}", method="DELETE")
    if response is None: return redirect(url_for('login', next=request.url))
    if response.status_code == 204: flash("Produto excluído!", "success")
    else: flash("Erro ao excluir produto.", "danger")
    return redirect(url_for("produtos_list"))

# --- Rotas de Planos --- (Simplificado)
@app.route("/planos")
@login_required
def planos_list():
    resp = api_request("/planos?limit=1000")
    if resp is None: return redirect(url_for('login', next=request.url))
    planos = resp.json() if resp.status_code == 200 else []
    if resp.status_code != 200 : flash("Erro ao carregar planos.", "warning")
    return render_template("planos/list.html", planos=planos)

@app.route("/planos/novo")
@login_required
def planos_novo():
    return render_template("planos/form.html", plano=None)

@app.route("/planos/<int:id>/editar")
@login_required
def planos_editar(id):
    resp = api_request(f"/planos/{id}")
    if resp is None: return redirect(url_for('login', next=request.url))
    plano = None
    if resp.status_code == 200:
        plano = resp.json()
    else:
        flash(f"Plano ID {id} não encontrado ({resp.status_code}).", "warning")
        return redirect(url_for("planos_list"))
    return render_template("planos/form.html", plano=plano)

@app.route("/planos/salvar", methods=["POST"])
@login_required
def planos_salvar():
    plano_id = request.form.get("id")
    try:
        plano_data = {
            "nome": request.form.get("nome"), "descricao": request.form.get("descricao"),
            "valor": float(request.form.get("valor", "0").replace(',', '.')),
            "periodo_meses": int(request.form.get("periodo_meses", "1"))
        }
        if plano_id:
            response = api_request(f"/planos/{plano_id}", method="PUT", json=plano_data)
            msg = "Plano atualizado!"; status_ok = 200
        else:
            response = api_request("/planos", method="POST", json=plano_data)
            msg = "Plano cadastrado!"; status_ok = 201

        if response and response.status_code == status_ok: flash(msg, "success")
        else:
            detail = response.json().get('detail', 'Erro desconhecido') if response else 'Sem resposta da API'
            flash(f"Erro ao salvar plano: {detail}", "danger")
            return render_template("planos/form.html", plano=plano_data, id=plano_id)
    except ValueError as e:
        flash(f"Erro ao converter valor numérico: {e}", "danger")
        return render_template("planos/form.html", plano=request.form, id=plano_id)
    except Exception as e:
        flash(f"Erro interno: {e}", "danger")
        app.logger.error(f"Erro ao salvar plano {plano_id}: {e}", exc_info=True)
        return render_template("planos/form.html", plano=request.form, id=plano_id)
    return redirect(url_for("planos_list"))

@app.route("/planos/deletar/<int:id>", methods=["POST"])
@login_required
def planos_deletar(id):
    response = api_request(f"/planos/{id}", method="DELETE")
    if response is None: return redirect(url_for('login', next=request.url))
    if response.status_code == 204: flash("Plano excluído!", "success")
    else:
        detail = "N/A"; status_code = "N/A"
        if response is not None:
             status_code=response.status_code
             try: detail = response.json().get("detail", response.text)
             except: detail = response.text
        flash(f"Erro ao excluir plano (API: {status_code}, {detail}). Pode estar em uso.", "danger")
    return redirect(url_for("planos_list"))

# --- Rotas de Mensalidades ---
@app.route("/mensalidades")
@login_required
def mensalidades_list():
    page = request.args.get('page', 1, type=int)
    limit = 20
    busca = request.args.get('busca', '')
    status_filtro = request.args.get('status', '')
    skip = (page - 1) * limit

    params = { "skip": skip, "limit": limit }
    if busca: params["busca_aluno"] = busca
    if status_filtro: params["status"] = status_filtro

    response = api_request("/mensalidades", params=params)
    if response is None: return redirect(url_for('login', next=request.url))

    mensalidades = []
    total_mensalidades = 0
    total_pages = 0
    if response.status_code == 200:
        data = response.json()
        mensalidades = data.get("mensalidades", [])
        total_mensalidades = data.get("total", 0)
        if total_mensalidades > 0 and limit > 0:
            total_pages = math.ceil(total_mensalidades / limit)
    else:
        flash(f"Erro ao carregar mensalidades ({response.status_code}).", "danger")

    return render_template("mensalidades/list.html", mensalidades=mensalidades, page=page, limit=limit,
                           total_pages=total_pages, total_mensalidades=total_mensalidades, busca=busca,
                           status_filtro=status_filtro)

@app.route("/mensalidades/pagar/<int:id>", methods=["POST"])
@login_required
def mensalidades_pagar(id):
    # Rota para pagamento manual
    response = api_request(f"/mensalidades/processar_pagamento/{id}", method="POST")
    if response is None: return redirect(url_for('login', next=request.url))

    if response.status_code == 200:
        flash("Pagamento manual registrado com sucesso!", "success")
    else:
        detail = "N/A"; status_code = "N/A"
        if response is not None:
            status_code=response.status_code
            try: detail = response.json().get("detail", response.text)
            except: detail = response.text
        flash(f"Erro ao registrar pagamento (API Status: {status_code}, Detalhe: {detail}).", "danger")
    # Redireciona de volta para a lista, mantendo filtros se possível
    return redirect(request.referrer or url_for("mensalidades_list"))


@app.route("/mensalidades/deletar/<int:id>", methods=["POST"])
@login_required
def mensalidades_deletar(id):
    response = api_request(f"/mensalidades/{id}", method="DELETE")
    if response is None: return redirect(url_for('login', next=request.url))
    if response.status_code == 204:
        flash("Mensalidade excluída com sucesso!", "success")
    else:
        detail = "N/A"; status_code = "N/A"
        if response is not None:
            status_code=response.status_code
            try: detail = response.json().get("detail", response.text)
            except: detail = response.text
        flash(f"Erro ao excluir mensalidade (API Status: {status_code}, Detalhe: {detail}).", "danger")
    return redirect(request.referrer or url_for("mensalidades_list"))


# --- Rotas de Eventos e Inscrições --- (Verificar paginação e filtros se necessário)
@app.route("/eventos")
@login_required
def eventos_list():
    resp = api_request("/eventos?limit=1000") # Assume limite alto
    if resp is None: return redirect(url_for('login', next=request.url))
    eventos = resp.json() if resp.status_code == 200 else []
    if resp.status_code != 200: flash("Erro ao carregar eventos.", "warning")
    
    # KPIs (exemplo simples, pode ser movido para API)
    kpis = { "total_eventos": len(eventos), "total_inscritos": 0, "total_arrecadado": 0.0 }
    for ev in eventos:
         inscricoes = ev.get('inscricoes', [])
         kpis["total_inscritos"] += len(inscricoes)
         for insc in inscricoes:
             if insc.get('status') == 'pago' and insc.get('valor_pago') is not None:
                 kpis["total_arrecadado"] += insc['valor_pago']

    return render_template("eventos/list.html", eventos=eventos, kpis=kpis)

@app.route("/eventos/novo")
@login_required
def eventos_novo():
    return render_template("eventos/form.html", evento=None)

@app.route("/eventos/<int:id>/editar")
@login_required
def eventos_editar(id):
    resp = api_request(f"/eventos/{id}")
    if resp is None: return redirect(url_for('login', next=request.url))
    evento = resp.json() if resp.status_code == 200 else None
    if not evento:
        flash(f"Evento ID {id} não encontrado ({resp.status_code}).", "warning")
        return redirect(url_for("eventos_list"))
    return render_template("eventos/form.html", evento=evento)

@app.route("/eventos/salvar", methods=["POST"])
@login_required
def eventos_salvar():
    evento_id = request.form.get("id")
    try:
        data = {
            "nome": request.form.get("nome"), "tipo": request.form.get("tipo"),
            "descricao": request.form.get("descricao"), "local": request.form.get("local"),
            "data_evento": request.form.get("data_evento"), # API valida formato
            "valor_inscricao": float(request.form.get("valor_inscricao", "0").replace(',', '.')),
            "capacidade": int(request.form.get("capacidade", "0")),
            "status": request.form.get("status"),
        }
        if evento_id:
            response = api_request(f"/eventos/{evento_id}", method="PUT", json=data)
            msg = "Evento atualizado!"; status_ok = 200
        else:
            response = api_request("/eventos", method="POST", json=data)
            msg = "Evento criado!"; status_ok = 201

        if response and response.status_code == status_ok:
            flash(msg, "success")
            new_ev_id = response.json().get('id') if not evento_id else evento_id
            if new_ev_id:
                return redirect(url_for('eventos_view', id=new_ev_id))
            else:
                return redirect(url_for('eventos_list'))
        else:
            detail = response.json().get('detail', 'Erro desconhecido') if response else 'Sem resposta'
            flash(f"Erro ao salvar evento: {detail}", "danger")
            return render_template("eventos/form.html", evento=data, id=evento_id)

    except ValueError as e:
        flash(f"Erro ao converter valor numérico: {e}", "danger")
        return render_template("eventos/form.html", evento=request.form, id=evento_id)
    except Exception as e:
        flash(f"Erro interno: {e}", "danger")
        app.logger.error(f"Erro ao salvar evento {evento_id}: {e}", exc_info=True)
        return render_template("eventos/form.html", evento=request.form, id=evento_id)


@app.route("/eventos/<int:id>")
@login_required
def eventos_view(id):
    evento_resp = api_request(f"/eventos/{id}")
    if evento_resp is None: return redirect(url_for('login', next=request.url))

    if evento_resp.status_code != 200:
        flash(f"Evento ID {id} não encontrado ({evento_resp.status_code}).", "warning")
        return redirect(url_for("eventos_list"))
    evento = evento_resp.json()

    # Busca inscrições para este evento
    inscricoes_resp = api_request(f"/inscricoes/evento/{id}?limit=2000") # Assume limite alto
    inscricoes = []
    if inscricoes_resp and inscricoes_resp.status_code == 200:
        inscricoes = inscricoes_resp.json()
    elif inscricoes_resp:
         flash(f"Erro ao carregar inscrições ({inscricoes_resp.status_code}).", "warning")

    # Busca todos os alunos ativos para o dropdown de inscrição
    alunos_resp = api_request("/alunos?status=ativo&limit=2000") # Assume limite alto
    alunos = []
    if alunos_resp and alunos_resp.status_code == 200:
        alunos = alunos_resp.json().get("alunos", [])
    elif alunos_resp:
         flash(f"Erro ao carregar alunos ({alunos_resp.status_code}).", "warning")

    return render_template("eventos/view.html", evento=evento, inscricoes=inscricoes, alunos=alunos)


@app.route("/eventos/inscrever", methods=["POST"])
@login_required
def eventos_inscrever():
    evento_id = request.form.get("evento_id")
    aluno_id = request.form.get("aluno_id")

    if not evento_id: return redirect(url_for('eventos_list')) # Volta pra lista se não souber o evento
    if not aluno_id:
        flash("Selecione um aluno para inscrever.", "warning")
        return redirect(url_for("eventos_view", id=evento_id))

    data = {"evento_id": int(evento_id), "aluno_id": int(aluno_id)}
    response = api_request("/inscricoes", method="POST", json=data)

    if response and response.status_code == 201: # API retorna 201 para criação
        flash("Aluno inscrito com sucesso!", "success")
    else:
        detail = "N/A"; status_code = "N/A"
        if response is not None:
             status_code = response.status_code
             try: detail = response.json().get("detail", response.text)
             except: detail = response.text
        flash(f"Erro ao inscrever aluno (API Status: {status_code}, Detalhe: {detail}).", "danger")

    return redirect(url_for("eventos_view", id=evento_id))

@app.route("/inscricoes/<int:id>/pagar-manual", methods=["POST"])
@login_required
def inscricao_pagar_manual(id):
    evento_id = request.form.get("evento_id") # Pega do form hidden
    if not evento_id:
         flash("ID do evento não encontrado para redirecionamento.", "error")
         # Tenta buscar a inscrição para achar o evento_id se falhar
         insc_resp = api_request(f"/inscricoes/{id}")
         if insc_resp and insc_resp.status_code == 200:
             evento_id = insc_resp.json().get('evento_id')
         else:
             return redirect(url_for('eventos_list')) # Fallback

    response = api_request(f"/inscricoes/{id}/confirmar-pagamento-manual", method="POST")

    if response and response.status_code == 200:
        flash("Pagamento manual da inscrição confirmado!", "success")
    else:
        detail = "N/A"; status_code = "N/A"
        if response is not None:
            status_code = response.status_code
            try: detail = response.json().get("detail", response.text)
            except: detail = response.text
        flash(f"Erro ao confirmar pagamento manual (API Status: {status_code}, Detalhe: {detail}).", "danger")

    return redirect(url_for("eventos_view", id=evento_id))

@app.route("/eventos/<int:id>/deletar", methods=["POST"])
@login_required
def eventos_deletar(id):
    response = api_request(f"/eventos/{id}", method="DELETE")
    if response is None: return redirect(url_for('login', next=request.url))
    if response.status_code == 204:
        flash("Evento excluído com sucesso!", "success")
    else:
        detail = "N/A"; status_code = "N/A"
        if response is not None:
            status_code = response.status_code
            try: detail = response.json().get("detail", response.text)
            except: detail = response.text
        flash(f"Erro ao excluir evento (API Status: {status_code}, Detalhe: {detail}). Pode haver inscrições.", "danger")
    return redirect(url_for("eventos_list"))

@app.route("/inscricoes/<int:id>/deletar", methods=["POST"])
@login_required
def inscricao_deletar(id):
    evento_id = request.form.get("evento_id")
    if not evento_id: flash("ID do evento ausente.", "error"); return redirect(url_for('eventos_list'))

    response = api_request(f"/inscricoes/{id}", method="DELETE")
    if response is None: return redirect(url_for('login', next=request.url))

    if response.status_code == 204:
        flash("Inscrição removida com sucesso!", "success")
    else:
        detail = "N/A"; status_code = "N/A"
        if response is not None:
            status_code = response.status_code
            try: detail = response.json().get("detail", response.text)
            except: detail = response.text
        flash(f"Erro ao remover inscrição (API Status: {status_code}, Detalhe: {detail}).", "danger")
    return redirect(url_for("eventos_view", id=evento_id))

@app.route("/inscricoes/<int:id>/cancelar", methods=["POST"])
@login_required
def inscricao_cancelar(id):
    evento_id = request.form.get("evento_id")
    if not evento_id: flash("ID do evento ausente.", "error"); return redirect(url_for('eventos_list'))

    response = api_request(f"/inscricoes/{id}/cancelar", method="POST")
    if response is None: return redirect(url_for('login', next=request.url))

    if response.status_code == 200:
        flash("Inscrição cancelada com sucesso!", "success")
    else:
        detail = "N/A"; status_code = "N/A"
        if response is not None:
            status_code = response.status_code
            try: detail = response.json().get("detail", response.text)
            except: detail = response.text
        flash(f"Erro ao cancelar inscrição (API Status: {status_code}, Detalhe: {detail}).", "danger")
    return redirect(url_for("eventos_view", id=evento_id))


# --- Rotas de Usuários (Admin) ---
@app.route("/usuarios")
@login_required
@admin_required # Garante que só admin acesse
def usuarios_list():
    resp = api_request("/usuarios?limit=1000")
    if resp is None: return redirect(url_for('login', next=request.url))
    usuarios = resp.json() if resp.status_code == 200 else []
    if resp.status_code != 200: flash("Erro ao carregar usuários.", "warning")
    # Adiciona o ID do usuário logado para evitar auto-exclusão no template
    logged_user_id = session.get('user_info', {}).get('id')
    return render_template("usuarios/list.html", usuarios=usuarios, logged_user_id=logged_user_id)

@app.route("/usuarios/novo")
@login_required
@admin_required
def usuarios_novo():
    return render_template("usuarios/form.html", usuario=None)

@app.route("/usuarios/editar/<int:id>")
@login_required
@admin_required
def usuarios_editar(id):
    resp = api_request(f"/usuarios/{id}")
    if resp is None: return redirect(url_for('login', next=request.url))
    usuario = resp.json() if resp.status_code == 200 else None
    if not usuario:
        flash(f"Usuário ID {id} não encontrado ({resp.status_code}).", "warning")
        return redirect(url_for("usuarios_list"))
    return render_template("usuarios/form.html", usuario=usuario)

@app.route("/usuarios/salvar", methods=["POST"])
@login_required
@admin_required
def usuarios_salvar():
    user_id = request.form.get("id")
    password = request.form.get("password")
    data = { "email": request.form.get("email"), "nome": request.form.get("nome"), "role": request.form.get("role") }
    if password: data['password'] = password # Só envia senha se preenchida

    try:
        if user_id:
            response = api_request(f"/usuarios/{user_id}", method="PUT", json=data)
            msg = "Usuário atualizado!"; status_ok = 200
        else:
            response = api_request("/usuarios", method="POST", json=data)
            msg = "Usuário criado!"; status_ok = 201

        if response and response.status_code == status_ok: flash(msg, "success")
        else:
            detail = response.json().get('detail', 'Erro desconhecido') if response else 'Sem resposta'
            flash(f"Erro ao salvar usuário: {detail}", "danger")
            return render_template("usuarios/form.html", usuario=data, id=user_id)
    except Exception as e:
         flash(f"Erro interno: {e}", "danger")
         app.logger.error(f"Erro ao salvar usuário {user_id}: {e}", exc_info=True)
         return render_template("usuarios/form.html", usuario=request.form, id=user_id) # Usa request.form

    return redirect(url_for("usuarios_list"))

@app.route("/usuarios/deletar/<int:id>", methods=["POST"])
@login_required
@admin_required
def usuarios_deletar(id):
    logged_user_id = session.get('user_info', {}).get('id')
    if id == logged_user_id:
        flash("Você não pode excluir seu próprio usuário.", "warning")
        return redirect(url_for("usuarios_list"))

    response = api_request(f"/usuarios/{id}", method="DELETE")
    if response is None: return redirect(url_for('login', next=request.url))

    if response.status_code == 204: flash("Usuário excluído!", "success")
    else:
        detail = "N/A"; status_code="N/A"
        if response is not None:
             status_code=response.status_code
             try: detail = response.json().get("detail", response.text)
             except: detail = response.text
        flash(f"Erro ao excluir usuário (API Status: {status_code}, Detalhe: {detail}).", "danger")
    return redirect(url_for("usuarios_list"))


# --- Rota Catch-all para 404 ---
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

# --- Execução Principal ---
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5700)

# from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
# import requests
# import os
# import logging
# from datetime import datetime, date, timedelta
# import math
# from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session # Adicione 'session'
# from functools import wraps # Adicione 'wraps'
# import requests

# app = Flask(__name__)
# app.secret_key = 'dev-secret-key-change-in-production'

# # API_BASE_URL = 'http://localhost:8000'
# API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8000')


# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )

# def login_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if 'access_token' not in session:
#             return redirect(url_for('login', next=request.url))
#         return f(*args, **kwargs)
#     return decorated_function

# def admin_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         user_info = session.get('user_info')
#         if not user_info or user_info.get('role') != 'administrador':
#             flash("Acesso restrito a administradores.", "error")
#             return redirect(url_for('index'))
#         return f(*args, **kwargs)
#     return decorated_function

# @app.route("/login", methods=["GET", "POST"])
# def login():
#     if request.method == "POST":
#         username = request.form.get("username")
#         password = request.form.get("password")
        
#         # O frontend envia os dados no formato que o OAuth2PasswordRequestForm espera
#         api_data = {"username": username, "password": password}
#         response = requests.post(f"{API_BASE_URL}/api/v1/auth/token", data=api_data)
        
#         if response.status_code == 200:
#             data = response.json()
#             session['access_token'] = data['access_token']
#             session['user_info'] = data['user_info'] # Armazena os dados do usuário
#             return redirect(url_for('index'))
#         else:
#             flash("Usuário ou senha inválidos.", "error")

#     return render_template("login.html",API_BASE_URL=API_BASE_URL)

# @app.route("/logout")
# def logout():
#     session.clear()
#     flash("Você saiu do sistema.", "success")
#     return redirect(url_for('login'))


# @app.template_filter('format_datetime')
# @login_required
# def format_datetime_filter(s):
#     if not s:
#         return ""
#     try:
#         # Tenta converter de string ISO para objeto datetime
#         dt_obj = datetime.fromisoformat(s)
#         return dt_obj.strftime('%d/%m/%Y %H:%M')
#     except (ValueError, TypeError):
#         return s

# @app.template_filter('format_date_br')
# def format_date_br_filter(value):
#     """Formata uma data (string YYYY-MM-DD ou objeto date) para DD/MM/YYYY."""
#     if not value:
#         return ""
#     try:
#         if isinstance(value, str):
#             dt_obj = date.fromisoformat(value)
#         elif isinstance(value, date):
#             dt_obj = value
#         else:
#             return value # Retorna o valor original se não for string ou date
#         return dt_obj.strftime('%d/%m/%Y')
#     except (ValueError, TypeError):
#         return value # Retorna original em caso de erro
    

# def api_request(endpoint, method='GET', data=None, files=None, json=None, params=None, headers=None):
#     """
#     Função auxiliar para fazer requisições à API FastAPI, incluindo o token de autenticação.
#     """
#     url = f"{API_BASE_URL}/api/v1{endpoint}"
    
#     # Prepara os cabeçalhos da requisição
#     request_headers = headers if headers is not None else {}
#     if 'access_token' in session and 'Authorization' not in request_headers:
#         request_headers['Authorization'] = f"Bearer {session['access_token']}"
    
#     try:
#         if method == 'GET':
#             response = requests.get(url, timeout=10, params=params, headers=request_headers)
#         elif method == 'POST':
#             response = requests.post(url, data=data, files=files, json=json, timeout=10, headers=request_headers)
#         elif method == 'PUT':
#             # A sua lógica original para PUT já lida com 'files'
#             if files:
#                 response = requests.put(url, data=data, files=files, timeout=10, headers=request_headers)
#             else:
#                 response = requests.put(url, data=data, json=json, timeout=10, headers=request_headers)
#         elif method == 'DELETE':
#             response = requests.delete(url, timeout=10, headers=request_headers)
        
#         # Se a API retornar "Não Autorizado", limpa a sessão para forçar um novo login
#         if response.status_code == 401:
#             session.clear()
        
#         app.logger.info(f"API Request: {method} {url} - Status: {response.status_code}")
#         return response
        
#     except requests.exceptions.RequestException as e:
#         app.logger.error(f"Erro na requisição {method} {url}: {e}")
#         return None


# @app.route('/')
# @login_required
# def index():
#     """Página inicial com estatísticas dinâmicas."""
#     stats = {
#         'total_alunos': 0,
#         'total_alunos_ativos': 0, # Novo campo para alunos ativos
#         'total_professores': 0,
#         'total_turmas': 0,
#         'total_eventos': 0
#     }
    
#     chart_data = {
#         "labels": [],
#         "datasets": {"alunos": [], "eventos": []}
#     }
    
#     try:
#         # Busca o total de ALUNOS ATIVOS
#         alunos_ativos_resp = api_request("/alunos?status=ativo&limit=1")
#         if alunos_ativos_resp and alunos_ativos_resp.status_code == 200:
#             stats['total_alunos_ativos'] = alunos_ativos_resp.json().get('total', 0)
        
#         # Busca o total geral de alunos
#         alunos_total_resp = api_request("/alunos?limit=1")
#         if alunos_total_resp and alunos_total_resp.status_code == 200:
#             stats['total_alunos'] = alunos_total_resp.json().get('total', 0)

#         # Busca as outras estatísticas
#         professores_response = api_request('/professores')
#         if professores_response and professores_response.status_code == 200:
#             stats['total_professores'] = len(professores_response.json())
        
#         turmas_response = api_request('/turmas')
#         if turmas_response and turmas_response.status_code == 200:
#             stats['total_turmas'] = len(turmas_response.json())
        
#         eventos_response = api_request('/eventos')
#         if eventos_response and eventos_response.status_code == 200:
#             stats['total_eventos'] = len(eventos_response.json())
            
#         # Busca os dados para o gráfico
#         chart_response = api_request("/dashboard/atividades-recentes")
#         if chart_response and chart_response.status_code == 200:
#             chart_data = chart_response.json()
                
#     except Exception as e:
#         app.logger.error(f"Erro ao buscar estatísticas do dashboard: {e}")
    
#     return render_template('index.html', stats=stats, chart_data=chart_data)

# @app.route('/alunos')
# @login_required
# def alunos_list():
#     page = request.args.get('page', 1, type=int)
#     limit = request.args.get('limit', 20, type=int)
#     busca = request.args.get('busca', '')
#     status = request.args.get('status', 'ativo')
#     skip = (page - 1) * limit

#     params = {
#         "skip": skip,
#         "limit": limit,
#         "nome": busca,
#         "status": status # ADICIONE ESTA LINHA
#     }
    
#     params = {k: v for k, v in params.items() if v}
#     response = api_request("/alunos", params=params)
    
#     alunos = []
#     total_alunos = 0
#     total_pages = 0

#     if response and response.status_code == 200:
#         data = response.json()
#         alunos = data.get("alunos", [])
#         total_alunos = data.get("total", 0)
#         if total_alunos > 0 and limit > 0:
#             total_pages = math.ceil(total_alunos / limit)

#     return render_template(
#         'alunos/list.html', 
#         alunos=alunos,
#         page=page,
#         limit=limit,
#         total_pages=total_pages,
#         total_alunos=total_alunos,
#         busca=busca,
#         status=status # ADICIONE ESTA LINHA
#     )


# @app.route('/alunos/<int:id>')
# @login_required
# def alunos_view(id):
#     """Visualizar detalhes de um aluno, incluindo idade, histórico e status."""
#     response = api_request(f'/alunos/{id}')
#     aluno = None
#     historico = []
#     status_info = {} # Prepara um dicionário para as informações de status

#     if response and response.status_code == 200:
#         aluno = response.json()
        
#         # Lógica da idade (já existente)
#         if aluno.get('data_nascimento'):
#             try:
#                 data_nasc = datetime.strptime(aluno['data_nascimento'], '%Y-%m-%d').date()
#                 hoje = date.today()
#                 idade = hoje.year - data_nasc.year - ((hoje.month, hoje.day) < (data_nasc.month, data_nasc.day))
#                 aluno['idade'] = idade
#             except ValueError:
#                 aluno['idade'] = None

#         # Busca o histórico de atividades
#         historico_response = api_request(f"/alunos/{id}/historico")
#         if historico_response and historico_response.status_code == 200:
#             historico_bruto = historico_response.json()
#             for evento in historico_bruto:
#                 data_obj = datetime.fromisoformat(evento['data'])
#                 evento['data_formatada'] = data_obj.strftime('%d/%m/%Y às %H:%M')
#             historico = historico_bruto
            
#         # --- NOVA LÓGICA PARA BUSCAR O STATUS ---
#         status_response = api_request(f"/alunos/{id}/status-detalhado")
#         if status_response and status_response.status_code == 200:
#             status_info = status_response.json()
#         # --- FIM DA NOVA LÓGICA ---

#     else:
#         flash('Aluno não encontrado.', 'error')
    
#     # Passa as novas informações para o template
#     return render_template('alunos/view.html', aluno=aluno, historico=historico, status_info=status_info)

# @app.route('/alunos/novo')
# @login_required
# def alunos_novo():
#     return render_template('alunos/form.html', aluno=None)


# @app.route('/alunos/<int:id>/editar')
# @login_required
# def alunos_editar(id):
#     response = api_request(f'/alunos/{id}')
#     aluno = None
#     if response and response.status_code == 200:
#         aluno = response.json()
#     else:
#         flash("Aluno não encontrado.", "error")
#         return redirect(url_for("alunos_list"))
#     return render_template('alunos/form.html', aluno=aluno)


# @app.route("/alunos/salvar", methods=["POST"])
# @login_required
# def alunos_salvar():
#     try: 
#         data = {
#             "nome": request.form.get("nome"),
#             "email": request.form.get("email"),
#             "cpf": request.form.get("cpf"),
#             "telefone": request.form.get("telefone"),
#             "data_nascimento": request.form.get("data_nascimento"),
#             "endereco": request.form.get("endereco"),
#             "observacoes": request.form.get("observacoes"),
#             # --- ADICIONE ESTAS LINHAS ---
#             "nome_responsavel": request.form.get("nome_responsavel"),
#             "cpf_responsavel": request.form.get("cpf_responsavel"),
#             "parentesco_responsavel": request.form.get("parentesco_responsavel"),
#             "telefone_responsavel": request.form.get("telefone_responsavel"),
#             "email_responsavel": request.form.get("email_responsavel"),
#             # --- FIM DA ADIÇÃO ---
#         }
#         data = {k: v for k, v in data.items() if v}
        
#         files = {}
#         if "foto_perfil" in request.files and request.files["foto_perfil"].filename != "":
#             foto = request.files["foto_perfil"]
#             files["foto"] = (foto.filename, foto.stream, foto.content_type)
        
#         aluno_id = request.form.get("id")
#         if aluno_id:
#             response = api_request(f"/alunos/{aluno_id}", method="PUT", data=data, files=files)
#             success_status = 200
#             success_message = "Aluno atualizado com sucesso!"
#         else:
#             response = api_request("/alunos", method="POST", data=data, files=files)
#             success_status = 201
#             success_message = "Aluno cadastrado com sucesso!"
            
#         if response and response.status_code == success_status:
#             flash(success_message, "success")
#         else:
#             error_msg = "Erro ao salvar aluno."
#             if response:
#                 try:
#                     error_detail = response.json().get("detail", "")
#                     if error_detail:
#                         error_msg += f" {error_detail}"
#                 except:
#                     pass
#             flash(error_msg, "error")
            
#     except Exception as e:
#         flash("Erro interno ao salvar aluno.", "error")
#         app.logger.error(f"Erro ao salvar aluno: {e}")
        
#     return redirect(url_for("alunos_list"))


# @app.route("/alunos/<int:id>/deletar", methods=["POST"])
# @login_required
# def alunos_deletar(id):
#     response = api_request(f"/alunos/{id}", method="DELETE")
#     if response and response.status_code == 204:
#         flash("Aluno excluído com sucesso!", "success")
#         app.logger.info(f"Aluno {id} excluído")
#     else:
#         flash("Erro ao excluir aluno.", "error")
#         app.logger.error(f"Erro ao excluir aluno {id}: {response.text if response else 'Sem resposta'}")
#     return redirect(url_for("alunos_list"))


# # ... (código existente das rotas de alunos) ...
#     return redirect(url_for("alunos_view", id=aluno_id))


# # === ROTAS PARA PROFESSORES ===

# @app.route('/professores')
# @login_required
# def professores_list():
#     response = api_request('/professores')
#     professores = []
#     if response and response.status_code == 200:
#         professores = response.json()
#     return render_template('professores/list.html', professores=professores)


# @app.route("/professores/novo")
# @login_required
# def professores_novo():
#     return render_template("professores/form.html", professor=None)


# @app.route("/professores/<int:id>")
# def professores_view(id):
#     response = api_request(f"/professores/{id}")
#     professor = None
#     if response and response.status_code == 200:
#         professor = response.json()
#     return render_template("professores/view.html", professor=professor)


# @app.route("/professores/<int:id>/editar")
# @login_required
# def professores_editar(id):
#     response = api_request(f"/professores/{id}")
#     professor = None
#     if response and response.status_code == 200:
#         professor = response.json()
#     else:
#         flash("Professor não encontrado.", "error")
#         return redirect(url_for("professores_list"))
#     return render_template("professores/form.html", professor=professor)


# @app.route("/professores/salvar", methods=["POST"])
# @login_required
# def professores_salvar():
#     try:
#         data = {
#             "nome": request.form.get("nome"),
#             "email": request.form.get("email"),
#             "cpf": request.form.get("cpf"),
#             "telefone": request.form.get("telefone"),
#             "data_nascimento": request.form.get("data_nascimento"),
#             "especialidade": request.form.get("especialidade"),
#             "data_contratacao": request.form.get("data_contratacao"),
#             "salario": request.form.get("salario"),
#             "observacoes": request.form.get("observacoes")
#         }
#         data = {k: v for k, v in data.items() if v}
        
#         files = {}
#         if "foto_perfil" in request.files and request.files["foto_perfil"].filename != "":
#             foto = request.files["foto_perfil"]
#             files["foto"] = (foto.filename, foto.stream, foto.content_type)
        
#         professor_id = request.form.get("id")
#         if professor_id:
#             response = api_request(f"/professores/{professor_id}", method="PUT", data=data, files=files)
#             success_status = 200
#             success_message = "Professor atualizado com sucesso!"
#         else:
#             response = api_request("/professores", method="POST", data=data, files=files)
#             success_status = 201
#             success_message = "Professor cadastrado com sucesso!"
        
#         if response and response.status_code == success_status:
#             flash(success_message, "success")
#         else:
#             error_msg = "Erro ao salvar professor."
#             if response:
#                 try:
#                     error_detail = response.json().get("detail", "")
#                     if error_detail:
#                         error_msg += f" {error_detail}"
#                 except:
#                     pass
#             flash(error_msg, "error")
#     except Exception as e:
#         flash("Erro interno ao salvar professor.", "error")
#         app.logger.error(f"Erro interno ao salvar professor: {e}")
        
#     return redirect(url_for("professores_list"))

# @app.route("/professores/<int:id>/deletar", methods=["POST"])
# @login_required
# def professores_deletar(id):
#     response = api_request(f"/professores/{id}", method="DELETE")
#     if response and response.status_code == 204:
#         flash("Professor excluído com sucesso!", "success")
#     else:
#         flash("Erro ao excluir professor.", "error")
#     return redirect(url_for("professores_list"))


# # === ROTAS PARA TURMAS ===
# @app.route("/turmas")
# @login_required
# def turmas_list():
#     response = api_request("/turmas")
#     turmas = []
#     if response and response.status_code == 200:
#         turmas = response.json()
#     return render_template("turmas/list.html", turmas=turmas)

# @app.route("/turmas/novo")
# @login_required
# def turmas_novo():
#     professores_response = api_request("/professores")
#     professores = professores_response.json() if professores_response and professores_response.status_code == 200 else []
#     return render_template("turmas/form.html", turma=None, professores=professores)


# @app.route("/turmas/<int:id>")
# @login_required
# def turmas_view(id):
#     turma_response = api_request(f"/turmas/{id}")
#     turma = None
#     if turma_response and turma_response.status_code == 200:
#         turma = turma_response.json()
    
#     return render_template("turmas/view.html", turma=turma)


# @app.route("/turmas/<int:id>/editar")
# @login_required
# def turmas_editar(id):
#     turma_response = api_request(f"/turmas/{id}")
#     turma = None
#     if turma_response and turma_response.status_code == 200:
#         turma = turma_response.json()
#     else:
#         flash("Turma não encontrada.", "error")
#         return redirect(url_for("turmas_list"))
        
#     professores_response = api_request("/professores")
#     professores = professores_response.json() if professores_response and professores_response.status_code == 200 else []

#     return render_template("turmas/form.html", turma=turma, professores=professores)


# @app.route("/turmas/salvar", methods=["POST"])
# @login_required
# def turmas_salvar():
#     try:
#         turma_data = {
#             "nome": request.form.get("nome"),
#             "modalidade": request.form.get("modalidade"),
#             "horario": request.form.get("horario"),
#             "dias_semana": "Segunda, Quarta, Sexta",
#             "professor_id": int(request.form.get("professor_id")) if request.form.get("professor_id") else None,
#             "nivel": request.form.get("nivel"),
#             "capacidade_maxima": int(request.form.get("capacidade_maxima")) if request.form.get("capacidade_maxima") else None,
#             "valor_mensalidade": float(request.form.get("valor_mensalidade").replace(',', '.')) if request.form.get("valor_mensalidade") else None,
#             "idade_minima": int(request.form.get("idade_minima")) if request.form.get("idade_minima") else None,
#             "ativa": request.form.get("ativa") == "1",
#             "descricao": request.form.get("descricao"),
#             "observacoes": request.form.get("observacoes")
#         }
        
#         # final_data = {
#         #     k: v for k, v in turma_data.items()
#         #     if v is not None
#         # }
#         final_data = turma_data
        
#         turma_id = request.form.get("id")
        
#         if turma_id:
#             response = api_request(f"/turmas/{turma_id}", method="PUT", json=final_data)
#             success_status = 200
#             success_message = "Turma atualizada com sucesso!"
#         else:
#             response = api_request("/turmas", method="POST", json=final_data)
#             success_status = 201
#             success_message = "Turma cadastrada com sucesso!"
            
#         if response and response.status_code == success_status:
#             flash(success_message, "success")
#         else:
#             error_msg = "Erro ao salvar turma."
#             if response:
#                 try:
#                     error_detail = response.json().get("detail", "")
#                     if error_detail:
#                         error_msg += f" Detalhe: {error_detail}"
#                 except:
#                     pass
#             flash(error_msg, "error")
            
#     except Exception as e:
#         flash(f"Erro interno ao salvar turma. {e}", "error")
#         app.logger.error(f"Erro ao salvar turma: {e}")
        
#     return redirect(url_for("turmas_list"))


# @app.route("/turmas/<int:id>/deletar", methods=["POST"])
# @login_required
# def turmas_deletar(id):
#     response = api_request(f"/turmas/{id}", method="DELETE")
#     if response and response.status_code == 204:
#         flash("Turma excluída com sucesso!", "success")
#     else:
#         error_msg = "Erro ao excluir turma."
#         if response:
#             try:
#                 error_detail = response.json().get("detail", "")
#                 if error_detail:
#                     error_msg += f" Detalhe: {error_detail}"
#             except:
#                 pass
#         flash(error_msg, "error")
#         app.logger.error(f"Erro ao excluir turma {id}: {response.text if response else 'Sem resposta'}")
#     return redirect(url_for("turmas_list"))




# @app.route("/matriculas")
# @login_required
# def matriculas_list():
#     # Pega os parâmetros da URL (ex: ?busca=Joao&status=ativa)
#     busca = request.args.get('busca', '')
#     status = request.args.get('status', '')

#     # Monta a URL da API com os parâmetros
#     endpoint = "/matriculas?"
#     params = []
#     if busca:
#         params.append(f"busca={busca}")
#     if status:
#         params.append(f"status={status}")
    
#     endpoint += "&".join(params)
    
#     response = api_request(endpoint)
#     matriculas = []
#     if response and response.status_code == 200:
#         matriculas = response.json()
        
#     return render_template("matriculas/list.html", matriculas=matriculas, busca=busca, status=status)


# @app.route("/matriculas/novo")
# @login_required
# def matriculas_novo():
#     # CORREÇÃO 1: Pede um limite alto para garantir que todos os alunos venham no dropdown
#     alunos_response = api_request("/alunos?limit=2000") 
#     turmas_response = api_request("/turmas")
#     planos_response = api_request("/planos")
    
#     alunos = []
#     if alunos_response and alunos_response.status_code == 200:
#         # CORREÇÃO 2: Extrai a lista de dentro da resposta paginada
#         data = alunos_response.json()
#         alunos = data.get("alunos", [])

#     turmas = turmas_response.json() if turmas_response and turmas_response.status_code == 200 else []
#     planos = planos_response.json() if planos_response and planos_response.status_code == 200 else []
    
#     return render_template("matriculas/form.html", alunos=alunos, turmas=turmas, planos=planos, matricula=None)



# @app.route("/matriculas/salvar", methods=["POST"])
# @login_required
# def matriculas_salvar():
#     try:
#         # Pega os IDs do formulário
#         aluno_id = request.form.get("aluno_id")
#         turma_id = request.form.get("turma_id")
#         plano_id = request.form.get("plano_id")

#         # Validação para garantir que todos os campos foram selecionados
#         if not all([aluno_id, turma_id, plano_id]):
#             flash("Erro: Todos os campos (Aluno, Turma e Plano) são obrigatórios.", "error")
#             return redirect(url_for("matriculas_novo"))

#         matricula_data = {
#             "aluno_id": int(aluno_id),
#             "turma_id": int(turma_id),
#             "plano_id": int(plano_id)
#         }
        
#         response = api_request("/matriculas", method="POST", json=matricula_data)
        
#         if response and response.status_code == 201:
#             flash("Matrícula realizada com sucesso!", "success")
#         else:
#             error_msg = "Erro ao realizar matrícula."
#             if response:
#                 try:
#                     error_detail = response.json().get("detail", "")
#                     if isinstance(error_detail, list):
#                          # Lida com erros de validação do Pydantic
#                         error_msg += " Verifique os dados: " + ", ".join([e.get('msg', '') for e in error_detail])
#                     elif error_detail:
#                         error_msg += f" Detalhe: {error_detail}"
#                 except:
#                     error_msg += f" (Status: {response.status_code})"
#             flash(error_msg, "error")
#             # Em caso de erro na API, redireciona de volta para o formulário
#             return redirect(url_for("matriculas_novo"))
            
#     except ValueError:
#         flash("Erro: Valores inválidos fornecidos para aluno, turma ou plano.", "error")
#         return redirect(url_for("matriculas_novo"))
#     except Exception as e:
#         flash(f"Erro interno ao salvar a matrícula: {e}", "error")
#         return redirect(url_for("matriculas_novo"))
        
#     return redirect(url_for("matriculas_list"))


# @app.route("/matriculas/<int:id>/editar")
# @login_required
# def matriculas_editar(id):
#     matricula_response = api_request(f"/matriculas/{id}")
    
#     # CORREÇÃO 1: Pede um limite alto
#     alunos_response = api_request("/alunos?limit=2000")
#     turmas_response = api_request("/turmas")
#     planos_response = api_request("/planos")
    
#     if not matricula_response or matricula_response.status_code != 200:
#         flash("Matrícula não encontrada!", "error")
#         return redirect(url_for("matriculas_list"))
    
#     matricula = matricula_response.json()
    
#     alunos = []
#     if alunos_response and alunos_response.status_code == 200:
#         # CORREÇÃO 2: Extrai a lista
#         data = alunos_response.json()
#         alunos = data.get("alunos", [])
        
#     turmas = turmas_response.json() if turmas_response and turmas_response.status_code == 200 else []
#     planos = planos_response.json() if planos_response and planos_response.status_code == 200 else []
    
#     return render_template("matriculas/form.html", matricula=matricula, alunos=alunos, turmas=turmas, planos=planos)


# @app.route("/matriculas/salvar_edicao", methods=["POST"])
# @login_required
# def matriculas_salvar_edicao():
#     try:
#         matricula_id = request.form.get("id")
#         matricula_data = {
#             "aluno_id": int(request.form.get("aluno_id")),
#             "turma_id": int(request.form.get("turma_id")),
#             "ativa": True if request.form.get("ativa") == 'on' else False
#         }
        
#         response = api_request(f"/matriculas/{matricula_id}", method="PUT", json=matricula_data)
        
#         if response and response.status_code == 200:
#             flash("Matrícula atualizada com sucesso!", "success")
#         else:
#             flash("Erro ao atualizar matrícula.", "error")
#     except Exception as e:
#         flash(f"Erro interno ao salvar a edição. {e}", "error")
        
#     return redirect(url_for("matriculas_list"))


# @app.route("/matriculas/status/<int:id>", methods=["POST"])
# @login_required
# def matriculas_status(id):
#     try:
#         # Chama o novo endpoint da API que faz toda a lógica de alternar
#         response = api_request(f"/matriculas/{id}/toggle-status", method="POST")
        
#         if response and response.status_code == 200:
#             # Pega o novo status da resposta da API para a mensagem flash
#             new_status = response.json().get("ativa")
#             flash(f"Matrícula {'ativada' if new_status else 'trancada'} com sucesso!", "success")
#         else:
#             flash("Erro ao atualizar o status da matrícula.", "error")
#     except Exception as e:
#         flash(f"Erro interno ao alterar o status da matrícula: {e}", "error")
        
#     return redirect(url_for("matriculas_list"))



# @app.route("/matriculas/deletar/<int:id>", methods=["POST"])
# @login_required
# def matriculas_deletar(id):
#     response = api_request(f"/matriculas/{id}", method="DELETE")
#     if response and response.status_code == 204:
#         flash("Matrícula excluída com sucesso!", "success")
#     else:
#         flash("Erro ao excluir matrícula.", "error")
#     return redirect(url_for("matriculas_list"))



# @app.route("/financeiro/dashboard")
# @login_required
# def financeiro_dashboard():
#     hoje = date.today()
#     primeiro_dia_mes = hoje.replace(day=1)

#     balanco_response = api_request(f"/financeiro/balanco?data_inicio={primeiro_dia_mes.strftime('%Y-%m-%d')}&data_fim={hoje.strftime('%Y-%m-%d')}")
#     stats = {}
#     if balanco_response and balanco_response.status_code == 200:
#         stats = balanco_response.json()
    
#     transacoes_response = api_request("/financeiro/transacoes?limit=5")
#     transacoes = []
#     if transacoes_response and transacoes_response.status_code == 200:
#         transacoes_data = transacoes_response.json()
#         for transacao in transacoes_data:
#             if transacao.get('data'):
#                 transacao['data'] = datetime.fromisoformat(transacao['data'])
#             transacoes.append(transacao)
    
#     # Buscamos as categorias da API
#     categorias_response = api_request("/categorias")
#     categorias = categorias_response.json() if categorias_response and categorias_response.status_code == 200 else []
    
#     # Busca por mensalidades pendentes
#     mensalidades_pendentes_response = api_request("/mensalidades?status=pendente")
#     mensalidades_pendentes = []
#     if mensalidades_pendentes_response and mensalidades_pendentes_response.status_code == 200:
#         mensalidades_pendentes = mensalidades_pendentes_response.json()

#     return render_template(
#         "financeiro/dashboard.html", 
#         stats=stats, 
#         transacoes=transacoes, 
#         categorias=categorias,
#         mensalidades_pendentes=mensalidades_pendentes
#     )


# @app.route("/financeiro/transacoes")
# @login_required
# def financeiro_transacoes():
#     tipo_filtro = request.args.get('tipo')
#     categoria_filtro = request.args.get('categoria')
#     busca_filtro = request.args.get('busca')
#     data_inicio_filtro = request.args.get('data_inicio')
#     data_fim_filtro = request.args.get('data_fim')

#     endpoint_transacoes = "/financeiro/transacoes"
#     query_params_transacoes = []
#     if tipo_filtro: query_params_transacoes.append(f"tipo={tipo_filtro}")
#     if categoria_filtro: query_params_transacoes.append(f"categoria={categoria_filtro}")
#     if busca_filtro: query_params_transacoes.append(f"busca={busca_filtro}")
#     if data_inicio_filtro: query_params_transacoes.append(f"data_inicio={data_inicio_filtro}")
#     if data_fim_filtro: query_params_transacoes.append(f"data_fim={data_fim_filtro}")
    
#     if query_params_transacoes:
#         endpoint_transacoes += "?" + "&".join(query_params_transacoes)
        
#     response_transacoes = api_request(endpoint_transacoes)
#     transacoes = []
#     if response_transacoes and response_transacoes.status_code == 200:
#         transacoes_data = response_transacoes.json()
#         for transacao in transacoes_data:
#             if transacao.get('data'):
#                 transacao['data'] = datetime.fromisoformat(transacao['data'])
#             transacoes.append(transacao)

#     endpoint_balanco = "/financeiro/balanco"
#     query_params_balanco = []
#     if data_inicio_filtro: query_params_balanco.append(f"data_inicio={data_inicio_filtro}")
#     if data_fim_filtro: query_params_balanco.append(f"data_fim={data_fim_filtro}")

#     if query_params_balanco:
#         endpoint_balanco += "?" + "&".join(query_params_balanco)
    
#     balanco_response = api_request(endpoint_balanco)
#     stats = {}
#     if balanco_response and balanco_response.status_code == 200:
#         stats = balanco_response.json()
    
#     # Buscamos as categorias da API
#     categorias_response = api_request("/categorias")
#     categorias = categorias_response.json() if categorias_response and categorias_response.status_code == 200 else []
    
#     return render_template("financeiro/transacoes.html", transacoes=transacoes, stats=stats, categorias=categorias)


# @app.route("/financeiro/salvar_transacao", methods=["POST"])
# @login_required
# def financeiro_salvar_transacao():
#     try:
#         transacao_data = {
#             "id": request.form.get("id"),
#             "tipo": request.form.get("tipo"),
#             "categoria": request.form.get("categoria"),
#             "descricao": request.form.get("descricao"),
#             "valor": float(request.form.get("valor").replace(',', '.')),
#             "status": request.form.get("status"),
#             "observacoes": request.form.get("observacoes"),
#             "data": request.form.get("data")
#         }
        
#         transacao_data = {k: v for k, v in transacao_data.items() if v}

#         transacao_id = request.form.get("id")
#         if transacao_id:
#             response = api_request(f"/financeiro/transacoes/{transacao_id}", method="PUT", json=transacao_data)
#             success_message = "Transação atualizada com sucesso!"
#         else:
#             response = api_request("/financeiro/transacoes", method="POST", json=transacao_data)
#             success_message = "Transação salva com sucesso!"

#         if response and response.status_code in [200, 201]:
#             flash(success_message, "success")
#         else:
#             error_msg = "Erro ao salvar transação."
#             if response:
#                 try:
#                     error_detail = response.json().get("detail", "")
#                     if error_detail:
#                         error_msg += f" Detalhe: {error_detail}"
#                 except:
#                     pass
#             flash(error_msg, "error")

#     except Exception as e:
#         flash(f"Erro interno ao salvar transação: {e}", "error")
    
#     return redirect(url_for("financeiro_transacoes"))


# @app.route("/financeiro/deletar_transacao/<int:id>", methods=["POST"])
# @login_required
# def financeiro_deletar_transacao(id):
#     response = api_request(f"/financeiro/transacoes/{id}", method="DELETE")
#     if response and response.status_code == 204:
#         flash("Transação excluída com sucesso!", "success")
#     else:
#         flash("Erro ao excluir transação.", "error")
#     return redirect(url_for("financeiro_transacoes"))
    
    
# @app.route("/produtos")
# @login_required
# def produtos_list():
#     response = api_request("/produtos")
#     produtos = []
#     if response and response.status_code == 200:
#         produtos = response.json()
#     return render_template("produtos/list.html", produtos=produtos)


# @app.route("/produtos/novo")
# @login_required
# def produtos_novo():
#     return render_template("produtos/form.html", produto=None)


# @app.route("/produtos/<int:id>/editar")
# @login_required
# def produtos_editar(id):
#     response = api_request(f"/produtos/{id}")
#     produto = None
#     if response and response.status_code == 200:
#         produto = response.json()
#     else:
#         flash("Produto não encontrado.", "error")
#         return redirect(url_for("produtos_list"))
#     return render_template("produtos/form.html", produto=produto)
  
  
# @app.route("/produtos/salvar", methods=["POST"])
# @login_required
# def produtos_salvar():
#     try:
#         produto_data = {
#             "codigo": request.form.get("codigo"),
#             "nome": request.form.get("nome"),
#             "descricao": request.form.get("descricao"),
#             "preco_custo": float(request.form.get("preco_custo").replace(',', '.')),
#             "preco_venda": float(request.form.get("preco_venda").replace(',', '.')),
#             "quantidade_estoque": int(request.form.get("quantidade_estoque"))
#         }

#         produto_data = {k: v for k, v in produto_data.items() if v}
        
#         produto_id = request.form.get("id")
#         if produto_id:
#             response = api_request(f"/produtos/{produto_id}", method="PUT", json=produto_data)
#             success_message = "Produto atualizado com sucesso!"
#         else:
#             response = api_request("/produtos", method="POST", json=produto_data)
#             success_message = "Produto cadastrado com sucesso!"

#         if response and response.status_code in [200, 201]:
#             flash(success_message, "success")
#         else:
#             error_msg = "Erro ao salvar produto."
#             if response:
#                 try:
#                     error_detail = response.json().get("detail", "")
#                     if error_detail:
#                         error_msg += f" Detalhe: {error_detail}"
#                 except:
#                     pass
#             flash(error_msg, "error")

#     except Exception as e:
#         flash(f"Erro interno ao salvar produto: {e}", "error")
    
#     return redirect(url_for("produtos_list"))


# @app.route("/produtos/deletar/<int:id>", methods=["POST"])
# @login_required
# def produtos_deletar(id):
#     response = api_request(f"/produtos/{id}", method="DELETE")
#     if response and response.status_code == 204:
#         flash("Produto excluído com sucesso!", "success")
#     else:
#         flash("Erro ao excluir produto.", "error")
#     return redirect(url_for("produtos_list"))
    
    
# @app.route("/planos")
# @login_required
# def planos_list():
#     response = api_request("/planos")
#     planos = []
#     if response and response.status_code == 200:
#         planos = response.json()
#     return render_template("planos/list.html", planos=planos)


# @app.route("/planos/novo")
# @login_required
# def planos_novo():
#     return render_template("planos/form.html", plano=None)


# @app.route("/planos/<int:id>/editar")
# def planos_editar(id):
#     response = api_request(f"/planos/{id}")
#     plano = None
#     if response and response.status_code == 200:
#         plano = response.json()
#     else:
#         flash("Plano não encontrado.", "error")
#         return redirect(url_for("planos_list"))
#     return render_template("planos/form.html", plano=plano)


# @app.route("/planos/salvar", methods=["POST"])
# @login_required
# def planos_salvar():
#     try:
#         plano_data = {
#             "nome": request.form.get("nome"),
#             "descricao": request.form.get("descricao"),
#             "valor": float(request.form.get("valor").replace(',', '.')),
#             "periodo_meses": int(request.form.get("periodo_meses"))
#         }

#         plano_data = {k: v for k, v in plano_data.items() if v}
        
#         plano_id = request.form.get("id")
#         if plano_id:
#             response = api_request(f"/planos/{plano_id}", method="PUT", json=plano_data)
#             success_message = "Plano atualizado com sucesso!"
#         else:
#             response = api_request("/planos", method="POST", json=plano_data)
#             success_message = "Plano cadastrado com sucesso!"

#         if response and response.status_code in [200, 201]:
#             flash(success_message, "success")
#         else:
#             error_msg = "Erro ao salvar plano."
#             if response:
#                 try:
#                     error_detail = response.json().get("detail", "")
#                     if error_detail:
#                         error_msg += f" Detalhe: {error_detail}"
#                 except:
#                     pass
#             flash(error_msg, "error")

#     except Exception as e:
#         flash(f"Erro interno ao salvar plano: {e}", "error")
    
#     return redirect(url_for("planos_list"))


# @app.route("/planos/deletar/<int:id>", methods=["POST"])
# @login_required
# def planos_deletar(id):
#     response = api_request(f"/planos/{id}", method="DELETE")
#     if response and response.status_code == 204:
#         flash("Plano excluído com sucesso!", "success")
#     else:
#         flash("Erro ao excluir plano.", "error")
#     return redirect(url_for("planos_list"))
    
    
    
# @app.route("/mensalidades")
# @login_required
# def mensalidades_list():
#     page = request.args.get('page', 1, type=int)
#     limit = 20 # Define o limite por página aqui (pode ser ajustável depois)
#     busca = request.args.get('busca', '')
#     status_filtro = request.args.get('status', '') # Filtro de status pendente/pago
#     skip = (page - 1) * limit

#     # Monta os parâmetros para a API
#     params = {
#         "skip": skip,
#         "limit": limit
#     }
#     if busca:
#         params["busca_aluno"] = busca
#     if status_filtro:
#         params["status"] = status_filtro

#     response = api_request("/mensalidades", params=params)

#     mensalidades = []
#     total_mensalidades = 0
#     total_pages = 0

#     if response and response.status_code == 200:
#         data = response.json()
#         mensalidades = data.get("mensalidades", [])
#         total_mensalidades = data.get("total", 0)
#         if total_mensalidades > 0 and limit > 0:
#             total_pages = math.ceil(total_mensalidades / limit)
#     else:
#         flash("Erro ao carregar mensalidades da API.", "error")

#     return render_template(
#         "mensalidades/list.html",
#         mensalidades=mensalidades,
#         page=page,
#         limit=limit,
#         total_pages=total_pages,
#         total_mensalidades=total_mensalidades,
#         busca=busca,
#         status_filtro=status_filtro # Passa o filtro para o template
#     )


# @app.route("/mensalidades/novo")
# @login_required
# def mensalidades_novo():
#     alunos_response = api_request("/alunos")
#     alunos = alunos_response.json() if alunos_response and alunos_response.status_code == 200 else []
#     planos_response = api_request("/planos")
#     planos = planos_response.json() if planos_response and planos_response.status_code == 200 else []
    
#     return render_template("mensalidades/form.html", alunos=alunos, planos=planos)


# @app.route("/mensalidades/salvar", methods=["POST"])
# @login_required
# def mensalidades_salvar():
#     try:
#         mensalidade_data = {
#             "aluno_id": int(request.form.get("aluno_id")),
#             "plano_id": int(request.form.get("plano_id")),
#             "valor": float(request.form.get("valor").replace(',', '.')),
#             "data_vencimento": request.form.get("data_vencimento")
#         }
        
#         response = api_request("/mensalidades", method="POST", json=mensalidade_data)
        
#         if response and response.status_code == 201:
#             flash("Mensalidade cadastrada com sucesso!", "success")
#         else:
#             error_msg = "Erro ao cadastrar mensalidade."
#             if response:
#                 try:
#                     error_detail = response.json().get("detail", "")
#                     if error_detail:
#                         error_msg += f" Detalhe: {error_detail}"
#                 except:
#                     pass
#             flash(error_msg, "error")

#     except Exception as e:
#         flash(f"Erro interno ao salvar mensalidade: {e}", "error")
    
#     return redirect(url_for("mensalidades_list"))


# @app.route("/mensalidades/pagar/<int:id>", methods=["POST"])
# @login_required
# def mensalidades_pagar(id):
#     response = api_request(f"/mensalidades/processar_pagamento/{id}", method="POST")
#     if response and response.status_code == 200:
#         flash("Pagamento processado com sucesso!", "success")
#     else:
#         flash("Erro ao processar pagamento.", "error")
#     return redirect(url_for("mensalidades_list"))


# @app.route("/mensalidades/deletar/<int:id>", methods=["POST"])
# @login_required
# def mensalidades_deletar(id):
#     response = api_request(f"/mensalidades/{id}", method="DELETE")
#     if response and response.status_code == 204:
#         flash("Mensalidade excluída com sucesso!", "success")
#     else:
#         flash("Erro ao excluir mensalidade.", "error")
#     return redirect(url_for("mensalidades_list"))


# @app.route("/mensalidades/pagar-online/<int:id>", methods=["POST"])
# @login_required
# def mensalidades_pagar_online(id):
#     """
#     Gera o link de pagamento do Mercado Pago chamando a API de forma segura.
#     Esta é a rota que o botão 'Pagar Online' da interface chama.
#     """
#     # CORREÇÃO: Esta é a URL correta da API para gerar o link da mensalidade
#     response = api_request(f"/pagamentos/gerar/mensalidade/{id}", method="POST")
    
#     if response and response.status_code == 200:
#         return jsonify(response.json())
#     else:
#         error_message = "Falha ao gerar link de pagamento."
#         if response:
#             try:
#                 error_message += f" Detalhe: {response.json().get('detail', 'Erro desconhecido da API')}"
#             except:
#                  error_message += f" (Status: {response.status_code})"
#         return jsonify({"error": error_message}), 500
    
# @app.context_processor
# def inject_global_vars():
#     """Injeta variáveis globais em todos os templates."""
#     return dict(API_BASE_URL=API_BASE_URL)
    
# @app.route("/eventos")
# @login_required
# def eventos_list():
#     response = api_request("/eventos")
#     eventos = response.json() if response and response.status_code == 200 else []
    
#     # KPIs para o dashboard de eventos
#     kpis = {
#         "total_eventos": len(eventos),
#         "total_arrecadado": sum(inscricao['valor_pago'] for evento in eventos for inscricao in evento.get('inscricoes', []) if inscricao.get('valor_pago')),
#         "total_inscritos": sum(len(evento.get('inscricoes', [])) for evento in eventos)
#     }

#     return render_template("eventos/list.html", eventos=eventos, kpis=kpis)


# @app.route("/eventos/novo")
# @login_required
# def eventos_novo():
#     return render_template("eventos/form.html", evento=None)

# @app.route("/eventos/<int:id>/editar")
# @login_required
# def eventos_editar(id):
#     response = api_request(f"/eventos/{id}")
#     evento = response.json() if response and response.status_code == 200 else None
#     if not evento:
#         flash("Evento não encontrado.", "error")
#         return redirect(url_for("eventos_list"))
#     return render_template("eventos/form.html", evento=evento)


# @app.route("/eventos/salvar", methods=["POST"])
# @login_required
# def eventos_salvar():
#     try:
#         data = {
#             "nome": request.form.get("nome"),
#             "tipo": request.form.get("tipo"),
#             "descricao": request.form.get("descricao"),
#             "local": request.form.get("local"),
#             "data_evento": request.form.get("data_evento"),
#             "valor_inscricao": float(request.form.get("valor_inscricao", 0)),
#             "capacidade": int(request.form.get("capacidade", 0)),
#             "status": request.form.get("status"),
#         }
        
#         evento_id = request.form.get("id")
#         if evento_id:
#             response = api_request(f"/eventos/{evento_id}", method="PUT", json=data)
#             msg = "Evento atualizado com sucesso!"
#         else:
#             response = api_request("/eventos", method="POST", json=data)
#             msg = "Evento criado com sucesso!"

#         if response and response.status_code in [200, 201]:
#             flash(msg, "success")
#         else:
#             flash("Erro ao salvar evento.", "error")
#     except Exception as e:
#         flash(f"Erro interno: {e}", "error")

#     return redirect(url_for("eventos_list"))


# @app.route("/eventos/<int:id>")
# @login_required
# def eventos_view(id):
#     evento_resp = api_request(f"/eventos/{id}")
#     inscricoes_resp = api_request(f"/inscricoes/evento/{id}")
    
#     # CORREÇÃO 1: Pede um limite alto para garantir que todos os alunos apareçam no dropdown
#     alunos_resp = api_request("/alunos?limit=2000") 

#     evento = evento_resp.json() if evento_resp and evento_resp.status_code == 200 else None
#     inscricoes = inscricoes_resp.json() if inscricoes_resp and inscricoes_resp.status_code == 200 else []
    
#     alunos = []
#     if alunos_resp and alunos_resp.status_code == 200:
#         # CORREÇÃO 2: Extrai a lista 'alunos' de dentro da resposta da API
#         data = alunos_resp.json()
#         alunos = data.get("alunos", [])

#     if not evento:
#         flash("Evento não encontrado.", "error")
#         return redirect(url_for("eventos_list"))

#     return render_template("eventos/view.html", evento=evento, inscricoes=inscricoes, alunos=alunos)


# @app.route("/eventos/inscrever", methods=["POST"])
# @login_required
# def eventos_inscrever():
#     evento_id = request.form.get("evento_id")
#     aluno_id = request.form.get("aluno_id")
    
#     if not aluno_id:
#         flash("Selecione um aluno para inscrever.", "error")
#         return redirect(url_for("eventos_view", id=evento_id))
        
#     data = {"evento_id": int(evento_id), "aluno_id": int(aluno_id)}
#     response = api_request("/inscricoes", method="POST", json=data)

#     # CORREÇÃO: Aceita 200 ou 201 como sucesso
#     if response and response.status_code in [200, 201]:
#         flash("Aluno inscrito com sucesso!", "success")
#     else:
#         error = response.json().get('detail') if response else 'desconhecido'
#         flash(f"Erro ao inscrever aluno: {error}", "error")

#     return redirect(url_for("eventos_view", id=evento_id))



# @app.route("/inscricoes/<int:id>/pagar-manual", methods=["POST"])
# @login_required
# def inscricao_pagar_manual(id):
#     evento_id = request.form.get("evento_id")
#     response = api_request(f"/inscricoes/{id}/confirmar-pagamento-manual", method="POST")
#     if response and response.status_code == 200:
#         flash("Pagamento da inscrição confirmado!", "success")
#     else:
#         flash("Erro ao confirmar pagamento.", "error")
#     return redirect(url_for("eventos_view", id=evento_id))


# @app.route("/eventos/<int:id>/deletar", methods=["POST"])
# @login_required
# def eventos_deletar(id):
#     response = api_request(f"/eventos/{id}", method="DELETE")
#     if response and response.status_code == 204:
#         flash("Evento excluído com sucesso!", "success")
#     else:
#         flash("Erro ao excluir o evento.", "error")
#     return redirect(url_for("eventos_list"))


# @app.route("/inscricoes/<int:id>/deletar", methods=["POST"])
# @login_required
# def inscricao_deletar(id):
#     evento_id = request.form.get("evento_id")
#     response = api_request(f"/inscricoes/{id}", method="DELETE")
#     if response and response.status_code == 204:
#         flash("Inscrição removida com sucesso!", "success")
#     else:
#         flash("Erro ao remover inscrição.", "error")
#     return redirect(url_for("eventos_view", id=evento_id))


# @app.route("/inscricoes/<int:id>/pagar-online", methods=["POST"])
# @login_required
# def inscricao_pagar_online(id):
#     """Gera o link de pagamento do Mercado Pago para uma inscrição de evento."""
#     response = api_request(f"/pagamentos/gerar/evento/{id}", method="POST")
#     if response and response.status_code == 200:
#         return jsonify(response.json())
#     else:
#         return jsonify({"error": "Falha ao gerar link de pagamento para o evento"}), 500


# @app.route("/inscricoes/<int:id>/cancelar", methods=["POST"])
# @login_required
# def inscricao_cancelar(id):
#     evento_id = request.form.get("evento_id")
#     response = api_request(f"/inscricoes/{id}/cancelar", method="POST")
#     if response and response.status_code == 200:
#         flash("Inscrição cancelada com sucesso!", "success")
#     else:
#         error = response.json().get('detail') if response else 'desconhecido'
#         flash(f"Erro ao cancelar inscrição: {error}", "error")
#     return redirect(url_for("eventos_view", id=evento_id))


# # Em frontend/app.py (adicione no final do arquivo)

# # === ROTAS PARA USUÁRIOS (Acesso Restrito a Admins) ===

# @app.route("/usuarios")
# @login_required
# @admin_required
# def usuarios_list():
#     response = api_request("/usuarios")
#     usuarios = response.json() if response and response.status_code == 200 else []
#     return render_template("usuarios/list.html", usuarios=usuarios)

# @app.route("/usuarios/novo")
# @login_required
# @admin_required
# def usuarios_novo():
#     return render_template("usuarios/form.html", usuario=None)

# @app.route("/usuarios/editar/<int:id>")
# @login_required
# @admin_required
# def usuarios_editar(id):
#     # A API já protege contra acesso indevido, mas validamos aqui também.
#     response = api_request(f"/usuarios/{id}")
#     usuario = response.json() if response and response.status_code == 200 else None
#     if not usuario:
#         flash("Usuário não encontrado.", "error")
#         return redirect(url_for("usuarios_list"))
#     return render_template("usuarios/form.html", usuario=usuario)

# @app.route("/usuarios/salvar", methods=["POST"])
# @login_required
# @admin_required
# def usuarios_salvar():
#     user_id = request.form.get("id")
#     password = request.form.get("password")
    
#     data = {
#         "email": request.form.get("email"),
#         "nome": request.form.get("nome"),
#         "role": request.form.get("role"),
#     }
#     # Só adiciona a senha se ela foi preenchida (para não apagar a senha ao editar)
#     if password:
#         data['password'] = password

#     if user_id:
#         response = api_request(f"/usuarios/{user_id}", method="PUT", json=data)
#         msg = "Usuário atualizado com sucesso!"
#     else:
#         response = api_request("/usuarios", method="POST", json=data)
#         msg = "Usuário criado com sucesso!"

#     if response and response.status_code in [200, 201]:
#         flash(msg, "success")
#     else:
#         error = response.json().get('detail') if response else 'desconhecido'
#         flash(f"Erro ao salvar usuário: {error}", "error")

#     return redirect(url_for("usuarios_list"))

# @app.route("/usuarios/deletar/<int:id>", methods=["POST"])
# @login_required
# @admin_required
# def usuarios_deletar(id):
#     # Evita que o admin se auto-delete
#     if id == session.get('user_info', {}).get('id'):
#         flash("Você não pode excluir seu próprio usuário.", "error")
#         return redirect(url_for("usuarios_list"))

#     response = api_request(f"/usuarios/{id}", method="DELETE")
#     if response and response.status_code == 204:
#         flash("Usuário excluído com sucesso!", "success")
#     else:
#         flash("Erro ao excluir usuário.", "error")
#     return redirect(url_for("usuarios_list"))


# # Em frontend/app.py

# # Em frontend/app.py

# @app.route("/login/callback")
# def login_callback():
#     token = request.args.get('token')
#     if not token:
#         flash("Falha na autenticação.", "error")
#         return redirect(url_for('login'))
        
#     user_info_resp = api_request("/auth/me", headers={"Authorization": f"Bearer {token}"})
    
#     if user_info_resp and user_info_resp.status_code == 200:
#         user_info = user_info_resp.json()
        
#         # --- LÓGICA DE VERIFICAÇÃO DE STATUS PENDENTE ---
#         if user_info.get('role') == 'pendente':
#             flash("Sua conta foi criada e está aguardando aprovação de um administrador.", "info")
#             return redirect(url_for('login'))
#         # --- FIM DA LÓGICA ---

#         session['access_token'] = token
#         session['user_info'] = user_info
#         return redirect(url_for('index'))
#     else:
#         flash("Não foi possível obter os dados do usuário.", "error")
#         return redirect(url_for('login'))

# # Adicione estas novas rotas ao final do seu arquivo frontend/app.py

# # === ROTAS DO PORTAL DO ALUNO ===

# @app.route("/portal/login", methods=["GET", "POST"])
# def portal_aluno_login():
#     if request.method == "POST":
#         username = request.form.get("username")
#         password = request.form.get("password")
        
#         api_data = {"username": username, "password": password}
#         response = requests.post(f"{API_BASE_URL}/api/v1/auth/token", data=api_data)
        
#         if response.status_code == 200:
#             data = response.json()
#             user_info = data.get('user_info', {})
            
#             # Apenas permite o login se a role for 'aluno'
#             if user_info.get('role') == 'aluno':
#                 session['access_token'] = data['access_token']
#                 session['user_info'] = user_info
#                 return redirect(url_for('portal_aluno_dashboard'))
#             else:
#                 flash("Acesso negado. Esta área é exclusiva para alunos.", "error")
#         else:
#             flash("Email ou senha inválidos.", "error")

#     return render_template("portal_aluno/login.html")


# @app.route("/portal/register", methods=["GET", "POST"])
# def portal_aluno_register():
#     if request.method == "POST":
#         data = {
#             "nome": request.form.get("nome"),
#             "email": request.form.get("email"),
#             "password": request.form.get("password"),
#             "telefone": request.form.get("telefone"),
#             "data_nascimento": request.form.get("data_nascimento"),
#         }
        
#         # Filtra valores vazios para não enviar para a API
#         data_to_send = {k: v for k, v in data.items() if v}

#         response = api_request("/portal/register", method="POST", json=data_to_send)
        
#         if response and response.status_code == 201:
#             flash("Cadastro realizado com sucesso! Faça seu login.", "success")
#             return redirect(url_for('portal_aluno_login'))
#         else:
#             error = response.json().get('detail') if response else 'Tente novamente.'
#             flash(f"Erro no cadastro: {error}", "error")

#     return render_template("portal_aluno/register.html")


# @app.route("/portal/dashboard")
# @login_required
# def portal_aluno_dashboard():
#     if session.get('user_info', {}).get('role') != 'aluno':
#         flash("Acesso não autorizado.", "error")
#         return redirect(url_for('portal_aluno_login'))

#     response = api_request("/portal/me")
#     if response and response.status_code == 200:
#         aluno = response.json()
#         return render_template("portal_aluno/dashboard.html", aluno=aluno)
#     else:
#         flash("Não foi possível carregar seus dados. Por favor, faça o login novamente.", "error")
#         return redirect(url_for('portal_aluno_login'))


# @app.route("/portal/editar", methods=["GET", "POST"])
# @login_required
# def portal_aluno_edit():
#     if session.get('user_info', {}).get('role') != 'aluno':
#         return redirect(url_for('portal_aluno_login'))

#     if request.method == "POST":
#         data = {
#             "nome": request.form.get("nome"),
#             "telefone": request.form.get("telefone"),
#             "data_nascimento": request.form.get("data_nascimento")
#         }
#         update_data = {k: v for k, v in data.items() if v}

#         response = api_request("/portal/me", method="PUT", json=update_data)
#         if response and response.status_code == 200:
#             flash("Perfil atualizado com sucesso!", "success")
#             return redirect(url_for('portal_aluno_dashboard'))
#         else:
#             flash("Erro ao atualizar o perfil.", "error")
    
#     response = api_request("/portal/me")
#     if response and response.status_code == 200:
#         aluno = response.json()
#         return render_template("portal_aluno/edit_profile.html", aluno=aluno) 
    
#     return redirect(url_for('portal_aluno_dashboard'))


# if __name__ == '__main__':
#     print("Iniciando aplicação Flask de depuração...")
#     app.run(debug=False, host='0.0.0.0', port=5700)
    
    