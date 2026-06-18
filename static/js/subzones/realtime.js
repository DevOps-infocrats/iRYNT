export function initRealtimeStatus(tableElement) {
    if (!tableElement) {
        return;
    }

    const provided = (window.subzoneAnalyticsData && window.subzoneAnalyticsData.operations) || [];
    const rows = provided.length ? provided : [
        { task: 'Inbound dispatch', status: 'In transit', vehicles: 12, drivers: 9, eta: '00:24' },
        { task: 'Emergency pickup', status: 'Delayed', vehicles: 3, drivers: 3, eta: '01:10' },
        { task: 'Warehouse rotation', status: 'Idle', vehicles: 6, drivers: 5, eta: 'N/A' },
    ];

    tableElement.innerHTML = rows.map(row => `
        <tr>
            <td>${row.task}</td>
            <td><span class="badge bg-secondary">${row.status}</span></td>
            <td>${row.vehicles}</td>
            <td>${row.drivers}</td>
            <td>${row.eta || 'N/A'}</td>
        </tr>
    `).join('');
}
