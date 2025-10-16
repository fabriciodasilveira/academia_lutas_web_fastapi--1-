Sistema de Gestão para Academia de Lutas (FVS-Fight)
Um sistema web completo para gerenciamento de academias de artes marciais, dividido em duas interfaces principais: um painel administrativo robusto e um portal do aluno moderno e responsivo (PWA).

🚀 Sobre o Projeto
Este projeto foi desenvolvido para centralizar e automatizar as operações diárias de uma academia, desde o controle de alunos e turmas até a gestão financeira e de eventos. A solução conta com um backend robusto construído em FastAPI e duas interfaces de frontend distintas para atender às necessidades de administradores e alunos.

Arquitetura do Sistema
O sistema é desacoplado, com um backend que serve uma API RESTful e dois frontends que a consomem.

Snippet de código

graph TD
    subgraph Usuários
        Admin[Administrador/Gerente]
        Aluno[Aluno]
    end

    subgraph Frontends
        PainelGestao[Painel de Gestão (Flask) <br> em academia-gestao.onrender.com]
        PWA[Portal do Aluno (PWA) <br> em academia-api.onrender.com/portal]
    end
    
    subgraph Backend
        API[API RESTful (FastAPI) <br> em academia-api.onrender.com]
    end

    subgraph Banco de Dados
        DB[(PostgreSQL <br> na Neon/Render)]
    end

    subgraph Serviços Externos
        Stripe[Stripe <br> (Gateway de Pagamento)]
        Google[Google Cloud <br> (OAuth 2.0)]
        Cloudflare[Cloudflare R2 <br> (Armazenamento de Fotos)]
    end

    Admin --> PainelGestao
    Aluno --> PWA
    
    PainelGestao --> API
    PWA --> API

    API --> DB
    API --> Stripe
    API --> Google
    API --> Cloudflare
    
✨ Funcionalidades Principais
Painel de Gestão (Admin)
🔑 Autenticação Segura: Sistema de login com diferentes níveis de permissão (administrador, gerente).

📊 Dashboard Principal: Visão geral com estatísticas de alunos, turmas e eventos.

🎓 Gestão de Alunos: CRUD completo de alunos, com busca, paginação, filtros por status (ativos/inativos) e campos condicionais para responsáveis de menores.

🥋 Gestão de Professores: Cadastro e gerenciamento de professores e suas especialidades.

⏰ Gestão de Turmas: Criação de turmas com horários, associação de professores e controle de capacidade.

📅 Gestão de Eventos: Criação de eventos e inscrição manual de alunos.

💳 Gestão de Mensalidades: Visualização de mensalidades e registro de pagamentos manuais.

📈 Financeiro: Dashboard com balanço de receitas e despesas.

Portal do Aluno (PWA)
📱 Progressive Web App (PWA): Pode ser "instalado" na tela inicial do celular com ícone personalizado.

🔐 Login Social e Seguro: Login com email/senha ou via conta Google.

👤 Perfil do Aluno: Visualização e edição dos dados cadastrais, incluindo upload de foto de perfil otimizada.

💳 Carteirinha Digital: Uma carteirinha virtual com foto, dados e número de matrícula.

💰 Central Financeira: Lista unificada de todas as pendências (mensalidades e inscrições em eventos).

💸 Pagamento Online: Integração com a Stripe para pagamento de pendências com Cartão, Pix ou Boleto via Checkout.

🗓️ Inscrição em Eventos: Visualização de eventos disponíveis e inscrição com um clique.

🛠️ Tecnologias Utilizadas
Backend
Python 3.11+

FastAPI: Para a criação da API RESTful de alta performance.

SQLAlchemy: ORM para interação com o banco de dados.

Pydantic: Para validação e serialização de dados.

Pillow: Para processamento e otimização de imagens no servidor.

Boto3: Para integração com o serviço de armazenamento S3 (Cloudflare R2).

Uvicorn: Como servidor ASGI para rodar a API.

Frontend (Painel de Gestão)
Flask: Para renderização das páginas e gerenciamento de sessões.

Jinja2: Como motor de templates.

Bootstrap 5: Para a construção da interface responsiva.

Gunicorn: Como servidor WSGI para produção.

