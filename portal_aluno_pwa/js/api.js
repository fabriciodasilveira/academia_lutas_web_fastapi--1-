const API_BASE_URL = 'http://localhost:8000/api/v1';

const api = {
    async request(endpoint, method = 'GET', body = null, requiresAuth = true) {
        const url = `${API_BASE_URL}${endpoint}`;
        const headers = new Headers({
            'Content-Type': 'application/json'
        });

        if (requiresAuth) {
            const token = localStorage.getItem('accessToken');
            if (!token) {
                // Redireciona para login se o token não existir
                window.location.hash = '/login';
                return;
            }
            headers.append('Authorization', `Bearer ${token}`);
        }

        const config = {
            method: method,
            headers: headers,
        };

        if (body) {
            config.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(url, config);
            if (response.status === 401) {
                localStorage.removeItem('accessToken');
                window.location.hash = '/login';
                return;
            }
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Ocorreu um erro na API');
            }
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },

    // Funções de autenticação
    login: (email, password) => {
        // O login do FastAPI espera dados de formulário, não JSON
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);
        
        return fetch(`${API_BASE_URL}/auth/token`, {
            method: 'POST',
            body: formData
        }).then(response => {
            if (!response.ok) throw new Error('Falha no login');
            return response.json();
        });
    },
    
    register: (data) => api.request('/portal/register', 'POST', data, false),

    // Funções do aluno
    getProfile: () => api.request('/portal/me'),
    updateProfile: (data) => api.request('/portal/me', 'PUT', data),

    getPayments: () => api.request('/mensalidades'), // Assumindo que este endpoint filtra pelo aluno logado
    getEvents: () => api.request('/eventos')
};