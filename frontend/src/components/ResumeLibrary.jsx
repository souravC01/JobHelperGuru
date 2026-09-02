import React, { useState, useEffect, useRef } from 'react';
import {
  FileText,
  Plus,
  Trash2,
  CheckCircle,
  Upload,
  AlertCircle,
  Loader2,
  FileCheck,
  Sparkles,
} from 'lucide-react';
import { getResumes, addResume, deleteResume, uploadResumeFile } from '../api/client';

export default function ResumeLibrary({ onResumesUpdated }) {
  const [resumes, setResumes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newName, setNewName] = useState('');
  const [newContent, setNewContent] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [uploadingDoc, setUploadingDoc] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);
  const directFileInputRef = useRef(null);

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
    if (!window.confirm('Are you sure you want to delete this resume profile?')) return;
    try {
      await deleteResume(id);
      await loadResumes();
    } catch (err) {
      alert('Failed to delete resume');
    }
  };

  // Handles parsing PDF, DOCX, or text file into form
  const handleProcessFile = async (file) => {
    if (!file) return;
    setUploadingDoc(true);
    setError('');
    const suggestedTitle = file.name.replace(/\.[^/.]+$/, '');
    if (!newName) {
      setNewName(suggestedTitle);
    }

    try {
      // If it's a plain text/md file, we can parse locally or via API
      if (file.name.endsWith('.txt') || file.name.endsWith('.md')) {
        const text = await file.text();
        setNewContent(text);
      } else {
        // PDF or DOCX: use backend document extractor
        const res = await uploadResumeFile(file, suggestedTitle);
        setNewName(res.name);
        setNewContent(res.content);
        // Refresh library in background since backend added it
        await loadResumes();
      }
    } catch (err) {
      setError(err.message || 'Failed to extract text from file.');
    } finally {
      setUploadingDoc(false);
    }
  };

  // Direct 1-click upload from header
  const handleDirectUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setLoading(true);
    try {
      const suggestedTitle = file.name.replace(/\.[^/.]+$/, '');
      if (file.name.endsWith('.txt') || file.name.endsWith('.md')) {
        const text = await file.text();
        await addResume({ name: suggestedTitle, content: text });
      } else {
        await uploadResumeFile(file, suggestedTitle);
      }
      await loadResumes();
    } catch (err) {
      alert(err.message || 'Failed to upload document');
    } finally {
      setLoading(false);
      if (directFileInputRef.current) directFileInputRef.current.value = '';
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) {
      handleProcessFile(file);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass-panel p-6">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <FileText className="text-indigo-400" size={22} />
            <span>My Resume Profiles ({resumes.length})</span>
          </h2>
          <p className="text-xs text-slate-300 mt-1">
            Upload tailored versions of your resume (PDF, Word DOCX, Markdown, or Text). The app automatically compares them to find your best fit.
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {/* 1-Click Upload PDF / DOCX */}
          <button
            onClick={() => directFileInputRef.current?.click()}
            className="btn-secondary text-xs flex items-center gap-1.5"
            title="Upload PDF or Word resume directly"
          >
            <Upload size={14} className="text-cyan-400" />
            <span>Quick Upload (PDF / DOCX)</span>
          </button>
          <input
            ref={directFileInputRef}
            type="file"
            accept=".pdf,.docx,.doc,.txt,.md"
            onChange={handleDirectUpload}
            className="hidden"
          />

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
      </div>

      {/* Resumes Grid */}
      {loading ? (
        <div className="text-center py-16 space-y-3">
          <Loader2 size={24} className="animate-spin text-indigo-400 mx-auto" />
          <p className="text-xs text-slate-400">Loading your resumes...</p>
        </div>
      ) : resumes.length === 0 ? (
        <div className="glass-panel p-12 text-center space-y-4">
          <div className="w-14 h-14 rounded-2xl bg-indigo-600/20 text-indigo-400 flex items-center justify-center mx-auto border border-indigo-500/30">
            <FileText size={28} />
          </div>
          <div>
            <h3 className="font-bold text-slate-100 text-base">No resumes uploaded yet</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto mt-1">
              Upload your <strong>PDF</strong>, <strong>Word (.docx)</strong>, or text resumes to rank them against jobs and optimize your bullet points.
            </p>
          </div>

          <div className="flex items-center justify-center gap-3 pt-2">
            <button
              onClick={() => directFileInputRef.current?.click()}
              className="btn-primary text-xs"
            >
              <Upload size={14} />
              <span>Upload PDF / Word Resume</span>
            </button>
            <button
              onClick={() => setShowAddModal(true)}
              className="btn-secondary text-xs"
            >
              <Plus size={14} />
              <span>Paste Text Manually</span>
            </button>
          </div>
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
                    className="text-slate-400 hover:text-rose-400 p-1 transition-colors"
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
                <p className="text-[11px] text-slate-400">
                  Added: {new Date(resume.created_at).toLocaleDateString()}
                </p>
                <div className="mt-3 bg-slate-950/70 p-3 rounded-lg border border-slate-800 font-mono text-[11px] text-slate-300 h-32 overflow-hidden line-clamp-6 leading-relaxed">
                  {resume.content}
                </div>
              </div>
              <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-400">
                <span className="flex items-center gap-1 text-emerald-400 font-semibold">
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
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto">
          <div className="glass-panel bg-slate-900 border border-slate-700 w-full max-w-2xl my-8 p-6 rounded-2xl space-y-4 animate-fade-in shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-indigo-500/20 text-indigo-400">
                  <FileText size={18} />
                </div>
                <h3 className="text-base font-bold text-white">Add Resume Profile</h3>
              </div>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-white text-lg font-bold p-1"
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

            {/* Document Drag & Drop Dropzone */}
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition-all ${
                dragOver
                  ? 'border-indigo-400 bg-indigo-950/40'
                  : 'border-slate-700 hover:border-slate-600 bg-slate-950/40 hover:bg-slate-950/60'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.doc,.txt,.md"
                onChange={(e) => handleProcessFile(e.target.files[0])}
                className="hidden"
              />
              {uploadingDoc ? (
                <div className="space-y-2">
                  <Loader2 size={24} className="animate-spin text-indigo-400 mx-auto" />
                  <p className="text-xs text-indigo-300 font-semibold">
                    Extracting text from document...
                  </p>
                </div>
              ) : (
                <div className="space-y-1.5">
                  <div className="flex items-center justify-center gap-2 text-slate-300 text-xs font-semibold">
                    <Upload size={16} className="text-cyan-400" />
                    <span>Drop your resume here or click to browse</span>
                  </div>
                  <p className="text-[11px] text-slate-400">
                    Supports <strong>.PDF</strong>, <strong>.DOCX (Word)</strong>, <strong>.TXT</strong>, <strong>.MD</strong>
                  </p>
                </div>
              )}
            </div>

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Resume Title / Target Domain
                </label>
                <input
                  type="text"
                  placeholder="e.g. Senior Backend Engineer (Python/PostgreSQL) or Product Manager"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="input-field text-xs"
                  required
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-xs font-semibold text-slate-300">
                    Extracted Resume Content
                  </label>
                  <span className="text-[10px] text-slate-400">
                    {newContent ? `${newContent.split(/\s+/).length} words extracted` : 'Paste or upload file'}
                  </span>
                </div>
                <textarea
                  placeholder="Extracted or pasted resume text will appear here. You can edit or tweak bullet points as needed..."
                  rows={8}
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
                  disabled={submitting || uploadingDoc}
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
