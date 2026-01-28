/**
 * ITSM Learning Agent - Frontend Application
 */

// State
let currentRunId = null;
let currentSkillId = null;

// DOM Elements
const statusIndicator = document.getElementById('status-indicator');
const statusText = statusIndicator.querySelector('.status-text');
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const uploadPreview = document.getElementById('upload-preview');
const previewFilename = document.getElementById('preview-filename');
const previewCount = document.getElementById('preview-count');
const processBtn = document.getElementById('process-btn');
const clearUpload = document.getElementById('clear-upload');
const resultsBody = document.getElementById('results-body');
const skillsList = document.getElementById('skills-list');
const activeSkillsList = document.getElementById('active-skills-list');
const pendingBadge = document.getElementById('pending-skills-badge');
const modal = document.getElementById('skill-modal');

// Navigation
document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        const tabId = tab.dataset.tab;

        // Update active tab
        document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');

        // Show corresponding content
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        document.getElementById(`${tabId}-tab`).classList.add('active');

        // Refresh data for certain tabs
        if (tabId === 'skills') {
            loadProposedSkills();
            loadActiveSkills();
        }
    });
});

// Health Check
async function checkHealth() {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();

        if (data.ollama_available) {
            statusIndicator.classList.add('connected');
            statusIndicator.classList.remove('error');
            statusText.textContent = 'Ollama Connected';
        } else {
            statusIndicator.classList.remove('connected');
            statusIndicator.classList.add('error');
            statusText.textContent = 'Ollama Not Available';
        }
    } catch (error) {
        statusIndicator.classList.remove('connected');
        statusIndicator.classList.add('error');
        statusText.textContent = 'Server Error';
    }
}

// File Upload
let uploadedFile = null;

dropZone.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
});

function handleFileSelect(file) {
    if (!file.name.endsWith('.json') && !file.name.endsWith('.csv')) {
        alert('Please upload a JSON or CSV file');
        return;
    }

    uploadedFile = file;
    previewFilename.textContent = file.name;

    // Count tickets (rough estimate for preview)
    const reader = new FileReader();
    reader.onload = (e) => {
        const content = e.target.result;
        let count = 0;

        if (file.name.endsWith('.json')) {
            try {
                const data = JSON.parse(content);
                count = Array.isArray(data) ? data.length : (data.tickets?.length || 0);
            } catch {
                count = 0;
            }
        } else {
            // CSV - count lines minus header
            count = content.split('\n').length - 1;
        }

        previewCount.textContent = `${count} tickets found`;
    };
    reader.readAsText(file);

    dropZone.style.display = 'none';
    uploadPreview.style.display = 'block';
}

clearUpload.addEventListener('click', () => {
    uploadedFile = null;
    fileInput.value = '';
    dropZone.style.display = 'flex';
    uploadPreview.style.display = 'none';
});

// Process Tickets
processBtn.addEventListener('click', async () => {
    if (!uploadedFile) return;

    processBtn.disabled = true;
    processBtn.textContent = '⏳ Uploading...';

    try {
        // Upload file
        const formData = new FormData();
        formData.append('file', uploadedFile);

        const uploadResponse = await fetch('/api/tickets/upload', {
            method: 'POST',
            body: formData
        });

        if (!uploadResponse.ok) {
            throw new Error('Upload failed');
        }

        const uploadData = await uploadResponse.json();
        currentRunId = uploadData.run_id;

        processBtn.textContent = '🔄 Processing...';

        // Process tickets
        const processResponse = await fetch(`/api/tickets/process/${currentRunId}`, {
            method: 'POST'
        });

        if (!processResponse.ok) {
            throw new Error('Processing failed');
        }

        const results = await processResponse.json();

        // Update dashboard
        updateDashboard(results);

        // Switch to dashboard tab
        document.querySelector('[data-tab="dashboard"]').click();

        // Check for new skills
        loadProposedSkills();

        // Reset upload state
        clearUpload.click();

    } catch (error) {
        alert('Error: ' + error.message);
    } finally {
        processBtn.disabled = false;
        processBtn.textContent = '🚀 Process Tickets';
    }
});

// Update Dashboard
function updateDashboard(results) {
    document.getElementById('stat-total').textContent = results.total_tickets;

    // Calculate accuracy from results
    if (results.results && results.results.length > 0) {
        const catCorrect = results.results.filter(r => r.category_correct === true).length;
        const routeCorrect = results.results.filter(r => r.routing_correct === true).length;
        const resCorrect = results.results.filter(r => r.resolution_correct === true).length;
        const total = results.results.length;

        document.getElementById('stat-category').textContent =
            Math.round((catCorrect / total) * 100) + '%';
        document.getElementById('stat-routing').textContent =
            Math.round((routeCorrect / total) * 100) + '%';
        document.getElementById('stat-resolution').textContent =
            Math.round((resCorrect / total) * 100) + '%';
    }

    // Update results table
    resultsBody.innerHTML = '';

    if (!results.results || results.results.length === 0) {
        resultsBody.innerHTML = '<tr class="empty-row"><td colspan="6">No results</td></tr>';
        return;
    }

    results.results.forEach(result => {
        const row = document.createElement('tr');

        const catStatus = result.category_correct === true ? 'correct' :
            result.category_correct === false ? 'incorrect' : 'unknown';
        const routeStatus = result.routing_correct === true ? 'correct' :
            result.routing_correct === false ? 'incorrect' : 'unknown';
        const resStatus = result.resolution_correct === true ? 'correct' :
            result.resolution_correct === false ? 'incorrect' : 'unknown';

        const overallStatus = (catStatus === 'correct' && routeStatus === 'correct') ? 'correct' :
            (catStatus === 'incorrect' || routeStatus === 'incorrect') ? 'incorrect' : 'unknown';

        row.innerHTML = `
            <td>${result.ticket.id}</td>
            <td>${truncate(result.ticket.title, 40)}</td>
            <td><span class="status-badge ${catStatus}">${result.prediction.predicted_category}</span></td>
            <td><span class="status-badge ${routeStatus}">${result.prediction.predicted_routing}</span></td>
            <td>${truncate(result.prediction.predicted_resolution, 50)}</td>
            <td><span class="status-badge ${overallStatus}">${overallStatus}</span></td>
        `;

        resultsBody.appendChild(row);
    });
}

