from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import requests
import os
import logging
from datetime import datetime, date, timedelta

app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-in-production'

API_BASE_URL = 'http://localhost:8000'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def api_request(endpoint, method='GET', data=None, files=None, json=None):
    url = f"{API_BASE_URL}/api/v1{endpoint}"
    try:
        if method == 'GET':
            response = requests.get(url, timeout=10)
        elif method == 'POST':
            response = requests.post(url, data=data, files=files, json=json, timeout=10)
        elif method == 'PUT':
            if files:
                response = requests.put(url, data=data, files=files, json=json, timeout=10)
            else:
                response = requests.put(url, data=data, json=json, timeout=10)
        elif method == 'DELETE':
            response = requests.delete(url, timeout=10)
        app.logger.info(f"API Request: {method} {url} - Status: {response.status_code}")
        return response
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Erro na requisição {method} {url}: {e}")
        return None


@app.route('/')
def index():
    stats = {
        'total_alunos': 0,
        'total_professores': 0,
        'total_turmas': 0,
        'total_eventos': 0
    }
    
    try:
        endpoints = [
            ('total_alunos', '/alunos'),
            ('total_professores', '/professores'), 
            ('total_turmas', '/turmas'),
            ('total_eventos', '/eventos')
        ]
        
        for stat_name, endpoint in endpoints:
            response = api_request(f"{endpoint}?limit=10000")
            if response and response.status_code == 200:
                stats[stat_name] = len(response.json())
                
    except Exception as e:
        app.logger.error(f"Erro ao buscar estatísticas: {e}")
    
    return render_template('index.html', stats=stats)

@app.route('/alunos')
def alunos_list():
    response = api_request('/alunos')
    alunos = []
    if response and response.status_code == 200:
        alunos = response.json()
    return render_template('alunos/list.html', alunos=alunos)

# === ROTAS PARA ALUNOS ===
@app.route('/alunos/<int:id>')
def alunos_view(id):
    response = api_request(f'/alunos/{id}')
    aluno = None
    if response and response.status_code == 200:
        aluno = response.json()
    return render_template('alunos/view.html', aluno=aluno)

@app.route('/alunos/novo')
def alunos_novo():
    return render_template('alunos/form.html', aluno=None)

@app.route('/alunos/<int:id>/editar')
def alunos_editar(id):
    response = api_request(f'/alunos/{id}')
    aluno = None
    if response and response.status_code == 200:
        aluno = response.json()
    else:
        flash("Aluno não encontrado.", "error")
        return redirect(url_for("alunos_list"))
    return render_template('alunos/form.html', aluno=aluno)

@app.route("/alunos/salvar", methods=["POST"])
def alunos_salvar():
    try:
        data = {
            "nome": request.form.get("nome"),
            "email": request.form.get("email"),
            "cpf": request.form.get("cpf"),
            "telefone": request.form.get("telefone"),
            "data_nascimento": request.form.get("data_nascimento"),
            "endereco": request.form.get("endereco"),
            "observacoes": request.form.get("observacoes")
        }
        data = {k: v for k, v in data.items() if v}
        
        files = {}
        if "foto_perfil" in request.files and request.files["foto_perfil"].filename != "":
            foto = request.files["foto_perfil"]
            files["foto"] = (foto.filename, foto.stream, foto.content_type)
        
        aluno_id = request.form.get("id")
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
        else:
            error_msg = "Erro ao salvar aluno."
            if response:
                try:
                    error_detail = response.json().get("detail", "")
                    if error_detail:
                        error_msg += f" {error_detail}"
                except:
                    pass
            flash(error_msg, "error")
            
    except Exception as e:
        flash("Erro interno ao salvar aluno.", "error")
        app.logger.error(f"Erro ao salvar aluno: {e}")
        
    return redirect(url_for("alunos_list"))

