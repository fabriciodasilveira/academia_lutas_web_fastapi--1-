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

// --- FUNÇÕES DO MODAL PIX (NOVO) ---

async function exibirModalPix(endpoint) {
    // 1. Injeta o HTML do Modal se ainda não existir
    if (!document.getElementById('pixModal')) {
        const modalHtml = `
        <div class="modal fade" id="pixModal" tabindex="-1" aria-hidden="true" data-bs-backdrop="static">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title"><i class="fas fa-qrcode text-success me-2"></i>Pagamento via Pix</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body text-center" id="pixModalBody">
                        <div class="spinner-border text-primary" role="status"></div>
                        <p class="mt-2">Gerando código Pix...</p>
                    </div>
                    <div class="modal-footer justify-content-center">
                        <button type="button" class="btn btn-outline-secondary btn-sm" data-bs-dismiss="modal">Fechar</button>
                    </div>
                </div>
            </div>
        </div>`;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }

    // 2. Exibe o Modal
    const pixModalElement = document.getElementById('pixModal');
    const pixModal = new bootstrap.Modal(pixModalElement);
    const modalBody = document.getElementById('pixModalBody');
    
    // Reseta o conteúdo para loading
    modalBody.innerHTML = '<div class="spinner-border text-primary" role="status"></div><p class="mt-2">Gerando código Pix...</p>';
    pixModal.show();

    try {
        // 3. Chama a API
        const data = await api.request(endpoint, 'POST');

        // 4. Preenche com o QR Code
        modalBody.innerHTML = `
            <p class="text-muted mb-3 small">Abra o app do seu banco e escaneie o QR Code:</p>
            
            <img src="data:image/jpeg;base64,${data.qr_code_base64}" class="img-fluid border rounded mb-3" style="max-width: 220px;">
            
            <div class="d-grid gap-2">
                <label class="small text-start text-muted mb-0">Ou copie e cole o código:</label>
                <div class="input-group mb-3">
                    <input type="text" class="form-control form-control-sm" value="${data.qr_code}" id="pixCopiaCola" readonly style="font-size: 0.8rem;">
                    <button class="btn btn-primary btn-sm" type="button" onclick="copiarPix()">
                        <i class="fas fa-copy"></i> Copiar
                    </button>
                </div>
            </div>
            
            <div class="alert alert-success small mb-0">
                <i class="fas fa-check-circle"></i> Após o pagamento, a baixa será automática em instantes.
            </div>
        `;

    } catch (error) {
        console.error("Erro Pix:", error);
        let msg = error.message || "Erro desconhecido ao gerar Pix.";
        if(msg.includes("400")) msg = "Falha: Verifique se seu CPF está preenchido no perfil.";
        
        modalBody.innerHTML = `
            <div class="text-center text-danger">
                <i class="fas fa-exclamation-circle fa-3x mb-3"></i>
                <p>${msg}</p>
            </div>
        `;
    }
}

window.copiarPix = function() {
    const copyText = document.getElementById("pixCopiaCola");
    copyText.select();
    copyText.setSelectionRange(0, 99999); // Mobile
    navigator.clipboard.writeText(copyText.value).then(() => {
        const btn = document.querySelector('#pixModal .input-group button');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-check"></i> Copiado!';
        btn.classList.replace('btn-primary', 'btn-success');
        setTimeout(() => {
            btn.innerHTML = originalText;
            btn.classList.replace('btn-success', 'btn-primary');
        }, 2000);
    });
}

// --- FUNÇÕES DE PAGAMENTO (Chamadas pelos botões) ---

async function pagarMensalidadeOnline(event, mensalidadeId) {
    await exibirModalPix(`/pagamentos/pix/mensalidade/${mensalidadeId}`);
}

async function pagarEventoOnline(event, inscricaoId) {
    await exibirModalPix(`/pagamentos/pix/inscricao/${inscricaoId}`);
}


// --- INICIALIZAÇÃO E ROTAS (Router) ---

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

