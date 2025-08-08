# Frontend Academia de Lutas

Sistema de gerenciamento para academia de lutas com interface web moderna e responsiva.

## 🚀 Características

### Design e Interface
- Interface moderna e elegante com Bootstrap 5.3
- Design responsivo para desktop, tablet e mobile
- Paleta de cores profissional (azul, verde, amarelo)
- Animações e transições suaves
- Ícones Font Awesome para melhor experiência

### Funcionalidades
- **Dashboard Principal**: Visão geral com estatísticas em tempo real
- **Gestão de Alunos**: Cadastro, edição, listagem e busca
- **Gestão de Professores**: Cadastro, edição, listagem e filtros
- **Gestão de Turmas**: Criação e gerenciamento de turmas
- **Gestão de Eventos**: Calendário e organização de eventos
- **Dashboard Financeiro**: Controle financeiro com gráficos interativos

## 🛠️ Tecnologias Utilizadas

### Backend
- **Flask 3.0**: Framework web Python
- **Requests**: Comunicação com API
- **Python-dotenv**: Gerenciamento de variáveis de ambiente

### Frontend
- **Bootstrap 5.3**: Framework CSS responsivo
- **jQuery 3.7**: Biblioteca JavaScript
- **Chart.js**: Gráficos interativos
- **Font Awesome 6.4**: Ícones vetoriais

### Recursos Avançados
- Máscaras de input para telefone, CPF, CEP
- Validação de formulários em tempo real
- Sistema de notificações toast
- Upload de arquivos para fotos
- Auto-save de formulários
- Loading states para melhor UX

## 📁 Estrutura do Projeto

```
frontend/
├── app.py                 # Aplicação Flask principal
├── config.py             # Configurações
├── requirements.txt      # Dependências Python
├── static/
│   ├── css/
│   │   └── style.css    # Estilos customizados
│   ├── js/
│   │   └── main.js      # JavaScript customizado
│   └── img/             # Imagens
└── templates/
    ├── base.html        # Template base
    ├── index.html       # Dashboard principal
    ├── alunos/          # Templates de alunos
    ├── professores/     # Templates de professores
    ├── turmas/          # Templates de turmas
    ├── eventos/         # Templates de eventos
    └── financeiro/      # Templates financeiros
```

## 🚀 Como Executar

### Pré-requisitos
- Python 3.11+
- API FastAPI rodando na porta 8000

### Instalação
1. Clone o repositório
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

### Execução
1. Inicie a API FastAPI (porta 8000)
2. Execute o frontend:
   ```bash
   python app.py
   ```
3. Acesse: http://localhost:5000

## 🔧 Configuração

### Variáveis de Ambiente
Crie um arquivo `.env` com:
```
SECRET_KEY=sua-chave-secreta
API_BASE_URL=http://localhost:8000/api/v1
```

### Integração com API
O frontend se conecta automaticamente à API FastAPI através das configurações em `config.py`.

## 📱 Responsividade

O sistema foi desenvolvido com abordagem mobile-first:
- **Desktop**: Layout completo com sidebar e múltiplas colunas
- **Tablet**: Layout adaptado com navegação colapsável
- **Mobile**: Interface otimizada para toque com navegação hamburger

## 🎨 Personalização

### Cores
As cores principais podem ser alteradas no arquivo `static/css/style.css`:
```css
:root {
    --primary-color: #2563eb;
    --secondary-color: #10b981;
    --accent-color: #f59e0b;
}
```

### Componentes
Todos os componentes seguem o padrão Bootstrap 5.3 e podem ser facilmente customizados.

## 📊 Funcionalidades Detalhadas

### Dashboard
- Cards com estatísticas em tempo real
- Gráficos de atividades mensais
- Ações rápidas para cadastros
- Notificações do sistema

### Gestão de Alunos
- Lista paginada com busca
- Formulário completo de cadastro
- Upload de foto de perfil
- Filtros por status
- Validação de dados

### Gestão de Professores
- Lista com filtros por especialidade
- Cadastro com informações profissionais
- Controle de salários
- Certificações e qualificações

### Dashboard Financeiro
- Gráficos de receitas e despesas
- Controle de fluxo de caixa
- Categorização de transações
- Relatórios visuais

## 🔒 Segurança

- Validação de dados no frontend e backend
- Sanitização de inputs
- Proteção contra XSS
- Validação de uploads de arquivo

## 🚀 Deploy

Para deploy em produção:
1. Configure um servidor WSGI (Gunicorn)
2. Use um proxy reverso (Nginx)
3. Configure HTTPS
4. Defina variáveis de ambiente de produção

## 📞 Suporte

Sistema desenvolvido para gerenciamento completo de academias de lutas com foco em usabilidade e performance.

