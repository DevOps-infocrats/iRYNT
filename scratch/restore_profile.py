import json
import os

log_path = r"C:\Users\yadve\.gemini\antigravity-ide\brain\0b38bbb9-84ab-4c8b-ac8d-920522203c2d\.system_generated\logs\transcript.jsonl"
target_template = r"c:\Users\yadve\OneDrive\Desktop\Pratap infocrats\VIL_Project_docs\vil-project-full-report\templates\drivers\profile.html"

original_lines = []
found = False

with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        step = json.loads(line)
        if step.get('type') == 'VIEW_FILE':
            content = step.get('content', '')
            if 'Total Lines: 367' in content and 'Driver Profile' in content:
                # Extract the lines
                raw_lines = content.split('\n')
                for rl in raw_lines:
                    if ': ' in rl:
                        parts = rl.split(': ', 1)
                        if parts[0].strip().isdigit():
                            original_lines.append(parts[1] + '\n')
                found = True
                break

if found and original_lines:
    print("Original chunk (len = {}):\n".format(len(original_lines)), "".join(original_lines[32:51]))
    
    # We want to replace lines 33 to 50 (index 32 to 49 inclusive)
    new_chunk = [
        "                        {% if can_mark_attendance and profile.driver_profile %}\n",
        "                            {% if profile.today_attendance.status == 'checked_in' %}\n",
        "                                <a href=\"{{ url_for('attendance.live') }}\" class=\"btn btn-outline-danger\">Check Out (Verification Required)</a>\n",
        "                            {% elif profile.today_attendance.status == 'absent' %}\n",
        "                                <a href=\"{{ url_for('attendance.live') }}\" class=\"btn btn-outline-success\">Check In (Verification Required)</a>\n",
        "                            {% else %}\n",
        "                                <button type=\"button\" class=\"btn btn-outline-secondary\" disabled>Checked Out</button>\n",
        "                            {% endif %}\n",
        "                        {% endif %}\n"
    ]
    
    reconstructed = original_lines[:32] + new_chunk + original_lines[50:]
    
    with open(target_template, 'w', encoding='utf-8') as out:
        out.writelines(reconstructed)
    print("Restored and updated successfully!")
else:
    print("Not found in logs or empty lines.")
