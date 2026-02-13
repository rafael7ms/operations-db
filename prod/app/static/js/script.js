// Main JavaScript for Operations DB

let apiUrl = '/api';

// Initialize the app
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
});

function setupEventListeners() {
    // Add any global event listeners here
    console.log('Operations DB initialized');
}

// ==================== Employee Functions ====================

function editEmployee(employeeId) {
    window.location.href = `/employees/${employeeId}/edit`;
}

function deleteEmployee(employeeId) {
    if (confirm('Are you sure you want to delete this employee?')) {
        fetch(`${apiUrl}/employees/${employeeId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            alert('Employee deleted successfully!');
            location.reload();
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error deleting employee');
        });
    }
}

function submitEmployeeForm() {
    const form = document.getElementById('addEmployeeForm');
    const formData = new FormData(form);
    const data = {};

    formData.forEach((value, key) => {
        data[key] = value;
    });

    fetch(`${apiUrl}/employees`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        alert('Employee created successfully!');
        document.getElementById('addEmployeeModal').querySelector('.btn-close').click();
        location.reload();
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error creating employee');
    });
}

// ==================== Schedule Functions ====================

function editSchedule(scheduleId) {
    // TODO: Implement edit schedule
    alert('Edit schedule functionality not yet implemented');
}

function deleteSchedule(scheduleId) {
    if (confirm('Are you sure you want to delete this schedule?')) {
        fetch(`${apiUrl}/schedules/${scheduleId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            alert('Schedule deleted successfully!');
            location.reload();
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error deleting schedule');
        });
    }
}

function submitScheduleForm() {
    const form = document.getElementById('addScheduleForm');
    const formData = new FormData(form);
    const data = {};

    formData.forEach((value, key) => {
        data[key] = value;
    });

    fetch(`${apiUrl}/schedules`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        alert('Schedule created successfully!');
        document.getElementById('addScheduleModal').querySelector('.btn-close').click();
        location.reload();
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error creating schedule');
    });
}

function uploadSchedules() {
    // Create a modal-like interface for file selection
    const container = document.createElement('div');
    container.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);z-index:1000;display:flex;justify-content:center;align-items:center;';

    const modal = document.createElement('div');
    modal.style.cssText = 'background:white;padding:2rem;border-radius:8px;max-width:500px;width:90%;';
    modal.innerHTML = `
        <h3>Upload Schedules</h3>
        <p>Upload schedule Excel file. Optionally upload employee file for RUEX ID matching.</p>
        <form id="scheduleUploadForm" style="margin-top:1rem;">
            <div style="margin-bottom:1rem;">
                <label style="display:block;margin-bottom:0.5rem;font-weight:bold;">Schedule File (required)</label>
                <input type="file" id="scheduleFile" accept=".xlsx,.xls" style="width:100%;padding:0.5rem;border:1px solid #ccc;border-radius:4px;">
                <small style="color:#666;">Excel file with columns: Employee - ID, Date - Nominal Date, Earliest - Start, Latest - Stop, Work - Code</small>
            </div>
            <div style="margin-bottom:1rem;">
                <label style="display:block;margin-bottom:0.5rem;font-weight:bold;">Employee File (optional)</label>
                <input type="file" id="employeeFile" accept=".xlsx,.xls" style="width:100%;padding:0.5rem;border:1px solid #ccc;border-radius:4px;">
                <small style="color:#666;">Employee Excel file for RUEX ID matching (first letter + last name)</small>
            </div>
            <div style="display:flex;gap:0.5rem;justify-content:flex-end;">
                <button type="button" id="cancelUpload" class="btn btn-secondary">Cancel</button>
                <button type="submit" class="btn btn-primary">Upload</button>
            </div>
        </form>
    `;

    container.appendChild(modal);
    document.body.appendChild(container);

    const form = document.getElementById('scheduleUploadForm');
    const cancelBtn = document.getElementById('cancelUpload');

    function closeModal() {
        document.body.removeChild(container);
    }

    cancelBtn.addEventListener('click', closeModal);

    form.addEventListener('submit', e => {
        e.preventDefault();

        const scheduleFile = document.getElementById('scheduleFile').files[0];
        const employeeFile = document.getElementById('employeeFile').files[0];

        if (!scheduleFile) {
            alert('Please select a schedule file');
            return;
        }

        if (!confirm(`Upload ${scheduleFile.name}? This will add schedules to the database.`)) {
            closeModal();
            return;
        }

        const formData = new FormData();
        formData.append('file', scheduleFile);
        if (employeeFile) {
            formData.append('employee_file', employeeFile);
        }

        showLoading('Uploading schedules...');

        fetch('/api/schedules/batch', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            closeModal();
            if (data.success_count || data.error_count) {
                const msg = `Import completed: ${data.success_count} schedules imported, ${data.error_count} errors`;
                alert(msg + (data.errors ? '\n\nErrors:\n' + data.errors.join('\n') : ''));
            } else {
                alert('Error: ' + (data.message || data.error || 'Unknown error'));
            }
            location.reload();
        })
        .catch(error => {
            hideLoading();
            closeModal();
            console.error('Error:', error);
            alert('Error uploading file: ' + error.message);
        });
    });
}

