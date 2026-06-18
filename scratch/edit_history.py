import os

target_file = 'templates/attendance/history.html'
with open(target_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Normalize
content_norm = content.replace('\r\n', '\n')

search_str = """                <thead class="table-light">
                    <tr>
                        <th>Date</th>
                        <th>Driver</th>
                        <th>Shift</th>
                        <th>Check-in</th>
                        <th>Check-out</th>
                        <th>Status</th>
                        <th>Hours</th>
                        <th>Notes</th>
                    </tr>
                </thead>
                <tbody>
                    {% if records %}
                        {% for record in records %}
                            <tr>
                                <td>{{ record.date.strftime('%Y-%m-%d') }}</td>
                                <td>{{ record.driver.user.username if record.driver and record.driver.user else 'N/A' }}</td>
                                <td>{{ record.shift_name or 'Default' }}</td>
                                <td>{{ to_india_datetime(record.check_in).strftime('%Y-%m-%d %H:%M:%S') if record.check_in else '—' }}</td>
                                <td>{{ to_india_datetime(record.check_out).strftime('%Y-%m-%d %H:%M:%S') if record.check_out else '—' }}</td>
                                <td>{{ record.status }}</td>
                                <td>{{ record.hours_worked or '—' }}</td>
                                <td>{{ record.notes or '—' }}</td>
                            </tr>"""

replace_str = """                <thead class="table-light">
                    <tr>
                        <th>Date</th>
                        <th>Driver</th>
                        <th>Shift</th>
                        <th>Check-in</th>
                        <th>Check-out</th>
                        <th>Status</th>
                        <th>Hours</th>
                        <th>Notes</th>
                        <th>Verification</th>
                    </tr>
                </thead>
                <tbody>
                    {% if records %}
                        {% for record in records %}
                            <tr>
                                <td>{{ record.date.strftime('%Y-%m-%d') }}</td>
                                <td>{{ record.driver.user.username if record.driver and record.driver.user else 'N/A' }}</td>
                                <td>{{ record.shift_name or 'Default' }}</td>
                                <td>{{ to_india_datetime(record.check_in).strftime('%Y-%m-%d %H:%M:%S') if record.check_in else '—' }}</td>
                                <td>{{ to_india_datetime(record.check_out).strftime('%Y-%m-%d %H:%M:%S') if record.check_out else '—' }}</td>
                                <td>{{ record.status }}</td>
                                <td>{{ record.hours_worked or '—' }}</td>
                                <td>{{ record.notes or '—' }}</td>
                                <td>
                                    {% if record.selfie_storage_path %}
                                        <a href="{{ url_for('attendance.view_verification_image', attendance_id=record.id, image_type='selfie') }}" target="_blank" class="badge bg-info text-decoration-none">Selfie</a>
                                    {% endif %}
                                    {% if record.dashboard_storage_path %}
                                        <a href="{{ url_for('attendance.view_verification_image', attendance_id=record.id, image_type='dashboard') }}" target="_blank" class="badge bg-secondary text-decoration-none">Dashboard</a>
                                    {% endif %}
                                    {% if not record.selfie_storage_path and not record.dashboard_storage_path %}
                                        <span class="text-soft">—</span>
                                    {% endif %}
                                </td>
                            </tr>"""

if search_str.replace('\r\n', '\n') in content_norm:
    updated = content_norm.replace(search_str.replace('\r\n', '\n'), replace_str.replace('\r\n', '\n'))
    with open(target_file, 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(updated)
    print("Success: templates/attendance/history.html updated!")
else:
    print("Error: Search block not found.")
