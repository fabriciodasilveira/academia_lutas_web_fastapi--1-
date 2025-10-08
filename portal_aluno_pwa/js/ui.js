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
    }
};