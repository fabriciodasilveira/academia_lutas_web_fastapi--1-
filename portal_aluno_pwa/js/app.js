const appRoot = document.getElementById('app-root');

// --- CORREÇÃO AQUI: Adicionamos a rota para '/edit-profile' ---
const routes = {
    '/login': { page: '/portal/pages/login.html', handler: handleLoginPage, public: true },
    '/register': { page: '/portal/pages/register.html', handler: handleRegisterPage, public: true },
    '/dashboard': { page: '/portal/pages/dashboard.html', handler: handleDashboardPage },
    '/edit-profile': { page: '/portal/pages/edit_profile.html', handler: handleEditProfilePage }, 
    '/payments': { page: '/portal/pages/payments.html', handler: handlePaymentsPage },
    '/events': { page: '/portal/pages/events.html', handler: handleEventsPage }
};

// Roteador (sem alterações, mas incluído para o arquivo ficar completo)
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
        // Marca o link de navegação ativo
        document.querySelectorAll('.nav__link').forEach(link => {
            link.classList.remove('nav__link--active');
            if (link.getAttribute('href') === `#${path}`) {
                link.classList.add('nav__link--active');
            }
        });

        const response = await fetch(route.page);
        appRoot.innerHTML = await response.text();
        if (route.handler) {
            route.handler();
        }
    } catch (error) {
        appRoot.innerHTML = `<p class="text-danger">Erro ao carregar a página.</p>`;
    }
};

// --- Handlers de Página (sem alterações, mas incluídos para o arquivo ficar completo) ---

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
        
        // Atualiza a foto do perfil
        const profilePic = document.getElementById('profile-picture');
        if (profile.foto) {
            profilePic.src = `http://localhost:8000${profile.foto}`;
        } else {
            profilePic.src = '/portal/images/default-avatar.png';
        }

        document.getElementById('aluno-nome').innerText = profile.nome;
        document.getElementById('aluno-email').innerText = profile.email;
        document.getElementById('aluno-telefone').innerText = profile.telefone || 'Não informado';
        document.getElementById('aluno-nascimento').innerText = profile.data_nascimento ? new Date(profile.data_nascimento + 'T00:00:00').toLocaleDateString('pt-BR') : 'Não informada';
    } catch (error) {
        ui.showAlert('Não foi possível carregar seus dados.');
    }
}


// ... (código anterior do app.js) ...

async function handleEditProfilePage() {
    const form = document.getElementById('edit-profile-form');
    const elements = {
        nome: document.getElementById('nome'),
        email: document.getElementById('email'),
        cpf: document.getElementById('cpf'),
        telefone: document.getElementById('telefone'),
        dataNascimento: document.getElementById('data_nascimento'),
        endereco: document.getElementById('endereco'),
        observacoes: document.getElementById('observacoes'),
        foto: document.getElementById('foto'),
        fotoPreview: document.getElementById('foto-preview')
    };

    // 1. Preenche o formulário com os dados da API (sem máscaras)
    try {
        const profile = await api.getProfile();
        elements.nome.value = profile.nome || '';
        elements.email.value = profile.email || '';
        elements.cpf.value = profile.cpf || '';
        elements.telefone.value = profile.telefone || '';
        elements.dataNascimento.value = profile.data_nascimento || '';
        elements.endereco.value = profile.endereco || '';
        elements.observacoes.value = profile.observacoes || '';
        if (profile.foto) {
            elements.fotoPreview.src = `http://localhost:8000${profile.foto}`;
        }
    } catch (error) {
        console.error("Erro ao carregar dados do perfil:", error);
        ui.showAlert('Erro ao carregar seus dados para edição.');
    }

    // Preview da foto
    elements.foto.addEventListener('change', () => {
        const file = elements.foto.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => { elements.fotoPreview.src = e.target.result; };
            reader.readAsDataURL(file);
        }
    });

    // 2. Lida com o envio do formulário (sem validação)
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const button = form.querySelector('button[type="submit"]');
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Salvando...';
        
        const formData = new FormData();
        formData.append('nome', elements.nome.value);
        formData.append('cpf', elements.cpf.value);
        formData.append('telefone', elements.telefone.value);
        formData.append('data_nascimento', elements.dataNascimento.value);
        formData.append('endereco', elements.endereco.value);
        formData.append('observacoes', elements.observacoes.value);
        if (elements.foto.files[0]) {
            formData.append('foto', elements.foto.files[0]);
        }

        try {
            await api.updateProfile(formData);
            alert('Perfil atualizado com sucesso!');
            window.location.hash = '/dashboard';
        } catch (error) {
            ui.showAlert(error.message || 'Não foi possível salvar as alterações.');
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-save me-1"></i> Salvar Alterações';
        }
    });
}

// ... (resto do app.js) ...



async function handlePaymentsPage() {
    const list = document.getElementById('payments-list');
    try {
        const payments = await api.getPayments();
        if (payments.length === 0) {
            list.innerHTML = '<p class="text-muted">Nenhuma mensalidade encontrada.</p>';
            return;
        }
        list.innerHTML = payments.map(p => `
            <div class="list-group-item d-flex justify-content-between align-items-center">
                <div>
                    <h6 class="mb-1">${p.plano.nome}</h6>
                    <small>Vencimento: ${new Date(p.data_vencimento + 'T00:00:00').toLocaleDateString()}</small>
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
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/portal/sw.js')
            .then(() => console.log('Service Worker registrado com sucesso.'))
            .catch(err => console.error('Erro no registro do Service Worker:', err));
    }
    
    document.getElementById('logout-button').addEventListener('click', () => {
        localStorage.removeItem('accessToken');
        window.location.hash = '/login';
    });
    
    router();
});