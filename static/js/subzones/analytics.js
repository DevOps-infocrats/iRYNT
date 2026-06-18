export function renderSubzoneAnalyticsChart(canvas) {
    if (!canvas) {
        return;
    }

    const ctx = canvas.getContext('2d');
    if (!ctx) {
        return;
    }

    const provided = (window.subzoneAnalyticsData && window.subzoneAnalyticsData) || {};
    const labels = provided.labels && provided.labels.length ? provided.labels : ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const deploymentValues = provided.deploymentValues && provided.deploymentValues.length ? provided.deploymentValues : [28, 42, 35, 58, 51, 63, 72];
    const attendanceValues = provided.attendanceValues && provided.attendanceValues.length ? provided.attendanceValues : [65, 58, 72, 68, 75, 82, 88];

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Deployment activity',
                    data: deploymentValues,
                    borderColor: 'rgba(255, 122, 24, 0.95)',
                    backgroundColor: 'rgba(255, 122, 24, 0.15)',
                    tension: 0.35,
                    fill: true,
                },
                {
                    label: 'Attendance trend',
                    data: attendanceValues,
                    borderColor: 'rgba(77, 150, 255, 0.95)',
                    backgroundColor: 'rgba(77, 150, 255, 0.12)',
                    tension: 0.35,
                    fill: true,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom' },
            },
            scales: {
                x: { grid: { display: false } },
                y: { grid: { color: 'rgba(232, 228, 224, 0.7)' }, beginAtZero: true },
            },
        },
    });
}
