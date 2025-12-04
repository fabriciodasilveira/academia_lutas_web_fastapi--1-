// Arquivo: portal_aluno_pwa/js/app.js

const appRoot = document.getElementById('app-root');

const routes = {
    '/login': { page: '/portal/pages/login.html', handler: handleLoginPage, public: true },
    '/login/callback': { handler: handleLoginCallback, public: true },
    '/register': { page: '/portal/pages/register.html', handler: handleRegisterPage, public: true },
    '/dashboard': { page: '/portal/pages/dashboard.html', handler: handleDashboardPage },
    '/carteirinha': { page: '/portal/pages/carteirinha.html', handler: handleCarteirinhaPage },
    '/edit-profile': { page: '/portal/pages/edit_profile.html', handler: handleEditProfilePage },
    '/payments': { page: '/portal/pages/payments.html', handler: handlePaymentsPage },
    '/events': { page: '/portal/pages/events.html', handler: handleEventsPage },
    '/beneficios': { page: '/portal/pages/beneficios.html', handler: handleBeneficiosPage }
};

// --- FUNÇÃO PARA GERENCIAR O MODAL DO PIX ---
async function exibirModalPix(endpoint) {
    // 1. Cria o HTML do Modal dinamicamente (se não existir)
    if (!document.getElementById('pixModal')) {
        const modalHtml = `
        <div class="modal fade" id="pixModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title"><i class="fas fa-qrcode text-success me-2"></i>Pagamento via PIX</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body text-center" id="pixModalBody">
                        <div class="spinner-border text-primary" role="status"></div>
                        <p class="mt-2">Gerando QR Code...</p>
                    </div>
                </div>
            </div>
        </div>`;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }

    // 2. Abre o Modal
    const pixModal = new bootstrap.Modal(document.getElementById('pixModal'));
    pixModal.show();
    
    const modalBody = document.getElementById('pixModalBody');
    modalBody.innerHTML = '<div class="spinner-border text-primary" role="status"></div><p class="mt-2">Gerando QR Code...</p>';

    try {
        // 3. Chama a API
        const data = await api.request(endpoint, 'POST');

        // 4. Renderiza o QR Code e o Copia e Cola
        modalBody.innerHTML = `
            <p class="text-muted mb-3">Escaneie o QR Code ou use o Copia e Cola:</p>
            
            <img src="data:image/jpeg;base64,${data.qr_code_base64}" class="img-fluid border rounded mb-3" style="max-width: 250px;">
            
            <div class="input-group mb-3">
                <input type="text" class="form-control" value="${data.qr_code}" id="pixCopiaCola" readonly>
                <button class="btn btn-outline-secondary" type="button" onclick="copiarPix()">
                    <i class="fas fa-copy"></i>
                </button>
            </div>
            
            <div class="alert alert-info small">
                <i class="fas fa-info-circle"></i> Após pagar no seu banco, aguarde alguns instantes e atualize a página.
            </div>
        `;

    } catch (error) {
        console.error(error);
        let msg = error.message || "Erro desconhecido";
        if(msg.includes("400")) msg = "Erro: Verifique se seu CPF está cadastrado no perfil.";
        modalBody.innerHTML = `<div class="alert alert-danger">${msg}</div>`;
    }
}

// Função global auxiliar para copiar
window.copiarPix = function() {
    const copyText = document.getElementById("pixCopiaCola");
    copyText.select();
    copyText.setSelectionRange(0, 99999); // Para mobile
    navigator.clipboard.writeText(copyText.value);
    alert("Código PIX copiado!");
}

// --- FUNÇÕES DE PAGAMENTO LIMPAS ---

async function pagarMensalidadeOnline(event, mensalidadeId) {
    // Chama o modal diretamente para a rota de PIX de mensalidade
    await exibirModalPix(`/pagamentos/pix/mensalidade/${mensalidadeId}`);
}

async function pagarEventoOnline(event, inscricaoId) {
    // Chama o modal diretamente para a rota de PIX de evento
    await exibirModalPix(`/pagamentos/pix/inscricao/${inscricaoId}`);
}


