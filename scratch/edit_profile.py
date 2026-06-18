import zipfile
import os

zip_path = '../vil_zip_4.0.zip'
target_file = 'templates/drivers/profile.html'

# 1. Extract from zip
with zipfile.ZipFile(zip_path, 'r') as z:
    content = z.read('vil-project-full-report/templates/drivers/profile.html').decode('utf-8')

# 2. Define search and replace block
search_block = """                        {% if can_mark_attendance and profile.driver_profile %}
                            {% if profile.today_attendance.status == 'checked_in' %}
                                <form method="post" action="{{ url_for('attendance.mark') }}" class="m-0">
                                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                                    <input type="hidden" name="driver_profile_id" value="{{ profile.driver_profile.id }}">
                                    <input type="hidden" name="action" value="check_out">
                                    <button type="submit" class="btn btn-outline-danger">Check Out</button>
                                </form>
                            {% elif profile.today_attendance.status == 'absent' %}
                                <form method="post" action="{{ url_for('attendance.mark') }}" class="m-0">
                                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                                    <input type="hidden" name="driver_profile_id" value="{{ profile.driver_profile.id }}">
                                    <input type="hidden" name="action" value="check_in">
                                    <button type="submit" class="btn btn-outline-success">Check In</button>
                                </form>
                            {% else %}
                                <button type="button" class="btn btn-outline-secondary" disabled>Checked Out</button>
                            {% endif %}
                        {% endif %}"""

replace_block = """                        {% if can_mark_attendance and profile.driver_profile %}
                            {% if profile.today_attendance.status == 'checked_in' %}
                                <a href="{{ url_for('attendance.live') }}" class="btn btn-outline-danger">Check Out (Verification Required)</a>
                            {% elif profile.today_attendance.status == 'absent' %}
                                <a href="{{ url_for('attendance.live') }}" class="btn btn-outline-success">Check In (Verification Required)</a>
                            {% else %}
                                <button type="button" class="btn btn-outline-secondary" disabled>Checked Out</button>
                            {% endif %}
                        {% endif %}"""

# Replace normalizing line endings to prevent matching issues
content_norm = content.replace('\r\n', '\n')
search_norm = search_block.replace('\r\n', '\n')
replace_norm = replace_block.replace('\r\n', '\n')

if search_norm in content_norm:
    updated = content_norm.replace(search_norm, replace_norm)
    # Write back with original line endings
    os.makedirs(os.path.dirname(target_file), exist_ok=True)
    with open(target_file, 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(updated)
    print("Success: File templates/drivers/profile.html restored and updated!")
else:
    print("Error: Search block not found in original file contents.")
