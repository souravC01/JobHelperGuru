import React, { useState, useEffect } from 'react';
import { FileText, Plus, Trash2, CheckCircle, Upload, AlertCircle } from 'lucide-react';
import { getResumes, addResume, deleteResume } from '../api/client';

export default function ResumeLibrary({ onResumesUpdated }) {
  const [resumes, setResumes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newName, setNewName] = useState('');
  const [newContent, setNewContent] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadResumes = async () => {
    setLoading(true);
    try {
      const data = await getResumes();
      setResumes(data);
      if (onResumesUpdated) onResumesUpdated(data);
    } catch (err) {
      setError('Failed to load resumes');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadResumes();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!newName.trim() || !newContent.trim()) {
      setError('Both resume title and content are required.');
      return;
    }
    setSubmitting(true);
    setError('');
    try {
      await addResume({ name: newName.trim(), content: newContent.trim() });
      setNewName('');
      setNewContent('');
      setShowAddModal(false);
      await loadResumes();
    } catch (err) {
      setError(err.message || 'Failed to save resume.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this resume?')) return;
    try {
      await deleteResume(id);
      await loadResumes();
    } catch (err) {
      alert('Failed to delete resume');
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (!newName) {
      setNewName(file.name.replace(/\.[^/.]+$/, ''));
    }
    const reader = new FileReader();
    reader.onload = (event) => {
      setNewContent(event.target.result);
    };
    reader.readAsText(file);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass-panel p-6">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <FileText className="text-indigo-400" size={22} />
            <span>My Resume Library</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Store tailored versions of your resume (e.g. Backend, Full-Stack, Machine Learning) to automatically match against target job descriptions.
          </p>
        </div>
        <button
          onClick={() => {
            setError('');
            setShowAddModal(true);
          }}
          className="btn-primary text-xs"
        >
          <Plus size={16} />
          <span>Add New Resume</span>
        </button>
      </div>

      {/* Resumes Grid */}
      {loading ? (
        <div className="text-center py-12 text-slate-500 text-sm">Loading your resumes...</div>
      ) : resumes.length === 0 ? (
        <div className="glass-panel p-10 text-center space-y-3">
          <FileText className="mx-auto text-slate-600" size={40} />
          <h3 className="font-semibold text-slate-300 text-base">No resumes added yet</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Upload or paste your resume text to enable the Best-Fit Resume Matcher and Bullet Point Optimizer.
          </p>
          <button
            onClick={() => setShowAddModal(true)}
            className="btn-primary text-xs mx-auto mt-2"
          >
            <Plus size={14} />
            <span>Add Your First Resume</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {resumes.map((resume) => (
            <div key={resume.id} className="glass-card p-5 flex flex-col justify-between space-y-4">
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <h3 className="font-bold text-slate-100 text-sm line-clamp-1">{resume.name}</h3>
                  <button
                    onClick={() => handleDelete(resume.id)}
                    title="Delete resume"
                    className="text-slate-500 hover:text-rose-400 p-1 transition-colors"
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
                <p className="text-[11px] text-slate-400">
                  Added: {new Date(resume.created_at).toLocaleDateString()}
                </p>
                <div className="mt-3 bg-slate-950/60 p-3 rounded-lg border border-slate-800/80 font-mono text-[11px] text-slate-400 h-28 overflow-hidden line-clamp-5 leading-relaxed">
                  {resume.content}
                </div>
              </div>
              <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-400">
                <span className="flex items-center gap-1 text-emerald-400">
                  <CheckCircle size={13} /> Ready for matching
                </span>
                <span>{resume.content.split(/\s+/).length} words</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Resume Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-panel bg-slate-900 border border-slate-700 w-full max-w-2xl p-6 rounded-2xl space-y-4 animate-fade-in shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <FileText size={18} className="text-indigo-400" />
                <span>Add Resume Profile</span>
              </h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-white text-lg font-bold"
              >
                ✕
              </button>
            </div>

            {error && (
              <div className="p-3 bg-rose-500/20 border border-rose-500/40 rounded-lg text-rose-300 text-xs flex items-center gap-2">
                <AlertCircle size={14} />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Resume Name / Target Domain
                </label>
                <input
                  type="text"
                  placeholder="e.g. Backend Engineer (Python/FastAPI) or Full Stack Dev"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="input-field"
                  required
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-xs font-semibold text-slate-300">
                    Resume Content (Text, Markdown, or pasted CV)
                  </label>
                  <label className="text-[11px] text-indigo-400 hover:text-indigo-300 cursor-pointer flex items-center gap-1 font-medium">
                    <Upload size={12} />
                    <span>Upload .txt/.md file</span>
                    <input
                      type="file"
                      accept=".txt,.md"
                      onChange={handleFileUpload}
                      className="hidden"
                    />
                  </label>
                </div>
                <textarea
                  placeholder="Paste your work history, skills, and project bullet points here..."
                  rows={9}
                  value={newContent}
                  onChange={(e) => setNewContent(e.target.value)}
                  className="input-field font-mono text-xs"
                  required
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="btn-secondary text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="btn-primary text-xs"
                >
                  {submitting ? 'Saving...' : 'Save to Library'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
