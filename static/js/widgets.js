const initDashboardWidgets = () => {
    animateCounters();
    refreshLiveOperations();
    populateNotifications();
    populateTimeline();
};

const animateCounters = () => {
    const counters = document.querySelectorAll('[data-counter]');
    counters.forEach((element) => {
        const target = Number(element.dataset.counter) || 0;
        let value = 0;
        const step = Math.max(1, Math.round(target / 50));
        const animate = () => {
            value += step;
            if (value >= target) {
                element.textContent = target;
                return;
            }
            element.textContent = value;
            window.requestAnimationFrame(animate);
        };
        animate();
    });
};

const refreshLiveOperations = (filters = {}) => {
    const tableBody = document.getElementById('liveOperationsTable');
    if (!tableBody) {
        return;
    }

    const sampleRows = (window.dashboardData && window.dashboardData.live_operations) || [];

    const filtered = sampleRows.filter((row) => {
        if (!filters.company || filters.company === 'all') {
            return true;
        }
        return row.task.toLowerCase().includes(filters.company.toLowerCase());
    });

    if (filtered.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-4">No live operations available.</td></tr>';
        return;
    }

    tableBody.innerHTML = filtered.map((row) => {
        const statusClass = row.status === 'Active'
            ? 'text-success'
            : row.status === 'In progress'
                ? 'text-primary'
                : row.status === 'Pending'
                    ? 'text-warning'
                    : 'text-muted';

        return `
            <tr>
                <td>${row.task}</td>
                <td class="${statusClass}">${row.status}</td>
                <td>${row.vehicles}</td>
                <td>${row.drivers}</td>
                <td>${row.eta}</td>
            </tr>
        `;
    }).join('');
};

const populateNotifications = () => {
    const feed = document.getElementById('notificationFeed');
    if (!feed) {
        return;
    }

    const items = (window.dashboardData && window.dashboardData.notifications) || [
        { message: 'No urgent alerts. All systems normal.', time: 'Now' },
    ];

    feed.innerHTML = items.map((item) => `
        <li>
            <div>
                <strong>${item.message}</strong>
                <span class="d-block text-soft small">${item.time}</span>
            </div>
        </li>
    `).join('');
};

const fetchNotificationBadge = async () => {
    try {
        const res = await fetch('/notifications/unread_count');
        if (!res.ok) return;
        const data = await res.json();
        const badge = document.getElementById('notificationBadge');
        if (!badge) return;
        if (data.unread && data.unread > 0) {
            badge.textContent = data.unread > 9 ? '9+' : data.unread;
            badge.classList.remove('visually-hidden');
        } else {
            badge.textContent = '';
            badge.classList.add('visually-hidden');
        }
    } catch (e) {
        // ignore
    }
};

const fetchNavbarNotifications = async () => {
    try {
        const res = await fetch('/notifications/feed?per_page=5');
        if (!res.ok) return;
        const data = await res.json();
        const list = document.getElementById('navbarNotificationList');
        if (!list) return;
        if (!data.items || data.items.length === 0) {
            list.innerHTML = '<li class="text-muted py-3 text-center">No notifications</li>';
            return;
        }
        list.innerHTML = data.items.map((item) => {
            return `
            <li class="px-2 py-2 border-bottom">
                <a href="/notifications/" class="text-decoration-none d-block">
                    <div class="d-flex justify-content-between">
                        <div>
                            <div class="small text-muted">${item.module || item.type} · <strong class="fw-semibold">${item.priority}</strong></div>
                            <div class="text-truncate" style="max-width:260px;">${item.message}</div>
                            <div class="small text-soft">${new Date(item.created_at).toLocaleString()}</div>
                        </div>
                    </div>
                </a>
            </li>
        `;
        }).join('');
    } catch (e) {
        // ignore
    }
};

const markAllRead = async () => {
    try {
        const res = await fetch('/notifications/mark_all_read', { method: 'POST' });
        if (!res.ok) return;
        await fetchNotificationBadge();
        await fetchNavbarNotifications();
    } catch (e) {}
};

document.addEventListener('DOMContentLoaded', () => {
    const markAllBtn = document.getElementById('markAllReadBtn');
    if (markAllBtn) {
        markAllBtn.addEventListener('click', (e) => {
            e.preventDefault();
            markAllRead();
        });
    }
    // initial fetch
    fetchNotificationBadge();
    fetchNavbarNotifications();
    // periodic refresh every 60 seconds
    setInterval(() => {
        fetchNotificationBadge();
    }, 60000);
});

const populateTimeline = () => {
    const timeline = document.getElementById('activityTimeline');
    if (!timeline) {
        return;
    }

    const events = (window.dashboardData && window.dashboardData.timeline) || [
        { title: 'No recent events', description: 'Timeline data is not available.', when: 'Now' },
    ];

    timeline.innerHTML = events.map((item) => `
        <div class="timeline-item">
            <h4 class="mb-1">${item.title}</h4>
            <p class="mb-2">${item.description}</p>
            <span class="text-soft small">${item.when}</span>
        </div>
    `).join('');
};

window.animateCounters = animateCounters;
window.refreshLiveOperations = refreshLiveOperations;
window.populateNotifications = populateNotifications;
window.populateTimeline = populateTimeline;
window.updateKpiWidgets = animateCounters;
