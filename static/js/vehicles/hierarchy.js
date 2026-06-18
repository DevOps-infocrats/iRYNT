export function initHierarchyControls(options) {
    const companyField = document.querySelector(options.companySelector);
    const circleField = document.querySelector(options.circleSelector);
    const clientField = document.querySelector(options.clientSelector);
    const projectField = document.querySelector(options.projectSelector);
    const subzoneField = document.querySelector(options.subzoneSelector);

    const previewCompany = document.querySelector(options.previewCompany);
    const previewCircle = document.querySelector(options.previewCircle);
    const previewClient = document.querySelector(options.previewClient);
    const previewProject = document.querySelector(options.previewProject);
    const previewSubzone = document.querySelector(options.previewSubzone);

    function clearSelect(select) {
        if (!select) return;
        select.innerHTML = '<option value="">Select</option>';
        select.value = '';
        if (window.jQuery && window.jQuery(select).data('select2')) {
            window.jQuery(select).trigger('change');
        } else {
            select.dispatchEvent(new Event('change'));
        }
    }

    async function loadOptions(url, queryValue, targetSelect, placeholder) {
        if (!targetSelect) return;
        if (!queryValue) {
            clearSelect(targetSelect);
            targetSelect.disabled = true;
            if (window.jQuery && window.jQuery(targetSelect).data('select2')) {
                window.jQuery(targetSelect).trigger('change');
            }
            return;
        }

        try {
            const response = await fetch(`${url}?${new URLSearchParams(queryValue)}`);
            const items = await response.json();
            targetSelect.innerHTML = `<option value="">${placeholder}</option>`;
            items.forEach((item) => {
                const option = document.createElement('option');
                option.value = item.id;
                option.textContent = item.text;
                targetSelect.appendChild(option);
            });
            targetSelect.disabled = false;
        } catch (error) {
            console.warn('Failed to load hierarchy options', error);
            targetSelect.innerHTML = `<option value="">${placeholder}</option>`;
            targetSelect.disabled = true;
        }
        if (window.jQuery && window.jQuery(targetSelect).data('select2')) {
            window.jQuery(targetSelect).trigger('change');
        }
    }

    function updatePreview() {
        if (previewCompany && companyField) previewCompany.textContent = companyField.selectedOptions[0]?.text || '–';
        if (previewCircle && circleField) previewCircle.textContent = circleField.selectedOptions[0]?.text || '–';
        if (previewClient && clientField) previewClient.textContent = clientField.selectedOptions[0]?.text || '–';
        if (previewProject && projectField) previewProject.textContent = projectField.selectedOptions[0]?.text || '–';
        if (previewSubzone && subzoneField) previewSubzone.textContent = subzoneField.selectedOptions[0]?.text || '–';
    }

    if (window.jQuery) {
        if (companyField) {
            window.jQuery(companyField).on('change', async () => {
                await loadOptions(options.ajaxUrls.circles, { company_id: companyField.value }, circleField, 'Select circle');
                clearSelect(clientField);
                clearSelect(projectField);
                clearSelect(subzoneField);
                updatePreview();
            });
        }
        if (circleField) {
            window.jQuery(circleField).on('change', async () => {
                await loadOptions(options.ajaxUrls.clients, { circle_id: circleField.value }, clientField, 'Select client');
                clearSelect(projectField);
                clearSelect(subzoneField);
                updatePreview();
            });
        }
        if (clientField) {
            window.jQuery(clientField).on('change', async () => {
                await loadOptions(options.ajaxUrls.projects, { client_id: clientField.value }, projectField, 'Select project');
                clearSelect(subzoneField);
                updatePreview();
            });
        }
        if (projectField) {
            window.jQuery(projectField).on('change', async () => {
                await loadOptions(options.ajaxUrls.subzones, { project_id: projectField.value }, subzoneField, 'Select subzone');
                updatePreview();
            });
        }
        if (subzoneField) {
            window.jQuery(subzoneField).on('change', updatePreview);
        }
    } else {
        companyField?.addEventListener('change', async () => {
            await loadOptions(options.ajaxUrls.circles, { company_id: companyField.value }, circleField, 'Select circle');
            clearSelect(clientField);
            clearSelect(projectField);
            clearSelect(subzoneField);
            updatePreview();
        });

        circleField?.addEventListener('change', async () => {
            await loadOptions(options.ajaxUrls.clients, { circle_id: circleField.value }, clientField, 'Select client');
            clearSelect(projectField);
            clearSelect(subzoneField);
            updatePreview();
        });

        clientField?.addEventListener('change', async () => {
            await loadOptions(options.ajaxUrls.projects, { client_id: clientField.value }, projectField, 'Select project');
            clearSelect(subzoneField);
            updatePreview();
        });

        projectField?.addEventListener('change', async () => {
            await loadOptions(options.ajaxUrls.subzones, { project_id: projectField.value }, subzoneField, 'Select subzone');
            updatePreview();
        });

        subzoneField?.addEventListener('change', updatePreview);
    }
    updatePreview();
}
