const initDashboardCharts = () => {
    if (typeof Chart === 'undefined') {
        return;
    }

    const attendanceCanvas = document.getElementById('attendanceTrendChart');
    const deploymentCanvas = document.getElementById('deploymentAnalyticsChart');

    const sharedOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false,
            },
            tooltip: {
                backgroundColor: '#1F2530',
                titleColor: '#ffffff',
                bodyColor: '#f5f5f5',
                borderColor: 'rgba(255,255,255,0.1)',
                borderWidth: 1,
            },
        },
        scales: {
            x: {
                grid: {
                    display: false,
                },
                ticks: {
                    color: '#666b72',
                },
            },
            y: {
                beginAtZero: true,
                grid: {
                    color: 'rgba(34, 48, 60, 0.08)',
                },
                ticks: {
                    color: '#666b72',
                },
            },
        },
    };

    if (attendanceCanvas) {
        const trend = (window.dashboardData && window.dashboardData.attendance_trend) || null;
        const labels = trend && trend.labels && trend.labels.length ? trend.labels : ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        const dataVals = trend && trend.values && trend.values.length ? trend.values : [72, 78, 81, 85, 88, 86, 90];
        new Chart(attendanceCanvas, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Attendance',
                        data: dataVals,
                        borderColor: '#FF4D8D',
                        backgroundColor: 'rgba(255, 77, 141, 0.16)',
                        tension: 0.35,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        fill: true,
                    },
                ],
            },
            options: {
                ...sharedOptions,
                plugins: {
                    ...sharedOptions.plugins,
                    tooltip: {
                        ...sharedOptions.plugins.tooltip,
                        callbacks: {
                            label: (context) => `${context.parsed.y}% attendance`,
                        },
                    },
                },
            },
        });
    }

    if (deploymentCanvas) {
        const deploymentData = (window.dashboardData && window.dashboardData.deployment) || null;
        const depLabels = (deploymentData && deploymentData.labels && deploymentData.labels.length) ? deploymentData.labels : ['Routes', 'Shifts', 'Assets', 'Tasks'];
        const depVals = (deploymentData && deploymentData.values && deploymentData.values.length) ? deploymentData.values : [88, 76, 92, 81];
        new Chart(deploymentCanvas, {
            type: 'bar',
            data: {
                labels: depLabels,
                datasets: [
                    {
                        label: 'Utilization',
                        data: depVals,
                        backgroundColor: ['#FF7A18', '#4D96FF', '#2FBF71', '#F4A261'],
                        borderRadius: 12,
                        maxBarThickness: 28,
                    },
                ],
            },
            options: {
                ...sharedOptions,
                scales: {
                    ...sharedOptions.scales,
                    x: {
                        ...sharedOptions.scales.x,
                        grid: {
                            display: false,
                        },
                    },
                },
            },
        });
    }
};