@app.route("/alunos/<int:id>/deletar", methods=["POST"])
def alunos_deletar(id):
    response = api_request(f"/alunos/{id}", method="DELETE")
    if response and response.status_code == 204:
        flash("Aluno excluído com sucesso!", "success")
        app.logger.info(f"Aluno {id} excluído")
    else:
        flash("Erro ao excluir aluno.", "error")
        app.logger.error(f"Erro ao excluir aluno {id}: {response.text if response else 'Sem resposta'}")
    return redirect(url_for("alunos_list"))


# ... (código existente das rotas de alunos) ...
    return redirect(url_for("alunos_view", id=aluno_id))

# === ROTAS PARA EVENTOS ===
# ... (resto do arquivo) ...

# === ROTAS PARA EVENTOS ===
@app.route('/eventos/novo')
def eventos_novo():
    return render_template('eventos/form.html', evento=None)

@app.route("/eventos")
def eventos_list():
    response = api_request("/eventos")
    eventos = []
    if response and response.status_code == 200:
        eventos = response.json()
    return render_template("eventos/list.html", eventos=eventos)


# === ROTAS PARA PROFESSORES ===
@app.route('/professores')
def professores_list():
    response = api_request('/professores')
    professores = []
    if response and response.status_code == 200:
        professores = response.json()
    return render_template('professores/list.html', professores=professores)

@app.route("/professores/novo")
def professores_novo():
    return render_template("professores/form.html", professor=None)

@app.route("/professores/<int:id>")
def professores_view(id):
    response = api_request(f"/professores/{id}")
    professor = None
    if response and response.status_code == 200:
        professor = response.json()
    return render_template("professores/view.html", professor=professor)

@app.route("/professores/<int:id>/editar")
def professores_editar(id):
    response = api_request(f"/professores/{id}")
    professor = None
    if response and response.status_code == 200:
        professor = response.json()
    else:
        flash("Professor não encontrado.", "error")
        return redirect(url_for("professores_list"))
    return render_template("professores/form.html", professor=professor)

@app.route("/professores/salvar", methods=["POST"])
def professores_salvar():
    try:
        data = {
            "nome": request.form.get("nome"),
            "email": request.form.get("email"),
            "cpf": request.form.get("cpf"),
            "telefone": request.form.get("telefone"),
            "data_nascimento": request.form.get("data_nascimento"),
            "especialidade": request.form.get("especialidade"),
            "data_contratacao": request.form.get("data_contratacao"),
            "salario": request.form.get("salario"),
            "observacoes": request.form.get("observacoes")
        }
        data = {k: v for k, v in data.items() if v}
        
        files = {}
        if "foto_perfil" in request.files and request.files["foto_perfil"].filename != "":
            foto = request.files["foto_perfil"]
            files["foto"] = (foto.filename, foto.stream, foto.content_type)
        
        professor_id = request.form.get("id")
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
        else:
            error_msg = "Erro ao salvar professor."
            if response:
                try:
                    error_detail = response.json().get("detail", "")
                    if error_detail:
                        error_msg += f" {error_detail}"
                except:
                    pass
            flash(error_msg, "error")
    except Exception as e:
        flash("Erro interno ao salvar professor.", "error")
        app.logger.error(f"Erro interno ao salvar professor: {e}")
        
    return redirect(url_for("professores_list"))

@app.route("/professores/<int:id>/deletar", methods=["POST"])
def professores_deletar(id):
    response = api_request(f"/professores/{id}", method="DELETE")
    if response and response.status_code == 204:
        flash("Professor excluído com sucesso!", "success")
    else:
        flash("Erro ao excluir professor.", "error")
    return redirect(url_for("professores_list"))


# === ROTAS PARA TURMAS ===
@app.route("/turmas")
def turmas_list():
    response = api_request("/turmas")
    turmas = []
    if response and response.status_code == 200:
        turmas = response.json()
    return render_template("turmas/list.html", turmas=turmas)

