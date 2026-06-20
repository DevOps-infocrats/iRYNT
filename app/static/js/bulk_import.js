document.addEventListener('DOMContentLoaded', function() {
    const downloadBtn = document.getElementById('download-template');
    const chooseFileBtn = document.getElementById('choose-file');
    const fileInput = document.getElementById('excel-file');
    const importBtn = document.getElementById('import-users');
    const downloadErrorsBtn = document.getElementById('download-errors');
    const summaryDiv = document.getElementById('validation-summary');
    const summaryText = document.getElementById('summary-text');
    const errorDiv = document.getElementById('error-report');
    const errorTableBody = document.querySelector('#error-table tbody');

    // Download template
    downloadBtn.addEventListener('click', function() {
        window.location.href = '/user-management/bulk-import/template';
    });

    // Choose file
    chooseFileBtn.addEventListener('click', function() {
        fileInput.click();
    });

    // When file selected, validate
    fileInput.addEventListener('change', function() {
        if (!fileInput.files.length) return;
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        fetch('/user-management/bulk-import/validate', {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
        })
        .then(res => res.json())
        .then(data => {
            // Show validation summary
            summaryDiv.style.display = 'block';
            summaryText.textContent = JSON.stringify(data.summary, null, 2);
            // Populate errors table
            if (data.errors && data.errors.length) {
                errorDiv.style.display = 'block';
                errorTableBody.innerHTML = '';
                data.errors.forEach(err => {
                    const tr = document.createElement('tr');
                    const tdRow = document.createElement('td');
                    tdRow.textContent = err.row_number;
                    const tdCol = document.createElement('td');
                    tdCol.textContent = err.column || '';
                    const tdMsg = document.createElement('td');
                    tdMsg.textContent = err.message;
                    tr.appendChild(tdRow);
                    tr.appendChild(tdCol);
                    tr.appendChild(tdMsg);
                    errorTableBody.appendChild(tr);
                });
                downloadErrorsBtn.style.display = 'inline-block';
                importBtn.disabled = true;
            } else {
                // No errors – enable import
                errorDiv.style.display = 'none';
                downloadErrorsBtn.style.display = 'none';
                importBtn.disabled = false;
            }
        })
        .catch(err => {
            alert('Validation failed: ' + err);
        });
    });

    // Import users
    importBtn.addEventListener('click', function() {
        fetch('/user-management/bulk-import/import', {
            method: 'POST',
            credentials: 'same-origin'
        })
        .then(res => res.json())
        .then(data => {
            alert('Import completed. Created: ' + data.created + ', Updated: ' + data.updated + ', Failed: ' + data.failed);
            // Reset UI
            summaryDiv.style.display = 'none';
            errorDiv.style.display = 'none';
            downloadErrorsBtn.style.display = 'none';
            importBtn.disabled = true;
            fileInput.value = '';
        })
        .catch(err => {
            alert('Import failed: ' + err);
        });
    });

    // Download error report
    downloadErrorsBtn.addEventListener('click', function() {
        window.location.href = '/user-management/bulk-import/error-report';
    });
});
