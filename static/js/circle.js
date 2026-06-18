document.addEventListener('DOMContentLoaded', function () {
    const companySelect = $('#companySelect');
    const companyPreviewCol = document.getElementById('companyPreviewCol');
    const companyPreview = document.getElementById('companyPreview');
    const companyIdField = document.querySelector('input[name="company_id"]');
    const circleCode = document.getElementById('circle_code');
    const circleName = document.getElementById('circle_name');
    const submitBtn = document.querySelector('input[name="submit"]') || document.querySelector('button[type="submit"]');
    const codeFeedback = document.getElementById('codeFeedback');

    function toggleForm(enabled) {
        [circleCode, circleName, document.getElementById('status')].forEach(el => {
            if (!el) return;
            el.disabled = !enabled;
        });
        if (submitBtn) submitBtn.disabled = !enabled;
    }

    function renderCompanyPreview(data) {
        if (!data) return;
        companyPreview.innerHTML = `
            <div><strong>${data.company_name}</strong></div>
            <div class="text-muted">${data.company_code}</div>
            <div class="text-muted">${data.location || ''}</div>
            <div class="text-success">${data.status}</div>
        `;
        companyPreviewCol.style.display = 'block';
    }

    companySelect.select2({
        placeholder: 'Select company',
        allowClear: true,
        ajax: {
            url: '/circles/companies/search',
            dataType: 'json',
            delay: 250,
            data: function (params) {
                return { q: params.term };
            },
            processResults: function (data) {
                return { results: data.items };
            },
        },
        templateResult: function (item) {
            if (!item.id) return item.text;
            return $('<div><div><strong>' + item.company_name + '</strong> <small>(' + item.company_code + ')</small></div></div>');
        }
    });

    companySelect.on('select2:select', function (e) {
        const item = e.params.data;
        companyIdField.value = item.id;
        renderCompanyPreview(item);
        toggleForm(true);
    });

    companySelect.on('select2:clear', function () {
        companyIdField.value = '';
        companyPreviewCol.style.display = 'none';
        toggleForm(false);
    });

    // initially disabled
    toggleForm(false);

    // duplicate check
    if (circleCode) {
        circleCode.addEventListener('blur', function () {
            const code = circleCode.value.trim().toUpperCase();
            const company_id = companyIdField.value;
            if (!code || !company_id) return;
            fetch(`/circles/check_code?company_id=${company_id}&code=${encodeURIComponent(code)}`)
                .then(r => r.json())
                .then(data => {
                    if (data.exists) {
                        codeFeedback.style.display = 'block';
                        codeFeedback.textContent = 'That code is already in use for the selected company.';
                        circleCode.classList.add('is-invalid');
                    } else {
                        codeFeedback.style.display = 'none';
                        circleCode.classList.remove('is-invalid');
                    }
                });
        });
    }

    // reset handling
    document.getElementById('resetButton').addEventListener('click', function () {
        companySelect.val(null).trigger('change');
        companyPreviewCol.style.display = 'none';
        toggleForm(false);
    });
});
