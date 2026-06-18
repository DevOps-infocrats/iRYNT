document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.querySelector('#workforceSearch');
    const suggestions = document.querySelector('#searchSuggestions');
    const companySelect = document.querySelector('#company_id');
    const circleSelect = document.querySelector('#circle_id');
    const clientSelect = document.querySelector('#client_id');
    const projectSelect = document.querySelector('#project_id');

    if (window.jQuery && window.jQuery.fn.select2) {
        document.querySelectorAll('.select2').forEach(function (element) {
            window.jQuery(element).select2({
                minimumResultsForSearch: 5,
                width: '100%',
                dropdownParent: window.jQuery(document.body),
            });
        });
    }

    function fetchHierarchy(type, parentId, target) {
        if (!target) return;
        target.innerHTML = '<option value="">Loading...</option>';
        fetch(`/users/ajax/hierarchy?type=${type}&parent_id=${encodeURIComponent(parentId || '')}`)
            .then(function (response) {
                return response.json();
            })
            .then(function (data) {
                target.innerHTML = '<option value="">Select ' + target.getAttribute('data-label') + '</option>';
                data.forEach(function (item) {
                    const option = document.createElement('option');
                    option.value = item.id;
                    option.textContent = item.text;
                    target.appendChild(option);
                });
                if (window.jQuery && window.jQuery.fn.select2) {
                    window.jQuery(target).trigger('change.select2');
                }
            })
            .catch(function () {
                target.innerHTML = '<option value="">Select ' + target.getAttribute('data-label') + '</option>';
            });
    }

    if (companySelect && circleSelect) {
        companySelect.addEventListener('change', function () {
            fetchHierarchy('circle', this.value, circleSelect);
            fetchHierarchy('client', '', clientSelect);
            fetchHierarchy('project', '', projectSelect);
        });
    }

    if (circleSelect && clientSelect) {
        circleSelect.addEventListener('change', function () {
            fetchHierarchy('client', this.value, clientSelect);
            fetchHierarchy('project', '', projectSelect);
        });
    }

    if (clientSelect && projectSelect) {
        clientSelect.addEventListener('change', function () {
            fetchHierarchy('project', this.value, projectSelect);
        });
    }

    if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener('input', function () {
            const query = this.value.trim();
            if (debounceTimer) {
                clearTimeout(debounceTimer);
            }
            if (!query) {
                suggestions.classList.remove('active');
                return;
            }
            debounceTimer = setTimeout(function () {
                fetch(`/users/ajax/search?q=${encodeURIComponent(query)}`)
                    .then(function (response) {
                        return response.json();
                    })
                    .then(function (items) {
                        if (!items.length) {
                            suggestions.innerHTML = '<ul><li>No matching workforce records found.</li></ul>';
                        } else {
                            suggestions.innerHTML = '<ul>' + items.map(function (item) {
                                return `<li data-user-id="${item.id}"><strong>${item.name}</strong> <span class="text-soft">${item.email}</span> <span class="badge bg-info ms-2">${item.role}</span></li>`;
                            }).join('') + '</ul>';
                        }
                        suggestions.classList.add('active');
                    });
            }, 350);
        });

        document.addEventListener('click', function (event) {
            if (!event.target.closest('#searchSuggestions') && event.target !== searchInput) {
                suggestions.classList.remove('active');
            }
        });

        suggestions.addEventListener('click', function (event) {
            const item = event.target.closest('li');
            if (item && item.dataset.userId) {
                window.location.href = `/users/${item.dataset.userId}`;
            }
        });
    }

    const attendanceCanvas = document.getElementById('attendanceChart');
    const roleCanvas = document.getElementById('roleDistributionChart');

    if (attendanceCanvas) {
        const profileAnalytics = window.profileAnalytics || (window.dashboardData && window.dashboardData.attendance_trend) || null;
        const labels = profileAnalytics && profileAnalytics.labels && profileAnalytics.labels.length ? profileAnalytics.labels : ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        const dataVals = profileAnalytics && profileAnalytics.values && profileAnalytics.values.length ? profileAnalytics.values : [82, 88, 91, 94, 96, 89, 84];
        new Chart(attendanceCanvas, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Workforce Attendance',
                    data: dataVals,
                    fill: true,
                    borderColor: '#FF7A18',
                    backgroundColor: 'rgba(255, 122, 24, 0.18)',
                    tension: 0.32,
                }],
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false },
                },
                scales: {
                    x: { grid: { color: 'rgba(31, 37, 48, 0.06)' } },
                    y: { beginAtZero: true, max: 100 },
                },
            },
        });
    }

    if (roleCanvas) {
        const roleData = window.profileAnalytics && window.profileAnalytics.role_labels && window.profileAnalytics.role_values ? {
            labels: window.profileAnalytics.role_labels,
            values: window.profileAnalytics.role_values
        } : null;
        const labels = roleData && roleData.labels && roleData.labels.length ? roleData.labels : ['Super Admin', 'Manager', 'Driver', 'Helper', 'Customer', 'Operations'];
        const values = roleData && roleData.values && roleData.values.length ? roleData.values : [8, 14, 28, 20, 12, 18];
        new Chart(roleCanvas, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: ['#FF7A18', '#4D96FF', '#2FBF71', '#FF4D8D', '#F4A261', '#8C8681'],
                    borderWidth: 0,
                }],
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom' },
                },
            },
        });
    }
});
