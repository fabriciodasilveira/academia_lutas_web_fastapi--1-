const appRoot = document.getElementById('app-root');

const routes = {
    '/login': { page: '/portal/pages/login.html', handler: handleLoginPage, public: true },
    '/login/callback': { handler: handleLoginCallback, public: true },
    '/register': { page: '/portal/pages/register.html', handler: handleRegisterPage, public: true },
    '/dashboard': { page: '/portal/pages/dashboard.html', handler: handleDashboardPage },
    '/carteirinha': { page: '/portal/pages/carteirinha.html', handler: handleCarteirinhaPage },
    '/edit-profile': { page: '/portal/pages/edit_profile.html', handler: handleEditProfilePage },
    '/payments': { page: '/portal/pages/payments.html', handler: handlePaymentsPage },
    '/events': { page: '/portal/pages/events.html', handler: handleEventsPage }
};

const router = async () => {
    const hashParts = window.location.hash.split('?');
    const path = hashParts[0].slice(1) || '/dashboard';
    const urlParams = new URLSearchParams(hashParts[1] || '');

    // Lógica para mostrar o alerta de pagamento
    if (urlParams.has('payment')) {
        const paymentStatus = urlParams.get('payment');
        
        // Atraso para garantir que a página carregou antes de mostrar o alerta
        setTimeout(() => {
            if (paymentStatus === 'success') {
                ui.showAlert('Pagamento realizado com sucesso!', 'success');
            } else if (paymentStatus === 'canceled') {
                ui.showAlert('O pagamento foi cancelado.', 'info');
            }
            // Limpa os parâmetros da URL para não mostrar o alerta novamente ao recarregar
            window.history.replaceState(null, null, window.location.pathname + `#${path}`);
        }, 500);
    }
    
    const route = routes[path] || routes['/dashboard'];
    
    const token = localStorage.getItem('accessToken');
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

// ... (todas as outras funções do app.js permanecem exatamente iguais) ...

let stripe;

async function initializeStripe() {
    try {
        const keyData = await api.request('/pagamentos/stripe-key', 'GET', null, false, false);
        if (keyData && keyData.publicKey && keyData.publicKey.startsWith('pk_')) {
            stripe = Stripe(keyData.publicKey);
        } else {
            console.error("Chave pública da Stripe inválida ou não recebida da API.");
            ui.showAlert("Erro de configuração: A chave de pagamento é inválida.");
        }
    } catch (error) {
        console.error("Falha ao buscar a chave da Stripe:", error);
        ui.showAlert("Não foi possível conectar ao sistema de pagamento.");
    }
}

async function pagarMensalidadeOnline(event, mensalidadeId) {
    if (!stripe) {
        ui.showAlert("O sistema de pagamento não está pronto. Tente novamente em alguns segundos.");
        return;
    }
    const button = event.currentTarget;
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Abrindo...';
    try {
        const sessionData = await api.request(`/pagamentos/stripe/mensalidade/${mensalidadeId}`, 'POST');
        if (sessionData.sessionId) {
            const { error } = await stripe.redirectToCheckout({ sessionId: sessionData.sessionId });
            if (error) throw new Error(error.message);
        } else {
            throw new Error('Não foi possível iniciar a sessão de pagamento.');
        }
    } catch (error) {
        ui.showAlert(error.message || 'Não foi possível iniciar o pagamento.');
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-credit-card me-1"></i>Pagar Online';
    }
}

async function pagarEventoOnline(event, inscricaoId) {
    if (!stripe) {
        ui.showAlert("O sistema de pagamento não está pronto. Tente novamente em alguns segundos.");
        return;
    }
    const button = event.currentTarget;
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Abrindo...';
    try {
        const sessionData = await api.request(`/pagamentos/stripe/evento/${inscricaoId}`, 'POST');
        if (sessionData.sessionId) {
            const { error } = await stripe.redirectToCheckout({ sessionId: sessionData.sessionId });
            if (error) throw new Error(error.message);
        } else {
            throw new Error('Não foi possível iniciar a sessão de pagamento.');
        }
    } catch (error) {
        ui.showAlert(error.message || 'Não foi possível iniciar o pagamento.');
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-credit-card me-1"></i>Pagar Online';
    }
}

function handleLoginCallback() {
    ui.toggleNav(false);
    appRoot.innerHTML = '<p class="text-center mt-5">Autenticando...</p>';
    const params = new URLSearchParams(window.location.hash.split('?')[1]);
    const token = params.get('token');
    if (token) {
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            if (payload.role !== 'aluno') {
                window.location.hash = '/login';
                setTimeout(() => ui.showAlert("Login com Google permitido somente para alunos."), 100);
                return;
            }
            if (payload.role === 'pendente') {
                 window.location.hash = '/login';
                setTimeout(() => ui.showAlert("Sua conta está aguardando aprovação de um administrador."), 100);
                return;
            }
            localStorage.setItem('accessToken', token);
            window.location.hash = '/dashboard';
        } catch (e) {
            window.location.hash = '/login';
            setTimeout(() => ui.showAlert("Token de autenticação inválido."), 100);
        }
    } else {
        window.location.hash = '/login';
        setTimeout(() => ui.showAlert("Falha na autenticação com Google."), 100);
    }
}

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
    const togglePassword = document.getElementById('togglePassword');
    const password = document.getElementById('password');
    if (togglePassword && password) {
        const icon = togglePassword.querySelector('i');
        togglePassword.addEventListener('click', function () {
            const type = password.getAttribute('type') === 'password' ? 'text' : 'password';
            password.setAttribute('type', type);
            icon.classList.toggle('fa-eye');
            icon.classList.toggle('fa-eye-slash');
        });
    }
}

