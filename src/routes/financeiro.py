"""
Rotas financeiras para o sistema web de gerenciamento da academia.
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from src.models import db, Financeiro, Pagamento, Matricula, Aluno
from src.utils.auth import token_obrigatorio, gerente_ou_admin_obrigatorio
import logging

financeiro_bp = Blueprint('financeiro', __name__)

@financeiro_bp.route('/transacoes', methods=['POST'])
@gerente_ou_admin_obrigatorio
def registrar_transacao():
    """Endpoint para registrar uma nova transação financeira (receita ou despesa)."""
    data = request.get_json()
    
    if not data or not data.get('tipo') or not data.get('categoria') or not data.get('valor'):
        return jsonify({'mensagem': 'Dados incompletos. Tipo, categoria e valor são obrigatórios'}), 400
    
    # Verifica se o tipo é válido
    tipos_validos = ['receita', 'despesa']
    if data.get('tipo') not in tipos_validos:
        return jsonify({'mensagem': 'Tipo inválido. Use: receita ou despesa'}), 400
    
    # Processa data da transação
    data_transacao = datetime.utcnow()
    if data.get('data'):
        try:
            data_transacao = datetime.strptime(data.get('data'), '%Y-%m-%d')
        except ValueError:
            return jsonify({'mensagem': 'Formato de data inválido. Use YYYY-MM-DD'}), 400
    
    # Cria a transação
    nova_transacao = Financeiro(
        tipo=data.get('tipo'),
        categoria=data.get('categoria'),
        valor=data.get('valor'),
        descricao=data.get('descricao'),
        responsavel_id=request.usuario_id,  # ID do usuário autenticado
        data=data_transacao
    )
    
    db.session.add(nova_transacao)
    db.session.commit()
    
    return jsonify({
        'mensagem': 'Transação registrada com sucesso',
        'transacao': nova_transacao.to_dict()
    }), 201

@financeiro_bp.route('/transacoes', methods=['GET'])
@gerente_ou_admin_obrigatorio
def listar_transacoes():
    """Endpoint para listar transações financeiras com filtros opcionais."""
    # Parâmetros de filtro
    tipo = request.args.get('tipo')
    categoria = request.args.get('categoria')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    # Constrói a query base
    query = Financeiro.query
    
    # Aplica filtros se fornecidos
    if tipo:
        query = query.filter(Financeiro.tipo == tipo)
    if categoria:
        query = query.filter(Financeiro.categoria == categoria)
    
    # Filtra por período
    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d')
            query = query.filter(Financeiro.data >= data_inicio_obj)
        except ValueError:
            return jsonify({'mensagem': 'Formato de data_inicio inválido. Use YYYY-MM-DD'}), 400
    
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d')
            query = query.filter(Financeiro.data <= data_fim_obj)
        except ValueError:
            return jsonify({'mensagem': 'Formato de data_fim inválido. Use YYYY-MM-DD'}), 400
    
    # Executa a query
    transacoes = query.order_by(Financeiro.data.desc()).all()
    
    return jsonify({
        'transacoes': [transacao.to_dict() for transacao in transacoes]
    }), 200

@financeiro_bp.route('/transacoes/<int:id>', methods=['GET'])
@gerente_ou_admin_obrigatorio
def obter_transacao(id):
    """Endpoint para obter uma transação financeira específica."""
    transacao = Financeiro.query.get_or_404(id)
    return jsonify({
        'transacao': transacao.to_dict()
    }), 200

@financeiro_bp.route('/transacoes/<int:id>', methods=['PUT'])
@gerente_ou_admin_obrigatorio
def atualizar_transacao(id):
    """Endpoint para atualizar uma transação financeira."""
    transacao = Financeiro.query.get_or_404(id)
    data = request.get_json()
    
    # Atualiza os campos fornecidos
    if data.get('tipo'):
        # Verifica se o tipo é válido
        tipos_validos = ['receita', 'despesa']
        if data.get('tipo') not in tipos_validos:
            return jsonify({'mensagem': 'Tipo inválido. Use: receita ou despesa'}), 400
        transacao.tipo = data.get('tipo')
    
    if data.get('categoria'):
        transacao.categoria = data.get('categoria')
    
    if 'valor' in data:
        transacao.valor = data.get('valor')
    
    if 'descricao' in data:
        transacao.descricao = data.get('descricao')
    
    if data.get('data'):
        try:
            transacao.data = datetime.strptime(data.get('data'), '%Y-%m-%d')
        except ValueError:
            return jsonify({'mensagem': 'Formato de data inválido. Use YYYY-MM-DD'}), 400
    
    db.session.commit()
    
    return jsonify({
        'mensagem': 'Transação atualizada com sucesso',
        'transacao': transacao.to_dict()
    }), 200

@financeiro_bp.route('/transacoes/<int:id>', methods=['DELETE'])
@gerente_ou_admin_obrigatorio
def excluir_transacao(id):
    """Endpoint para excluir uma transação financeira."""
    transacao = Financeiro.query.get_or_404(id)
    
    db.session.delete(transacao)
    db.session.commit()
    
    return jsonify({
        'mensagem': 'Transação excluída com sucesso'
    }), 200

@financeiro_bp.route('/pagamentos', methods=['POST'])
@token_obrigatorio
def registrar_pagamento():
    """Endpoint para registrar um novo pagamento de mensalidade."""
    data = request.get_json()
    
    if not data or not data.get('matricula_id') or not data.get('valor') or not data.get('forma_pagamento'):
        return jsonify({'mensagem': 'Dados incompletos. Matrícula, valor e forma de pagamento são obrigatórios'}), 400
    
    # Verifica se a matrícula existe
    matricula = Matricula.query.get(data.get('matricula_id'))
    if not matricula:
        return jsonify({'mensagem': 'Matrícula não encontrada'}), 404
    
    # Cria o pagamento
    novo_pagamento = Pagamento(
        matricula_id=data.get('matricula_id'),
        valor=data.get('valor'),
        desconto=data.get('desconto', 0),
        forma_pagamento=data.get('forma_pagamento'),
        observacoes=data.get('observacoes'),
        registrado_por=request.usuario_id  # ID do usuário autenticado
    )
    
    db.session.add(novo_pagamento)
    
    # Registra também como receita no financeiro
    aluno = Aluno.query.get(matricula.aluno_id)
    descricao = f"Pagamento de mensalidade - {aluno.nome if aluno else 'Aluno ID: ' + str(matricula.aluno_id)}"
    
    nova_receita = Financeiro(
        tipo='receita',
        categoria='mensalidade',
        valor=data.get('valor'),
        descricao=descricao,
        responsavel_id=request.usuario_id,
        data=datetime.utcnow()
    )
    
    db.session.add(nova_receita)
    db.session.commit()
    
    return jsonify({
        'mensagem': 'Pagamento registrado com sucesso',
        'pagamento': novo_pagamento.to_dict()
    }), 201

@financeiro_bp.route('/pagamentos', methods=['GET'])
@token_obrigatorio
def listar_pagamentos():
    """Endpoint para listar pagamentos com filtros opcionais."""
    # Parâmetros de filtro
    matricula_id = request.args.get('matricula_id', type=int)
    aluno_id = request.args.get('aluno_id', type=int)
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    # Constrói a query base
    query = Pagamento.query
    
    # Aplica filtros se fornecidos
    if matricula_id:
        query = query.filter(Pagamento.matricula_id == matricula_id)
    
    if aluno_id:
        # Busca todas as matrículas do aluno
        matriculas_ids = [m.id for m in Matricula.query.filter_by(aluno_id=aluno_id).all()]
        if matriculas_ids:
            query = query.filter(Pagamento.matricula_id.in_(matriculas_ids))
        else:
            # Se o aluno não tem matrículas, retorna lista vazia
            return jsonify({'pagamentos': []}), 200
    
    # Filtra por período
    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d')
            query = query.filter(Pagamento.data_pagamento >= data_inicio_obj)
        except ValueError:
            return jsonify({'mensagem': 'Formato de data_inicio inválido. Use YYYY-MM-DD'}), 400
    
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d')
            query = query.filter(Pagamento.data_pagamento <= data_fim_obj)
        except ValueError:
            return jsonify({'mensagem': 'Formato de data_fim inválido. Use YYYY-MM-DD'}), 400
    
    # Executa a query
    pagamentos = query.order_by(Pagamento.data_pagamento.desc()).all()
    
    # Prepara resposta com dados relacionados
    resultado = []
    for pagamento in pagamentos:
        matricula = Matricula.query.get(pagamento.matricula_id)
        aluno = Aluno.query.get(matricula.aluno_id) if matricula else None
        
        item = pagamento.to_dict()
        item['aluno_nome'] = aluno.nome if aluno else None
        item['aluno_id'] = aluno.id if aluno else None
        
        resultado.append(item)
    
    return jsonify({
        'pagamentos': resultado
    }), 200

@financeiro_bp.route('/balanco', methods=['GET'])
@gerente_ou_admin_obrigatorio
def obter_balanco():
    """Endpoint para obter o balanço financeiro (receitas - despesas) em um período."""
    # Parâmetros de filtro
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    # Datas padrão: mês atual
    if not data_inicio:
        data_inicio = datetime.utcnow().replace(day=1).strftime('%Y-%m-%d')
    if not data_fim:
        data_fim = datetime.utcnow().strftime('%Y-%m-%d')
    
    try:
        data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d')
        data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d')
    except ValueError:
        return jsonify({'mensagem': 'Formato de data inválido. Use YYYY-MM-DD'}), 400
    
    # Calcula total de receitas
    receitas = db.session.query(db.func.sum(Financeiro.valor)).filter(
        Financeiro.tipo == 'receita',
        Financeiro.data >= data_inicio_obj,
        Financeiro.data <= data_fim_obj
    ).scalar() or 0
    
    # Calcula total de despesas
    despesas = db.session.query(db.func.sum(Financeiro.valor)).filter(
        Financeiro.tipo == 'despesa',
        Financeiro.data >= data_inicio_obj,
        Financeiro.data <= data_fim_obj
    ).scalar() or 0
    
    # Calcula balanço
    balanco = receitas - despesas
    
    # Obtém detalhes por categoria
    categorias_receita = db.session.query(
        Financeiro.categoria, 
        db.func.sum(Financeiro.valor).label('total')
    ).filter(
        Financeiro.tipo == 'receita',
        Financeiro.data >= data_inicio_obj,
        Financeiro.data <= data_fim_obj
    ).group_by(Financeiro.categoria).all()
    
    categorias_despesa = db.session.query(
        Financeiro.categoria, 
        db.func.sum(Financeiro.valor).label('total')
    ).filter(
        Financeiro.tipo == 'despesa',
        Financeiro.data >= data_inicio_obj,
        Financeiro.data <= data_fim_obj
    ).group_by(Financeiro.categoria).all()
    
    return jsonify({
        'periodo': {
            'data_inicio': data_inicio,
            'data_fim': data_fim
        },
        'receitas': receitas,
        'despesas': despesas,
        'balanco': balanco,
        'detalhes': {
            'receitas': {cat[0]: cat[1] for cat in categorias_receita},
            'despesas': {cat[0]: cat[1] for cat in categorias_despesa}
        }
    }), 200