WhiteNoise: Para servir arquivos estáticos em produção.

Frontend (Portal do Aluno - PWA)
Vanilla JavaScript (ES6+): Para toda a lógica de roteamento, chamadas de API e manipulação do DOM.

HTML5 / CSS3: Estrutura e estilo.

Bootstrap 5: Para componentes de UI.

Service Worker: Para funcionalidades offline e de PWA.

Banco de Dados & Infraestrutura
PostgreSQL: Banco de dados relacional para produção (hospedado na Neon ou Render).

SQLite: Para desenvolvimento local.

Render: Plataforma de nuvem para o deploy dos serviços.

Cloudflare R2: Serviço de armazenamento de objetos (S3-compatible) para as fotos de perfil.

⚙️ Configuração e Instalação (Ambiente Local)
Siga os passos abaixo para rodar o projeto em sua máquina local.

Pré-requisitos
Python 3.11 ou superior

Git

1. Clone o Repositório
Bash

git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio
2. Configure o Backend (API)
Bash

# Crie e ative o ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# Instale as dependências
pip install -r requirements.txt

# Crie o banco de dados local
python -c "from src.database import Base, engine; Base.metadata.create_all(bind=engine)"

# Crie o primeiro usuário administrador
python create_first_user.py
3. Configure o Frontend (Painel de Gestão)
Bash

# Navegue até a pasta do frontend
cd frontend

# Crie e ative um ambiente virtual separado
python3 -m venv .venv
source .venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
4. Variáveis de Ambiente (.env)
Crie um arquivo chamado .env na raiz do projeto e preencha com suas chaves (use os valores de teste para desenvolvimento):

# Chave secreta para a API (pode gerar uma com 'openssl rand -hex 32')
SECRET_KEY=sua_chave_secreta_aqui

# Chaves da Stripe (modo de teste)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLIC_KEY=pk_test_...

# Chaves do Google OAuth 2.0
GOOGLE_CLIENT_ID=seu-id-de-cliente.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=seu-segredo-de-cliente

# URL do PWA (para desenvolvimento local)
FRONTEND_PWA_URL=http://localhost:8000/portal

# Credenciais do Cloudflare R2 (opcional para dev local)
S3_BUCKET_NAME=...
S3_ENDPOINT_URL=...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
PUBLIC_BUCKET_URL=...
Crie também um arquivo .env dentro da pasta frontend/ com a chave SECRET_KEY para o Flask.

5. Rode a Aplicação
Abra dois terminais separados.

Terminal 1 (Backend):

Bash

# Na raiz do projeto
source .venv/bin/activate
uvicorn main:app --reload --port 8000
Terminal 2 (Frontend):

Bash

# Na pasta frontend/
source .venv/bin/activate
flask run --port 5700
Acesse o Painel de Gestão em: http://localhost:5700

Acesse o Portal do Aluno em: http://localhost:8000/portal

🚀 Deploy em Produção (Render)
O deploy é feito em 3 serviços distintos no Render:

Banco de Dados (PostgreSQL):

Crie um novo serviço "PostgreSQL".

Copie a "Internal Database URL".

Backend (API - Web Service):

Root Directory: (em branco)

Build Command: pip install -r requirements.txt

Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT

Variáveis de Ambiente: Configure todas as chaves do .env, usando a DATABASE_URL interna do banco criado e as URLs públicas dos serviços do Render para BACKEND_URL e FRONTEND_URL.

Frontend (Gestão - Web Service):

Root Directory: frontend

Build Command: pip install -r requirements.txt

Start Command: gunicorn app:app

Variáveis de Ambiente: Configure a SECRET_KEY e a API_BASE_URL apontando para a URL pública do seu serviço de backend.

Lembre-se de atualizar os "URIs de redirecionamento autorizados" no Google Cloud Console com a URL de callback da sua API no Render.

🗺️ Roadmap de Melhorias
[ ] Implementar o Webhook da Stripe para confirmação automática de pagamentos.

[ ] Criar sistema de relatórios avançados no painel de gestão.

[ ] Adicionar controle de frequência de alunos nas turmas.

[ ] Desenvolver um sistema de notificações para alunos e administradores