/**
 * ITSM Learning Agent - Modern Frontend
 */

// State
let currentRunId = null;

// DOM Elements
const statusIndicator = document.getElementById('status-indicator');
const fileInput = document.getElementById('file-input');
const uploadBox = document.getElementById('upload-box');
const filePreview = document.getElementById('file-preview');
const processingStatus = document.getElementById('processing-status');
const skillModal = document.getElementById('skill-modal');
const modalOverlay = document.getElementById('modal-overlay');
const modalClose = document.getElementById('modal-close');

// Navigation
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
        const page = item.dataset.page;
        
        // Update active nav
        document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
        item.classList.add('active');
        
        // Show page
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        document.getElementById(`${page}-page`).classList.add('active');
        
        // Load data
        if (page === 'skills') loadProposedSkills();
    });
});

// File upload
uploadBox.addEventListener('click', () => fileInput.click());
uploadBox.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadBox.style.borderColor = 'var(--primary)';
});
uploadBox.addEventListener('dragleave', () => {
    uploadBox.style.borderColor = 'var(--border-color)';
});
uploadBox.addEventListener('drop', (e) => {
    e.preventDefault();
    if (e.dataTransfer.files.length) {
        handleFileSelect(e.dataTransfer.files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) handleFileSelect(e.target.files[0]);
});

function handleFileSelect(file) {
    if (!file.name.endsWith('.json') && !file.name.endsWith('.csv')) {
        alert('Please select a CSV or JSON file');
        return;
    }
    uploadBox.style.display = 'none';
    filePreview.style.display = 'block';
    document.getElementById('preview-filename').textContent = file.name;
    document.getElementById('preview-size').textContent = (file.size / 1024).toFixed(1) + ' KB';
}

document.getElementById('clear-file')?.addEventListener('click', () => {
    fileInput.value = '';
    uploadBox.style.display = 'block';
    filePreview.style.display = 'none';
});

document.getElementById('process-btn')?.addEventListener('click', async () => {
    const file = fileInput.files[0];
    if (!file) return;
    
    filePreview.style.display = 'none';
    processingStatus.style.display = 'flex';
    document.getElementById('status-text').textContent = 'Uploading tickets...';
    
    try {
        // Upload
        const form = new FormData();
        form.append('file', file);
        const upResp = await fetch('/api/tickets/upload', { method: 'POST', body: form });
        if (!upResp.ok) throw new Error('Upload failed');
        const upData = await upResp.json();
        currentRunId = upData.run_id;
        
        // Process
        document.getElementById('status-text').textContent = 'Processing tickets...';
        const procResp = await fetch(`/api/tickets/process/${currentRunId}`, { method: 'POST' });
        if (!procResp.ok) throw new Error('Process failed');
        
        processingStatus.style.display = 'none';
        await loadResults();
        document.querySelector('[data-page="results"]').click();
    } catch (e) {
        document.getElementById('status-text').textContent = `Error: ${e.message}`;
    }
});

// Load results
async function loadResults() {
    try {
        const resp = await fetch(`/api/tickets/status/${currentRunId}`);
        if (!resp.ok) return;
        const data = await resp.json();
        
        // Update stats
        document.getElementById('stat-total').textContent = data.processed_tickets;
        
        const catAccuracy = data.accuracy?.category || 0;
        const routAccuracy = data.accuracy?.routing || 0;
        const resAccuracy = data.accuracy?.resolution || 0;
        
        document.getElementById('stat-category').textContent = (catAccuracy * 100).toFixed(0) + '%';
        document.getElementById('stat-routing').textContent = (routAccuracy * 100).toFixed(0) + '%';
        document.getElementById('stat-resolution').textContent = (resAccuracy * 100).toFixed(0) + '%';
        
        // Update results table
        const tbody = document.getElementById('results-body');
        tbody.innerHTML = '';
        
        if (data.results && data.results.length > 0) {
            data.results.forEach(r => {
                const row = document.createElement('tr');
                const catStatus = r.category_correct ? 'correct' : 'incorrect';
                const routStatus = r.routing_correct ? 'correct' : 'incorrect';
                row.innerHTML = `
                    <td>${r.ticket?.id || '-'}</td>
                    <td>${r.ticket?.title || '-'}</td>
                    <td><span class="status-badge ${catStatus}">${r.prediction?.predicted_category || '-'}</span></td>
                    <td><span class="status-badge ${routStatus}">${r.prediction?.predicted_routing || '-'}</span></td>
                    <td><span class="status-badge ${catStatus}">${catStatus === 'correct' ? '✓' : '✗'}</span></td>
                `;
                tbody.appendChild(row);
            });
        } else {
            tbody.innerHTML = '<tr class="empty-row"><td colspan="5">No results available</td></tr>';
        }
    } catch (e) {
        console.error('Failed to load results:', e);
    }
}

// Load proposed skills
async function loadProposedSkills() {
    try {
        const resp = await fetch('/api/skills/proposed');
        if (!resp.ok) return;
        const data = resp.json();
        
        const container = document.getElementById('pending-skills-grid');
        if (!container) return;
        
        const skills = data.skills || [];
        
        if (skills.length === 0) {
            container.innerHTML = '<div class="empty-message">No pending skills</div>';
            return;
        }
        
        container.innerHTML = '';
        skills.forEach(skill => {
            const card = document.createElement('div');
            card.className = 'skill-card';
            card.innerHTML = `
                <div class="skill-name">${skill.name || 'Unnamed Skill'}</div>
                <div class="skill-description">${skill.description || 'No description'}</div>
                <div class="skill-trigger">${skill.trigger_pattern || 'General'}</div>
            `;
            card.addEventListener('click', () => showSkillModal(skill));
            container.appendChild(card);
        });
        
        // Update badge
        const badge = document.getElementById('skills-badge');
        if (badge && skills.length > 0) {
            badge.textContent = skills.length;
            badge.style.display = 'inline-flex';
        }
    } catch (e) {
        console.error('Failed to load skills:', e);
    }
}

// Show skill modal
function showSkillModal(skill) {
    document.getElementById('modal-title').textContent = skill.name;
    document.getElementById('modal-body').innerHTML = `
        <p><strong>Description:</strong> ${skill.description}</p>
        <p><strong>Trigger:</strong> ${skill.trigger_pattern}</p>
        <p><strong>Source Tickets:</strong> ${skill.source_tickets?.join(', ') || 'N/A'}</p>
    `;
    
    document.getElementById('modal-approve')?.addEventListener('click', async () => {
        try {
            await fetch(`/api/skills/approve/${skill.id}`, { method: 'POST' });
            skillModal.style.display = 'none';
            loadProposedSkills();
        } catch (e) {
            console.error('Approve failed:', e);
        }
    });
    
    document.getElementById('modal-reject')?.addEventListener('click', async () => {
        try {
            await fetch(`/api/skills/reject/${skill.id}`, { method: 'POST' });
            skillModal.style.display = 'none';
            loadProposedSkills();
        } catch (e) {
            console.error('Reject failed:', e);
        }
    });
    
    skillModal.style.display = 'flex';
}

// Modal close
modalClose?.addEventListener('click', () => {
    skillModal.style.display = 'none';
});
modalOverlay?.addEventListener('click', () => {
    skillModal.style.display = 'none';
});

// Health check
async function checkHealth() {
    try {
        const resp = await fetch('/api/health');
        if (resp.ok) {
            statusIndicator.style.color = 'var(--primary)';
            statusIndicator.title = 'System healthy';
        } else {
            statusIndicator.style.color = '#d32f2f';
            statusIndicator.title = 'System error';
        }
    } catch {
        statusIndicator.style.color = '#d32f2f';
        statusIndicator.title = 'Connection failed';
    }
}

checkHealth();
setInterval(checkHealth, 30000);
