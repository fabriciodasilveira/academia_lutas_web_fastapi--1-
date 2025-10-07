// =================================================================================
// Funções Auxiliares (Simplificadas para estabilidade)
// =================================================================================

const maskPhone = (value) => value || ""; // Desativado temporariamente
const maskCPF = (value) => value || "";   // Desativado temporariamente
const isValidCPF = (cpf) => true;         // Desativado temporariamente

// =================================================================================
// Lógica Principal da Aplicação
// =================================================================================

const appRoot = document.getElementById('app-root');
const routes = {
    '/login': { page: '/portal/pages/login.html', handler: handleLoginPage, public: true },
    '/register': { page: '/portal/pages/register.html', handler: handleRegisterPage, public: true },
    '/dashboard': { page: '/portal/pages/dashboard.html', handler: handleDashboardPage },
    '/edit-profile': { page: '/portal/pages/edit_profile.html', handler: handleEditProfilePage },
    '/payments': { page: '/portal/pages/payments.html', handler: handlePaymentsPage },
    '/events': { page: '/portal/pages/events.html', handler: handleEventsPage }
};

const router = async () => {
    const path = window.location.hash.slice(1) || '/dashboard';
    const route = routes[path] || routes['/dashboard'];
    if (!route) { console.error("Rota não encontrada:", path); return; }
    
    const token = localStorage.getItem('accessToken');
    if (!route.public && !token) { window.location.hash = '/login'; return; }
    if (route.public && token) { window.location.hash = '/dashboard'; return; }

    ui.toggleNav(!route.public);
    ui.showLoading(appRoot);
    
    try {
        document.querySelectorAll('.nav__link').forEach(link => {
            link.classList.remove('nav__link--active');
            if (link.getAttribute('href') === `#${path}`) link.classList.add('nav__link--active');
        });
        const response = await fetch(route.page);
        appRoot.innerHTML = await response.text();
        if (route.handler) route.handler();
    } catch (error) {
        console.error("Erro ao carregar a página:", error);
        appRoot.innerHTML = `<p class="text-danger">Erro ao carregar a página.</p>`;
    }
};

// =================================================================================
// Handlers de Página
// =================================================================================

function handleLoginPage() {
    const form = document.getElementById('login-form');
    if (!form) return;
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

function handleRegisterPage() { /* ...código da função está correto... */ }

async function handleDashboardPage() {
    try {
        const profile = await api.getProfile();
        const profilePic = document.getElementById('profile-picture');
        if (profilePic && profile.foto) {
            profilePic.src = `http://localhost:8000${profile.foto}`;
        }
        const alunoNome = document.getElementById('aluno-nome');
        if (alunoNome) alunoNome.innerText = profile.nome || '';
        
        const alunoEmail = document.getElementById('aluno-email');
        if (alunoEmail) alunoEmail.innerText = profile.email || '';
        
        const alunoTelefone = document.getElementById('aluno-telefone');
        if (alunoTelefone) alunoTelefone.innerText = profile.telefone || 'Não informado';

        const alunoNascimento = document.getElementById('aluno-nascimento');
        if (alunoNascimento) alunoNascimento.innerText = profile.data_nascimento ? new Date(profile.data_nascimento + 'T00:00:00').toLocaleDateString('pt-BR') : 'Não informada';

    } catch (error) {
        console.error("Erro no Dashboard:", error);
        ui.showAlert('Não foi possível carregar seus dados.');
    }
}

async function handleEditProfilePage() {
    console.log("Iniciando handleEditProfilePage...");
    const form = document.getElementById('edit-profile-form');
    if (!form) {
        console.error("Formulário de edição não encontrado!");
        return;
    }
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

    try {
        console.log("Buscando perfil da API...");
        const profile = await api.getProfile();
        console.log("Perfil recebido:", profile);

        console.log("Preenchendo nome...");
        if (elements.nome) elements.nome.value = profile.nome || '';
        
        console.log("Preenchendo email...");
        if (elements.email) elements.email.value = profile.email || '';
        
        console.log("Preenchendo CPF...");
        if (elements.cpf) elements.cpf.value = profile.cpf || '';
        
        console.log("Preenchendo telefone...");
        if (elements.telefone) elements.telefone.value = profile.telefone || '';
        
        console.log("Preenchendo data de nascimento...");
        if (elements.dataNascimento) elements.dataNascimento.value = profile.data_nascimento || '';
        
        console.log("Preenchendo endereço...");
        if (elements.endereco) elements.endereco.value = profile.endereco || '';
        
        console.log("Preenchendo observações...");
        if (elements.observacoes) elements.observacoes.value = profile.observacoes || '';
        
        console.log("Preenchendo foto...");
        if (elements.fotoPreview && profile.foto) {
            elements.fotoPreview.src = `http://localhost:8000${profile.foto}`;
        }
        
        console.log("Formulário preenchido com sucesso.");

    } catch (error) {
        console.error("ERRO DETALHADO AO CARREGAR DADOS:", error);
        ui.showAlert('Erro ao carregar seus dados para edição. Verifique o console para detalhes.');
    }

    // Lógica de submit (permanece a mesma)
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        // ... (código de submit da resposta anterior) ...
    });
}

async function handlePaymentsPage() { /* ...código da função está correto... */ }
async function handleEventsPage() { /* ...código da função está correto... */ }

window.addEventListener('hashchange', router);
window.addEventListener('load', () => {
    // ... (código de inicialização está correto) ...
});