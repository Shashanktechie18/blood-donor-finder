// ─── Flash message auto-dismiss ─────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    // Dismiss flash messages on click
    document.querySelectorAll('.flash-message').forEach(msg => {
        msg.addEventListener('click', () => {
            msg.style.animation = 'fadeOut 0.3s ease forwards';
            setTimeout(() => msg.remove(), 300);
        });
        // Auto remove after 5s
        setTimeout(() => {
            if (msg.parentNode) msg.remove();
        }, 5000);
    });
});

// ─── Role Tab Switching (Login Page) ────────────────────────────
function switchRole(role) {
    document.querySelectorAll('.role-tab').forEach(tab => tab.classList.remove('active'));
    document.querySelector(`[data-role="${role}"]`).classList.add('active');
    document.getElementById('role-input').value = role;

    const usernameInput = document.getElementById('username');
    const hints = {
        admin: 'Enter admin username',
        donor: 'Enter your phone number',
        hospital: 'Enter hospital contact number'
    };
    usernameInput.placeholder = hints[role] || '';

    const labels = {
        admin: 'Username',
        donor: 'Phone Number',
        hospital: 'Contact Number'
    };
    const label = document.getElementById('username-label');
    if (label) label.textContent = labels[role] || 'Username';
}

// ─── Modal helpers ──────────────────────────────────────────────
function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
    document.body.style.overflow = '';
}

// Close modal on overlay click
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.classList.remove('active');
        document.body.style.overflow = '';
    }
});

// Close modal on Escape
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay.active').forEach(m => {
            m.classList.remove('active');
        });
        document.body.style.overflow = '';
    }
});

// ─── Edit Donor (Admin) ────────────────────────────────────────
function editDonor(btn) {
    document.getElementById('edit-donor-id').value = btn.getAttribute('data-id');
    document.getElementById('edit-donor-name').value = btn.getAttribute('data-name');
    document.getElementById('edit-donor-age').value = btn.getAttribute('data-age');
    document.getElementById('edit-donor-gender').value = btn.getAttribute('data-gender');
    document.getElementById('edit-donor-phone').value = btn.getAttribute('data-phone');
    document.getElementById('edit-donor-address').value = btn.getAttribute('data-address');
    document.getElementById('edit-donor-bg').value = btn.getAttribute('data-bg');
    document.getElementById('edit-donor-status').value = btn.getAttribute('data-status');
    openModal('edit-donor-modal');
}

// ─── Edit Hospital (Admin) ──────────────────────────────────────
function editHospital(btn) {
    document.getElementById('edit-hospital-id').value = btn.getAttribute('data-id');
    document.getElementById('edit-hospital-name').value = btn.getAttribute('data-name');
    document.getElementById('edit-hospital-address').value = btn.getAttribute('data-address');
    document.getElementById('edit-hospital-contact').value = btn.getAttribute('data-contact');
    openModal('edit-hospital-modal');
}

// ─── Delete confirmation ────────────────────────────────────────
function confirmDelete(formId) {
    if (confirm('Are you sure you want to delete this record? This action cannot be undone.')) {
        document.getElementById(formId).submit();
    }
}

// ─── Report Tabs ────────────────────────────────────────────────
function switchReportTab(tabName) {
    document.querySelectorAll('.report-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.report-section').forEach(s => s.classList.remove('active'));
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`report-${tabName}`).classList.add('active');
}

// ─── Bar Chart Rendering ────────────────────────────────────────
function renderBarChart(containerId, data) {
    const container = document.getElementById(containerId);
    if (!container || !data || data.length === 0) return;

    const maxVal = Math.max(...data.map(d => d.value), 1);

    let html = '';
    data.forEach(d => {
        const heightPct = (d.value / maxVal) * 100;
        html += `
            <div class="bar-item">
                <div class="bar-value">${d.value}</div>
                <div class="bar" style="height: ${Math.max(heightPct, 3)}%" title="${d.label}: ${d.value}"></div>
                <div class="bar-label">${d.label}</div>
            </div>
        `;
    });
    container.innerHTML = html;
}