function handleRegisterPage() {
    const form = document.getElementById('register-form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = { nome: e.target.nome.value, email: e.target.email.value, password: e.target.password.value };
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
        const profilePic = document.getElementById('profile-picture');
        if (profile.foto) {
            profilePic.src = profile.foto;
        } else {
            profilePic.src = '/portal/images/default-avatar.png';
        }
        document.getElementById('aluno-nome').innerText = profile.nome;
        document.getElementById('aluno-email').innerText = profile.email;
        document.getElementById('aluno-telefone').innerText = profile.telefone || 'Não informado';
        document.getElementById('aluno-nascimento').innerText = profile.data_nascimento ? new Date(profile.data_nascimento + 'T00:00:00').toLocaleDateString('pt-BR') : 'Não informada';
        const matriculasContainer = document.getElementById('matriculas-container');
        try {
            const matriculas = await api.getMatriculas();
            if (matriculas.length > 0) {
                matriculasContainer.innerHTML = `<ul class="list-group list-group-flush">${matriculas.map(m => `<li class="list-group-item d-flex justify-content-between align-items-center"><span>${m.turma.nome}</span><small class="text-muted">${m.turma.horario}</small></li>`).join('')}</ul>`;
            } else {
                matriculasContainer.innerHTML = '<p class="text-muted">Você não possui matrículas ativas no momento.</p>';
            }
        } catch (error) {
            matriculasContainer.innerHTML = '<p class="text-danger">Não foi possível carregar suas matrículas.</p>';
        }
    } catch (error) {
        ui.showAlert('Não foi possível carregar seus dados de perfil.');
    }
}

async function handleCarteirinhaPage() {
    try {
        const profile = await api.getProfile();
        const fotoEl = document.getElementById('aluno-foto');
        if (profile.foto) {
            fotoEl.src = profile.foto;
        } else {
            fotoEl.src = '/portal/images/default-avatar.png';
        }
        document.getElementById('aluno-nome').innerText = profile.nome;
        if (profile.id) {
            document.getElementById('aluno-matricula').innerText = 1000 + profile.id;
        }
        document.getElementById('aluno-email').innerText = profile.email || 'Não informado';
        document.getElementById('aluno-telefone').innerText = profile.telefone || 'Não informado';
        document.getElementById('aluno-nascimento').innerText = profile.data_nascimento ? new Date(profile.data_nascimento + 'T00:00:00').toLocaleDateString('pt-BR') : '--/--/----';
    } catch (error) {
        ui.showAlert('Não foi possível carregar os dados da sua carteirinha.');
    }
}

