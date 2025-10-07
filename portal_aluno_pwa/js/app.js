// =================================================================================
// Funções Auxiliares de Máscara e Validação (mais robustas)
// =================================================================================

const maskPhone = (value) => {
    if (!value) return "";
    let v = String(value).replace(/\D/g, '').slice(0, 11); // Limita a 11 dígitos
    if (v.length > 10) {
        return v.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
    } else if (v.length > 6) {
        return v.replace(/(\d{2})(\d{4})(\d{0,4})/, '($1) $2-$3');
    } else if (v.length > 2) {
        return v.replace(/(\d{2})(\d{0,5})/, '($1) $2');
    } else {
        return v.replace(/(\d*)/, '($1');
    }
};

const maskCPF = (value) => {
    if (!value) return "";
    return String(value)
        .replace(/\D/g, '')
        .slice(0, 11) // Garante que teremos no máximo 11 dígitos para a máscara
        .replace(/(\d{3})(\d)/, '$1.$2')
        .replace(/(\d{3})(\d)/, '$1.$2')
        .replace(/(\d{3})(\d{1,2})/, '$1-$2');
};

const isValidCPF = (cpf) => {
    if (typeof cpf !== 'string') return false;
    cpf = cpf.replace(/[^\d]/g, '');
    if (cpf.length !== 11 || !!cpf.match(/(\d)\1{10}/)) return false;
    let sum = 0, remainder;
    for (let i = 1; i <= 9; i++) sum += parseInt(cpf.substring(i - 1, i)) * (11 - i);
    remainder = (sum * 10) % 11;
    if ((remainder === 10) || (remainder === 11)) remainder = 0;
    if (remainder !== parseInt(cpf.substring(9, 10))) return false;
    sum = 0;
    for (let i = 1; i <= 10; i++) sum += parseInt(cpf.substring(i - 1, i)) * (12 - i);
    remainder = (sum * 10) % 11;
    if ((remainder === 10) || (remainder === 11)) remainder = 0;
    if (remainder !== parseInt(cpf.substring(10, 11))) return false;
    return true;
};


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

function handleLoginPage() { /* ...código da função está correto... */ }
function handleRegisterPage() { /* ...código da função está correto... */ }

async function handleDashboardPage() {
    try {
        const profile = await api.getProfile();
        const profilePic = document.getElementById('profile-picture');
        if (profile.foto) {
            profilePic.src = `http://localhost:8000${profile.foto}`;
        } else {
            profilePic.src = '/portal/images/default-avatar.png';
        }
        document.getElementById('aluno-nome').innerText = profile.nome || '';
        document.getElementById('aluno-email').innerText = profile.email || '';
        document.getElementById('aluno-telefone').innerText = maskPhone(profile.telefone); // Aplica a máscara na exibição
        document.getElementById('aluno-nascimento').innerText = profile.data_nascimento ? new Date(profile.data_nascimento + 'T00:00:00').toLocaleDateString('pt-BR') : 'Não informada';
    } catch (error) {
        ui.showAlert('Não foi possível carregar seus dados.');
    }
}

async function handleEditProfilePage() {
    const form = document.getElementById('edit-profile-form');
    if (!form) return;
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

    elements.telefone.addEventListener('input', (e) => e.target.value = maskPhone(e.target.value));
    elements.cpf.addEventListener('input', (e) => e.target.value = maskCPF(e.target.value));
    elements.foto.addEventListener('change', () => {
        const file = elements.foto.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => { elements.fotoPreview.src = e.target.result; };
            reader.readAsDataURL(file);
        }
    });

    try {
        const profile = await api.getProfile();
        elements.nome.value = profile.nome || '';
        elements.email.value = profile.email || '';
        elements.cpf.value = maskCPF(profile.cpf);
        elements.telefone.value = maskPhone(profile.telefone);
        elements.dataNascimento.value = profile.data_nascimento || '';
        elements.endereco.value = profile.endereco || '';
        elements.observacoes.value = profile.observacoes || '';
        if (profile.foto) {
            elements.fotoPreview.src = `http://localhost:8000${profile.foto}`;
        }
    } catch (error) {
        console.error("Erro detalhado ao preencher o formulário:", error);
        ui.showAlert('Erro ao carregar seus dados para edição. Verifique o console do navegador para detalhes.');
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        [elements.nome, elements.cpf, elements.telefone].forEach(ui.clearFieldError);
        let isValid = true;
        if (elements.cpf.value && !isValidCPF(elements.cpf.value)) {
            ui.showFieldError(elements.cpf, 'O CPF informado é inválido.');
            isValid = false;
        }
        if (!isValid) return;

        const button = form.querySelector('button[type="submit"]');
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Salvando...';
        
        const formData = new FormData();
        formData.append('nome', elements.nome.value);
        formData.append('cpf', elements.cpf.value.replace(/\D/g, ''));
        formData.append('telefone', elements.telefone.value.replace(/\D/g, ''));
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

async function handlePaymentsPage() { /* ...código da função está correto... */ }
async function handleEventsPage() { /* ...código da função está correto... */ }

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