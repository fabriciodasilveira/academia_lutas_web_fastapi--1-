// JavaScript customizado para Academia de Lutas

// Configuração da API
const API_BASE_URL = 'http://localhost:8005';

// Inicialização quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// Função principal de inicialização
function initializeApp() {
    // Adicionar animações aos cards
    animateCards();
    
    // Inicializar tooltips do Bootstrap
    initializeTooltips();
    
    // Configurar máscaras de input
    setupInputMasks();
    
    // Configurar validações de formulário
    setupFormValidations();
    
    // Configurar loading states
    setupLoadingStates();
    
    // Configurar auto-save (se necessário)
    setupAutoSave();
    
    // Configurar busca e filtros
    setupSearchAndFilters();
}

// Animações para cards
function animateCards() {
    const cards = document.querySelectorAll('.card');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in-up');
            }
        });
    }, {
        threshold: 0.1
    });
    
    cards.forEach(card => {
        observer.observe(card);
    });
}

// Inicializar tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Configurar máscaras de input
function setupInputMasks() {
    // Máscara para telefone
    const phoneInputs = document.querySelectorAll('input[type="tel"], input[name="telefone"]');
    phoneInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length >= 11) {
                value = value.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
            } else if (value.length >= 7) {
                value = value.replace(/(\d{2})(\d{4})(\d{0,4})/, '($1) $2-$3');
            } else if (value.length >= 3) {
                value = value.replace(/(\d{2})(\d{0,5})/, '($1) $2');
            }
            e.target.value = value;
        });
    });
    
    // Máscara para CPF
    const cpfInputs = document.querySelectorAll('input[data-mask="cpf"]');
    cpfInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            value = value.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
            e.target.value = value;
        });
    });
    
    // Máscara para CEP
    const cepInputs = document.querySelectorAll('input[data-mask="cep"]');
    cepInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            value = value.replace(/(\d{5})(\d{3})/, '$1-$2');
            e.target.value = value;
        });
    });
    
    // Formatação para valores monetários
    const currencyInputs = document.querySelectorAll('input[name*="valor"], input[name*="salario"]');
    currencyInputs.forEach(input => {
        input.addEventListener('blur', function(e) {
            const value = parseFloat(e.target.value);
            if (!isNaN(value)) {
                e.target.value = value.toFixed(2);
            }
        });
    });
}

// Configurar validações de formulário
function setupFormValidations() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(form)) {
                e.preventDefault();
                e.stopPropagation();
                showToast('Por favor, corrija os erros no formulário.', 'danger');
            }
            form.classList.add('was-validated');
        });
    });
}

// Função de validação de formulário
function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            isValid = false;
            showFieldError(field, 'Este campo é obrigatório');
        } else {
            clearFieldError(field);
        }
        
        // Validações específicas
        if (field.type === 'email' && field.value) {
            if (!isValidEmail(field.value)) {
                isValid = false;
                showFieldError(field, 'Email inválido');
            }
        }
        
        if (field.type === 'tel' && field.value) {
            if (!isValidPhone(field.value)) {
                isValid = false;
                showFieldError(field, 'Telefone inválido');
            }
        }
        
        if (field.type === 'date' && field.value) {
            const today = new Date();
            const inputDate = new Date(field.value);
            
            // Verificar se é uma data futura para eventos
            if (field.name === 'data_evento' && inputDate < today.setHours(0,0,0,0)) {
                isValid = false;
                showFieldError(field, 'A data do evento não pode ser no passado');
            }
        }
    });
    
    return isValid;
}

// Mostrar erro no campo
function showFieldError(field, message) {
    clearFieldError(field);
    
    field.classList.add('is-invalid');
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    
    field.parentNode.appendChild(errorDiv);
}

// Limpar erro do campo
function clearFieldError(field) {
    field.classList.remove('is-invalid');
    
    const errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

// Validar email
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Validar telefone
function isValidPhone(phone) {
    const phoneRegex = /^\(\d{2}\)\s\d{4,5}-\d{4}$/;
    return phoneRegex.test(phone);
}

// Configurar loading states
function setupLoadingStates() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                showLoading(submitBtn);
            }
        });
    });
}