@app.route("/turmas/novo")
def turmas_novo():
    professores_response = api_request("/professores")
    professores = professores_response.json() if professores_response and professores_response.status_code == 200 else []
    return render_template("turmas/form.html", turma=None, professores=professores)

@app.route("/turmas/<int:id>")
def turmas_view(id):
    turma_response = api_request(f"/turmas/{id}")
    turma = None
    if turma_response and turma_response.status_code == 200:
        turma = turma_response.json()
    
    return render_template("turmas/view.html", turma=turma)

@app.route("/turmas/<int:id>/editar")
def turmas_editar(id):
    turma_response = api_request(f"/turmas/{id}")
    turma = None
    if turma_response and turma_response.status_code == 200:
        turma = turma_response.json()
    else:
        flash("Turma não encontrada.", "error")
        return redirect(url_for("turmas_list"))
        
    professores_response = api_request("/professores")
    professores = professores_response.json() if professores_response and professores_response.status_code == 200 else []

    return render_template("turmas/form.html", turma=turma, professores=professores)

@app.route("/turmas/salvar", methods=["POST"])
def turmas_salvar():
    try:
        turma_data = {
            "nome": request.form.get("nome"),
            "modalidade": request.form.get("modalidade"),
            "horario": request.form.get("horario"),
            "dias_semana": "Segunda, Quarta, Sexta",
            "professor_id": int(request.form.get("professor_id")) if request.form.get("professor_id") else None,
            "nivel": request.form.get("nivel"),
            "capacidade_maxima": int(request.form.get("capacidade_maxima")) if request.form.get("capacidade_maxima") else None,
            "valor_mensalidade": float(request.form.get("valor_mensalidade").replace(',', '.')) if request.form.get("valor_mensalidade") else None,
            "idade_minima": int(request.form.get("idade_minima")) if request.form.get("idade_minima") else None,
            "ativa": request.form.get("ativa") == "1",
            "descricao": request.form.get("descricao"),
            "observacoes": request.form.get("observacoes")
        }
        
        final_data = {
            k: v for k, v in turma_data.items()
            if v is not None
        }
        
        turma_id = request.form.get("id")
        
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
        else:
            error_msg = "Erro ao salvar turma."
            if response:
                try:
                    error_detail = response.json().get("detail", "")
                    if error_detail:
                        error_msg += f" Detalhe: {error_detail}"
                except:
                    pass
            flash(error_msg, "error")
            
    except Exception as e:
        flash(f"Erro interno ao salvar turma. {e}", "error")
        app.logger.error(f"Erro ao salvar turma: {e}")
        
    return redirect(url_for("turmas_list"))

@app.route("/turmas/<int:id>/deletar", methods=["POST"])
def turmas_deletar(id):
    response = api_request(f"/turmas/{id}", method="DELETE")
    if response and response.status_code == 204:
        flash("Turma excluída com sucesso!", "success")
    else:
        error_msg = "Erro ao excluir turma."
        if response:
            try:
                error_detail = response.json().get("detail", "")
                if error_detail:
                    error_msg += f" Detalhe: {error_detail}"
            except:
                pass
        flash(error_msg, "error")
        app.logger.error(f"Erro ao excluir turma {id}: {response.text if response else 'Sem resposta'}")
    return redirect(url_for("turmas_list"))


# === ROTAS PARA MATRICULAS ===
@app.route("/matriculas")
def matriculas_list():
    response = api_request("/matriculas")
    matriculas = []
    if response and response.status_code == 200:
        matriculas = response.json()
    return render_template("matriculas/list.html", matriculas=matriculas)

@app.route("/matriculas/novo")
def matriculas_novo():
    alunos_response = api_request("/alunos")
    alunos = alunos_response.json() if alunos_response and alunos_response.status_code == 200 else []
    
    turmas_response = api_request("/turmas")
    turmas = turmas_response.json() if turmas_response and turmas_response.status_code == 200 else []
    
    # LINHA CORRIGIDA/ADICIONADA ABAIXO
    planos_response = api_request("/planos")
    planos = planos_response.json() if planos_response and planos_response.status_code == 200 else []
    
    return render_template("matriculas/form.html", alunos=alunos, turmas=turmas, planos=planos, matricula=None)