function showLoading(message) {
    let loading = document.getElementById('loadingOverlay');
    if (!loading) {
        loading = document.createElement('div');
        loading.id = 'loadingOverlay';
        loading.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);z-index:9999;display:flex;justify-content:center;align-items:center;color:white;font-size:1.2rem;';
        document.body.appendChild(loading);
    }
    loading.innerHTML = '<div class="spinner-border me-2" role="status"><span class="visually-hidden">Loading...</span></div>' + message;
    loading.style.display = 'flex';
}

function hideLoading() {
    const loading = document.getElementById('loadingOverlay');
    if (loading) {
        loading.style.display = 'none';
    }
}

function archiveOldSchedules() {
    if (confirm('Archive schedules older than 2 months? This cannot be undone.')) {
        // TODO: Call archive endpoint
        alert('Archive functionality not yet implemented');
    }
}

// ==================== Attendance Functions ====================

function submitAttendanceForm() {
    const form = document.getElementById('logAttendanceForm');
    const formData = new FormData(form);
    const data = {};

    formData.forEach((value, key) => {
        data[key] = value;
    });

    fetch(`${apiUrl}/attendances`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        alert('Attendance recorded successfully!');
        document.getElementById('logAttendanceModal').querySelector('.btn-close').click();
        location.reload();
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error recording attendance');
    });
}

function uploadAttendance() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.xlsx,.xls';
    input.onchange = e => {
        const file = e.target.files[0];
        if (!file) return;

        if (!confirm(`Upload ${file.name}? This will add attendance records to the database.`)) {
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        showLoading('Uploading attendance records...');

        fetch('/api/attendances/batch', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            if (data.success_count || data.error_count) {
                const msg = `Import completed: ${data.success_count} records imported, ${data.error_count} errors`;
                alert(msg + (data.errors ? '\n\nErrors:\n' + data.errors.join('\n') : ''));
            } else {
                alert('Error: ' + (data.message || data.error || 'Unknown error'));
            }
            location.reload();
        })
        .catch(error => {
            hideLoading();
            console.error('Error:', error);
            alert('Error uploading file: ' + error.message);
        });
    };
    input.click();
}

function archiveOldAttendances() {
    if (confirm('Archive attendance records older than 1 month? This cannot be undone.')) {
        // TODO: Call archive endpoint
        alert('Archive functionality not yet implemented');
    }
}

// ==================== Exception Functions ====================

function submitExceptionForm() {
    const form = document.getElementById('addExceptionForm');
    const formData = new FormData(form);
    const data = {};

    formData.forEach((value, key) => {
        data[key] = value;
    });

    fetch(`${apiUrl}/exceptions`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        alert('Exception record created successfully!');
        document.getElementById('addExceptionModal').querySelector('.btn-close').click();
        location.reload();
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error creating exception record');
    });
}

function processException(exceptionId) {
    if (confirm('Process this exception record?')) {
        fetch(`${apiUrl}/exceptions/${exceptionId}/process`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ processed_by: 1 }) // TODO: Get current user
        })
        .then(response => response.json())
        .then(data => {
            alert('Exception processed successfully!');
            location.reload();
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error processing exception');
        });
    }
}

