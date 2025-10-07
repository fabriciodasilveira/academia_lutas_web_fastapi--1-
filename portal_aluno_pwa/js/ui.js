const ui = {
    showLoading: (root) => {
        root.innerHTML = `
            <div class="d-flex justify-content-center align-items-center" style="height: 50vh;">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        `;
    },
    showAlert: (message, type = 'danger') => {
        const alertBox = document.createElement('div');
        alertBox.className = `alert alert-${type} alert-dismissible fade show`;
        alertBox.role = 'alert';
        alertBox.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        // Adiciona a um container de alertas se existir, ou ao topo do app-root
        const container = document.getElementById('alert-container') || document.getElementById('app-root');
        container.prepend(alertBox);
    },
    toggleNav: (show) => {
        document.getElementById('main-header').style.display = show ? 'flex' : 'none';
        document.getElementById('main-nav').style.display = show ? 'flex' : 'none';
    },
    
    showFieldError: (inputElement, message) => {
        inputElement.classList.add('is-invalid');
        let errorDiv = inputElement.nextElementSibling;
        if (!errorDiv || !errorDiv.classList.contains('invalid-feedback')) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'invalid-feedback';
            inputElement.parentNode.insertBefore(errorDiv, inputElement.nextSibling);
        }
        errorDiv.textContent = message;
    },

    clearFieldError: (inputElement) => {
        inputElement.classList.remove('is-invalid');
        const errorDiv = inputElement.nextElementSibling;
        if (errorDiv && errorDiv.classList.contains('invalid-feedback')) {
            errorDiv.remove();
        }
    }
};