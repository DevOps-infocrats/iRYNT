document.addEventListener('DOMContentLoaded', () => {
    const companySelect = document.getElementById('company_id');
    const circleSelect = document.getElementById('circle_id');
    const form = document.getElementById('clientForm');
    const submitButton = form ? form.querySelector('button[type="submit"]') : null;

    const fetchJson = async (url) => {
        const response = await fetch(url, { headers: { 'Accept': 'application/json' } });
        if (!response.ok) {
            throw new Error('Failed to load data.');
        }
        return response.json();
    };

    const loadCircleOptions = (circles, selectedId = null) => {
        if (!circleSelect) {
            return;
        }
        circleSelect.innerHTML = '<option value="">Select circle</option>';
        circles.forEach((circle) => {
            const option = document.createElement('option');
            option.value = circle.id;
            option.textContent = circle.text;
            if (selectedId && circle.id.toString() === selectedId.toString()) {
                option.selected = true;
            }
            circleSelect.appendChild(option);
        });
    };

    const fetchCircles = async (companyId) => {
        if (!companyId || !circleSelect) {
            if (circleSelect) {
                circleSelect.innerHTML = '<option value="">Select circle</option>';
            }
            return;
        }

        try {
            const selectedId = circleSelect.value || null;
            const data = await fetchJson(`/clients/circles/search?company_id=${encodeURIComponent(companyId)}`);
            loadCircleOptions(data.items || [], selectedId);
        } catch (error) {
            console.error(error);
        }
    };

    if (companySelect) {
        companySelect.addEventListener('change', async () => {
            const companyId = companySelect.value;
            await fetchCircles(companyId);
        });
        if (companySelect.value) {
            fetchCircles(companySelect.value);
        }
    }

    if (circleSelect) {
        circleSelect.addEventListener('change', () => {
            circleSelect.classList.remove('is-invalid');
        });
    }

    if (form && submitButton) {
        form.addEventListener('submit', (event) => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                form.classList.add('was-validated');
                return;
            }
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Saving...';
        });
    }

    const resetButton = document.getElementById('resetButton');
    if (resetButton) {
        resetButton.addEventListener('click', () => {
            if (form) {
                form.classList.remove('was-validated');
            }
            if (companySelect) {
                companySelect.value = '';
            }
            if (circleSelect) {
                circleSelect.innerHTML = '<option value="">Select circle</option>';
            }
        });
    }
});
