const API_BASE = '/api';

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function analyzeJob({ url, text }) {
  const res = await fetch(`${API_BASE}/jobs/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url, text }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Analysis failed' }));
    throw new Error(err.detail || 'Failed to analyze job');
  }
  return res.json();
}

export async function getResumes() {
  const res = await fetch(`${API_BASE}/resumes`);
  return res.json();
}

export async function addResume({ name, content }) {
  const res = await fetch(`${API_BASE}/resumes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, content }),
  });
  if (!res.ok) throw new Error('Failed to add resume');
  return res.json();
}

export async function uploadResumeFile(file, name = '') {
  const formData = new FormData();
  formData.append('file', file);
  if (name) {
    formData.append('name', name);
  }
  const res = await fetch(`${API_BASE}/resumes/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to upload document' }));
    throw new Error(err.detail || 'Failed to upload document');
  }
  return res.json();
}

export async function deleteResume(id) {
  const res = await fetch(`${API_BASE}/resumes/${id}`, { method: 'DELETE' });
  return res.json();
}

export async function matchResumes({ job, resumes }) {
  const res = await fetch(`${API_BASE}/resumes/match`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ job, resumes }),
  });
  if (!res.ok) throw new Error('Failed to rank resumes');
  return res.json();
}

export async function optimizeBullet({ target_job_title, section_type, target_keyword, target_keywords, existing_bullet, evidence_context }) {
  const res = await fetch(`${API_BASE}/resumes/optimize-bullet`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      target_job_title,
      section_type,
      target_keyword,
      target_keywords,
      existing_bullet,
      evidence_context,
    }),
  });
  if (!res.ok) throw new Error('Failed to optimize bullet');
  return res.json();
}

export async function generateOutreach({ job, resume_id, resume_content }) {
  const res = await fetch(`${API_BASE}/resumes/generate-outreach`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ job, resume_id, resume_content }),
  });
  if (!res.ok) throw new Error('Failed to generate outreach');
  return res.json();
}

export async function getApplications() {
  const res = await fetch(`${API_BASE}/applications`);
  return res.json();
}

export async function addApplication(appData) {
  const res = await fetch(`${API_BASE}/applications`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(appData),
  });
  if (!res.ok) throw new Error('Failed to save application');
  return res.json();
}

export async function updateApplication(id, updates) {
  const res = await fetch(`${API_BASE}/applications/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  });
  if (!res.ok) throw new Error('Failed to update application');
  return res.json();
}

export async function deleteApplication(id) {
  const res = await fetch(`${API_BASE}/applications/${id}`, { method: 'DELETE' });
  return res.json();
}

export function getExcelExportUrl() {
  return `${API_BASE}/export/excel`;
}

export async function getSettings() {
  const res = await fetch(`${API_BASE}/settings`);
  return res.json();
}

export async function updateSettings(settings) {
  const res = await fetch(`${API_BASE}/settings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings),
  });
  if (!res.ok) throw new Error('Failed to update settings');
  return res.json();
}

export async function testAISettings(settings) {
  const res = await fetch(`${API_BASE}/settings/test-ai`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings),
  });
  return res.json();
}
