from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import requests
import os
import logging

app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-in-production'

API_BASE_URL = 'http://localhost:8500'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def api_request(endpoint, method='GET', data=None, files=None):
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
    return render_template('index.html')

@app.route('/alunos')
def alunos_list():
    response = api_request('/alunos')
    alunos = []
    if response and response.status_code == 200:
        alunos = response.json()
    return render_template('alunos/list.html', alunos=alunos)

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
            app.logger.info(f"Professor salvo: {data.get('nome', 'N/A')}")
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
            app.logger.error(f"Erro ao salvar professor: {response.text if response else 'Sem resposta'}")
    except Exception as e:
        flash("Erro interno ao salvar professor.", "error")
        app.logger.error(f"Erro interno ao salvar professor: {e}")
    return redirect(url_for("professores_list"))

@app.route("/professores/<int:id>/deletar", methods=["POST"])
def professores_deletar(id):
    response = api_request(f"/professores/{id}", method="DELETE")
    if response and response.status_code == 204:
        flash("Professor excluído com sucesso!", "success")
        app.logger.info(f"Professor {id} excluído")
    else:
        flash("Erro ao excluir professor.", "error")
        app.logger.error(f"Erro ao excluir professor {id}")
    return redirect(url_for("professores_list"))

@app.route("/turmas")
def turmas_list():
    response = api_request("/turmas")
    turmas = []
    if response and response.status_code == 200:
        turmas = response.json()
    return render_template("turmas/list.html", turmas=turmas)

@app.route("/eventos")
def eventos_list():
    response = api_request("/eventos")
    eventos = []
    if response and response.status_code == 200:
        eventos = response.json()
    return render_template("eventos/list.html", eventos=eventos)

@app.route("/financeiro")
def financeiro_dashboard():
    return render_template("financeiro/dashboard.html")

if __name__ == '__main__':
    print("Iniciando aplicação Flask de depuração...")
    app.run(debug=True, host='0.0.0.0', port=5500)


