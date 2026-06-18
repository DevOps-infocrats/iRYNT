import { renderSubzoneAnalyticsChart } from './analytics.js';
import { initRealtimeStatus } from './realtime.js';

export function initSubzoneDashboard() {
    const counterElements = document.querySelectorAll('[data-counter]');
    counterElements.forEach(element => {
        const target = Number(element.dataset.counter || 0);
        let current = 0;
        const step = Math.max(1, Math.round(target / 45));
        const interval = setInterval(() => {
            current += step;
            if (current >= target) {
                element.textContent = target;
                clearInterval(interval);
            } else {
                element.textContent = current;
            }
        }, 12);
    });

    const operationsTable = document.getElementById('operationsTableBody');
    initRealtimeStatus(operationsTable);

    const analyticsCanvas = document.getElementById('subzoneAnalyticsChart');
    if (typeof Chart !== 'undefined' && analyticsCanvas) {
        renderSubzoneAnalyticsChart(analyticsCanvas);
    }
}