@app.route("/matriculas/salvar", methods=["POST"])
def matriculas_salvar():
    try:
        # Pega os IDs do formulário
        aluno_id = request.form.get("aluno_id")
        turma_id = request.form.get("turma_id")
        plano_id = request.form.get("plano_id")

        # Validação para garantir que todos os campos foram selecionados
        if not all([aluno_id, turma_id, plano_id]):
            flash("Erro: Todos os campos (Aluno, Turma e Plano) são obrigatórios.", "error")
            return redirect(url_for("matriculas_novo"))

        matricula_data = {
            "aluno_id": int(aluno_id),
            "turma_id": int(turma_id),
            "plano_id": int(plano_id)
        }
        
        response = api_request("/matriculas", method="POST", json=matricula_data)
        
        if response and response.status_code == 201:
            flash("Matrícula realizada com sucesso!", "success")
        else:
            error_msg = "Erro ao realizar matrícula."
            if response:
                try:
                    error_detail = response.json().get("detail", "")
                    if isinstance(error_detail, list):
                         # Lida com erros de validação do Pydantic
                        error_msg += " Verifique os dados: " + ", ".join([e.get('msg', '') for e in error_detail])
                    elif error_detail:
                        error_msg += f" Detalhe: {error_detail}"
                except:
                    error_msg += f" (Status: {response.status_code})"
            flash(error_msg, "error")
            # Em caso de erro na API, redireciona de volta para o formulário
            return redirect(url_for("matriculas_novo"))
            
    except ValueError:
        flash("Erro: Valores inválidos fornecidos para aluno, turma ou plano.", "error")
        return redirect(url_for("matriculas_novo"))
    except Exception as e:
        flash(f"Erro interno ao salvar a matrícula: {e}", "error")
        return redirect(url_for("matriculas_novo"))
        
    return redirect(url_for("matriculas_list"))

@app.route("/matriculas/editar/<int:id>", methods=["GET"])
def matriculas_editar(id):
    matricula_response = api_request(f"/matriculas/{id}")
    alunos_response = api_request("/alunos")
    turmas_response = api_request("/turmas")
    
    # LINHA CORRIGIDA/ADICIONADA ABAIXO
    planos_response = api_request("/planos")
    planos = planos_response.json() if planos_response and planos_response.status_code == 200 else []
    
    if not matricula_response or matricula_response.status_code != 200:
        flash("Matrícula não encontrada!", "error")
        return redirect(url_for("matriculas_list"))
    
    matricula = matricula_response.json()
    alunos = alunos_response.json() if alunos_response and alunos_response.status_code == 200 else []
    turmas = turmas_response.json() if turmas_response and turmas_response.status_code == 200 else []
    
    return render_template("matriculas/form.html", matricula=matricula, alunos=alunos, turmas=turmas, planos=planos)

@app.route("/matriculas/salvar_edicao", methods=["POST"])
def matriculas_salvar_edicao():
    try:
        matricula_id = request.form.get("id")
        matricula_data = {
            "aluno_id": int(request.form.get("aluno_id")),
            "turma_id": int(request.form.get("turma_id")),
            "ativa": True if request.form.get("ativa") == 'on' else False
        }
        
        response = api_request(f"/matriculas/{matricula_id}", method="PUT", json=matricula_data)
        
        if response and response.status_code == 200:
            flash("Matrícula atualizada com sucesso!", "success")
        else:
            flash("Erro ao atualizar matrícula.", "error")
    except Exception as e:
        flash(f"Erro interno ao salvar a edição. {e}", "error")
        
    return redirect(url_for("matriculas_list"))

