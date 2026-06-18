const initRealtimeUpdates = () => {
    if (typeof refreshRealtimeDashboard !== 'function') {
        return;
    }

    refreshRealtimeDashboard();
    window.setInterval(() => {
        refreshRealtimeDashboard();
    }, 12000);
};

const refreshRealtimeDashboard = () => {
    if (typeof refreshLiveOperations === 'function') {
        refreshLiveOperations(getDashboardFilters ? getDashboardFilters() : {});
    }
    if (typeof populateNotifications === 'function') {
        populateNotifications();
    }
    if (typeof populateTimeline === 'function') {
        populateTimeline();
    }
    updateNotificationBadge();
};

const updateNotificationBadge = () => {
    const badge = document.getElementById('notificationBadge');
    if (!badge) {
        return;
    }

    const notificationCount = (window.dashboardData && window.dashboardData.notifications && window.dashboardData.notifications.length) || 0;
    badge.textContent = notificationCount > 0 ? notificationCount.toString() : '';
    badge.style.visibility = notificationCount > 0 ? 'visible' : 'hidden';
};

window.refreshRealtimeDashboard = refreshRealtimeDashboard;
window.initRealtimeUpdates = initRealtimeUpdates;
