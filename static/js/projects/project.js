/**
 * Project Module JavaScript
 * Handles dependent dropdowns, form validation, and interactive behaviors
 */

document.addEventListener('DOMContentLoaded', () => {
    const companySelect = document.getElementById('company_id');
    const circleSelect = document.getElementById('circle_id');
    const clientSelect = document.getElementById('client_id');
    const projectCodeInput = document.getElementById('project_code');
    const projectForm = document.getElementById('projectForm');
    const submitButton = projectForm ? projectForm.querySelector('button[type="submit"]') : null;
    const resetButton = document.getElementById('resetButton');
    const hierarchyPreview = document.getElementById('hierarchyPreview');

    // ============================================================
    // HELPER FUNCTIONS
    // ============================================================

    const fetchJson = async (url) => {
        try {
            const response = await fetch(url, {
                headers: { 'Accept': 'application/json' }
            });
            if (!response.ok) {
                throw new Error('Failed to load data.');
            }
            return response.json();
        } catch (error) {
            console.error('Fetch error:', error);
            return { items: [] };
        }
    };

    const updateDropdown = (selectElement, items, selectedValue = null) => {
        if (!selectElement) return;

        const currentValue = selectElement.value;
        const placeholder = selectElement.querySelector('option:first-child');
        const placeholderText = placeholder ? placeholder.textContent : 'Select option';

        selectElement.innerHTML = `<option value="">${placeholderText}</option>`;
        
        items.forEach((item) => {
            const option = document.createElement('option');
            option.value = item.id;
            option.textContent = item.text;
            if (selectedValue && item.id.toString() === selectedValue.toString()) {
                option.selected = true;
            }
            selectElement.appendChild(option);
        });

        // Restore previous selection if it exists
        if (currentValue && !selectedValue) {
            selectElement.value = currentValue;
        }
    };

    const showHierarchyPreview = () => {
        if (!companySelect.value || !circleSelect.value || !clientSelect.value) {
            if (hierarchyPreview) hierarchyPreview.style.display = 'none';
            return;
        }

        const companyOption = companySelect.options[companySelect.selectedIndex];
        const circleOption = circleSelect.options[circleSelect.selectedIndex];
        const clientOption = clientSelect.options[clientSelect.selectedIndex];

        if (companyOption && circleOption && clientOption && hierarchyPreview) {
            document.getElementById('previewCompany').textContent = companyOption.textContent;
            document.getElementById('previewCircle').textContent = circleOption.textContent;
            document.getElementById('previewClient').textContent = clientOption.textContent;
            hierarchyPreview.style.display = 'block';
        }
    };

    const validateProjectCode = async (companyId, clientId, code) => {
        if (!code || !companyId || !clientId) return;

        try {
            const response = await fetch(
                `/projects/check_code?company_id=${encodeURIComponent(companyId)}&client_id=${encodeURIComponent(clientId)}&code=${encodeURIComponent(code)}`
            );
            const data = await response.json();
            
            if (data.exists) {
                projectCodeInput.classList.add('is-invalid');
                const feedback = projectCodeInput.nextElementSibling;
                if (feedback) {
                    feedback.textContent = 'Project code already exists for this client.';
                }
            } else {
                projectCodeInput.classList.remove('is-invalid');
                const feedback = projectCodeInput.nextElementSibling;
                if (feedback) {
                    feedback.textContent = '';
                }
            }
        } catch (error) {
            console.error('Validation error:', error);
        }
    };

    // ============================================================
    // CIRCLE DROPDOWN LOGIC
    // ============================================================

    if (companySelect) {
        companySelect.addEventListener('change', async () => {
            const companyId = companySelect.value;
            
            // Reset circle and client
            updateDropdown(circleSelect, []);
            updateDropdown(clientSelect, []);
            
            if (companyId) {
                // Load circles for selected company
                const data = await fetchJson(`/projects/circles/search?company_id=${encodeURIComponent(companyId)}`);
                updateDropdown(circleSelect, data.items || []);
            }

            showHierarchyPreview();
        });

        // Load circles on page load if company is already selected
        if (companySelect.value) {
            (async () => {
                const data = await fetchJson(`/projects/circles/search?company_id=${encodeURIComponent(companySelect.value)}`);
                updateDropdown(circleSelect, data.items || [], circleSelect.value);
            })();
        }
    }

    // ============================================================
    // CLIENT DROPDOWN LOGIC
    // ============================================================

    if (circleSelect) {
        circleSelect.addEventListener('change', async () => {
            const companyId = companySelect.value;
            const circleId = circleSelect.value;

            // Reset client
            updateDropdown(clientSelect, []);

            if (companyId && circleId) {
                // Load clients for selected circle
                const data = await fetchJson(
                    `/projects/clients/search?company_id=${encodeURIComponent(companyId)}&circle_id=${encodeURIComponent(circleId)}`
                );
                updateDropdown(clientSelect, data.items || []);
            }

            showHierarchyPreview();
        });

        // Load clients on page load if circle is already selected
        if (circleSelect.value) {
            (async () => {
                const companyId = companySelect.value;
                const circleId = circleSelect.value;
                if (companyId && circleId) {
                    const data = await fetchJson(
                        `/projects/clients/search?company_id=${encodeURIComponent(companyId)}&circle_id=${encodeURIComponent(circleId)}`
                    );
                    updateDropdown(clientSelect, data.items || [], clientSelect.value);
                }
            })();
        }
    }

    // ============================================================
    // CLIENT SELECTION HANDLER
    // ============================================================

    if (clientSelect) {
        clientSelect.addEventListener('change', () => {
            showHierarchyPreview();
        });
    }

    // ============================================================
    // PROJECT CODE VALIDATION
    // ============================================================

    if (projectCodeInput) {
        projectCodeInput.addEventListener('blur', () => {
            const code = projectCodeInput.value.trim().toUpperCase();
            if (code && companySelect.value && clientSelect.value) {
                validateProjectCode(companySelect.value, clientSelect.value, code);
            }
        });

        // Auto uppercase the project code
        projectCodeInput.addEventListener('input', (e) => {
            e.target.value = e.target.value.toUpperCase();
        });
    }

    // ============================================================
    // FORM SUBMISSION
    // ============================================================

    if (projectForm && submitButton) {
        projectForm.addEventListener('submit', (event) => {
            // Auto uppercase project code before submission
            if (projectCodeInput && projectCodeInput.value) {
                projectCodeInput.value = projectCodeInput.value.trim().toUpperCase();
            }

            // Validate form
            if (!projectForm.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                projectForm.classList.add('was-validated');
                return;
            }

            // Update button state
            submitButton.disabled = true;
            const originalText = submitButton.textContent;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Saving...';

            // Restore button on error (optional timeout)
            const timeout = setTimeout(() => {
                submitButton.disabled = false;
                submitButton.textContent = originalText;
            }, 5000);

            // Override to allow submission
            projectForm.classList.remove('was-validated');
        });
    }

    // ============================================================
    // RESET BUTTON
    // ============================================================

    if (resetButton) {
        resetButton.addEventListener('click', () => {
            if (projectForm) {
                projectForm.classList.remove('was-validated');
                projectForm.reset();
            }

            // Reset dropdowns
            if (companySelect) companySelect.value = '';
            if (circleSelect) {
                circleSelect.innerHTML = '<option value="">Select circle</option>';
            }
            if (clientSelect) {
                clientSelect.innerHTML = '<option value="">Select client</option>';
            }

            // Hide preview
            if (hierarchyPreview) hierarchyPreview.style.display = 'none';

            // Clear validation classes
            const inputs = projectForm.querySelectorAll('.form-control, .form-select');
            inputs.forEach(input => {
                input.classList.remove('is-invalid');
                input.classList.remove('is-valid');
            });
        });
    }

    // ============================================================
    // REAL-TIME VALIDATION
    // ============================================================

    // Form fields real-time validation
    const formInputs = projectForm ? projectForm.querySelectorAll('.form-control, .form-select') : [];
    formInputs.forEach(input => {
        input.addEventListener('blur', () => {
            if (input.value) {
                input.classList.remove('is-invalid');
            }
        });

        input.addEventListener('input', () => {
            if (input.classList.contains('is-invalid') && input.value) {
                input.classList.remove('is-invalid');
            }
        });
    });

    // ============================================================
    // PAGE LOAD - INITIALIZE PREVIEW IF HIERARCHY EXISTS
    // ============================================================

    if (companySelect.value && circleSelect.value && clientSelect.value) {
        showHierarchyPreview();
    }

    // ============================================================
    // KEYBOARD SHORTCUTS
    // ============================================================

    document.addEventListener('keydown', (e) => {
        // Ctrl+S / Cmd+S to submit
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            if (submitButton && !submitButton.disabled) {
                projectForm.submit();
            }
        }
    });
});

/**
 * Utility function to format project code
 */
function formatProjectCode(code) {
    return code
        .toUpperCase()
        .replace(/[^A-Z0-9_-]/g, '')
        .substring(0, 20);
}

/**
 * Utility function to validate project code
 */
function isValidProjectCode(code) {
    const pattern = /^[A-Z0-9_-]{2,20}$/;
    return pattern.test(code);
}