function deleteException(exceptionId) {
    if (confirm('Are you sure you want to delete this exception record?')) {
        fetch(`${apiUrl}/exceptions/${exceptionId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            alert('Exception record deleted successfully!');
            location.reload();
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error deleting exception record');
        });
    }
}

function uploadExceptions() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.xlsx,.xls';
    input.onchange = e => {
        const file = e.target.files[0];
        if (!file) return;

        if (!confirm(`Upload ${file.name}? This will add exception records to the database.`)) {
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        showLoading('Uploading exception records...');

        fetch('/api/exceptions/batch', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            if (data.success_count || data.error_count) {
                const msg = `Import completed: ${data.success_count} records imported, ${data.error_count} errors`;
                alert(msg + (data.errors ? '\n\nErrors:\n' + data.errors.join('\n') : ''));
            } else {
                alert('Error: ' + (data.message || data.error || 'Unknown error'));
            }
            location.reload();
        })
        .catch(error => {
            hideLoading();
            console.error('Error:', error);
            alert('Error uploading file: ' + error.message);
        });
    };
    input.click();
}

// ==================== Admin Option Functions ====================

function submitOptionForm() {
    const form = document.getElementById('addOptionForm');
    const formData = new FormData(form);
    const data = {};

    formData.forEach((value, key) => {
        data[key] = value;
    });

    fetch(`${apiUrl}/admin/options`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        alert('Admin option created successfully!');
        document.getElementById('addOptionModal').querySelector('.btn-close').click();
        location.reload();
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error creating admin option');
    });
}

function deleteOption(optionId) {
    if (confirm('Are you sure you want to delete this option?')) {
        // TODO: Implement delete option endpoint
        alert('Delete option functionality not yet implemented');
    }
}

// ==================== Reward Functions ====================

function submitAwardForm() {
    const form = document.getElementById('awardForm');
    const formData = new FormData(form);
    const data = {};

    formData.forEach((value, key) => {
        data[key] = value;
    });

    fetch(`${apiUrl}/rewards/award`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        alert('Points awarded successfully!');
        document.getElementById('awardModal').querySelector('.btn-close').click();
        location.reload();
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error awarding points');
    });
}

function submitReasonForm() {
    const form = document.getElementById('addReasonForm');
    const formData = new FormData(form);
    const data = {};

    formData.forEach((value, key) => {
        data[key] = value;
    });

    fetch(`${apiUrl}/admin/options`, {  // TODO: Create separate reward reasons endpoint
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            category: 'reward_reason',
            value: data.reason,
            is_active: data.is_active
        })
    })
    .then(response => response.json())
    .then(data => {
        alert('Reward reason added successfully!');
        document.getElementById('addReasonModal').querySelector('.btn-close').click();
        location.reload();
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error adding reward reason');
    });
}

// ==================== Reward Upload Function ====================

function uploadRewards() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.xlsx,.xls';
    input.onchange = e => {
        const file = e.target.files[0];
        if (!file) return;

        if (!confirm(`Upload ${file.name}? This will award points to employees.`)) {
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        showLoading('Uploading reward records...');

        fetch('/api/rewards/award/batch', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            if (data.success_count || data.error_count) {
                const msg = `Import completed: ${data.success_count} rewards created, ${data.error_count} errors`;
                alert(msg + (data.errors ? '\n\nErrors:\n' + data.errors.join('\n') : ''));
            } else {
                alert('Error: ' + (data.message || data.error || 'Unknown error'));
            }
            location.reload();
        })
        .catch(error => {
            hideLoading();
            console.error('Error:', error);
            alert('Error uploading file: ' + error.message);
        });
    };
    input.click();
}

// ==================== API Helper Functions ====================

function get(url) {
    return fetch(url)
        .then(response => response.json())
        .catch(error => console.error('API Error:', error));
}

function post(url, data) {
    return fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .catch(error => console.error('API Error:', error));
}

function put(url, data) {
    return fetch(url, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .catch(error => console.error('API Error:', error));
}

function del(url) {
    return fetch(url, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .catch(error => console.error('API Error:', error));
}
