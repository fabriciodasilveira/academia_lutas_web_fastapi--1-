const appRoot = document.getElementById('app-root');

// Definição das rotas do frontend
const routes = {
    '/login': { page: '/portal/pages/login.html', handler: handleLoginPage, public: true },
    '/register': { page: '/portal/pages/register.html', handler: handleRegisterPage, public: true },
    '/dashboard': { page: '/portal/pages/dashboard.html', handler: handleDashboardPage },
    '/edit-profile': { page: '/portal/pages/edit_profile.html', handler: handleEditProfilePage }, // <-- ROTA ADICIONADA
    '/payments': { page: '/portal/pages/payments.html', handler: handlePaymentsPage },
    '/events': { page: '/portal/pages/events.html', handler: handleEventsPage }
};

// ... (função router existente, sem alterações) ...
const router = async () => {
    // ...
};

// --- Handlers de Página ---

function handleLoginPage() {
    // ... (código existente) ...
}

function handleRegisterPage() {
    // ... (código existente) ...
}

async function handleDashboardPage() {
    try {
        const profile = await api.getProfile();
        document.getElementById('aluno-nome').innerText = profile.nome;
        document.getElementById('aluno-email').innerText = profile.email;
        document.getElementById('aluno-telefone').innerText = profile.telefone || 'Não informado';
        // Adicionada data de nascimento
        document.getElementById('aluno-nascimento').innerText = profile.data_nascimento ? new Date(profile.data_nascimento + 'T00:00:00').toLocaleDateString() : 'Não informada';
    } catch (error) {
        ui.showAlert('Não foi possível carregar seus dados.');
    }
}

// --- NOVA FUNÇÃO ADICIONADA ABAIXO ---

async function handleEditProfilePage() {
    const form = document.getElementById('edit-profile-form');
    const nomeInput = document.getElementById('nome');
    const emailInput = document.getElementById('email');
    const telefoneInput = document.getElementById('telefone');
    const dataNascimentoInput = document.getElementById('data_nascimento');

    // 1. Preencher o formulário com os dados atuais
    try {
        const profile = await api.getProfile();
        nomeInput.value = profile.nome || '';
        emailInput.value = profile.email || '';
        telefoneInput.value = profile.telefone || '';
        dataNascimentoInput.value = profile.data_nascimento || '';
    } catch (error) {
        ui.showAlert('Erro ao carregar seus dados para edição.');
    }

    // 2. Lidar com o envio do formulário
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const button = form.querySelector('button[type="submit"]');
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Salvando...';

        const updatedData = {
            nome: nomeInput.value,
            telefone: telefoneInput.value,
            data_nascimento: dataNascimentoInput.value,
        };

        try {
            await api.updateProfile(updatedData);
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
    // ... (código existente) ...
}

async function handleEventsPage() {
    // ... (código existente) ...
}


// Inicialização e eventos do navegador
window.addEventListener('hashchange', router);
// ... (resto do código existente) ...