@app.route("/matriculas/status/<int:id>", methods=["POST"])
def matriculas_status(id):
    try:
        matricula_response = api_request(f"/matriculas/{id}")
        if not matricula_response or matricula_response.status_code != 200:
            flash("Matrícula não encontrada.", "error")
            return redirect(url_for("matriculas_list"))
        
        matricula = matricula_response.json()
        new_status = not matricula.get("ativa", True)
        
        response = api_request(f"/matriculas/{id}", method="PUT", json={"ativa": new_status})
        
        if response and response.status_code == 200:
            flash(f"Matrícula {'destrancada' if new_status else 'trancada'} com sucesso!", "success")
        else:
            flash("Erro ao atualizar o status da matrícula.", "error")
    except Exception as e:
        flash(f"Erro interno ao trancar/destrancar a matrícula. {e}", "error")
        
    return redirect(url_for("matriculas_list"))


@app.route("/matriculas/deletar/<int:id>", methods=["POST"])
def matriculas_deletar(id):
    response = api_request(f"/matriculas/{id}", method="DELETE")
    if response and response.status_code == 204:
        flash("Matrícula excluída com sucesso!", "success")
    else:
        flash("Erro ao excluir matrícula.", "error")
    return redirect(url_for("matriculas_list"))


# === ROTAS PARA FINANCEIRO ===
# ... (outros imports)

@app.route("/financeiro/dashboard")
def financeiro_dashboard():
    hoje = date.today()
    primeiro_dia_mes = hoje.replace(day=1)

    balanco_response = api_request(f"/financeiro/balanco?data_inicio={primeiro_dia_mes.strftime('%Y-%m-%d')}&data_fim={hoje.strftime('%Y-%m-%d')}")
    stats = {}
    if balanco_response and balanco_response.status_code == 200:
        stats = balanco_response.json()
    
    transacoes_response = api_request("/financeiro/transacoes?limit=5")
    transacoes = []
    if transacoes_response and transacoes_response.status_code == 200:
        transacoes_data = transacoes_response.json()
        for transacao in transacoes_data:
            if transacao.get('data'):
                transacao['data'] = datetime.fromisoformat(transacao['data'])
            transacoes.append(transacao)
    
    # Buscamos as categorias da API
    categorias_response = api_request("/categorias")
    categorias = categorias_response.json() if categorias_response and categorias_response.status_code == 200 else []
    
    # Busca por mensalidades pendentes
    mensalidades_pendentes_response = api_request("/mensalidades?status=pendente")
    mensalidades_pendentes = []
    if mensalidades_pendentes_response and mensalidades_pendentes_response.status_code == 200:
        mensalidades_pendentes = mensalidades_pendentes_response.json()

    return render_template(
        "financeiro/dashboard.html", 
        stats=stats, 
        transacoes=transacoes, 
        categorias=categorias,
        mensalidades_pendentes=mensalidades_pendentes
    )

@app.route("/financeiro/transacoes")
def financeiro_transacoes():
    tipo_filtro = request.args.get('tipo')
    categoria_filtro = request.args.get('categoria')
    busca_filtro = request.args.get('busca')
    data_inicio_filtro = request.args.get('data_inicio')
    data_fim_filtro = request.args.get('data_fim')

    endpoint_transacoes = "/financeiro/transacoes"
    query_params_transacoes = []
    if tipo_filtro: query_params_transacoes.append(f"tipo={tipo_filtro}")
    if categoria_filtro: query_params_transacoes.append(f"categoria={categoria_filtro}")
    if busca_filtro: query_params_transacoes.append(f"busca={busca_filtro}")
    if data_inicio_filtro: query_params_transacoes.append(f"data_inicio={data_inicio_filtro}")
    if data_fim_filtro: query_params_transacoes.append(f"data_fim={data_fim_filtro}")
    
    if query_params_transacoes:
        endpoint_transacoes += "?" + "&".join(query_params_transacoes)
        
    response_transacoes = api_request(endpoint_transacoes)
    transacoes = []
    if response_transacoes and response_transacoes.status_code == 200:
        transacoes_data = response_transacoes.json()
        for transacao in transacoes_data:
            if transacao.get('data'):
                transacao['data'] = datetime.fromisoformat(transacao['data'])
            transacoes.append(transacao)

    endpoint_balanco = "/financeiro/balanco"
    query_params_balanco = []
    if data_inicio_filtro: query_params_balanco.append(f"data_inicio={data_inicio_filtro}")
    if data_fim_filtro: query_params_balanco.append(f"data_fim={data_fim_filtro}")

    if query_params_balanco:
        endpoint_balanco += "?" + "&".join(query_params_balanco)
    
    balanco_response = api_request(endpoint_balanco)
    stats = {}
    if balanco_response and balanco_response.status_code == 200:
        stats = balanco_response.json()
    
    # Buscamos as categorias da API
    categorias_response = api_request("/categorias")
    categorias = categorias_response.json() if categorias_response and categorias_response.status_code == 200 else []
    
    return render_template("financeiro/transacoes.html", transacoes=transacoes, stats=stats, categorias=categorias)


