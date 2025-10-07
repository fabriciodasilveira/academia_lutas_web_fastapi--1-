const appRoot = document.getElementById('app-root');

// Definição das rotas do frontend
const routes = {
    '/login': { page: '/portal/pages/login.html', handler: handleLoginPage, public: true },
    '/register': { page: '/portal/pages/register.html', handler: handleRegisterPage, public: true },
    '/dashboard': { page: '/portal/pages/dashboard.html', handler: handleDashboardPage },
    '/payments': { page: '/portal/pages/payments.html', handler: handlePaymentsPage },
    '/events': { page: '/portal/pages/events.html', handler: handleEventsPage }
};

// Roteador
const router = async () => {
    const path = window.location.hash.slice(1) || '/dashboard';
    const route = routes[path] || routes['/dashboard'];
    
    const token = localStorage.getItem('accessToken');
    if (!route.public && !token) {
        window.location.hash = '/login';
        return;
    }
    
    if (route.public && token) {
        window.location.hash = '/dashboard';
        return;
    }

    ui.toggleNav(!route.public);
    ui.showLoading(appRoot);
    
    try {
        const response = await fetch(route.page);
        appRoot.innerHTML = await response.text();
        if (route.handler) {
            route.handler();
        }
    } catch (error) {
        appRoot.innerHTML = `<p class="text-danger">Erro ao carregar a página.</p>`;
    }
};

// --- Handlers de Página ---

function handleLoginPage() {
    const form = document.getElementById('login-form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = e.target.username.value;
        const password = e.target.password.value;
        try {
            const data = await api.login(email, password);
            if (data.user_info.role !== 'aluno') {
                throw new Error("Acesso permitido somente a alunos.");
            }
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
        const data = {
            nome: e.target.nome.value,
            email: e.target.email.value,
            password: e.target.password.value
        };
        try {
            await api.register(data);
            alert('Cadastro realizado com sucesso! Você será redirecionado para o login.');
            window.location.hash = '/login';
        } catch (error) {
            ui.showAlert(error.message || 'Não foi possível completar o cadastro.');
        }
    });
}

async function handleDashboardPage() {
    try {
        const profile = await api.getProfile();
        document.getElementById('aluno-nome').innerText = profile.nome;
        document.getElementById('aluno-email').innerText = profile.email;
        document.getElementById('aluno-telefone').innerText = profile.telefone || 'Não informado';
    } catch (error) {
        ui.showAlert('Não foi possível carregar seus dados.');
    }
}

async function handlePaymentsPage() {
    const list = document.getElementById('payments-list');
    try {
        const payments = await api.getPayments(); // Você precisa criar este endpoint na API
        if (payments.length === 0) {
            list.innerHTML = '<p class="text-muted">Nenhuma mensalidade encontrada.</p>';
            return;
        }
        list.innerHTML = payments.map(p => `
            <div class="list-group-item d-flex justify-content-between align-items-center">
                <div>
                    <h6 class="mb-1">${p.plano.nome}</h6>
                    <small>Vencimento: ${new Date(p.data_vencimento).toLocaleDateString()}</small>
                </div>
                <span class="badge bg-${p.status === 'pago' ? 'success' : 'warning'}">${p.status}</span>
            </div>
        `).join('');
    } catch (error) {
        ui.showAlert('Não foi possível carregar seus pagamentos.');
    }
}

async function handleEventsPage() {
    const list = document.getElementById('events-list');
    try {
        const events = await api.getEvents();
        if (events.length === 0) {
            list.innerHTML = '<p class="text-muted">Nenhum evento futuro encontrado.</p>';
            return;
        }
        list.innerHTML = events.map(e => `
             <div class="card mb-3">
                <div class="card-body">
                    <h5 class="card-title">${e.nome}</h5>
                    <p class="card-text">${e.descricao || ''}</p>
                    <p class="card-text"><small class="text-muted">${new Date(e.data_evento).toLocaleString()}</small></p>
                </div>
            </div>
        `).join('');
    } catch (error) {
        ui.showAlert('Não foi possível carregar os eventos.');
    }
}


// Inicialização e eventos do navegador
window.addEventListener('hashchange', router);
window.addEventListener('load', () => {
    // Registra o Service Worker
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/portal/sw.js')
            .then(() => console.log('Service Worker registrado com sucesso.'))
            .catch(err => console.error('Erro no registro do Service Worker:', err));
    }
    
    // Configura o botão de logout
    document.getElementById('logout-button').addEventListener('click', () => {
        localStorage.removeItem('accessToken');
        window.location.hash = '/login';
    });
    
    router();
});