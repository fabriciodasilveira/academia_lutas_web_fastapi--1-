const API_BASE_URL = 'http://localhost:8000/api/v1';

const api = {
    async request(endpoint, method = 'GET', body = null, isFormData = false, requiresAuth = true) {
        const url = `${API_BASE_URL}${endpoint}`;
        const headers = new Headers();

        if (requiresAuth) {
            const token = localStorage.getItem('accessToken');
            if (!token) {
                window.location.hash = '/login';
                return;
            }
            headers.append('Authorization', `Bearer ${token}`);
        }

        const config = { method, headers };

        if (body) {
            if (isFormData) {
                config.body = body;
            } else {
                headers.append('Content-Type', 'application/json');
                config.body = JSON.stringify(body);
            }
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

    // --- FUNÇÃO DE LOGIN CORRIGIDA COM ASYNC/AWAIT ---
    login: async (email, password) => {
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);
        
        try {
            const response = await fetch(`${API_BASE_URL}/auth/token`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                let detail = 'Falha no login. Verifique seu email e senha.';
                try {
                    const errorData = await response.json();
                    detail = errorData.detail || detail;
                } catch (e) {
                    // Ignora o erro se a resposta não for JSON
                }
                throw new Error(detail);
            }
            return await response.json(); // Garante que a resposta JSON seja retornada
        } catch (error) {
            console.error("Erro na API de Login:", error);
            throw error; // Lança o erro para ser capturado pela interface
        }
    },
    
    register: (data) => api.request('/portal/register', 'POST', data, false, false),

    getProfile: () => api.request('/portal/me'),
    
    updateProfile: (formData) => api.request('/portal/me', 'PUT', formData, true, true),

    getPayments: () => api.request('/mensalidades'),
    getEvents: () => api.request('/eventos')
};