@app.route("/financeiro/salvar_transacao", methods=["POST"])
def financeiro_salvar_transacao():
    try:
        transacao_data = {
            "id": request.form.get("id"),
            "tipo": request.form.get("tipo"),
            "categoria": request.form.get("categoria"),
            "descricao": request.form.get("descricao"),
            "valor": float(request.form.get("valor").replace(',', '.')),
            "status": request.form.get("status"),
            "observacoes": request.form.get("observacoes"),
            "data": request.form.get("data")
        }
        
        transacao_data = {k: v for k, v in transacao_data.items() if v}

        transacao_id = request.form.get("id")
        if transacao_id:
            response = api_request(f"/financeiro/transacoes/{transacao_id}", method="PUT", json=transacao_data)
            success_message = "Transação atualizada com sucesso!"
        else:
            response = api_request("/financeiro/transacoes", method="POST", json=transacao_data)
            success_message = "Transação salva com sucesso!"

        if response and response.status_code in [200, 201]:
            flash(success_message, "success")
        else:
            error_msg = "Erro ao salvar transação."
            if response:
                try:
                    error_detail = response.json().get("detail", "")
                    if error_detail:
                        error_msg += f" Detalhe: {error_detail}"
                except:
                    pass
            flash(error_msg, "error")

    except Exception as e:
        flash(f"Erro interno ao salvar transação: {e}", "error")
    
    return redirect(url_for("financeiro_transacoes"))


@app.route("/financeiro/deletar_transacao/<int:id>", methods=["POST"])
def financeiro_deletar_transacao(id):
    response = api_request(f"/financeiro/transacoes/{id}", method="DELETE")
    if response and response.status_code == 204:
        flash("Transação excluída com sucesso!", "success")
    else:
        flash("Erro ao excluir transação.", "error")
    return redirect(url_for("financeiro_transacoes"))
    
# === ROTAS PARA PRODUTOS ===
@app.route("/produtos")
def produtos_list():
    response = api_request("/produtos")
    produtos = []
    if response and response.status_code == 200:
        produtos = response.json()
    return render_template("produtos/list.html", produtos=produtos)

@app.route("/produtos/novo")
def produtos_novo():
    return render_template("produtos/form.html", produto=None)

@app.route("/produtos/<int:id>/editar")
def produtos_editar(id):
    response = api_request(f"/produtos/{id}")
    produto = None
    if response and response.status_code == 200:
        produto = response.json()
    else:
        flash("Produto não encontrado.", "error")
        return redirect(url_for("produtos_list"))
    return render_template("produtos/form.html", produto=produto)
    