// Mostrar loading no botão
function showLoading(button) {
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Processando...';
    button.disabled = true;
    
    // Restaurar após 5 segundos (fallback)
    setTimeout(() => {
        button.innerHTML = originalText;
        button.disabled = false;
    }, 5000);
}

// Configurar auto-save
function setupAutoSave() {
    const autoSaveForms = document.querySelectorAll('form[data-autosave="true"]');
    
    autoSaveForms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
            input.addEventListener('change', function() {
                debounce(function() {
                    autoSaveForm(form);
                }, 1000)();
            });
        });
    });
}

// Auto-save do formulário
function autoSaveForm(form) {
    const formData = new FormData(form);
    const data = Object.fromEntries(formData);
    
    // Salvar no localStorage
    const formId = form.id || 'autosave-form';
    localStorage.setItem(`autosave-${formId}`, JSON.stringify(data));
    
    // Mostrar indicador de salvamento
    showAutoSaveIndicator();
}

// Mostrar indicador de auto-save
function showAutoSaveIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'alert alert-success alert-dismissible fade show position-fixed';
    indicator.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 250px;';
    indicator.innerHTML = `
        <i class="fas fa-check me-1"></i>
        Rascunho salvo automaticamente
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(indicator);
    
    // Remover após 3 segundos
    setTimeout(() => {
        if (indicator.parentNode) {
            indicator.remove();
        }
    }, 3000);
}

// Configurar busca e filtros
function setupSearchAndFilters() {
    // Configurar busca em tempo real
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const rows = document.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
    
    // Configurar filtros
    const filters = document.querySelectorAll('select[id$="Filter"]');
    filters.forEach(filter => {
        filter.addEventListener('change', function() {
            applyTableFilters();
        });
    });
}

// Aplicar filtros na tabela
function applyTableFilters() {
    const rows = document.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        let showRow = true;
        
        // Verificar cada filtro
        const filters = document.querySelectorAll('select[id$="Filter"]');
        filters.forEach(filter => {
            if (filter.value) {
                const columnIndex = getColumnIndexForFilter(filter.id);
                if (columnIndex >= 0) {
                    const cellText = row.cells[columnIndex].textContent.toLowerCase();
                    if (!cellText.includes(filter.value.toLowerCase())) {
                        showRow = false;
                    }
                }
            }
        });
        
        row.style.display = showRow ? '' : 'none';
    });
}

// Obter índice da coluna para o filtro
function getColumnIndexForFilter(filterId) {
    const filterMap = {
        'tipoFilter': 3,
        'categoriaFilter': 2,
        'statusFilter': 5,
        'modalidadeFilter': 1,
        'nivelFilter': 2
    };
    
    return filterMap[filterId] || -1;
}

// Função debounce
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Utilitários para API
const API = {
    async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };
        
        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            
            return await response.text();
        } catch (error) {
            console.error('API request failed:', error);
            showToast('Erro na comunicação com o servidor', 'danger');
            throw error;
        }
    },
    
    async get(endpoint) {
        return this.request(endpoint);
    },
    
    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    
    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },
    
    async delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE'
        });
    }
};

// Notificações toast
function showToast(message, type = 'info') {
    const toastContainer = getOrCreateToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remover do DOM após esconder
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

// Obter ou criar container de toasts
function getOrCreateToastContainer() {
    let container = document.getElementById('toast-container');
    
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    
    return container;
}

// Confirmar ação
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Limpar todos os filtros
function clearAllFilters() {
    const inputs = document.querySelectorAll('input[type="text"], input[type="date"], select');
    inputs.forEach(input => {
        if (input.type === 'text' || input.type === 'date') {
            input.value = '';
        } else if (input.tagName === 'SELECT') {
            input.selectedIndex = 0;
        }
    });
    
    // Mostrar todas as linhas
    const rows = document.querySelectorAll('tbody tr');
    rows.forEach(row => {
        row.style.display = '';
    });
}

// Formatar valores monetários
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

// Formatar datas
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
}

// Exportar funções globais
window.showToast = showToast;
window.confirmAction = confirmAction;
window.clearAllFilters = clearAllFilters;
window.formatCurrency = formatCurrency;
window.formatDate = formatDate;
window.API = API;

