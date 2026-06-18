/**
 * Roles & Access Control Module
 * Enterprise authorization and access intelligence
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeSelects();
    initializeHierarchy();
    initializeRoleRows();
});

function initializeSelects() {
    if ($.fn.select2) {
        $('.form-select').select2({
            allowClear: true,
            placeholder: 'Select an option',
            minimumResultsForSearch: 5,
        });
    }
}

function initializeHierarchy() {
    const hierarchyTree = document.querySelector('.hierarchy-tree');
    if (!hierarchyTree) return;

    const nodes = document.querySelectorAll('.hierarchy-node');
    nodes.forEach(node => {
        node.addEventListener('click', function() {
            const roleId = this.getAttribute('data-role-id');
            viewRoleDetails(roleId);
        });

        node.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.05)';
        });

        node.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });
}

function initializeRoleRows() {
    const roleRows = document.querySelectorAll('.role-row');
    roleRows.forEach(row => {
        row.addEventListener('click', function(e) {
            if (e.target.closest('.dropdown')) return;
            const roleId = this.getAttribute('data-role-id');
            // Could navigate or open detail panel
        });
    });
}

function viewRoleDetails(roleId) {
    // Navigate to role detail page
    window.location.href = `/roles/${roleId}/detail`;
}

// Filter form submission
const filterForm = document.querySelector('form');
if (filterForm) {
    filterForm.addEventListener('submit', function(e) {
        // Perform filtering
    });
}

// Export functionality
function exportPermissionMatrix() {
    console.log('Exporting permission matrix...');
    // Implementation would generate CSV/Excel export
}

function compareRoles() {
    const selected = document.querySelectorAll('input[name="role_select"]:checked');
    if (selected.length !== 2) {
        alert('Please select exactly 2 roles to compare');
        return;
    }

    const role1 = selected[0].value;
    const role2 = selected[1].value;
    window.location.href = `/roles/compare?role1=${role1}&role2=${role2}`;
}

function cloneRole(roleId) {
    // Show clone dialog
    console.log('Cloning role:', roleId);
}

function auditRoleAccess(roleId) {
    // Load and display audit logs
    console.log('Loading audit logs for:', roleId);
    
    fetch(`/roles/audit-logs?role_id=${roleId}`)
        .then(response => response.json())
        .then(data => {
            console.log('Audit logs:', data.logs);
            // Display audit logs in modal/panel
        })
        .catch(error => console.error('Error loading audit logs:', error));
}

// Real-time KPI updates (optional)
function updateKPIs() {
    fetch('/roles/kpis')
        .then(response => response.json())
        .then(data => {
            updateKPICards(data);
        })
        .catch(error => console.error('Error updating KPIs:', error));
}

function updateKPICards(kpis) {
    const kpiCards = document.querySelectorAll('.kpi-card');
    kpiCards.forEach((card, index) => {
        if (index < kpis.length) {
            const kpi = kpis[index];
            card.querySelector('.kpi-value').textContent = kpi.value;
            card.querySelector('.kpi-meta').textContent = kpi.description;
            card.querySelector('.kpi-footnote strong').textContent = kpi.trend;
        }
    });
}

// Hierarchy data loading (AJAX)
function loadHierarchy() {
    fetch('/roles/hierarchy')
        .then(response => response.json())
        .then(data => {
            console.log('Hierarchy data:', data);
            renderHierarchy(data);
        })
        .catch(error => console.error('Error loading hierarchy:', error));
}

function renderHierarchy(hierarchy) {
    // Implement hierarchy rendering based on data
    console.log('Rendering hierarchy...');
}

// Accessibility enhancements
function enhanceAccessibility() {
    const buttons = document.querySelectorAll('button, a.btn');
    buttons.forEach(btn => {
        if (!btn.getAttribute('aria-label')) {
            btn.setAttribute('aria-label', btn.textContent.trim());
        }
    });
}

// Initialize on page load
window.addEventListener('load', function() {
    enhanceAccessibility();
});
