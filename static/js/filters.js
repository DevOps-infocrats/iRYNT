const initDashboardFilters = () => {
    const formFields = {
        company: document.getElementById('filterCompany'),
        circle: document.getElementById('filterCircle'),
        client: document.getElementById('filterClient'),
        project: document.getElementById('filterProject'),
        subzone: document.getElementById('filterSubzone'),
        range: document.getElementById('filterDateRange'),
    };

    const defaultFilters = {
        company: 'all',
        circle: 'all',
        client: 'all',
        project: 'all',
        subzone: 'all',
        range: 'Last 30 days',
    };

    const loadFilters = () => {
        try {
            const stored = JSON.parse(localStorage.getItem('dashboardFilters') || '{}');
            return { ...defaultFilters, ...stored };
        } catch (error) {
            return defaultFilters;
        }
    };

    const filters = loadFilters();

    const syncFields = () => {
        Object.entries(formFields).forEach(([key, element]) => {
            if (!element) {
                return;
            }
            if (element.tagName.toLowerCase() === 'input') {
                element.value = filters[key];
            } else {
                element.value = filters[key] || 'all';
            }
        });
    };

    const saveFilters = () => {
        localStorage.setItem('dashboardFilters', JSON.stringify(filters));
    };

    const notifyFilterChange = () => {
        saveFilters();
        if (typeof updateDashboardData === 'function') {
            updateDashboardData(filters);
        }
        document.dispatchEvent(new CustomEvent('dashboardFiltersUpdated', { detail: { ...filters } }));
    };

    const attachListeners = () => {
        Object.entries(formFields).forEach(([key, element]) => {
            if (!element) {
                return;
            }
            element.addEventListener('change', () => {
                filters[key] = element.value;
                notifyFilterChange();
            });
        });
    };

    syncFields();
    attachListeners();
    notifyFilterChange();

    window.getDashboardFilters = () => ({ ...filters });
    window.updateDashboardData = (newFilters) => {
        if (typeof refreshLiveOperations === 'function') {
            refreshLiveOperations(newFilters);
        }
        if (typeof updateKpiWidgets === 'function') {
            updateKpiWidgets(newFilters);
        }
    };
};
