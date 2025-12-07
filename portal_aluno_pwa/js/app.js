const appRoot = document.getElementById('app-root');

// --- CONFIGURAÇÃO DE ROTAS ---
const routes = {
    // Rotas Públicas
    '/login': { page: '/portal/pages/login.html', handler: handleLoginPage, public: true },
    '/login/callback': { handler: handleLoginCallback, public: true },
    '/register': { page: '/portal/pages/register.html', handler: handleRegisterPage, public: true },
    
    // Rotas do Aluno
    '/dashboard': { page: '/portal/pages/dashboard.html', handler: handleDashboardPage },
    '/carteirinha': { page: '/portal/pages/carteirinha.html', handler: handleCarteirinhaPage },
    '/edit-profile': { page: '/portal/pages/edit_profile.html', handler: handleEditProfilePage },
    '/payments': { page: '/portal/pages/payments.html', handler: handlePaymentsPage },
    '/events': { page: '/portal/pages/events.html', handler: handleEventsPage },
    '/beneficios': { page: '/portal/pages/beneficios.html', handler: handleBeneficiosPage },

    // Rotas do Professor (NOVAS)
    '/prof/dashboard': { page: '/portal/pages/prof_dashboard.html', handler: handleProfDashboard },
    '/prof/alunos/novo': { page: '/portal/pages/prof_aluno_novo.html', handler: handleProfAlunoNovo },
    '/prof/matricula': { page: '/portal/pages/prof_matricula.html', handler: handleProfMatricula },
    '/prof/financeiro': { page: '/portal/pages/prof_financeiro.html', handler: handleProfFinanceiro },
};

// --- FUNÇÕES DE NAVEGAÇÃO ---

function updateActiveNav(path) {
    const role = localStorage.getItem('userRole');
    const navContainer = document.getElementById('main-nav');
    
    if (!navContainer) return; // Proteção caso a nav não exista no DOM

    if (role === 'aluno') {
        // Menu do Aluno
        navContainer.innerHTML = `
            <a href="#/dashboard" class="nav__link"><i class="fas fa-user nav__icon"></i><span class="nav__text">Perfil</span></a>
            <a href="#/payments" class="nav__link"><i class="fas fa-file-invoice-dollar nav__icon"></i><span class="nav__text">Pagamentos</span></a>
            <a href="#/events" class="nav__link"><i class="fas fa-calendar-alt nav__icon"></i><span class="nav__text">Eventos</span></a>
            <a href="#/carteirinha" class="nav__link"><i class="fas fa-id-card nav__icon"></i><span class="nav__text">Carteirinha</span></a>
            <a href="#/beneficios" class="nav__link"><i class="fas fa-handshake nav__icon"></i><span class="nav__text">Benefícios</span></a>
        `;
    } else {
        // Menu do Professor/Staff
        navContainer.innerHTML = `
            <a href="#/prof/dashboard" class="nav__link"><i class="fas fa-home nav__icon"></i><span class="nav__text">Início</span></a>
            <a href="#/prof/financeiro" class="nav__link"><i class="fas fa-cash-register nav__icon"></i><span class="nav__text">Caixa</span></a>
            <a href="#/prof/alunos/novo" class="nav__link"><i class="fas fa-user-plus nav__icon"></i><span class="nav__text">Cadastro</span></a>
            <a href="#/prof/matricula" class="nav__link"><i class="fas fa-clipboard-list nav__icon"></i><span class="nav__text">Matrícula</span></a>
        `;
    }

    const navLinks = document.querySelectorAll('.nav__link');
    navLinks.forEach(link => {
        link.classList.remove('nav__link--active');
        if (link.hash && path.startsWith(link.hash.slice(1))) {
            link.classList.add('nav__link--active');
        }
    });
}