// --- RESTO DO CÓDIGO DO APP.JS (Router, Navegação, etc) ---

function updateActiveNav(path) {
    const navLinks = document.querySelectorAll('.nav__link');
    navLinks.forEach(link => {
        link.classList.remove('nav__link--active');
        if (link.hash && path.startsWith(link.hash.slice(1))) {
            link.classList.add('nav__link--active');
        }
    });
}

const router = async () => {
    const path = (window.location.hash.slice(1).split('?')[0] || '/dashboard');
    updateActiveNav(path); 
    
    const route = routes[path] || routes['/dashboard'];
    const token = localStorage.getItem('accessToken');

    const appRootEl = document.getElementById('app-root');
    const bodyEl = document.body;

    if (path === '/login' || path === '/login/callback' || path === '/register') {
        bodyEl.classList.add('login-active');
        bodyEl.classList.remove('nav-active');
        appRootEl.classList.remove('container', 'py-4'); 
        appRootEl.classList.add('w-100', 'p-0'); 
    } else {
        bodyEl.classList.remove('login-active');
        bodyEl.classList.add('nav-active');
        appRootEl.classList.remove('w-100', 'p-0');
        appRootEl.classList.add('container', 'py-4'); 
    }

    if (!route.public && !token) {
        window.location.hash = '/login';
        return;
    }
    
    if (route.public && token && path !== '/login/callback') {
        window.location.hash = '/dashboard';
        return;
    }

    ui.toggleNav(!route.public);
    
    if (route.page) {
        ui.showLoading(appRoot);
        try {
            const response = await fetch(route.page);
            appRoot.innerHTML = await response.text();
        } catch (error) {
            appRoot.innerHTML = `<p class="text-danger">Erro ao carregar a página.</p>`;
        }
    }
    
    if (route.handler) {
        route.handler();
    }
};

function handleLoginCallback() {
    ui.toggleNav(false);
    appRoot.innerHTML = '<p class="text-center mt-5">Autenticando...</p>';
    const params = new URLSearchParams(window.location.hash.split('?')[1]);
    const token = params.get('token');
    if (token) {
        localStorage.setItem('accessToken', token);
        window.location.hash = '/dashboard';
    } else {
        window.location.hash = '/login';
    }
}

function handleLoginPage() {
    const form = document.getElementById('login-form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = e.target.username.value; 
        const password = e.target.password.value;
        try {
            const data = await api.login(username, password);
            if (data.user_info.role !== 'aluno') throw new Error("Acesso permitido somente a alunos.");
            localStorage.setItem('accessToken', data.access_token);
            window.location.hash = '/dashboard';
        } catch (error) {
            ui.showAlert(error.message || 'Email ou senha inválidos.');
        }
    });
}

function handleRegisterPage() {
    const form = document.getElementById('register-form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = { nome: e.target.nome.value, email: e.target.email.value, password: e.target.password.value };
        try {
            await api.register(data);
            alert('Cadastro realizado! Faça login.');
            window.location.hash = '/login';
        } catch (error) {
            ui.showAlert(error.message || 'Erro no cadastro.');
        }
    });
}

async function handleDashboardPage() {
    try {
        const profile = await api.getProfile();
        document.getElementById('aluno-nome').innerText = profile.nome;
        document.getElementById('aluno-email').innerText = profile.email;
        
        const matriculasContainer = document.getElementById('matriculas-container');
        try {
            const matriculas = await api.getMatriculas();
            if (matriculas.length > 0) {
                matriculasContainer.innerHTML = `<ul class="list-group list-group-flush">${matriculas.map(m => `<li class="list-group-item"><span>${m.turma.nome}</span></li>`).join('')}</ul>`;
            } else {
                matriculasContainer.innerHTML = '<p class="text-muted">Sem matrículas ativas.</p>';
            }
        } catch (e) {}
    } catch (error) {
        ui.showAlert('Erro ao carregar perfil.');
    }
}

