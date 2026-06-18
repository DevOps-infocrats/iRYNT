const initDashboard = () => {
    if (typeof initDashboardSidebar === 'function') {
        initDashboardSidebar();
    }
    if (typeof initDashboardFilters === 'function') {
        initDashboardFilters();
    }
    if (typeof initDashboardWidgets === 'function') {
        initDashboardWidgets();
    }
    if (typeof initDashboardCharts === 'function') {
        initDashboardCharts();
    }
    if (typeof initRealtimeUpdates === 'function') {
        initRealtimeUpdates();
    }

    const refreshButton = document.getElementById('refreshDashboard');
    if (refreshButton) {
        refreshButton.addEventListener('click', () => {
            if (typeof refreshRealtimeDashboard === 'function') {
                refreshRealtimeDashboard();
            }
        });
    }
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDashboard);
} else {
    initDashboard();
}

