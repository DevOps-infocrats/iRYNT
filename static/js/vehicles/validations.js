export function attachValidation(selector, options) {
    const input = document.querySelector(selector);
    const companyField = document.querySelector(options.companySelector);
    const circleField = document.querySelector(options.circleSelector);
    const clientField = document.querySelector(options.clientSelector);
    const projectField = document.querySelector(options.projectSelector);
    const subzoneField = document.querySelector(options.subzoneSelector);

    if (!input) {
        return;
    }

    async function checkVehicleNumber() {
        const value = input.value.trim().toUpperCase();
        if (!value) {
            return;
        }

        const params = new URLSearchParams({
            company_id: companyField?.value || '',
            circle_id: circleField?.value || '',
            client_id: clientField?.value || '',
            project_id: projectField?.value || '',
            subzone_id: subzoneField?.value || '',
            vehicle_number: value,
        });

        try {
            const url = `${options.checkUrl}?${params}`;
            const response = await fetch(url);
            const result = await response.json();
            if (result.exists) {
                input.classList.add('is-invalid');
                if (!input.nextElementSibling || !input.nextElementSibling.classList.contains('invalid-feedback')) {
                    const feedback = document.createElement('div');
                    feedback.className = 'invalid-feedback';
                    feedback.textContent = 'A vehicle with this number already exists for the selected subzone.';
                    input.parentElement.appendChild(feedback);
                }
            } else {
                input.classList.remove('is-invalid');
                if (input.nextElementSibling && input.nextElementSibling.classList.contains('invalid-feedback')) {
                    input.nextElementSibling.remove();
                }
            }
        } catch (error) {
            console.warn('Vehicle number validation failed', error);
        }
    }

    input.addEventListener('blur', checkVehicleNumber);
}