function truncate(str, len) {
    if (!str) return '';
    return str.length > len ? str.substring(0, len) + '...' : str;
}

// Load Proposed Skills
async function loadProposedSkills() {
    try {
        const response = await fetch('/api/skills/proposed');
        const data = await response.json();

        // Update badge
        if (data.count > 0) {
            pendingBadge.style.display = 'inline-block';
            pendingBadge.textContent = data.count;
        } else {
            pendingBadge.style.display = 'none';
        }

        // Update list
        if (data.count === 0) {
            skillsList.innerHTML = `
                <div class="empty-state">
                    <span class="empty-icon">🎓</span>
                    <h3>No pending skills</h3>
                    <p>When the agent learns new patterns, proposals will appear here for your review.</p>
                </div>
            `;
            return;
        }

        skillsList.innerHTML = '';
        data.skills.forEach(skill => {
            const card = document.createElement('div');
            card.className = 'skill-card';
            card.innerHTML = `
                <div class="skill-card-header">
                    <div>
                        <h4>${skill.name}</h4>
                        <span class="skill-trigger">Trigger: ${skill.trigger_pattern || 'Auto-detected'}</span>
                    </div>
                </div>
                <p>${skill.description}</p>
                <p style="font-size: 0.85rem; color: var(--text-muted);">
                    Source tickets: ${skill.source_tickets.join(', ')}
                </p>
                <div class="skill-actions">
                    <button class="btn btn-ghost" onclick="previewSkill('${skill.id}')">Preview</button>
                    <button class="btn btn-danger" onclick="rejectSkill('${skill.id}')">Reject</button>
                    <button class="btn btn-success" onclick="approveSkill('${skill.id}')">Approve</button>
                </div>
            `;
            skillsList.appendChild(card);
        });

    } catch (error) {
        console.error('Error loading proposed skills:', error);
    }
}

// Load Active Skills
async function loadActiveSkills() {
    try {
        const response = await fetch('/api/skills/');
        const data = await response.json();

        activeSkillsList.innerHTML = '';

        if (data.count === 0) {
            activeSkillsList.innerHTML = '<p style="color: var(--text-muted);">No active skills</p>';
            return;
        }

        data.skills.forEach(skill => {
            const card = document.createElement('div');
            card.className = 'active-skill-card';
            card.innerHTML = `
                <h4><span>✅</span> ${skill.name}</h4>
                <p>${skill.description}</p>
            `;
            activeSkillsList.appendChild(card);
        });

    } catch (error) {
        console.error('Error loading active skills:', error);
    }
}

// Skill Actions
async function previewSkill(skillId) {
    try {
        const response = await fetch(`/api/skills/proposed/${skillId}`);
        const skill = await response.json();

        currentSkillId = skillId;
        document.getElementById('modal-skill-name').textContent = skill.name;
        document.getElementById('modal-skill-trigger').textContent = `Trigger: ${skill.trigger_pattern || 'Auto-detected'}`;
        document.getElementById('modal-skill-content').textContent = skill.content;

        modal.classList.add('active');
    } catch (error) {
        alert('Error loading skill preview');
    }
}

async function approveSkill(skillId) {
    try {
        const response = await fetch(`/api/skills/approve/${skillId}`, {
            method: 'POST'
        });

        if (response.ok) {
            modal.classList.remove('active');
            loadProposedSkills();
            loadActiveSkills();
        } else {
            alert('Error approving skill');
        }
    } catch (error) {
        alert('Error approving skill');
    }
}

async function rejectSkill(skillId) {
    if (!confirm('Are you sure you want to reject this skill?')) return;

    try {
        const response = await fetch(`/api/skills/reject/${skillId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            modal.classList.remove('active');
            loadProposedSkills();
        } else {
            alert('Error rejecting skill');
        }
    } catch (error) {
        alert('Error rejecting skill');
    }
}

// Modal handlers
document.querySelector('.modal-close').addEventListener('click', () => {
    modal.classList.remove('active');
});

document.getElementById('modal-approve').addEventListener('click', () => {
    if (currentSkillId) approveSkill(currentSkillId);
});

document.getElementById('modal-reject').addEventListener('click', () => {
    if (currentSkillId) rejectSkill(currentSkillId);
});

modal.addEventListener('click', (e) => {
    if (e.target === modal) {
        modal.classList.remove('active');
    }
});

// Initialize
checkHealth();
loadActiveSkills();
setInterval(checkHealth, 30000); // Check every 30 seconds