async function handleEditProfilePage() {
    const form = document.getElementById('edit-profile-form');
    const nomeInput = document.getElementById('nome');
    const emailInput = document.getElementById('email');
    const cpfInput = document.getElementById('cpf');
    const telefoneInput = document.getElementById('telefone');
    const dataNascimentoInput = document.getElementById('data_nascimento');
    const enderecoInput = document.getElementById('endereco');
    const observacoesInput = document.getElementById('observacoes');
    const fotoInput = document.getElementById('foto');
    const fotoPreview = document.getElementById('foto-preview');
    const dadosResponsavelDiv = document.getElementById('dados-responsavel');
    const nomeResponsavelInput = document.getElementById('nome_responsavel');
    const cpfResponsavelInput = document.getElementById('cpf_responsavel');
    const parentescoResponsavelInput = document.getElementById('parentesco_responsavel');
    const telefoneResponsavelInput = document.getElementById('telefone_responsavel');
    const emailResponsavelInput = document.getElementById('email_responsavel');
    const camposResponsavel = dadosResponsavelDiv.querySelectorAll('input');

    function toggleResponsavelFields() {
        const dataNascimento = dataNascimentoInput.value;
        if (!dataNascimento) {
            dadosResponsavelDiv.style.display = 'none';
            camposResponsavel.forEach(input => input.required = false);
            return;
        }
        const hoje = new Date();
        const nascimento = new Date(dataNascimento);
        let idade = hoje.getFullYear() - nascimento.getFullYear();
        const m = hoje.getMonth() - nascimento.getMonth();
        if (m < 0 || (m === 0 && hoje.getDate() < nascimento.getDate())) {
            idade--;
        }
        if (idade < 18) {
            dadosResponsavelDiv.style.display = 'flex';
            nomeResponsavelInput.required = true;
            cpfResponsavelInput.required = true;
            parentescoResponsavelInput.required = true;
        } else {
            dadosResponsavelDiv.style.display = 'none';
            camposResponsavel.forEach(input => input.required = false);
        }
    }
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
            fotoPreview.src = profile.foto;
        }
        nomeResponsavelInput.value = profile.nome_responsavel || '';
        cpfResponsavelInput.value = profile.cpf_responsavel || '';
        parentescoResponsavelInput.value = profile.parentesco_responsavel || '';
        telefoneResponsavelInput.value = profile.telefone_responsavel || '';
        emailResponsavelInput.value = profile.email_responsavel || '';
        toggleResponsavelFields();
    } catch (error) {
        ui.showAlert('Erro ao carregar seus dados para edição.');
    }
    dataNascimentoInput.addEventListener('change', toggleResponsavelFields);
    fotoInput.addEventListener('change', () => {
        const file = fotoInput.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => { fotoPreview.src = e.target.result; };
            reader.readAsDataURL(file);
        }
    });
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const button = form.querySelector('button[type="submit"]');
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Salvando...';
        const formData = new FormData();
        formData.append('nome', nomeInput.value);
        formData.append('cpf', cpfInput.value);
        formData.append('telefone', telefoneInput.value);
        formData.append('data_nascimento', dataNascimentoInput.value);
        formData.append('endereco', enderecoInput.value);
        formData.append('observacoes', observacoesInput.value);
        formData.append('nome_responsavel', nomeResponsavelInput.value);
        formData.append('cpf_responsavel', cpfResponsavelInput.value);
        formData.append('parentesco_responsavel', parentescoResponsavelInput.value);
        formData.append('telefone_responsavel', telefoneResponsavelInput.value);
        formData.append('email_responsavel', emailResponsavelInput.value);
        if (fotoInput.files[0]) {
            formData.append('foto', fotoInput.files[0]);
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

async function handlePaymentsPage() {
    const list = document.getElementById('payments-list');
    try {
        const pendencias = await api.getPayments();
        if (pendencias.length === 0) {
            list.innerHTML = '<p class="text-muted text-center mt-4">Nenhuma pendência financeira encontrada.</p>';
            return;
        }
        pendencias.sort((a, b) => (a.status === 'pendente' ? -1 : 1) - (b.status === 'pendente' ? -1 : 1) || new Date(b.data_vencimento) - new Date(a.data_vencimento));
        list.innerHTML = pendencias.map(p => {
            const vencimento = new Date(p.data_vencimento + 'T00:00:00').toLocaleDateString('pt-BR');
            const isPendente = p.status === 'pendente';
            let iconClass = 'fa-file-invoice-dollar';
            let payFunction = `pagarMensalidadeOnline(event, ${p.id})`;
            if (p.tipo === 'inscricao') {
                iconClass = 'fa-calendar-alt';
                payFunction = `pagarEventoOnline(event, ${p.id})`;
            }
            return `<div class="list-group-item d-flex justify-content-between align-items-center flex-wrap"><div class="me-auto"><h6 class="mb-1"><i class="fas ${iconClass} me-2 text-muted"></i>${p.descricao}</h6><small class="text-muted">Vencimento: ${vencimento} | Valor: R$ ${p.valor.toFixed(2).replace('.', ',')}</small></div><div class="mt-2 mt-md-0">${isPendente && p.valor > 0 ? `<button class="btn btn-sm btn-primary" onclick="${payFunction}"><i class="fas fa-credit-card me-1"></i>Pagar Online</button>` : `<span class="badge bg-${p.status === 'pago' ? 'success' : 'secondary'}">${p.status.charAt(0).toUpperCase() + p.status.slice(1)}</span>`}</div></div>`;
        }).join('');
    } catch (error) {
        ui.showAlert('Não foi possível carregar suas pendências financeiras.');
    }
}

async function handleEventsPage() {
    const list = document.getElementById('events-list');
    try {
        const events = await api.getEvents();
        if (events.length === 0) {
            list.innerHTML = '<p class="text-muted text-center mt-4">Nenhum evento futuro encontrado.</p>';
            return;
        }
        list.innerHTML = events.map(e => {
            const dataEvento = new Date(e.data_evento).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
            return `<div class="card mb-3"><div class="card-body"><div class="d-flex justify-content-between align-items-start"><div><h5 class="card-title">${e.nome}</h5><p class="card-text"><small class="text-muted">${dataEvento}</small></p></div>${e.is_inscrito ? `<button class="btn btn-sm btn-success" disabled><i class="fas fa-check me-1"></i>Inscrito</button>` : (e.status !== 'Planejado' ? `<button class="btn btn-sm btn-secondary" disabled>${e.status}</button>` : `<button class="btn btn-sm btn-primary" onclick="inscreverEmEvento(event, ${e.id})">Inscrever-se</button>`)}</div><p class="card-text mt-2">${e.descricao || ''}</p></div></div>`;
        }).join('');
    } catch (error) {
        ui.showAlert('Não foi possível carregar os eventos.');
    }
}

async function inscreverEmEvento(event, eventoId) {
    const button = event.currentTarget;
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Inscrevendo...';
    try {
        await api.enrollInEvent(eventoId);
        ui.showAlert('Inscrição realizada com sucesso! A pendência já está na sua aba de Pagamentos.', 'success');
        button.classList.remove('btn-primary');
        button.classList.add('btn-success');
        button.innerHTML = '<i class="fas fa-check me-1"></i>Inscrito';
    } catch (error) {
        ui.showAlert(error.message || 'Não foi possível realizar a inscrição.');
        button.disabled = false;
        button.innerHTML = 'Inscrever-se';
    }
}

window.addEventListener('hashchange', router);
window.addEventListener('load', () => {
    initializeStripe();
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/portal/sw.js').then(() => console.log('Service Worker registrado com sucesso.')).catch(err => console.error('Erro no registro do Service Worker:', err));
    }
    document.getElementById('logout-button').addEventListener('click', () => {
        localStorage.removeItem('accessToken');
        window.location.hash = '/login';
    });
    router();
});