const router = async () => {
    // Determina a rota inicial baseada na role se estiver na raiz
    let currentHash = window.location.hash.slice(1).split('?')[0];
    if (!currentHash) {
        const role = localStorage.getItem('userRole');
        currentHash = (role === 'aluno') ? '/dashboard' : (role ? '/prof/dashboard' : '/login');
    }

    updateActiveNav(currentHash);
    
    const route = routes[currentHash] || routes['/login'];
    const token = localStorage.getItem('accessToken');

    const appRootEl = document.getElementById('app-root');
    const bodyEl = document.body;

    // Ajustes de layout para Login vs App
    if (route.public) {
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

    // Proteção de rotas
    if (!route.public && !token) {
        window.location.hash = '/login';
        return;
    }
    
    // Se logado e tentar acessar login, manda pra home
    if (route.public && token && currentHash !== '/login/callback') {
        const role = localStorage.getItem('userRole');
        window.location.hash = (role === 'aluno') ? '/dashboard' : '/prof/dashboard';
        return;
    }

    ui.toggleNav(!route.public);
    
    if (route.page) {
        ui.showLoading(appRoot);
        try {
            const response = await fetch(route.page);
            if (!response.ok) throw new Error("Página não encontrada");
            appRoot.innerHTML = await response.text();
        } catch (error) {
            console.error(error);
            appRoot.innerHTML = `<div class="alert alert-danger m-3">Erro ao carregar a página: ${error.message}. <br>Verifique se o arquivo HTML existe em <b>${route.page}</b></div>`;
        }
    }
    
    if (route.handler) {
        route.handler();
    }
};

// --- HANDLERS COMUNS ---

function handleLoginPage() {
    const form = document.getElementById('login-form');
    // Clona para remover listeners antigos
    const newForm = form.cloneNode(true);
    form.parentNode.replaceChild(newForm, form);

    newForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = e.target.username.value; 
        const password = e.target.password.value;
        const btn = newForm.querySelector('button');
        
        btn.disabled = true; btn.innerText = "Entrando...";

        try {
            const data = await api.login(username, password);
            
            // Permite Aluno, Professor ou Atendente
            const allowedRoles = ['aluno', 'professor', 'atendente', 'administrador'];
            if (!allowedRoles.includes(data.user_info.role)) {
                throw new Error("Tipo de usuário não suportado no Portal.");
            }

            localStorage.setItem('accessToken', data.access_token);
            localStorage.setItem('userRole', data.user_info.role);
            
            // Redirecionamento baseado na role
            if (data.user_info.role === 'aluno') {
                window.location.hash = '/dashboard';
            } else {
                window.location.hash = '/prof/dashboard';
            }
        } catch (error) {
            ui.showAlert(error.message || 'Email ou senha inválidos.');
        } finally {
            btn.disabled = false; btn.innerText = "Entrar";
        }
    });
}