@app.route("/produtos/salvar", methods=["POST"])
def produtos_salvar():
    try:
        produto_data = {
            "codigo": request.form.get("codigo"),
            "nome": request.form.get("nome"),
            "descricao": request.form.get("descricao"),
            "preco_custo": float(request.form.get("preco_custo").replace(',', '.')),
            "preco_venda": float(request.form.get("preco_venda").replace(',', '.')),
            "quantidade_estoque": int(request.form.get("quantidade_estoque"))
        }

        produto_data = {k: v for k, v in produto_data.items() if v}
        
        produto_id = request.form.get("id")
        if produto_id:
            response = api_request(f"/produtos/{produto_id}", method="PUT", json=produto_data)
            success_message = "Produto atualizado com sucesso!"
        else:
            response = api_request("/produtos", method="POST", json=produto_data)
            success_message = "Produto cadastrado com sucesso!"

        if response and response.status_code in [200, 201]:
            flash(success_message, "success")
        else:
            error_msg = "Erro ao salvar produto."
            if response:
                try:
                    error_detail = response.json().get("detail", "")
                    if error_detail:
                        error_msg += f" Detalhe: {error_detail}"
                except:
                    pass
            flash(error_msg, "error")

    except Exception as e:
        flash(f"Erro interno ao salvar produto: {e}", "error")
    
    return redirect(url_for("produtos_list"))

@app.route("/produtos/deletar/<int:id>", methods=["POST"])
def produtos_deletar(id):
    response = api_request(f"/produtos/{id}", method="DELETE")
    if response and response.status_code == 204:
        flash("Produto excluído com sucesso!", "success")
    else:
        flash("Erro ao excluir produto.", "error")
    return redirect(url_for("produtos_list"))
    
# === ROTAS PARA PLANOS ===
@app.route("/planos")
def planos_list():
    response = api_request("/planos")
    planos = []
    if response and response.status_code == 200:
        planos = response.json()
    return render_template("planos/list.html", planos=planos)

@app.route("/planos/novo")
def planos_novo():
    return render_template("planos/form.html", plano=None)

@app.route("/planos/<int:id>/editar")
def planos_editar(id):
    response = api_request(f"/planos/{id}")
    plano = None
    if response and response.status_code == 200:
        plano = response.json()
    else:
        flash("Plano não encontrado.", "error")
        return redirect(url_for("planos_list"))
    return render_template("planos/form.html", plano=plano)

@app.route("/planos/salvar", methods=["POST"])
def planos_salvar():
    try:
        plano_data = {
            "nome": request.form.get("nome"),
            "descricao": request.form.get("descricao"),
            "valor": float(request.form.get("valor").replace(',', '.')),
            "periodo_meses": int(request.form.get("periodo_meses"))
        }

        plano_data = {k: v for k, v in plano_data.items() if v}
        
        plano_id = request.form.get("id")
        if plano_id:
            response = api_request(f"/planos/{plano_id}", method="PUT", json=plano_data)
            success_message = "Plano atualizado com sucesso!"
        else:
            response = api_request("/planos", method="POST", json=plano_data)
            success_message = "Plano cadastrado com sucesso!"

        if response and response.status_code in [200, 201]:
            flash(success_message, "success")
        else:
            error_msg = "Erro ao salvar plano."
            if response:
                try:
                    error_detail = response.json().get("detail", "")
                    if error_detail:
                        error_msg += f" Detalhe: {error_detail}"
                except:
                    pass
            flash(error_msg, "error")

    except Exception as e:
        flash(f"Erro interno ao salvar plano: {e}", "error")
    
    return redirect(url_for("planos_list"))

@app.route("/planos/deletar/<int:id>", methods=["POST"])
def planos_deletar(id):
    response = api_request(f"/planos/{id}", method="DELETE")
    if response and response.status_code == 204:
        flash("Plano excluído com sucesso!", "success")
    else:
        flash("Erro ao excluir plano.", "error")
    return redirect(url_for("planos_list"))
    
# === ROTAS PARA MENSALIDADES ===
@app.route("/mensalidades")
def mensalidades_list():
    response = api_request("/mensalidades")
    mensalidades = []
    if response and response.status_code == 200:
        mensalidades = response.json()
    return render_template("mensalidades/list.html", mensalidades=mensalidades)

