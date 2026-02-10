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
    // TODO: Implement Excel upload
    alert('Upload schedules functionality not yet implemented');
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
    // TODO: Implement Excel upload
    alert('Upload attendance functionality not yet implemented');
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
    // TODO: Implement Excel upload
    alert('Batch upload functionality not yet implemented');
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