function handleLoginCallback() {
    ui.toggleNav(false);
    appRoot.innerHTML = '<p class="text-center mt-5">Autenticando...</p>';
    const params = new URLSearchParams(window.location.hash.split('?')[1]);
    const token = params.get('token');
    if (token) {
        // Precisaríamos decodificar o token ou chamar /me para saber a role
        // Por simplificação, vamos chamar /me
        localStorage.setItem('accessToken', token);
        api.getProfile().then(user => {
             localStorage.setItem('userRole', user.role); // Assumindo que getProfile retorna a role
             if (user.role === 'aluno') window.location.hash = '/dashboard';
             else window.location.hash = '/prof/dashboard';
        }).catch(() => window.location.hash = '/login');
    } else {
        window.location.hash = '/login';
    }
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

// --- HANDLERS DO ALUNO ---

async function handleDashboardPage() {
    try {
        const profile = await api.getProfile();
        document.getElementById('aluno-nome').innerText = profile.nome;
        document.getElementById('aluno-email').innerText = profile.email;
        document.getElementById('profile-picture').src = profile.foto || '/portal/images/icone.png';
        document.getElementById('aluno-telefone').innerText = profile.telefone || '-';
        document.getElementById('aluno-nascimento').innerText = profile.data_nascimento || '-';

        const matriculasContainer = document.getElementById('matriculas-container');
        try {
            const matriculas = await api.getMatriculas();
            if (matriculas.length > 0) {
                matriculasContainer.innerHTML = `<ul class="list-group list-group-flush">${matriculas.map(m => `<li class="list-group-item"><span>${m.turma.nome}</span></li>`).join('')}</ul>`;
            } else {
                matriculasContainer.innerHTML = '<p class="text-muted small p-2">Sem matrículas ativas.</p>';
            }
        } catch (e) { matriculasContainer.innerHTML = '<p class="text-danger small">Erro ao carregar.</p>'; }
    } catch (error) {
        ui.showAlert('Erro ao carregar perfil.');
    }
}

async function handleCarteirinhaPage() {
    try {
        const profile = await api.getProfile();
        document.getElementById('aluno-nome').innerText = profile.nome;
        document.getElementById('aluno-foto').src = profile.foto || '/portal/images/default-avatar.png';
        document.getElementById('aluno-matricula').innerText = 1000 + profile.id;
        document.getElementById('aluno-email').innerText = profile.email || '-';
        document.getElementById('aluno-telefone').innerText = profile.telefone || '-';
        document.getElementById('aluno-nascimento').innerText = profile.data_nascimento || '-';
        const statusEl = document.getElementById('aluno-status');
        statusEl.innerText = profile.status_geral === "Ativo" ? "Aluno Ativo" : "Inativo";
        statusEl.className = profile.status_geral === "Ativo" ? "badge bg-success" : "badge bg-secondary";
    } catch (error) {}
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
    
    if (fotoInput) {
        fotoInput.addEventListener('change', () => {
            const file = fotoInput.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (e) => { fotoPreview.src = e.target.result; };
                reader.readAsDataURL(file);
            }
        });
    }

    // --- SALVAR PERFIL ---
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        // Procura botão dentro do form ou pelo ID específico
        let button = form.querySelector('button[type="submit"]');
        if (!button) button = document.getElementById('btn-save-profile');
        
        if (button) {
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Salvando...';
        }
        
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
        
        if (fotoInput && fotoInput.files[0]) {
            formData.append('foto', fotoInput.files[0]);
        }
        
        try {
            await api.updateProfile(formData);
            ui.showAlert('Perfil atualizado com sucesso!', 'success');
            setTimeout(() => { window.location.hash = '/dashboard'; }, 1500);
        } catch (error) {
            ui.showAlert(error.message || 'Não foi possível salvar as alterações.', 'danger');
        } finally {
            if (button) {
                button.disabled = false;
                button.innerHTML = 'Salvar Alterações';
            }
        }
    });

    // --- LÓGICA DE TOGGLE DA SENHA (O QUE FALTAVA) ---
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
            const button = passwordForm.querySelector('button[type="submit"]');
            
            const current_password = document.getElementById('current_password').value;
            const new_password = document.getElementById('new_password').value;
            const confirm_password = document.getElementById('confirm_password').value;

            if (new_password !== confirm_password) {
                ui.showAlert('A nova senha e a confirmação não conferem.', 'danger');
                return;
            }

            if (button) {
                button.disabled = true;
                button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Atualizando...';
            }

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
                if (button) {
                    button.disabled = false;
                    button.innerHTML = 'Confirmar Alteração';
                }
            }
        });
    }
}

