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

// (Adicione esta função no início do arquivo, junto com as outras funções)
function updateActiveNav(path) {
    const navLinks = document.querySelectorAll('.nav__link');
    navLinks.forEach(link => {
        link.classList.remove('nav__link--active');
        if (link.hash && path.startsWith(link.hash.slice(1))) {
            link.classList.add('nav__link--active');
        }
    });
}

// Em portal_aluno_pwa/js/app.js

const router = async () => {
    // --- LÓGICA DE ALERTA DE PAGAMENTO (EXISTENTE) ---
    const currentHash = window.location.hash;
    const urlParams = new URLSearchParams(currentHash.split('?')[1] || '');
    
    if (urlParams.has('payment')) {
        const paymentStatus = urlParams.get('payment');
        const cleanPath = currentHash.split('?')[0];
        
        window.history.replaceState(null, null, window.location.pathname + cleanPath);
        
        setTimeout(() => {
            if (paymentStatus === 'success') {
                ui.showAlert('Pagamento realizado com sucesso!', 'success');
            } else if (paymentStatus === 'canceled') {
                ui.showAlert('O pagamento foi cancelado.', 'info');
            }
        }, 500);
    }
    
    const path = (window.location.hash.slice(1).split('?')[0] || '/dashboard');
    
    // ATUALIZA O LINK ATIVO NA NAV
    updateActiveNav(path); 
    
    const route = routes[path] || routes['/dashboard'];
    const token = localStorage.getItem('accessToken');

    // --- LÓGICA DE LAYOUT CORRIGIDA (FULL SCREEN) ---
    const appRootEl = document.getElementById('app-root');
    const bodyEl = document.body;

    if (path === '/login' || path === '/login/callback' || path === '/register') {
        // 1. ATIVA O MODO DE TELA CHEIA (LOGIN/REGISTER)
        bodyEl.classList.add('login-active');
        bodyEl.classList.remove('nav-active');
        
        // CORREÇÃO: Remove o container restritivo e paddings do Bootstrap
        // Isso remove as "beiradas brancas" laterais
        appRootEl.classList.remove('container', 'py-4'); 
        
        // Adiciona largura total e remove qualquer padding residual
        appRootEl.classList.add('w-100', 'p-0'); 
        
    } else {
        // 2. ATIVA O MODO DE NAVEGAÇÃO (INTERNO)
        bodyEl.classList.remove('login-active');
        bodyEl.classList.add('nav-active');
        
        // Restaura o container e paddings para as telas internas
        // Isso centraliza o conteúdo do dashboard corretamente
        appRootEl.classList.remove('w-100', 'p-0');
        appRootEl.classList.add('container', 'py-4'); 
    }
    // --- FIM DA LÓGICA DE LAYOUT ---

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

// --- VARIÁVEIS GLOBAIS DE PAGAMENTO ---

let stripe;
let currentPaymentProvider = 'stripe'; // Valor padrão de segurança


// Função unificada para abrir o Modal do PIX
async function exibirModalPix(endpoint) {
    // 1. Cria o HTML do Modal dinamicamente (se não existir)
    if (!document.getElementById('pixModal')) {
        const modalHtml = `
        <div class="modal fade" id="pixModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title"><i class="brands fa-pix text-success me-2"></i>Pagamento via PIX</h5>
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
        modalBody.innerHTML = `<div class="alert alert-danger">Erro ao gerar PIX: ${error.message}</div>`;
    }
}

// Função auxiliar para copiar
window.copiarPix = function() {
    const copyText = document.getElementById("pixCopiaCola");
    copyText.select();
    copyText.setSelectionRange(0, 99999);
    navigator.clipboard.writeText(copyText.value);
    alert("Código PIX copiado!");
}

// 1. NOVA FUNÇÃO DE INICIALIZAÇÃO (Substitui a initializeStripe)
async function initializePaymentSystem() {
    try {
        // Pergunta ao backend qual a configuração atual
        // A rota /pagamentos/config retorna { provider: 'mercadopago' ou 'stripe', stripePublicKey: ... }
        const config = await api.request('/pagamentos/config', 'GET', null, false, false);
        
        currentPaymentProvider = config.provider; 
        console.log(`Sistema de pagamento ativo: ${currentPaymentProvider.toUpperCase()}`);

        // Se for Stripe, precisamos inicializar o SDK com a chave pública
        if (currentPaymentProvider === 'stripe' && config.stripePublicKey) {
             stripe = Stripe(config.stripePublicKey);
        }
        // Se for Mercado Pago, a inicialização é feita no momento do redirecionamento

    } catch (error) {
        console.error("Falha ao inicializar sistema de pagamentos:", error);
    }
}

// 2. FUNÇÃO DE PAGAR MENSALIDADE (Híbrida)
async function pagarMensalidadeOnline(event, mensalidadeId) {
    // Usamos a nova rota de PIX Transparente
    await exibirModalPix(`/pagamentos/pix/mensalidade/${mensalidadeId}`);
}

async function pagarEventoOnline(event, inscricaoId) {
    // Usamos a nova rota de PIX Transparente
    await exibirModalPix(`/pagamentos/pix/inscricao/${inscricaoId}`);
}

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
        const username = e.target.username.value; // Variável renomeada
        const password = e.target.password.value;
        try {
            const data = await api.login(username, password);
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
        const profile = await api.getProfile(); // Agora a API retorna o status_geral
        
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
        document.getElementById('aluno-nascimento').innerText = profile.data_nascimento 
            ? new Date(profile.data_nascimento + 'T00:00:00').toLocaleDateString('pt-BR') 
            : '--/--/----';

        // --- LÓGICA PARA EXIBIR O STATUS ---
        const statusBadge = document.getElementById('aluno-status');
        if (profile.status_geral === "Ativo") {
            statusBadge.textContent = "Aluno Ativo";
            statusBadge.classList.add('bg-success');
            statusBadge.classList.remove('bg-secondary');
        } else {
            statusBadge.textContent = "Aluno Inativo";
            statusBadge.classList.add('bg-secondary');
            statusBadge.classList.remove('bg-success');
        }
        // --- FIM DA LÓGICA ---

    } catch (error) {
        ui.showAlert('Não foi possível carregar os dados da sua carteirinha.');
        // Limpa o status em caso de erro
        const statusBadge = document.getElementById('aluno-status');
        if(statusBadge) {
             statusBadge.textContent = "Erro ao carregar";
             statusBadge.classList.add('bg-danger');
        }
    }
}

async function handleEditProfilePage() {
    const form = document.getElementById('edit-profile-form');
    
    // Elementos do formulário de perfil
    const nomeInput = document.getElementById('nome');
    const emailInput = document.getElementById('email');
    const cpfInput = document.getElementById('cpf');
    const telefoneInput = document.getElementById('telefone');
    const dataNascimentoInput = document.getElementById('data_nascimento');
    const enderecoInput = document.getElementById('endereco');
    const observacoesInput = document.getElementById('observacoes');
    const fotoInput = document.getElementById('foto');
    const fotoPreview = document.getElementById('foto-preview');
    
    // Elementos do responsável
    const dadosResponsavelDiv = document.getElementById('dados-responsavel');
    const nomeResponsavelInput = document.getElementById('nome_responsavel');
    const cpfResponsavelInput = document.getElementById('cpf_responsavel');
    const parentescoResponsavelInput = document.getElementById('parentesco_responsavel');
    const telefoneResponsavelInput = document.getElementById('telefone_responsavel');
    const emailResponsavelInput = document.getElementById('email_responsavel');
    const camposResponsavel = dadosResponsavelDiv.querySelectorAll('input');

    // --- LÓGICA DE RESPONSÁVEL (MENOR DE 18) ---
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
        } else {
            dadosResponsavelDiv.style.display = 'none';
            camposResponsavel.forEach(input => input.required = false);
        }
    }

    // --- CARREGAR DADOS DO PERFIL ---
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
        
        // Dados do responsável
        nomeResponsavelInput.value = profile.nome_responsavel || '';
        cpfResponsavelInput.value = profile.cpf_responsavel || '';
        parentescoResponsavelInput.value = profile.parentesco_responsavel || '';
        telefoneResponsavelInput.value = profile.telefone_responsavel || '';
        emailResponsavelInput.value = profile.email_responsavel || '';
        
        toggleResponsavelFields();
    } catch (error) {
        ui.showAlert('Erro ao carregar seus dados para edição.');
    }

    // Eventos de mudança
    dataNascimentoInput.addEventListener('change', toggleResponsavelFields);
    
    fotoInput.addEventListener('change', () => {
        const file = fotoInput.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => { fotoPreview.src = e.target.result; };
            reader.readAsDataURL(file);
        }
    });

    // --- SALVAR PERFIL ---
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const button = document.getElementById('btn-save-profile');
        
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Salvando...';
        
        const formData = new FormData();
        formData.append('nome', nomeInput.value);
        formData.append('cpf', cpfInput.value);
        formData.append('telefone', telefoneInput.value);
        formData.append('data_nascimento', dataNascimentoInput.value);
        formData.append('endereco', enderecoInput.value);
        formData.append('observacoes', observacoesInput.value);
        
        // Dados responsável
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
            ui.showAlert('Perfil atualizado com sucesso!', 'success');
            setTimeout(() => { window.location.hash = '/dashboard'; }, 1500);
        } catch (error) {
            ui.showAlert(error.message || 'Não foi possível salvar as alterações.', 'danger');
            button.disabled = false;
            button.innerHTML = 'Salvar Alterações';
        }
    });

    // --- CÓDIGO QUE FALTAVA: LÓGICA DE ALTERAR SENHA (TOGGLE) ---
    const btnShowPassword = document.getElementById('btn-show-password-form');
    const passwordSection = document.getElementById('password-section');
    const btnCancelPassword = document.getElementById('btn-cancel-password');
    const toggleContainer = document.getElementById('toggle-password-container');

    if (btnShowPassword && passwordSection && toggleContainer) {
        btnShowPassword.addEventListener('click', () => {
            passwordSection.style.display = 'block';
            toggleContainer.style.display = 'none';
        });

        if (btnCancelPassword) {
            btnCancelPassword.addEventListener('click', () => {
                passwordSection.style.display = 'none';
                toggleContainer.style.display = 'block';
                const pwdForm = document.getElementById('update-password-form');
                if(pwdForm) pwdForm.reset(); 
            });
        }
    }

    // --- SALVAR SENHA ---
    const passwordForm = document.getElementById('update-password-form');
    if (passwordForm) {
        passwordForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            // Procura o botão de submit dentro deste formulário específico
            const button = passwordForm.querySelector('button[type="submit"]');
            
            const current_password = document.getElementById('current_password').value;
            const new_password = document.getElementById('new_password').value;
            const confirm_password = document.getElementById('confirm_password').value;

            if (new_password !== confirm_password) {
                ui.showAlert('A nova senha e a confirmação não conferem.', 'danger');
                return;
            }

            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Atualizando...';

            try {
                await api.updatePassword(current_password, new_password);
                ui.showAlert('Senha atualizada com sucesso!', 'success');
                passwordForm.reset();
                // Esconde o formulário após sucesso
                if (passwordSection && toggleContainer) {
                    passwordSection.style.display = 'none';
                    toggleContainer.style.display = 'block';
                }
            } catch (error) {
                ui.showAlert(error.message || 'Erro ao atualizar senha.', 'danger');
            } finally {
                button.disabled = false;
                button.innerHTML = 'Confirmar Alteração';
            }
        });
    }
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

// Nova função para destacar o link ativo na navegação
function updateActiveNav(path) {
    const navLinks = document.querySelectorAll('.nav__link');
    navLinks.forEach(link => {
        // Limpa a classe de todos
        link.classList.remove('nav__link--active');

        // Adiciona a classe se o href do link corresponder ao início do path
        // Ex: link.hash '#/dashboard' corresponde ao path '/dashboard'
        if (link.hash && path.startsWith(link.hash.slice(1))) {
            link.classList.add('nav__link--active');
        }
    });
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


// NOVA FUNÇÃO PARA A PÁGINA DE BENEFÍCIOS
async function handleBeneficiosPage() {
    const list = document.getElementById('partners-list');

    // --- EDITE OS DADOS AQUI, ADICIONANDO O CAMPO 'whatsapp' ---
    const partners = [
         {
            logo: '/portal/images/iron.png', // <-- Outro logo
            nome: 'Centro de Treinamento Iron Gym',
            desconto: '20% de desconto na Mensalidade.',
            whatsapp: '5532985062330' // <-- Outro número
        },
        {
            logo: '/portal/images/bull.png', // <-- Outro logo
            nome: 'Arthur Carvalho Duarte - ARQUITETURA E URBANISMO',
            desconto: 'Desconto de 20% em seu projeto.',
            whatsapp: '5532988810989' // <-- Outro número
        },
        {
            logo: '/portal/images/alexandria.png', // <-- Coloque o caminho correto para o logo
            nome: 'Alexandria Hamburgueria',             // <-- Nome do parceiro
            desconto: '20% de desconto em todos os Rodízios.', // <-- Descrição
            whatsapp: '5532933003620' // <-- NÚMERO DE WHATSAPP (somente números, com código do país e DDD)
        },
        {
            logo: '/portal/images/lucasStarck.png', // <-- Outro logo
            nome: 'Lucas Starck - Nutricionista Esportivo',
            desconto: 'Consulta com 50% de desconto para alunos ativos.',
            whatsapp: '5532998180941' // <-- Outro número
        },
       
        // {
        //     logo: '/portal/images/logo_parceiro_b.jpg', // <-- Outro logo
        //     nome: 'Empresa Parceira B',
        //     desconto: 'Outro benefício, como primeira consulta gratuita.',
        //     whatsapp: '5532988887777' // <-- Outro número
        // },
    ];
    // --- FIM DA EDIÇÃO ---

    if (partners.length === 0) {
        list.innerHTML = '<p class="text-muted text-center mt-4">Nenhum parceiro cadastrado no momento.</p>';
        return;
    }

    // --- CÓDIGO HTML ATUALIZADO PARA INCLUIR O BOTÃO ---
    list.innerHTML = partners.map(p => {
        // Prepara a mensagem para a URL (codifica caracteres especiais)
        const mensagemWhatsapp = encodeURIComponent("Sou da Academia AZE Studio e vim pelo clube de descontos para parceiros.");
        // Monta o link do WhatsApp apenas se o número existir
        const whatsappLink = p.whatsapp ? `https://wa.me/${p.whatsapp}?text=${mensagemWhatsapp}` : null;

        return `
        <div class="col-md-6 col-lg-4 mb-4">
            <div class="card h-100 text-center shadow-sm">
                <img src="${p.logo}" class="card-img-top mx-auto mt-3" alt="Logo ${p.nome}" style="max-height: 80px; width: auto; max-width: 150px; object-fit: contain;">
                <div class="card-body d-flex flex-column">
                    <h5 class="card-title">${p.nome}</h5>
                    <p class="card-text">${p.desconto}</p>
                    ${whatsappLink ? `
                    <a href="${whatsappLink}" target="_blank" class="btn btn-success mt-auto">
                        <i class="fab fa-whatsapp me-1"></i> Ir para o Parceiro
                    </a>
                    ` : ''}
                </div>
            </div>
        </div>
        `;
    }).join('');
    // --- FIM DA ATUALIZAÇÃO DO HTML ---
}


window.addEventListener('hashchange', router);
window.addEventListener('load', () => {
    // Substituímos initializeStripe() por initializePaymentSystem()
    initializePaymentSystem();
    
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/portal/sw.js')
            .then(() => console.log('Service Worker registrado.'))
            .catch(err => console.error('Erro SW:', err));
    }
    document.getElementById('logout-button').addEventListener('click', () => {
        localStorage.removeItem('accessToken');
        window.location.hash = '/login';
    });
    router();
});