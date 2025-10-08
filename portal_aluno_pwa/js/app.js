const appRoot = document.getElementById('app-root');

const routes = {
    '/login': { page: '/portal/pages/login.html', handler: handleLoginPage, public: true },
    '/register': { page: '/portal/pages/register.html', handler: handleRegisterPage, public: true },
    '/dashboard': { page: '/portal/pages/dashboard.html', handler: handleDashboardPage },
    '/edit-profile': { page: '/portal/pages/edit_profile.html', handler: handleEditProfilePage }, // <-- ROTA ADICIONADA
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
    const passwordInput = document.getElementById('password');
    const togglePasswordButton = document.getElementById('togglePassword');

    // Lógica para o envio do formulário de login (original)
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = e.target.username.value;
        const password = passwordInput.value; // Usando a variável já declarada
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

    // Lógica para o botão de mostrar/ocultar senha (nova)
    if (togglePasswordButton) {
        const icon = togglePasswordButton.querySelector('i');

        togglePasswordButton.addEventListener('click', function () {
            // Alterna o tipo do input de 'password' para 'text' e vice-versa
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);

            // Alterna o ícone do botão
            icon.classList.toggle('fa-eye');
            icon.classList.toggle('fa-eye-slash');
        });
    }
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



async function handleEditProfilePage() {
    const form = document.getElementById('edit-profile-form');
    // Mapeando todos os campos do formulário
    const nomeInput = document.getElementById('nome');
    const emailInput = document.getElementById('email');
    const cpfInput = document.getElementById('cpf');
    const telefoneInput = document.getElementById('telefone');
    const dataNascimentoInput = document.getElementById('data_nascimento');
    const enderecoInput = document.getElementById('endereco');
    const observacoesInput = document.getElementById('observacoes');
    const fotoInput = document.getElementById('foto');
    const fotoPreview = document.getElementById('foto-preview');

    // 1. Preencher o formulário com os dados atuais
    try {
        const profile = await api.getProfile();
        nomeInput.value = profile.nome || '';
        emailInput.value = profile.email || '';
        cpfInput.value = profile.cpf || '';
        telefoneInput.value = profile.telefone || '';
        dataNascimentoInput.value = profile.data_nascimento || '';
        enderecoInput.value = profile.endereco || '';
        observacoesInput.value = profile.observacoes || '';
        if (profile.foto) {
            fotoPreview.src = `http://localhost:8000${profile.foto}`;
        }
    } catch (error) {
        ui.showAlert('Erro ao carregar seus dados para edição.');
    }

    // Preview da foto ao selecionar
    fotoInput.addEventListener('change', () => {
        const file = fotoInput.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                fotoPreview.src = e.target.result;
            };
            reader.readAsDataURL(file);
        }
    });

    // 2. Lidar com o envio do formulário
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const button = form.querySelector('button[type="submit"]');
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Salvando...';
        
        // Montar FormData
        const formData = new FormData();
        formData.append('nome', nomeInput.value);
        formData.append('cpf', cpfInput.value);
        formData.append('telefone', telefoneInput.value);
        formData.append('data_nascimento', dataNascimentoInput.value);
        formData.append('endereco', enderecoInput.value);
        formData.append('observacoes', observacoesInput.value);

        if (fotoInput.files[0]) {
            formData.append('foto', fotoInput.files[0]);
        }

        try {
            // A API de update agora usa FormData
            await api.updateProfile(formData);
            alert('Perfil atualizado com sucesso!');
            window.location.hash = '/dashboard'; // Volta para o perfil
        } catch (error) {
            ui.showAlert(error.message || 'Não foi possível salvar as alterações.');
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-save me-1"></i> Salvar Alterações';
        }
    });
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