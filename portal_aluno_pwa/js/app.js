const appRoot = document.getElementById('app-root');

const routes = {
    '/login': { page: '/portal/pages/login.html', handler: handleLoginPage, public: true },
    '/login/callback': { handler: handleLoginCallback, public: true }, // <-- NOVA ROTA
    '/register': { page: '/portal/pages/register.html', handler: handleRegisterPage, public: true },
    '/dashboard': { page: '/portal/pages/dashboard.html', handler: handleDashboardPage },
    '/edit-profile': { page: '/portal/pages/edit_profile.html', handler: handleEditProfilePage },
    '/payments': { page: '/portal/pages/payments.html', handler: handlePaymentsPage },
    '/events': { page: '/portal/pages/events.html', handler: handleEventsPage }
};

// ... (função router existente, sem alterações) ...

// --- ADICIONE ESTA NOVA FUNÇÃO ---
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

// ... (resto das suas funções handle, como handleLoginPage, etc.) ...