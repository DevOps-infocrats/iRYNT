import { loadCompanies, loadCircles, loadClients, loadProjects, bindHierarchyPreview } from './hierarchy.js';
import { setupSubzoneCodeHandler, validateDuplicateCode } from './validations.js';

export function initSubzoneForm() {
    const companySelect = document.getElementById('companySelect');
    const circleSelect = document.getElementById('circleSelect');
    const clientSelect = document.getElementById('clientSelect');
    const projectSelect = document.getElementById('projectSelect');
    const previewPanel = document.getElementById('hierarchyPreview');
    const companyName = document.getElementById('previewCompany');
    const circleName = document.getElementById('previewCircle');
    const clientName = document.getElementById('previewClient');
    const projectName = document.getElementById('previewProject');
    const subzoneCodeInput = document.getElementById('subzoneCode');
    const codeFeedback = document.getElementById('subzoneCodeFeedback');
    const saveButton = document.getElementById('saveSubzoneButton');

    if (!companySelect || !circleSelect || !clientSelect || !projectSelect || !projectName) {
        return;
    }

    if (window.jQuery && window.jQuery().select2) {
        window.jQuery('.select2').select2({
            width: '100%',
            theme: 'bootstrap-5',
            placeholder: 'Search or select',
            allowClear: true,
        });
    }

    bindHierarchyPreview({ company: companySelect, circle: circleSelect, client: clientSelect, project: projectSelect, companyName, circleName, clientName, projectName, previewPanel });

    if (window.jQuery) {
        window.jQuery(companySelect).on('change', async () => {
            await loadCircles(companySelect.value, circleSelect);
            clientSelect.innerHTML = '<option value="">Select client</option>';
            clientSelect.disabled = true;
            window.jQuery(clientSelect).trigger('change');
            projectSelect.innerHTML = '<option value="">Select project</option>';
            projectSelect.disabled = true;
            window.jQuery(projectSelect).trigger('change');
        });

        window.jQuery(circleSelect).on('change', async () => {
            await loadClients(circleSelect.value, clientSelect);
            projectSelect.innerHTML = '<option value="">Select project</option>';
            projectSelect.disabled = true;
            window.jQuery(projectSelect).trigger('change');
        });

        window.jQuery(clientSelect).on('change', async () => {
            await loadProjects(clientSelect.value, projectSelect);
        });
    } else {
        companySelect.addEventListener('change', async () => {
            await loadCircles(companySelect.value, circleSelect);
            clientSelect.innerHTML = '<option value="">Select client</option>';
            clientSelect.disabled = true;
            projectSelect.innerHTML = '<option value="">Select project</option>';
            projectSelect.disabled = true;
        });

        circleSelect.addEventListener('change', async () => {
            await loadClients(circleSelect.value, clientSelect);
            projectSelect.innerHTML = '<option value="">Select project</option>';
            projectSelect.disabled = true;
        });

        clientSelect.addEventListener('change', async () => {
            await loadProjects(clientSelect.value, projectSelect);
        });
    }

    setupSubzoneCodeHandler(subzoneCodeInput, codeFeedback);

    if (subzoneCodeInput) {
        subzoneCodeInput.addEventListener('blur', async () => {
            if (!companySelect.value || !circleSelect.value || !clientSelect.value || !projectSelect.value) {
                return;
            }
            await validateDuplicateCode({
                companyId: companySelect.value,
                circleId: circleSelect.value,
                clientId: clientSelect.value,
                projectId: projectSelect.value,
                code: subzoneCodeInput.value.trim().toUpperCase(),
            }, codeFeedback);
        });
    }

    if (saveButton) {
        saveButton.addEventListener('click', () => {
            saveButton.classList.add('loading');
        });
    }

    const btnFetchLocation = document.getElementById('btnFetchLocation');
    const latitudeInput = document.getElementById('latitude');
    const longitudeInput = document.getElementById('longitude');
    const fetchStatus = document.getElementById('locationFetchStatus');

    if (btnFetchLocation) {
        btnFetchLocation.addEventListener('click', () => {
            if (!navigator.geolocation) {
                if (fetchStatus) {
                    fetchStatus.textContent = 'Geolocation is not supported by your browser.';
                    fetchStatus.className = 'ms-2 text-danger small';
                }
                return;
            }

            btnFetchLocation.disabled = true;
            const originalHtml = btnFetchLocation.innerHTML;
            btnFetchLocation.innerHTML = `
                <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                <span>Fetching...</span>
            `;
            if (fetchStatus) {
                fetchStatus.textContent = 'Acquiring GPS location...';
                fetchStatus.className = 'ms-2 text-soft small';
            }

            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const lat = position.coords.latitude.toFixed(6);
                    const lng = position.coords.longitude.toFixed(6);
                    if (latitudeInput) latitudeInput.value = lat;
                    if (longitudeInput) longitudeInput.value = lng;

                    // Trigger input event to update validation/state if necessary
                    if (latitudeInput) latitudeInput.dispatchEvent(new Event('input', { bubbles: true }));
                    if (longitudeInput) longitudeInput.dispatchEvent(new Event('input', { bubbles: true }));

                    btnFetchLocation.disabled = false;
                    btnFetchLocation.innerHTML = originalHtml;
                    if (fetchStatus) {
                        fetchStatus.textContent = 'Location filled successfully!';
                        fetchStatus.className = 'ms-2 text-success small';
                    }
                },
                (error) => {
                    console.error('Error fetching location:', error);
                    let errMsg = 'Failed to fetch location.';
                    if (error.code === error.PERMISSION_DENIED) {
                        errMsg = 'Location permission denied by user.';
                    } else if (error.code === error.POSITION_UNAVAILABLE) {
                        errMsg = 'Location information is unavailable.';
                    } else if (error.code === error.TIMEOUT) {
                        errMsg = 'Request to get user location timed out.';
                    }
                    btnFetchLocation.disabled = false;
                    btnFetchLocation.innerHTML = originalHtml;
                    if (fetchStatus) {
                        fetchStatus.textContent = errMsg;
                        fetchStatus.className = 'ms-2 text-danger small';
                    }
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 0
                }
            );
        });
    }
}

export function initSubzoneListFilters() {
    const filterSelects = document.querySelectorAll('.dashboard-filter select');
    filterSelects.forEach(select => {
        select.addEventListener('change', () => {
            // Placeholder for live filtering integration.
        });
    });
}
