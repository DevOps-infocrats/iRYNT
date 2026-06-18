document.addEventListener('DOMContentLoaded', function () {
    const authForm = document.getElementById('authForm');
    const loginButton = document.getElementById('loginButton');
    const authSpinner = document.getElementById('authSpinner');
    const togglePassword = document.getElementById('togglePassword');
    const passwordInput = document.getElementById('loginPassword');

    function toggleLoading(isLoading) {
        if (!loginButton || !authSpinner) return;
        loginButton.disabled = isLoading;
        authSpinner.classList.toggle('d-none', !isLoading);
    }

    function setAlert(message, type = 'danger') {
        const existing = document.getElementById('authAlert');
        if (existing) existing.remove();
        const alert = document.createElement('div');
        alert.id = 'authAlert';
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.role = 'alert';
        alert.innerHTML = `
            <span>${message}</span>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        authForm.parentNode.insertBefore(alert, authForm);
    }

    if (togglePassword && passwordInput) {
        togglePassword.addEventListener('click', function () {
            const isPassword = passwordInput.type === 'password';
            passwordInput.type = isPassword ? 'text' : 'password';
            togglePassword.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password');
            togglePassword.querySelector('.material-symbols-outlined').textContent = isPassword ? 'visibility_off' : 'visibility';
        });
    }

    if (authForm) {
        authForm.addEventListener('submit', async function (event) {
            event.preventDefault();
            authForm.classList.remove('was-validated');

            if (!authForm.checkValidity()) {
                authForm.classList.add('was-validated');
                return;
            }

            toggleLoading(true);
            const formData = new FormData(authForm);
            const body = new URLSearchParams();
            formData.forEach((value, key) => body.append(key, value));

            try {
                const response = await fetch(authForm.action, {
                    method: authForm.method,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                    body,
                });
                const data = await response.json();
                if (!data.success) {
                    setAlert(data.message || 'Unable to sign in. Please check your credentials.');
                    toggleLoading(false);
                    return;
                }
                window.location.href = data.redirect || '/attendance/live';
            } catch (error) {
                setAlert('Unable to process login. Please try again later.');
                toggleLoading(false);
            }
        });
    }

    const inputs = authForm ? authForm.querySelectorAll('input') : [];
    inputs.forEach((input) => {
        input.addEventListener('focus', () => {
            input.classList.add('focus-ring');
        });
        input.addEventListener('blur', () => {
            input.classList.remove('focus-ring');
        });
    });
});
