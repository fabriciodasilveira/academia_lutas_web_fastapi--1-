#!/usr/bin/env python3.11
from flask import Flask
import requests

app = Flask(__name__)

@app.route('/')
def hello():
    return "<h1>Flask Funcionando!</h1><a href='/test'>Testar API</a>"

@app.route('/test')
def test_api():
    try:
        response = requests.get('http://localhost:8000/api/v1/alunos', timeout=5)
        return f"<h1>API Test</h1><p>Status: {response.status_code}</p><p>Data: {response.text[:200]}...</p>"
    except Exception as e:
        return f"<h1>API Test</h1><p>Erro: {e}</p>"

if __name__ == '__main__':
    print("Iniciando Flask mínimo...")
    app.run(debug=True, host='0.0.0.0', port=5000)