@app.route("/mensalidades/novo")
def mensalidades_novo():
    alunos_response = api_request("/alunos")
    alunos = alunos_response.json() if alunos_response and alunos_response.status_code == 200 else []
    planos_response = api_request("/planos")
    planos = planos_response.json() if planos_response and planos_response.status_code == 200 else []
    
    return render_template("mensalidades/form.html", alunos=alunos, planos=planos)

@app.route("/mensalidades/salvar", methods=["POST"])
def mensalidades_salvar():
    try:
        mensalidade_data = {
            "aluno_id": int(request.form.get("aluno_id")),
            "plano_id": int(request.form.get("plano_id")),
            "valor": float(request.form.get("valor").replace(',', '.')),
            "data_vencimento": request.form.get("data_vencimento")
        }
        
        response = api_request("/mensalidades", method="POST", json=mensalidade_data)
        
        if response and response.status_code == 201:
            flash("Mensalidade cadastrada com sucesso!", "success")
        else:
            error_msg = "Erro ao cadastrar mensalidade."
            if response:
                try:
                    error_detail = response.json().get("detail", "")
                    if error_detail:
                        error_msg += f" Detalhe: {error_detail}"
                except:
                    pass
            flash(error_msg, "error")

    except Exception as e:
        flash(f"Erro interno ao salvar mensalidade: {e}", "error")
    
    return redirect(url_for("mensalidades_list"))

@app.route("/mensalidades/pagar/<int:id>", methods=["POST"])
def mensalidades_pagar(id):
    response = api_request(f"/mensalidades/processar_pagamento/{id}", method="POST")
    if response and response.status_code == 200:
        flash("Pagamento processado com sucesso!", "success")
    else:
        flash("Erro ao processar pagamento.", "error")
    return redirect(url_for("mensalidades_list"))

@app.route("/mensalidades/deletar/<int:id>", methods=["POST"])
def mensalidades_deletar(id):
    response = api_request(f"/mensalidades/{id}", method="DELETE")
    if response and response.status_code == 204:
        flash("Mensalidade excluída com sucesso!", "success")
    else:
        flash("Erro ao excluir mensalidade.", "error")
    return redirect(url_for("mensalidades_list"))


if __name__ == '__main__':
    print("Iniciando aplicação Flask de depuração...")
    app.run(debug=False, host='0.0.0.0', port=5700)

@app.route("/mensalidades")
def mensalidades_list():
    response = api_request("/mensalidades")
    mensalidades = []
    if response and response.status_code == 200:
        mensalidades = response.json()
    return render_template("mensalidades/list.html", mensalidades=mensalidades)

@app.route("/mensalidades/pagar/<int:id>", methods=["POST"])
def mensalidades_pagar(id):
    response = api_request(f"/mensalidades/processar_pagamento/{id}", method="POST")
    if response and response.status_code == 200:
        flash("Pagamento processado com sucesso!", "success")
    else:
        flash("Erro ao processar pagamento.", "error")
    return redirect(url_for("mensalidades_list"))


# Em frontend/app.py

# ... (resto do seu código) ...

# === ROTA PARA GERAR LINK DE PAGAMENTO ===
@app.route("/mensalidades/pagar-online/<int:id>", methods=["POST"])
def mensalidades_pagar_online(id):
    """Gera o link de pagamento do Mercado Pago e retorna como JSON."""
    # Chama o endpoint da API que cria a preferência de pagamento
    response = api_request(f"/pagamentos/gerar/{id}", method="POST")
    
    if response and response.status_code == 200:
        return jsonify(response.json())
    else:
        error_message = "Falha ao gerar link de pagamento."
        if response:
            try:
                error_message += f" Detalhe: {response.json().get('detail', '')}"
            except:
                pass
        return jsonify({"error": error_message}), 500
    
    
    # Em frontend/app.py

