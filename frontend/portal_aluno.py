# frontend/portal_aluno.py

from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from functools import wraps
from utils import api_request

# Cria um "Blueprint", que é como uma mini-aplicação para o portal
portal_bp = Blueprint('portal', __name__, url_prefix='/portal', template_folder='templates/portal')

# Protetor de rotas específico para o aluno
def aluno_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verifica se o token é do tipo 'aluno'
        if 'access_token' not in session or session.get('user_info', {}).get('type') != 'aluno':
            return redirect(url_for('portal.login'))
        return f(*args, **kwargs)
    return decorated_function

@portal_bp.route('/')
@aluno_login_required
def dashboard():
    """Página inicial do portal do aluno."""
    return render_template('dashboard.html')

@portal_bp.route('/login')
def login():
    """Tela de login exclusiva para alunos."""
    return render_template('login.html')

@portal_bp.route("/login/callback")
def login_callback():
    """Recebe o token da API após o login com Google e finaliza a sessão."""
    token = request.args.get('token')
    if not token:
        flash("Falha na autenticação via Google.", "error")
        return redirect(url_for('portal.login'))
        
    # Usa o token para buscar os dados do aluno na API
    user_info_resp = api_request("/auth/me/aluno", headers={"Authorization": f"Bearer {token}"})
    
    if user_info_resp and user_info_resp.status_code == 200:
        aluno_info = user_info_resp.json()
        session['access_token'] = token
        # Armazena as informações do aluno e o tipo de token
        session['user_info'] = {
            "id": aluno_info.get('id'),
            "nome": aluno_info.get('nome'),
            "email": aluno_info.get('email'),
            "type": "aluno" # Identifica a sessão como de um aluno
        }
        return redirect(url_for('portal.dashboard'))
    else:
        flash("Não foi possível obter os dados do aluno após o login.", "error")
        return redirect(url_for('portal.login'))

@portal_bp.route('/logout')
def logout():
    session.clear()
    flash("Você saiu do portal.", "success")
    return redirect(url_for('portal.login'))