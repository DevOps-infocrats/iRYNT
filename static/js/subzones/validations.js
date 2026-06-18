export function setupSubzoneCodeHandler(codeInput, statusText) {
    if (!codeInput) return;
    codeInput.addEventListener('input', () => {
        codeInput.value = codeInput.value.toUpperCase();
        if (statusText) {
            statusText.textContent = '';
        }
    });
}

export async function validateDuplicateCode({ companyId, circleId, clientId, projectId, code }, feedbackElement) {
    if (!companyId || !circleId || !clientId || !projectId || !code) {
        return;
    }

    const query = new URLSearchParams({
        company_id: companyId,
        circle_id: circleId,
        client_id: clientId,
        project_id: projectId,
        subzone_code: code,
    });

    const response = await fetch(`/subzones/ajax/check-code?${query.toString()}`);
    const result = await response.json();

    if (result.exists) {
        if (feedbackElement) {
            feedbackElement.textContent = 'A subzone with this code already exists for the selected project.';
            feedbackElement.classList.add('text-danger');
        }
        return false;
    }

    if (feedbackElement) {
        feedbackElement.textContent = 'Code available';
        feedbackElement.classList.remove('text-danger');
        feedbackElement.classList.add('text-success');
    }
    return true;
}
