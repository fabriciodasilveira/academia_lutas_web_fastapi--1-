#!/usr/bin/env python3.11
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "<h1>Flask Funcionando!</h1>"

@app.route('/test')
def test():
    return "<h1>Teste OK</h1>"

if __name__ == '__main__':
    print("Iniciando Flask mínimo...")
    app.run(debug=False, host='0.0.0.0', port=5000)

