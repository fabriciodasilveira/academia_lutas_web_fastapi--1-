const API_BASE_URL = '/api/v1';

const api = {
    // Funções auxiliares
    getMatriculas: () => api.request('/portal/matriculas'),
    
    updatePassword: (current_password, new_password) => {
        return api.request('/portal/me/update-password', 'PUT', { current_password, new_password });
    },

    login: async (username, password) => {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);
        
        try {
            const response = await fetch(`${API_BASE_URL}/auth/token`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                let detail = 'Falha no login.';
                try {
                    const errorData = await response.json();
                    detail = errorData.detail || detail;
                } catch (e) {}
                throw new Error(detail);
            }
            return await response.json();
        } catch (error) {
            console.error("Erro na API de Login:", error);
            throw error;
        }
    },
    
    register: (data) => api.request('/portal/register', 'POST', data, false, false),
    getProfile: () => api.request('/portal/me'),
    updateProfile: (formData) => api.request('/portal/me', 'PUT', formData, true, true),
    getPayments: () => api.request('/portal/pendencias'),
    getEvents: () => api.request('/portal/eventos'),
    enrollInEvent: (eventoId) => api.request(`/portal/eventos/${eventoId}/inscrever`, 'POST'),

    // --- FUNÇÃO PRINCIPAL DE REQUISIÇÃO (CORRIGIDA) ---
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
            
            // Se não autorizado, desloga
            if (response.status === 401) {
                localStorage.removeItem('accessToken');
                window.location.hash = '/login';
                return;
            }

            // --- A CORREÇÃO VITAL ESTÁ AQUI ---
            // Se o status for 204 (Sucesso sem conteúdo), retorna null
            // e NÃO tenta fazer .json(), evitando o erro.
            if (response.status === 204) {
                return null;
            }
            // ----------------------------------

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Ocorreu um erro na API');
            }
            
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }
};