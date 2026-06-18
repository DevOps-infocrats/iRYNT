function createOption(item, display) {
    const option = document.createElement('option');
    option.value = item.id;
    option.textContent = display;
    return option;
}

export async function loadCompanies(companySelect) {
    if (!companySelect) return;
    const response = await fetch('/subzones/ajax/companies');
    const companies = await response.json();
    companySelect.innerHTML = '<option value="">Select company</option>' + companies.map(company => `
        <option value="${company.id}">${company.name} (${company.code})</option>
    `).join('');
    if (window.jQuery && window.jQuery(companySelect).data('select2')) {
        window.jQuery(companySelect).trigger('change');
    }
}

export async function loadCircles(companyId, circleSelect) {
    if (!circleSelect) return;
    circleSelect.disabled = !companyId;
    circleSelect.innerHTML = '<option value="">Select circle</option>';
    if (!companyId) {
        if (window.jQuery && window.jQuery(circleSelect).data('select2')) {
            window.jQuery(circleSelect).trigger('change');
        }
        return;
    }
    const response = await fetch(`/subzones/ajax/circles?company_id=${companyId}`);
    const circles = await response.json();
    circleSelect.innerHTML += circles.map(circle => `
        <option value="${circle.id}">${circle.name} (${circle.code})</option>
    `).join('');
    if (window.jQuery && window.jQuery(circleSelect).data('select2')) {
        window.jQuery(circleSelect).trigger('change');
    }
}

export async function loadClients(circleId, clientSelect) {
    if (!clientSelect) return;
    clientSelect.disabled = !circleId;
    clientSelect.innerHTML = '<option value="">Select client</option>';
    if (!circleId) {
        if (window.jQuery && window.jQuery(clientSelect).data('select2')) {
            window.jQuery(clientSelect).trigger('change');
        }
        return;
    }
    const response = await fetch(`/subzones/ajax/clients?circle_id=${circleId}`);
    const clients = await response.json();
    clientSelect.innerHTML += clients.map(client => `
        <option value="${client.id}">${client.name} (${client.code})</option>
    `).join('');
    if (window.jQuery && window.jQuery(clientSelect).data('select2')) {
        window.jQuery(clientSelect).trigger('change');
    }
}

export async function loadProjects(clientId, projectSelect) {
    if (!projectSelect) return;
    projectSelect.disabled = !clientId;
    projectSelect.innerHTML = '<option value="">Select project</option>';
    if (!clientId) {
        if (window.jQuery && window.jQuery(projectSelect).data('select2')) {
            window.jQuery(projectSelect).trigger('change');
        }
        return;
    }
    const response = await fetch(`/subzones/ajax/projects?client_id=${clientId}`);
    const projects = await response.json();
    projectSelect.innerHTML += projects.map(project => `
        <option value="${project.id}">${project.name} (${project.code})</option>
    `).join('');
    if (window.jQuery && window.jQuery(projectSelect).data('select2')) {
        window.jQuery(projectSelect).trigger('change');
    }
}

export function bindHierarchyPreview(elements) {
    const { company, circle, client, project, companyName, circleName, clientName, projectName, previewPanel } = elements;
    if (!company || !circle || !client || !project || !previewPanel) return;

    function updatePreview() {
        companyName.textContent = company.selectedOptions[0]?.textContent || '—';
        circleName.textContent = circle.selectedOptions[0]?.textContent || '—';
        clientName.textContent = client.selectedOptions[0]?.textContent || '—';
        projectName.textContent = project.selectedOptions[0]?.textContent || '—';
        const hasSelection = company.value && circle.value && client.value && project.value;
        previewPanel.style.display = hasSelection ? 'grid' : 'none';
    }

    [company, circle, client, project].forEach(select => {
        if (window.jQuery) {
            window.jQuery(select).on('change', updatePreview);
        } else {
            select.addEventListener('change', updatePreview);
        }
    });
    updatePreview();
}