async function handlePaymentsPage() {
    const list = document.getElementById('payments-list');
    try {
        const pendencias = await api.getPayments();
        if (!pendencias || pendencias.length === 0) {
            list.innerHTML = '<p class="text-muted text-center mt-4">Nenhuma pendência.</p>';
            return;
        }
        list.innerHTML = pendencias.map(p => {
            const vencimento = new Date(p.data_vencimento + 'T00:00:00').toLocaleDateString('pt-BR');
            const isPendente = p.status === 'pendente';
            let payFunction = p.tipo === 'inscricao' ? `pagarEventoOnline(event, ${p.id})` : `pagarMensalidadeOnline(event, ${p.id})`;
            let icon = p.tipo === 'inscricao' ? 'fa-calendar-check' : 'fa-file-invoice-dollar';

            return `
            <div class="list-group-item d-flex justify-content-between align-items-center flex-wrap py-3">
                <div class="me-auto">
                    <div class="fw-bold"><i class="fas ${icon} me-2 text-muted"></i>${p.descricao}</div>
                    <div class="small text-muted">Venc: ${vencimento} • Valor: <strong>R$ ${p.valor.toFixed(2)}</strong></div>
                </div>
                <div class="mt-2 mt-md-0">
                    ${isPendente && p.valor > 0 ? 
                        `<button class="btn btn-sm btn-primary shadow-sm" onclick="${payFunction}"><i class="fas fa-qrcode me-1"></i> Pagar Pix</button>` : 
                        `<span class="badge bg-${p.status === 'pago' ? 'success' : 'secondary'} rounded-pill">${p.status}</span>`
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
        if (!events || events.length === 0) {
            list.innerHTML = '<p class="text-muted text-center mt-4">Nenhum evento disponível.</p>';
            return;
        }
        list.innerHTML = events.map(e => {
             const data = new Date(e.data_evento).toLocaleDateString('pt-BR');
             const hora = new Date(e.data_evento).toLocaleTimeString('pt-BR', {hour: '2-digit', minute:'2-digit'});
             
             return `
            <div class="card mb-3 shadow-sm border-0">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h5 class="card-title fw-bold text-primary mb-1">${e.nome}</h5>
                            <small class="text-muted"><i class="far fa-calendar me-1"></i>${data} às ${hora}</small>
                        </div>
                        <div>
                             ${e.is_inscrito ? 
                                `<span class="badge bg-success"><i class="fas fa-check me-1"></i>Inscrito</span>` : 
                                (e.status === 'Ativo' ? `<button class="btn btn-sm btn-primary" onclick="inscreverEmEvento(event, ${e.id})">Inscrever</button>` : `<span class="badge bg-secondary">${e.status}</span>`)
                             }
                        </div>
                    </div>
                    <p class="card-text mt-2 small text-secondary">${e.descricao || 'Sem descrição.'}</p>
                    <div class="small text-muted">Valor: <strong>R$ ${e.valor_inscricao.toFixed(2)}</strong></div>
                </div>
            </div>`;
        }).join('');
    } catch (error) { console.error(error); }
}

async function handleBeneficiosPage() {
    const list = document.getElementById('partners-list');
    const mensagemWhatsapp = encodeURIComponent("Sou da Academia AZE Studio e vim pelo clube de descontos para parceiros.");
    const partners = [
         { logo: '/portal/images/iron.png', nome: 'Centro de Treinamento Iron Gym', desconto: '25% de desconto na Mensalidade.', whatsapp: '5532985062330' },
         { logo: '/portal/images/bull.png', nome: 'Arthur Carvalho Duarte - ARQUITETURA', desconto: 'Desconto de 20% em seu projeto.', whatsapp: '5532988810989' },
         { logo: '/portal/images/alexandria.png', nome: 'Alexandria Hamburgueria', desconto: '20% de desconto em todos os Rodízios.', whatsapp: '5532933003620' },
         { logo: '/portal/images/lucasStarck.png', nome: 'Lucas Starck - Nutricionista', desconto: 'Consulta com 50% de desconto.', whatsapp: '5532998180941' },
         { logo: '/portal/images/casadoanimal.png', nome: 'Casa do Animal Porto', desconto: '25% compra de animais, 20% para Acessórios Pet', whatsapp: '5532998641939' },
         { logo: '/portal/images/mamaefazaFesta.png', nome: 'Mamãe Faz a Festa', desconto: '20% de desconto em todos serviços.', whatsapp: '5532988992094' },
         { logo: '/portal/images/farmaciabompreco.png', nome: 'Farmácia Bom Preço', desconto: '20% compra de medicamentos.', whatsapp: '5532988015391' },
         { logo: '/portal/images/studiosbanni.png', nome: 'Studio Sbanni', desconto: '20% de desconto em todos serviços.', whatsapp: '5532999553342' },
         { logo: '/portal/images/abrace.png', nome: 'Abrace Studio de Pilates', desconto: '10% de desconto na Mensalidade.', whatsapp: '5532988758320' },
    ];

    list.innerHTML = partners.map(p => `
        <div class="col-6 col-md-4 mb-4">
            <div class="card h-100 text-center shadow-sm border-0 p-2">
                <img src="${p.logo}" class="card-img-top mx-auto mt-2" alt="${p.nome}" style="max-height: 60px; width: auto; max-width: 100%; object-fit: contain;">
                <div class="card-body d-flex flex-column p-2">
                    <h6 class="card-title small fw-bold mb-1">${p.nome}</h6>
                    <p class="card-text x-small text-muted mb-2" style="font-size: 0.75rem;">${p.desconto}</p>
                    ${p.whatsapp ? `<a href="https://wa.me/${p.whatsapp}?text=${mensagemWhatsapp}" target="_blank" class="btn btn-success btn-sm mt-auto py-0" style="font-size: 0.75rem;"><i class="fab fa-whatsapp"></i> Contato</a>` : ''}
                </div>
            </div>
        </div>
    `).join('');
}

// --- HANDLERS DO PROFESSOR (NOVOS) ---

async function handleProfDashboard() {
    // A página HTML já tem os links estáticos, não precisa carregar dados
    console.log("Dashboard do Professor carregado.");
}

async function handleProfAlunoNovo() {
    const form = document.getElementById('form-novo-aluno');
    form.onsubmit = async (e) => {
        e.preventDefault();
        const btn = form.querySelector('button');
        const originalText = btn.innerHTML;
        btn.disabled = true; btn.innerHTML = 'Salvando...';

        const formData = new FormData(form);
        
        try {
            // Usa a rota principal de alunos (reutilização)
            await api.request('/alunos', 'POST', formData, true); 
            ui.showAlert('Aluno cadastrado com sucesso!', 'success');
            form.reset();
        } catch (err) {
            ui.showAlert(err.message, 'danger');
        } finally {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    };
}

async function handleProfFinanceiro() {
    const inputBusca = document.getElementById('busca-aluno');
    const btnBuscar = document.getElementById('btn-buscar');
    const lista = document.getElementById('lista-mensalidades');

    const carregar = async (termo = '') => {
        lista.innerHTML = '<div class="text-center py-3"><div class="spinner-border text-primary"></div></div>';
        try {
            const contas = await api.request(`/portal-professor/mensalidades-pendentes?busca=${termo}`);
            
            if (contas.length === 0) {
                lista.innerHTML = '<p class="text-muted text-center">Nenhuma mensalidade pendente encontrada.</p>';
                return;
            }

            lista.innerHTML = contas.map(c => `
                <div class="list-group-item p-3">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <h6 class="mb-0 fw-bold">${c.aluno.nome}</h6>
                        <span class="badge bg-warning text-dark">Pendente</span>
                    </div>
                    <div class="small text-muted mb-2">
                        Venc: ${new Date(c.data_vencimento).toLocaleDateString('pt-BR')} <br>
                        Plano: ${c.plano.nome}
                    </div>
                    <div class="d-flex justify-content-between align-items-center">
                        <h5 class="mb-0 text-primary">R$ ${c.valor.toFixed(2)}</h5>
                        <button class="btn btn-success btn-sm" onclick="receberDinheiro(${c.id}, '${c.aluno.nome}', ${c.valor})">
                            <i class="fas fa-hand-holding-usd me-1"></i> Receber
                        </button>
                    </div>
                </div>
            `).join('');
        } catch (err) {
            lista.innerHTML = '<p class="text-danger text-center">Erro ao carregar.</p>';
        }
    };

    btnBuscar.onclick = () => carregar(inputBusca.value);
    // Carrega inicial
    carregar();
}

async function handleProfMatricula() {
    // Referências aos elementos
    const searchInput = document.getElementById('search-aluno');
    const hiddenIdInput = document.getElementById('selected-aluno-id');
    const resultsContainer = document.getElementById('results-aluno');
    
    const selectTurma = document.getElementById('select-turma');
    const selectPlano = document.getElementById('select-plano');
    const form = document.getElementById('form-matricula');

    // 1. Carrega apenas Turmas e Planos (removemos o carregamento de Alunos aqui)
    try {
        const [turmas, planos] = await Promise.all([
            api.request('/turmas'),
            api.request('/planos')
        ]);

        selectTurma.innerHTML += turmas.map(t => `<option value="${t.id}">${t.nome} (${t.modalidade})</option>`).join('');
        selectPlano.innerHTML += planos.map(p => `<option value="${p.id}">${p.nome} - R$ ${p.valor}</option>`).join('');
    } catch (e) {
        ui.showAlert('Erro ao carregar listas de Turmas/Planos.', 'danger');
    }

    // 2. Lógica de Busca de Aluno (Ao digitar)
    let debounceTimer;
    searchInput.addEventListener('input', (e) => {
        const termo = e.target.value;
        
        clearTimeout(debounceTimer);
        hiddenIdInput.value = ''; // Reseta o ID se mudar o texto
        
        if (termo.length < 3) {
            resultsContainer.style.display = 'none';
            return;
        }

        // Aguarda 300ms para não chamar a API a cada letra
        debounceTimer = setTimeout(async () => {
            resultsContainer.innerHTML = '<div class="list-group-item text-muted"><small>Buscando...</small></div>';
            resultsContainer.style.display = 'block';

            try {
                // Busca na API filtrando por nome
                const data = await api.request(`/alunos?nome=${termo}&limit=5`);
                const alunos = data.alunos || [];

                if (alunos.length === 0) {
                    resultsContainer.innerHTML = '<div class="list-group-item text-muted"><small>Nenhum aluno encontrado.</small></div>';
                } else {
                    resultsContainer.innerHTML = alunos.map(a => `
                        <a href="#" class="list-group-item list-group-item-action" onclick="selecionarAluno(${a.id}, '${a.nome}')">
                            <div class="fw-bold">${a.nome}</div>
                            <small class="text-muted">CPF: ${a.cpf || '---'}</small>
                        </a>
                    `).join('');
                }
            } catch (err) {
                resultsContainer.style.display = 'none';
            }
        }, 300);
    });

    // Função global para selecionar o aluno da lista
    window.selecionarAluno = (id, nome) => {
        searchInput.value = nome;       // Mostra o nome
        hiddenIdInput.value = id;       // Guarda o ID
        resultsContainer.style.display = 'none'; // Esconde a lista
        if(event) event.preventDefault();
    };

    // Fecha a lista se clicar fora
    document.addEventListener('click', (e) => {
        if (searchInput && resultsContainer && !searchInput.contains(e.target) && !resultsContainer.contains(e.target)) {
            resultsContainer.style.display = 'none';
        }
    });

    // 3. Envio do Formulário
    form.onsubmit = async (e) => {
        e.preventDefault();
        
        if (!hiddenIdInput.value) {
            ui.showAlert('Por favor, pesquise e selecione um aluno da lista.', 'warning');
            searchInput.focus();
            return;
        }

        const btn = form.querySelector('button');
        btn.disabled = true; btn.innerHTML = 'Matriculando...';

        const data = {
            aluno_id: parseInt(hiddenIdInput.value),
            turma_id: parseInt(selectTurma.value),
            plano_id: parseInt(selectPlano.value)
        };

        try {
            await api.request('/matriculas', 'POST', data);
            ui.showAlert('Matrícula realizada com sucesso!', 'success');
            form.reset();
            hiddenIdInput.value = '';
        } catch (err) {
            ui.showAlert(err.message, 'danger');
        } finally {
            btn.disabled = false; btn.innerHTML = '<i class="fas fa-check me-2"></i> Realizar Matrícula';
        }
    };
}

// --- FUNÇÕES GLOBAIS DE AÇÃO ---

window.receberDinheiro = async (id, nome, valor) => {
    if(!confirm(`Confirmar recebimento de R$ ${valor.toFixed(2)} de ${nome} em DINHEIRO?`)) return;

    try {
        await api.request(`/portal-professor/mensalidades/${id}/receber-dinheiro`, 'POST');
        alert('Pagamento recebido com sucesso!'); // Alert simples para confirmação
        // Recarrega a lista chamando o handler novamente se o elemento existir
        const btnBuscar = document.getElementById('btn-buscar');
        if(btnBuscar) btnBuscar.click();
    } catch (err) {
        alert('Erro: ' + err.message);
    }
};

async function inscreverEmEvento(event, eventoId) {
    const btn = event.currentTarget;
    btn.disabled = true; btn.innerHTML = '...';
    try {
        await api.enrollInEvent(eventoId);
        ui.showAlert('Inscrição realizada! Verifique a aba Pagamentos.', 'success');
        handleEventsPage(); // Recarrega
    } catch (error) {
        ui.showAlert(error.message || 'Erro ao inscrever.');
        btn.disabled = false; btn.innerHTML = 'Inscrever';
    }
}

// Lógica de Pix (Modal e Polling)
let pixPollingInterval = null;

async function exibirModalPix(endpoint, itemType, itemId) {
    if (pixPollingInterval) clearInterval(pixPollingInterval);

    if (!document.getElementById('pixModal')) {
        const modalHtml = `
        <div class="modal fade" id="pixModal" tabindex="-1" aria-hidden="true" data-bs-backdrop="static">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title"><i class="fas fa-qrcode text-success me-2"></i>Pagamento via Pix</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body text-center" id="pixModalBody"></div>
                    <div class="modal-footer justify-content-center">
                        <button type="button" class="btn btn-outline-secondary btn-sm" data-bs-dismiss="modal">Fechar</button>
                    </div>
                </div>
            </div>
        </div>`;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        document.getElementById('pixModal').addEventListener('hidden.bs.modal', () => {
            if (pixPollingInterval) clearInterval(pixPollingInterval);
        });
    }

    const pixModalElement = document.getElementById('pixModal');
    const pixModal = new bootstrap.Modal(pixModalElement);
    const modalBody = document.getElementById('pixModalBody');
    
    modalBody.innerHTML = `<div class="spinner-border text-primary" role="status"></div><p class="mt-2">Gerando código Pix...</p>`;
    pixModal.show();

    try {
        const data = await api.request(endpoint, 'POST');

        modalBody.innerHTML = `
            <p class="text-muted mb-3 small">Escaneie o QR Code abaixo:</p>
            <img src="data:image/jpeg;base64,${data.qr_code_base64}" class="img-fluid border rounded mb-3 shadow-sm" style="max-width: 220px;">
            <div class="d-grid gap-2 mb-3">
                <div class="input-group">
                    <input type="text" class="form-control form-control-sm" value="${data.qr_code}" id="pixCopiaCola" readonly>
                    <button class="btn btn-primary btn-sm" type="button" onclick="copiarPix()">
                        <i class="fas fa-copy"></i>
                    </button>
                </div>
                <small class="text-muted" style="font-size: 0.75rem;">Ou copie o código acima</small>
            </div>
            <div class="alert alert-light border d-flex align-items-center justify-content-center gap-2" role="alert">
                <div class="spinner-border spinner-border-sm text-secondary" role="status"></div>
                <span class="small text-muted">Aguardando pagamento...</span>
            </div>
        `;

        if (itemType && itemId) {
            pixPollingInterval = setInterval(async () => {
                try {
                    const statusRes = await api.request(`/pagamentos/status/${itemType}/${itemId}`);
                    if (statusRes.status === 'pago') {
                        clearInterval(pixPollingInterval);
                        modalBody.innerHTML = `
                            <div class="py-5 animate-success">
                                <div class="mb-3"><i class="fas fa-check-circle text-success" style="font-size: 5rem;"></i></div>
                                <h4 class="text-success fw-bold">Pagamento Confirmado!</h4>
                            </div>
                        `;
                        setTimeout(() => {
                            pixModal.hide();
                            if (window.location.hash.includes('payments')) handlePaymentsPage();
                            else if (window.location.hash.includes('events')) handleEventsPage();
                            ui.showAlert('Pagamento realizado!', 'success');
                        }, 2500);
                    }
                } catch (err) { console.error(err); }
            }, 3000);
        }

    } catch (error) {
        modalBody.innerHTML = `<div class="text-danger"><i class="fas fa-exclamation-circle fa-2x"></i><p>${error.message}</p></div>`;
    }
}

window.copiarPix = function() {
    const copyText = document.getElementById("pixCopiaCola");
    copyText.select();
    copyText.setSelectionRange(0, 99999);
    navigator.clipboard.writeText(copyText.value);
    alert("Código copiado!");
}

async function pagarMensalidadeOnline(event, id) { await exibirModalPix(`/pagamentos/pix/mensalidade/${id}`, 'mensalidade', id); }
async function pagarEventoOnline(event, id) { await exibirModalPix(`/pagamentos/pix/inscricao/${id}`, 'inscricao', id); }

// Inicialização
window.addEventListener('hashchange', router);
window.addEventListener('load', () => {
    if ('serviceWorker' in navigator) navigator.serviceWorker.register('/portal/sw.js').catch(console.error);
    
    document.getElementById('logout-button').addEventListener('click', () => {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('userRole');
        window.location.hash = '/login';
    });
    
    router();
});