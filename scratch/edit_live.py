import os

target_file = 'templates/attendance/live.html'
with open(target_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Normalize
content_norm = content.replace('\r\n', '\n')

# 1. Update Table Headers
search_headers = """                        <th>Hours</th>
                        <th>Geo Status</th>
                        <th class="text-end">Actions</th>"""

replace_headers = """                        <th>Hours</th>
                        <th>Geo Status</th>
                        <th>Verification</th>
                        <th class="text-end">Actions</th>"""

# 2. Update Table Rows
search_rows = """                                <td>{{ driver.hours_worked if driver.hours_worked else '-' }}</td>
                                <td>
                                    {% if driver.geo_status == 'GEO_VERIFIED' %}
                                        <span class="badge bg-success">GEO VERIFIED</span>
                                    {% elif driver.geo_status == 'OUTSIDE_GEOFENCE' %}
                                        <span class="badge bg-warning text-dark">OUTSIDE GEOFENCE</span>
                                    {% elif driver.geo_status == 'LOW_ACCURACY' %}
                                        <span class="badge bg-info text-white">LOW ACCURACY</span>
                                    {% elif driver.geo_status == 'MANUAL_OVERRIDE' %}
                                        <span class="badge bg-secondary">MANUAL OVERRIDE</span>
                                    {% else %}
                                        <span class="text-soft">Pending</span>
                                    {% endif %}
                                    <div class="small text-soft">
                                        {{ driver.subzone_name or 'No subzone' }}
                                        {% if driver.allowed_radius %} / Radius {{ driver.allowed_radius }}m{% endif %}
                                        {% if driver.geo_distance_meters is not none %} / Distance {{ driver.geo_distance_meters }}m{% endif %}
                                    </div>
                                </td>"""

replace_rows = """                                <td>{{ driver.hours_worked if driver.hours_worked else '-' }}</td>
                                <td>
                                    {% if driver.geo_status == 'GEO_VERIFIED' %}
                                        <span class="badge bg-success">GEO VERIFIED</span>
                                    {% elif driver.geo_status == 'OUTSIDE_GEOFENCE' %}
                                        <span class="badge bg-warning text-dark">OUTSIDE GEOFENCE</span>
                                    {% elif driver.geo_status == 'LOW_ACCURACY' %}
                                        <span class="badge bg-info text-white">LOW ACCURACY</span>
                                    {% elif driver.geo_status == 'MANUAL_OVERRIDE' %}
                                        <span class="badge bg-secondary">MANUAL OVERRIDE</span>
                                    {% else %}
                                        <span class="text-soft">Pending</span>
                                    {% endif %}
                                    <div class="small text-soft">
                                        {{ driver.subzone_name or 'No subzone' }}
                                        {% if driver.allowed_radius %} / Radius {{ driver.allowed_radius }}m{% endif %}
                                        {% if driver.geo_distance_meters is not none %} / Distance {{ driver.geo_distance_meters }}m{% endif %}
                                    </div>
                                </td>
                                <td>
                                    {% if driver.attendance_id %}
                                        {% if driver.selfie_storage_path %}
                                            <a href="{{ url_for('attendance.view_verification_image', attendance_id=driver.attendance_id, image_type='selfie') }}" target="_blank" class="badge bg-info text-decoration-none">Selfie</a>
                                        {% endif %}
                                        {% if driver.dashboard_storage_path %}
                                            <a href="{{ url_for('attendance.view_verification_image', attendance_id=driver.attendance_id, image_type='dashboard') }}" target="_blank" class="badge bg-secondary text-decoration-none">Dashboard</a>
                                        {% endif %}
                                        {% if not driver.selfie_storage_path and not driver.dashboard_storage_path %}
                                            <span class="text-soft">—</span>
                                        {% endif %}
                                    {% else %}
                                        <span class="text-soft">—</span>
                                    {% endif %}
                                </td>"""

# 3. Update JavaScript tag and inject Modal HTML
search_js = """<script>
document.addEventListener('DOMContentLoaded', function () {
    const statusMessage = document.getElementById('geoStatusMessage');

    document.querySelectorAll('.attendance-geo-form').forEach(function (form) {
        form.addEventListener('submit', function (event) {
            if (form.dataset.geoReady === '1') {
                return;
            }

            event.preventDefault();
            const submitter = event.submitter;
            if (submitter && submitter.name) {
                let actionInput = form.querySelector('input[name="' + submitter.name + '"][type="hidden"]');
                if (!actionInput) {
                    actionInput = document.createElement('input');
                    actionInput.type = 'hidden';
                    actionInput.name = submitter.name;
                    form.appendChild(actionInput);
                }
                actionInput.value = submitter.value;
            }

            if (!navigator.geolocation) {
                statusMessage.textContent = 'GPS is not supported by this browser. Attendance will be sent for manual geo review.';
                form.dataset.geoReady = '1';
                form.submit();
                return;
            }

            statusMessage.textContent = 'Requesting live GPS for attendance verification...';
            navigator.geolocation.getCurrentPosition(
                function (position) {
                    form.querySelector('.geo-latitude').value = position.coords.latitude;
                    form.querySelector('.geo-longitude').value = position.coords.longitude;
                    form.querySelector('.geo-accuracy').value = position.coords.accuracy;
                    statusMessage.textContent = 'GPS captured. Submitting attendance for geo verification.';
                    form.dataset.geoReady = '1';
                    form.submit();
                },
                function () {
                    statusMessage.textContent = 'GPS could not be captured. Attendance will be sent for manual geo review.';
                    form.dataset.geoReady = '1';
                    form.submit();
                },
                {
                    enableHighAccuracy: true,
                    timeout: 12000,
                    maximumAge: 0
                }
            );
        });
    });
});
</script>"""

replace_js = """<!-- Glassmorphic Camera Verification Modal -->
<div class="modal fade" id="verificationModal" data-bs-backdrop="static" data-bs-keyboard="false" tabindex="-1" aria-labelledby="verificationModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered modal-lg">
        <div class="modal-content border-0 shadow-lg" style="background: rgba(30, 34, 45, 0.85); backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px); border-radius: 16px; color: #fff; border: 1px solid rgba(255, 255, 255, 0.1) !important;">
            <div class="modal-header border-0 pb-0">
                <h5 class="modal-title" id="verificationModalLabel" style="font-weight: 700; background: linear-gradient(135deg, #a5b4fc, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Identity & Vehicle Verification</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close" id="btnCancelVerification"></button>
            </div>
            <div class="modal-body p-4">
                <form id="verificationForm" method="post" action="{{ url_for('attendance.mark') }}" enctype="multipart/form-data">
                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                    <input type="hidden" name="driver_profile_id" id="modalDriverProfileId">
                    <input type="hidden" name="action" id="modalAction">
                    <input type="hidden" name="latitude" id="modalLatitude">
                    <input type="hidden" name="longitude" id="modalLongitude">
                    <input type="hidden" name="accuracy" id="modalAccuracy">
                    
                    <input type="hidden" name="selfie_data" id="modalSelfieData">
                    <input type="hidden" name="dashboard_data" id="modalDashboardData">

                    <!-- Camera status indicator -->
                    <div id="cameraAlert" class="alert alert-info py-2 px-3 small border-0 mb-3" style="background: rgba(99, 102, 241, 0.15); color: #c7d2fe; display: none;"></div>

                    <div class="row g-4">
                        <!-- Left Side: Live Capture / Stream -->
                        <div class="col-12 col-md-6">
                            <div class="card bg-dark text-white border-0 overflow-hidden" style="border-radius: 12px; height: 280px; position: relative;">
                                <video id="videoElement" autoplay playsinline class="w-100 h-100" style="object-fit: cover; background: #000;"></video>
                                <canvas id="canvasElement" style="display: none;"></canvas>
                                
                                <div class="camera-overlay-text small text-center w-100 py-1" style="position: absolute; bottom: 0; background: rgba(0,0,0,0.6); color: #fff;">
                                    Live Camera Feed
                                </div>
                            </div>
                            
                            <div class="d-flex justify-content-center gap-2 mt-3">
                                <button type="button" class="btn btn-primary btn-sm d-flex align-items-center gap-1 px-3 py-2" id="btnCapture" style="background: linear-gradient(135deg, #6366f1, #4f46e5); border: none; border-radius: 8px; font-weight: 500;">
                                    <span class="material-symbols-outlined fs-6">photo_camera</span> Capture Frame
                                </button>
                            </div>
                        </div>

                        <!-- Right Side: Selfie & Dashboard Tabs & Previews -->
                        <div class="col-12 col-md-6">
                            <!-- Tabs Navigation -->
                            <ul class="nav nav-pills mb-3 gap-2" id="verificationTabs" role="tablist">
                                <li class="nav-item" role="presentation">
                                    <button class="nav-link active px-3 py-2 small" id="selfie-capture-tab" data-bs-toggle="pill" data-bs-target="#selfie-capture-pane" type="button" role="tab" style="border-radius: 8px; color: #fff; background: rgba(255,255,255,0.08);">
                                        1. Driver Selfie
                                    </button>
                                </li>
                                <li class="nav-item" role="presentation">
                                    <button class="nav-link px-3 py-2 small" id="dashboard-capture-tab" data-bs-toggle="pill" data-bs-target="#dashboard-capture-pane" type="button" role="tab" style="border-radius: 8px; color: #fff; background: rgba(255,255,255,0.08);">
                                        2. Vehicle Dashboard
                                    </button>
                                </li>
                            </ul>

                            <div class="tab-content" id="verificationTabsContent">
                                <!-- Tab 1: Selfie -->
                                <div class="tab-pane fade show active" id="selfie-capture-pane" role="tabpanel" aria-labelledby="selfie-capture-tab">
                                    <div class="preview-container border rounded d-flex align-items-center justify-content-center bg-black overflow-hidden" style="height: 150px; border-color: rgba(255,255,255,0.15) !important;">
                                        <img id="selfiePreview" src="" class="img-fluid h-100" style="object-fit: contain; display: none;">
                                        <span id="selfiePlaceholder" class="text-muted small">No selfie captured yet</span>
                                    </div>
                                    
                                    <div class="mt-3">
                                        <label class="form-label small text-soft">Or manual file upload (JPG/PNG/WEBP)</label>
                                        <input type="file" name="selfie_file" id="selfieFileInput" accept="image/*" class="form-control form-control-sm bg-transparent border-secondary text-white">
                                    </div>
                                </div>

                                <!-- Tab 2: Dashboard -->
                                <div class="tab-pane fade" id="dashboard-capture-pane" role="tabpanel" aria-labelledby="dashboard-capture-tab">
                                    <div class="preview-container border rounded d-flex align-items-center justify-content-center bg-black overflow-hidden" style="height: 150px; border-color: rgba(255,255,255,0.15) !important;">
                                        <img id="dashboardPreview" src="" class="img-fluid h-100" style="object-fit: contain; display: none;">
                                        <span id="dashboardPlaceholder" class="text-muted small">No dashboard captured yet</span>
                                    </div>
                                    
                                    <div class="mt-3">
                                        <label class="form-label small text-soft">Or manual file upload (JPG/PNG/WEBP)</label>
                                        <input type="file" name="dashboard_file" id="dashboardFileInput" accept="image/*" class="form-control form-control-sm bg-transparent border-secondary text-white">
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Footer Warning & Controls -->
                    <div class="border-top border-secondary mt-4 pt-3 d-flex flex-column flex-sm-row justify-content-between align-items-center gap-3">
                        <span class="text-soft small" id="gpsStatusModal">GPS location status: Pending</span>
                        <div class="d-flex gap-2">
                            <button type="button" class="btn btn-outline-secondary btn-sm" data-bs-dismiss="modal" id="btnModalClose">Cancel</button>
                            <button type="submit" class="btn btn-success btn-sm px-4" id="btnSubmitAttendance" style="background: linear-gradient(135deg, #10b981, #059669); border: none; border-radius: 8px;">
                                Confirm & Submit
                            </button>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>

<style>
/* Glassmorphism modal styling */
#verificationModal .nav-link.active {
    background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
    font-weight: 600;
}
.camera-overlay-text {
    font-weight: 500;
    letter-spacing: 0.5px;
}
.preview-container {
    transition: all 0.3s ease;
}
.preview-container:hover {
    border-color: rgba(99, 102, 241, 0.4) !important;
}
</style>

<script>
document.addEventListener('DOMContentLoaded', function () {
    const statusMessage = document.getElementById('geoStatusMessage');
    const modal = new bootstrap.Modal(document.getElementById('verificationModal'));
    
    let activeStream = null;
    let currentTab = 'selfie'; // 'selfie' or 'dashboard'
    
    const video = document.getElementById('videoElement');
    const canvas = document.getElementById('canvasElement');
    const cameraAlert = document.getElementById('cameraAlert');
    
    // UI elements for tab states
    const selfiePreview = document.getElementById('selfiePreview');
    const selfiePlaceholder = document.getElementById('selfiePlaceholder');
    const dashboardPreview = document.getElementById('dashboardPreview');
    const dashboardPlaceholder = document.getElementById('dashboardPlaceholder');
    
    // Hidden data storage fields
    const modalSelfieData = document.getElementById('modalSelfieData');
    const modalDashboardData = document.getElementById('modalDashboardData');

    function stopCamera() {
        if (activeStream) {
            activeStream.getTracks().forEach(track => track.stop());
            activeStream = null;
        }
    }

    function startCamera(facingMode) {
        stopCamera();
        
        // Browser media query constraints
        const constraints = {
            video: { 
                facingMode: facingMode,
                width: { ideal: 640 },
                height: { ideal: 480 }
            }
        };
        
        navigator.mediaDevices.getUserMedia(constraints)
            .then(stream => {
                activeStream = stream;
                video.srcObject = stream;
                cameraAlert.style.display = 'none';
            })
            .catch(err => {
                console.warn("Camera access denied or unavailable: ", err);
                cameraAlert.textContent = "Camera unavailable. You can upload files manually below.";
                cameraAlert.style.display = 'block';
            });
    }

    // Intercept row actions
    document.querySelectorAll('.attendance-geo-form').forEach(function (form) {
        form.addEventListener('submit', function (event) {
            event.preventDefault();
            
            const submitter = event.submitter;
            const action = submitter ? submitter.value : 'check_in';
            const driverId = form.querySelector('input[name="driver_profile_id"]').value;
            
            // Set modal values
            document.getElementById('modalDriverProfileId').value = driverId;
            document.getElementById('modalAction').value = action;
            
            // Clear prior modal state
            modalSelfieData.value = '';
            modalDashboardData.value = '';
            selfiePreview.style.display = 'none';
            selfiePlaceholder.style.display = 'block';
            dashboardPreview.style.display = 'none';
            dashboardPlaceholder.style.display = 'block';
            document.getElementById('selfieFileInput').value = '';
            document.getElementById('dashboardFileInput').value = '';
            document.getElementById('gpsStatusModal').textContent = 'GPS location status: Pending';
            
            // Default back to selfie tab
            const triggerEl = document.querySelector('#verificationTabs button[data-bs-target="#selfie-capture-pane"]');
            bootstrap.Tab.getInstance(triggerEl)?.show() || new bootstrap.Tab(triggerEl).show();
            currentTab = 'selfie';
            
            modal.show();
            startCamera('user');
        });
    });

    // Handle Tab toggling
    document.getElementById('selfie-capture-tab').addEventListener('shown.bs.tab', function () {
        currentTab = 'selfie';
        startCamera('user');
    });

    document.getElementById('dashboard-capture-tab').addEventListener('shown.bs.tab', function () {
        currentTab = 'dashboard';
        startCamera('environment');
    });

    // Capture Frame Action
    document.getElementById('btnCapture').addEventListener('click', function () {
        if (!activeStream) {
            alert("Camera feed is not active. Please use the manual file upload fallback.");
            return;
        }
        
        canvas.width = video.videoWidth || 640;
        canvas.height = video.videoHeight || 480;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        // Convert to base64 jpeg with compression quality 0.8
        const dataUrl = canvas.toDataURL('image/jpeg', 0.8);
        
        if (currentTab === 'selfie') {
            modalSelfieData.value = dataUrl;
            selfiePreview.src = dataUrl;
            selfiePreview.style.display = 'block';
            selfiePlaceholder.style.display = 'none';
        } else {
            modalDashboardData.value = dataUrl;
            dashboardPreview.src = dataUrl;
            dashboardPreview.style.display = 'block';
            dashboardPlaceholder.style.display = 'none';
        }
    });

    // Stop camera on modal close
    document.getElementById('verificationModal').addEventListener('hidden.bs.modal', function () {
        stopCamera();
    });

    // Form Submission with Geolocation Fetch
    document.getElementById('verificationForm').addEventListener('submit', function (event) {
        event.preventDefault();
        
        const form = event.target;
        const statusText = document.getElementById('gpsStatusModal');
        statusText.textContent = "Acquiring live GPS coordinates for verification...";
        
        const submitBtn = document.getElementById('btnSubmitAttendance');
        submitBtn.disabled = true;
        
        if (!navigator.geolocation) {
            statusText.textContent = "GPS is not supported. Submitting...";
            form.submit();
            return;
        }
        
        navigator.geolocation.getCurrentPosition(
            function (position) {
                document.getElementById('modalLatitude').value = position.coords.latitude;
                document.getElementById('modalLongitude').value = position.coords.longitude;
                document.getElementById('modalAccuracy').value = position.coords.accuracy;
                statusText.textContent = "GPS captured successfully! Submitting...";
                form.submit();
            },
            function () {
                statusText.textContent = "GPS capture failed. Submitting for manual review...";
                form.submit();
            },
            {
                enableHighAccuracy: true,
                timeout: 12000,
                maximumAge: 0
            }
        );
    });
});
</script>"""

# Normalize all strings
content_norm = content_norm.replace(search_headers.replace('\r\n', '\n'), replace_headers.replace('\r\n', '\n'))
content_norm = content_norm.replace(search_rows.replace('\r\n', '\n'), replace_rows.replace('\r\n', '\n'))
content_norm = content_norm.replace(search_js.replace('\r\n', '\n'), replace_js.replace('\r\n', '\n'))

# Save
with open(target_file, 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(content_norm)
print("Success: templates/attendance/live.html updated!")
