const API_BASE = '/api';

export function getToken() {
  return localStorage.getItem('jh_token') || '';
}

export function setAuth(token, user) {
  if (token) localStorage.setItem('jh_token', token);
  if (user) localStorage.setItem('jh_user', JSON.stringify(user));
}

export function clearAuth() {
  localStorage.removeItem('jh_token');
  localStorage.removeItem('jh_user');
}

export function getCurrentUser() {
  const raw = localStorage.getItem('jh_user');
  try {
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export async function authFetch(url, options = {}) {
  const token = getToken();
  const headers = { ...(options.headers || {}) };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const res = await fetch(url, { ...options, headers });
  if (res.status === 401) {
    clearAuth();
    window.dispatchEvent(new CustomEvent('jh_auth_unauthorized'));
  }
  return res;
}

async function parseApiError(res, defaultMsg) {
  let errorMsg = defaultMsg;
  let canSwitchOffline = res.status === 502;
  let modelName = '';

  try {
    const data = await res.json();
    if (data?.detail) {
      if (typeof data.detail === 'object') {
        errorMsg = data.detail.message || defaultMsg;
        canSwitchOffline = data.detail.can_switch_offline ?? canSwitchOffline;
        modelName = data.detail.model_name || '';
      } else {
        errorMsg = data.detail;
      }
    }
  } catch (e) {
    // ignore
  }

  const err = new Error(errorMsg);
  err.canSwitchOffline = canSwitchOffline;
  err.modelName = modelName;
  err.status = res.status;
  return err;
}

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

// --- Auth APIs ---
export async function registerUser({ email, password, name }) {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, name }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({ detail: 'Registration failed' }));
    throw new Error(data.detail || 'Registration failed');
  }
  const data = await res.json();
  setAuth(data.token, data.user);
  return data;
}

export async function loginUser({ email, password }) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({ detail: 'Login failed' }));
    throw new Error(data.detail || 'Login failed');
  }
  const data = await res.json();
  setAuth(data.token, data.user);
  return data;
}

export async function googleAuthUser(credential) {
  const res = await fetch(`${API_BASE}/auth/google`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ credential }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({ detail: 'Google sign-in failed' }));
    throw new Error(data.detail || 'Google sign-in failed');
  }
  const data = await res.json();
  setAuth(data.token, data.user);
  return data;
}

export async function getMe() {
  const res = await authFetch(`${API_BASE}/auth/me`);
  if (!res.ok) throw new Error('Failed to get user profile');
  const user = await res.json();
  if (user) {
    localStorage.setItem('jh_user', JSON.stringify(user));
  }
  return user;
}

export function logoutUser() {
  clearAuth();
  window.dispatchEvent(new CustomEvent('jh_auth_logout'));
}

// --- Job Analyzer ---
export async function analyzeJob({ url, text }) {
  const res = await authFetch(`${API_BASE}/jobs/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url, text }),
  });
  if (!res.ok) {
    throw await parseApiError(res, 'Failed to analyze job');
  }
  return res.json();
}

// --- Resumes ---
export async function getResumes() {
  const res = await authFetch(`${API_BASE}/resumes`);
  if (!res.ok) throw new Error('Failed to load resumes');
  return res.json();
}

export async function addResume({ name, content }) {
  const res = await authFetch(`${API_BASE}/resumes`, {
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
  const res = await authFetch(`${API_BASE}/resumes/upload`, {
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
  const res = await authFetch(`${API_BASE}/resumes/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete resume');
  return res.json();
}

export async function matchResumes(payload) {
  const job = payload?.job || (payload?.title || payload?.required_skills ? payload : null);
  const resumes = payload?.resumes;
  const res = await authFetch(`${API_BASE}/resumes/match`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ job, resumes }),
  });
  if (!res.ok) {
    throw await parseApiError(res, 'Failed to rank resumes');
  }
  return res.json();
}

export async function optimizeBullet({
  target_job_title,
  section_type,
  target_keyword,
  target_keywords,
  existing_bullet,
  evidence_context,
}) {
  const res = await authFetch(`${API_BASE}/resumes/optimize-bullet`, {
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
  if (!res.ok) {
    throw await parseApiError(res, 'Failed to optimize bullet');
  }
  return res.json();
}

export async function generateOutreach({ job, resume_id, resume_content }) {
  const res = await authFetch(`${API_BASE}/resumes/generate-outreach`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ job, resume_id, resume_content }),
  });
  if (!res.ok) {
    throw await parseApiError(res, 'Failed to generate outreach');
  }
  return res.json();
}

// --- Applications Tracker ---
export async function getApplications() {
  const res = await authFetch(`${API_BASE}/applications`);
  if (!res.ok) throw new Error('Failed to load applications');
  return res.json();
}

export async function addApplication(appData) {
  const res = await authFetch(`${API_BASE}/applications`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(appData),
  });
  if (!res.ok) throw new Error('Failed to save application');
  return res.json();
}

export async function updateApplication(id, updates) {
  const res = await authFetch(`${API_BASE}/applications/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  });
  if (!res.ok) throw new Error('Failed to update application');
  return res.json();
}

export async function deleteApplication(id) {
  const res = await authFetch(`${API_BASE}/applications/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete application');
  return res.json();
}

export function getExcelExportUrl() {
  return `${API_BASE}/export/excel`;
}

export async function downloadExcelReport() {
  const res = await authFetch(`${API_BASE}/export/excel`);
  if (!res.ok) throw new Error('Failed to export Excel spreadsheet');
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `job_tracker_${new Date().toISOString().slice(0, 10)}.xlsx`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

// --- Settings ---
export async function getSettings() {
  const res = await authFetch(`${API_BASE}/settings`);
  if (!res.ok) throw new Error('Failed to load settings');
  return res.json();
}

export async function updateSettings(settings) {
  const res = await authFetch(`${API_BASE}/settings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings),
  });
  if (!res.ok) throw new Error('Failed to update settings');
  return res.json();
}

export async function testAISettings(settings) {
  const res = await authFetch(`${API_BASE}/settings/test-ai`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings),
  });
  return res.json();
}