// --- HANDLERS DE PÁGINAS ---

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
    try {
        const profile = await api.getProfile();
        document.getElementById('nome').value = profile.nome || '';
        document.getElementById('email').value = profile.email || '';
        document.getElementById('cpf').value = profile.cpf || '';
        document.getElementById('telefone').value = profile.telefone || '';
        document.getElementById('data_nascimento').value = profile.data_nascimento || '';
        document.getElementById('endereco').value = profile.endereco || '';
        document.getElementById('observacoes').value = profile.observacoes || '';
        document.getElementById('foto-preview').src = profile.foto || '/portal/images/default-avatar.png';

        const form = document.getElementById('edit-profile-form');
        form.onsubmit = async (e) => {
            e.preventDefault();
            const btn = document.getElementById('btn-save-profile');
            btn.disabled = true; btn.innerHTML = 'Salvando...';
            
            const formData = new FormData(form);
            // Adicione o arquivo manualmente se selecionado, pois FormData às vezes falha com input file vazio
            const fileInput = document.getElementById('foto');
            if (fileInput.files.length > 0) {
                formData.set('foto', fileInput.files[0]);
            }

            try {
                await api.updateProfile(formData);
                ui.showAlert('Perfil atualizado!', 'success');
            } catch (err) {
                ui.showAlert('Erro ao atualizar: ' + err.message);
            } finally {
                btn.disabled = false; btn.innerHTML = 'Salvar Alterações';
            }
        };
        
        // Preview de imagem
        document.getElementById('foto').onchange = (e) => {
            if(e.target.files[0]) {
                const reader = new FileReader();
                reader.onload = function(ev) { document.getElementById('foto-preview').src = ev.target.result; };
                reader.readAsDataURL(e.target.files[0]);
            }
        };
        
    } catch (e) { console.error(e); }
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

async function handleBeneficiosPage() {
    const list = document.getElementById('partners-list');
    // Mantém a lista de parceiros que você já tinha
    const partners = [
         { logo: '/portal/images/iron.png', nome: 'Centro de Treinamento Iron Gym', desconto: '20% de desconto na Mensalidade.', whatsapp: '5532985062330' },
         { logo: '/portal/images/bull.png', nome: 'Arthur Carvalho Duarte - ARQUITETURA', desconto: 'Desconto de 20% em seu projeto.', whatsapp: '5532988810989' },
         { logo: '/portal/images/alexandria.png', nome: 'Alexandria Hamburgueria', desconto: '20% de desconto em todos os Rodízios.', whatsapp: '5532933003620' },
         { logo: '/portal/images/lucasStarck.png', nome: 'Lucas Starck - Nutricionista', desconto: 'Consulta com 50% de desconto.', whatsapp: '5532998180941' }
    ];

    list.innerHTML = partners.map(p => `
        <div class="col-6 col-md-4 mb-4">
            <div class="card h-100 text-center shadow-sm border-0 p-2">
                <img src="${p.logo}" class="card-img-top mx-auto mt-2" alt="${p.nome}" style="max-height: 60px; width: auto; max-width: 100%; object-fit: contain;">
                <div class="card-body d-flex flex-column p-2">
                    <h6 class="card-title small fw-bold mb-1">${p.nome}</h6>
                    <p class="card-text x-small text-muted mb-2" style="font-size: 0.75rem;">${p.desconto}</p>
                    ${p.whatsapp ? `<a href="https://wa.me/${p.whatsapp}?text=Sou%20aluno%20da%20Academia..." target="_blank" class="btn btn-success btn-sm mt-auto py-0" style="font-size: 0.75rem;"><i class="fab fa-whatsapp"></i> Contato</a>` : ''}
                </div>
            </div>
        </div>
    `).join('');
}

window.addEventListener('hashchange', router);
window.addEventListener('load', () => {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/portal/sw.js').catch(err => console.error('Erro SW:', err));
    }
    document.getElementById('logout-button').addEventListener('click', () => {
        localStorage.removeItem('accessToken');
        window.location.hash = '/login';
    });
    router();
});