async function handleCarteirinhaPage() {
    try {
        const profile = await api.getProfile();
        document.getElementById('aluno-nome').innerText = profile.nome;
        document.getElementById('aluno-matricula').innerText = 1000 + profile.id;
        document.getElementById('aluno-status').innerText = profile.status_geral === "Ativo" ? "Aluno Ativo" : "Inativo";
        document.getElementById('aluno-status').className = profile.status_geral === "Ativo" ? "badge bg-success" : "badge bg-secondary";
    } catch (error) {}
}

async function handleEditProfilePage() {
    // ... (código de edição de perfil mantido igual, apenas certifique-se de que está lá) ...
    // Se precisar do código completo dessa função, avise.
    // Por brevidade, assumo que você manterá a lógica de preenchimento de formulário.
    console.log("Carregando edição de perfil...");
    const profile = await api.getProfile();
    document.getElementById('nome').value = profile.nome;
    // ... etc ...
}

async function handlePaymentsPage() {
    const list = document.getElementById('payments-list');
    try {
        const pendencias = await api.getPayments();
        if (pendencias.length === 0) {
            list.innerHTML = '<p class="text-muted text-center mt-4">Nenhuma pendência.</p>';
            return;
        }
        list.innerHTML = pendencias.map(p => {
            const vencimento = new Date(p.data_vencimento + 'T00:00:00').toLocaleDateString('pt-BR');
            const isPendente = p.status === 'pendente';
            let payFunction = p.tipo === 'inscricao' ? `pagarEventoOnline(event, ${p.id})` : `pagarMensalidadeOnline(event, ${p.id})`;
            
            return `
            <div class="list-group-item d-flex justify-content-between align-items-center flex-wrap">
                <div class="me-auto">
                    <h6 class="mb-1">${p.descricao}</h6>
                    <small class="text-muted">Venc: ${vencimento} | R$ ${p.valor.toFixed(2)}</small>
                </div>
                <div class="mt-2 mt-md-0">
                    ${isPendente && p.valor > 0 ? 
                        `<button class="btn btn-sm btn-primary" onclick="${payFunction}"><i class="fas fa-qrcode me-1"></i>Pagar PIX</button>` : 
                        `<span class="badge bg-${p.status === 'pago' ? 'success' : 'secondary'}">${p.status}</span>`
                    }
                </div>
            </div>`;
        }).join('');
    } catch (error) {
        ui.showAlert('Erro ao carregar pagamentos.');
    }
}

async function handleEventsPage() {
    const list = document.getElementById('events-list');
    try {
        const events = await api.getEvents();
        if (events.length === 0) {
            list.innerHTML = '<p class="text-muted text-center mt-4">Nenhum evento.</p>';
            return;
        }
        list.innerHTML = events.map(e => `
            <div class="card mb-3">
                <div class="card-body">
                    <h5 class="card-title">${e.nome}</h5>
                    <p>${e.descricao || ''}</p>
                    ${!e.is_inscrito && e.status === 'Ativo' ? 
                        `<button class="btn btn-sm btn-primary" onclick="inscreverEmEvento(event, ${e.id})">Inscrever-se</button>` : 
                        `<button class="btn btn-sm btn-secondary" disabled>${e.is_inscrito ? 'Inscrito' : e.status}</button>`
                    }
                </div>
            </div>
        `).join('');
    } catch (error) {}
}

async function inscreverEmEvento(event, eventoId) {
    try {
        await api.enrollInEvent(eventoId);
        ui.showAlert('Inscrição realizada!', 'success');
        handleEventsPage(); // Recarrega a lista
    } catch (error) {
        ui.showAlert(error.message || 'Erro ao inscrever.');
    }
}

async function handleBeneficiosPage() {
    // ... (código de benefícios existente) ...
}

window.addEventListener('hashchange', router);
window.addEventListener('load', () => {
    // Inicialização simplificada (removemos initializePaymentSystem pois não precisamos configurar Stripe)
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/portal/sw.js').catch(err => console.error('Erro SW:', err));
    }
    document.getElementById('logout-button').addEventListener('click', () => {
        localStorage.removeItem('accessToken');
        window.location.hash = '/login';
    });
    router();
});