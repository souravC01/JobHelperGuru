import React, { useState, useEffect, useRef } from 'react';
import {
  FileText,
  Plus,
  Trash2,
  CheckCircle,
  Upload,
  AlertCircle,
  Loader2,
  X,
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

  const handleProcessFile = async (file) => {
    if (!file) return;
    setUploadingDoc(true);
    setError('');
    const suggestedTitle = file.name.replace(/\.[^/.]+$/, '');
    if (!newName) {
      setNewName(suggestedTitle);
    }

    try {
      if (file.name.endsWith('.txt') || file.name.endsWith('.md')) {
        const text = await file.text();
        setNewContent(text);
      } else {
        const res = await uploadResumeFile(file, suggestedTitle);
        setNewName(res.name);
        setNewContent(res.content);
        await loadResumes();
      }
    } catch (err) {
      setError(err.message || 'Failed to extract text from file.');
    } finally {
      setUploadingDoc(false);
    }
  };

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
      {/* Corporate Header */}
      <div className="card-corporate p-6 bg-white border border-[#e0e0e0] rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-none">
        <div>
          <h2 className="text-base font-bold text-[#000000] flex items-center gap-2 tracking-tight">
            <FileText className="text-[#0a66c2]" size={18} />
            <span>Resume Vault ({resumes.length})</span>
          </h2>
          <p className="text-xs text-[#666666] mt-1">
            Store tailored versions of your resume (PDF, Word DOCX, Markdown, or Text) for automatic ATS matching.
          </p>
        </div>

        <div className="flex items-center gap-2.5 flex-wrap">
          <button
            onClick={() => directFileInputRef.current?.click()}
            className="btn-secondary-corporate text-xs"
            title="Upload PDF or Word resume directly"
          >
            <Upload size={13} />
            <span>Quick Upload (PDF/DOCX)</span>
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
            className="btn-primary-corporate text-xs"
          >
            <Plus size={14} />
            <span>Add New Resume</span>
          </button>
        </div>
      </div>

      {/* Resumes Grid */}
      {loading ? (
        <div className="text-center py-16 space-y-3">
          <Loader2 size={24} className="animate-spin text-[#0a66c2] mx-auto" />
          <p className="text-xs text-[#666666] font-mono">Loading resume vault...</p>
        </div>
      ) : resumes.length === 0 ? (
        <div className="card-corporate p-12 bg-white border border-[#e0e0e0] text-center space-y-4 rounded-lg shadow-none">
          <div className="w-12 h-12 rounded-full bg-[#0a66c2]/10 text-[#0a66c2] flex items-center justify-center mx-auto border border-[#0a66c2]/20">
            <FileText size={24} />
          </div>
          <div>
            <h3 className="font-bold text-[#000000] text-sm">No resumes in vault yet</h3>
            <p className="text-xs text-[#666666] max-w-md mx-auto mt-1">
              Upload your <strong>PDF</strong>, <strong>Word (.docx)</strong>, or plain text resumes to rank them against jobs and generate tailored bullet points.
            </p>
          </div>

          <div className="flex items-center justify-center gap-2.5 pt-2">
            <button
              onClick={() => directFileInputRef.current?.click()}
              className="btn-primary-corporate text-xs"
            >
              <Upload size={13} />
              <span>Upload PDF / Word</span>
            </button>
            <button
              onClick={() => setShowAddModal(true)}
              className="btn-secondary-corporate text-xs"
            >
              <Plus size={13} />
              <span>Paste Text</span>
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {resumes.map((resume) => (
            <div key={resume.id} className="card-corporate p-5 bg-white border border-[#e0e0e0] hover:border-[#c1c6d4] transition-all rounded-lg flex flex-col justify-between space-y-4 shadow-none">
              <div>
                <div className="flex items-start justify-between gap-2 mb-1.5">
                  <h3 className="font-bold text-[#000000] text-sm line-clamp-1">{resume.name}</h3>
                  <button
                    onClick={() => handleDelete(resume.id)}
                    title="Delete resume"
                    className="text-[#666666] hover:text-[#b24020] p-1 transition-colors"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
                <p className="text-[10px] font-mono text-[#666666]">
                  Added: {new Date(resume.created_at).toLocaleDateString()}
                </p>
                <div className="mt-3 bg-[#f3f6f8] p-3 rounded border border-[#e0e0e0] font-mono text-[11px] text-[#000000] h-28 overflow-hidden line-clamp-5 leading-relaxed">
                  {resume.content}
                </div>
              </div>
              <div className="pt-2 border-t border-[#e0e0e0] flex items-center justify-between text-[11px] text-[#666666]">
                <span className="flex items-center gap-1 text-[#057642] font-semibold text-[11px]">
                  <CheckCircle size={12} /> Ready for ATS Matching
                </span>
                <span className="font-mono text-[10px] text-[#666666]">{resume.content.split(/\s+/).length} words</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Resume Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="card-corporate bg-white border border-[#e0e0e0] w-full max-w-2xl my-8 p-6 rounded-xl space-y-4 animate-fade-in shadow-xl text-[#000000]">
            <div className="flex items-center justify-between pb-3 border-b border-[#e0e0e0]">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-full bg-[#0a66c2]/10 text-[#0a66c2]">
                  <FileText size={16} />
                </div>
                <h3 className="text-sm font-bold text-[#000000] tracking-tight">Add Resume Profile</h3>
              </div>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-[#666666] hover:text-[#000000] p-1 transition-colors"
              >
                <X size={16} />
              </button>
            </div>

            {error && (
              <div className="p-3 bg-[#b24020]/10 border border-[#b24020]/25 rounded-lg text-[#b24020] text-xs flex items-center gap-2">
                <AlertCircle size={14} className="shrink-0" />
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
              className={`border border-dashed rounded-lg p-6 text-center cursor-pointer transition-all ${
                dragOver
                  ? 'border-[#0a66c2] bg-[#f0f7fe]'
                  : 'border-[#e0e0e0] hover:border-[#0a66c2] bg-[#f3f6f8] hover:bg-[#f0f7fe]'
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
                  <Loader2 size={20} className="animate-spin text-[#0a66c2] mx-auto" />
                  <p className="text-xs text-[#0a66c2] font-semibold font-mono">
                    Extracting text from document...
                  </p>
                </div>
              ) : (
                <div className="space-y-1.5">
                  <div className="flex items-center justify-center gap-2 text-[#000000] text-xs font-semibold">
                    <Upload size={14} className="text-[#0a66c2]" />
                    <span>Drop your resume here or click to browse</span>
                  </div>
                  <p className="text-[11px] text-[#666666]">
                    Supports <strong>.PDF</strong>, <strong>.DOCX (Word)</strong>, <strong>.TXT</strong>, <strong>.MD</strong>
                  </p>
                </div>
              )}
            </div>

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-[#000000] mb-1">
                  Resume Title / Target Domain
                </label>
                <input
                  type="text"
                  placeholder="e.g. Senior Backend Engineer (Go/PostgreSQL) or Full Stack Developer"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="input-corporate w-full text-xs"
                  required
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-xs font-semibold text-[#000000]">
                    Extracted Resume Content
                  </label>
                  <span className="text-[10px] font-mono text-[#666666]">
                    {newContent ? `${newContent.split(/\s+/).length} words` : 'Paste or drop file'}
                  </span>
                </div>
                <textarea
                  placeholder="Extracted or pasted resume text will appear here. You can edit or tweak bullet points as needed..."
                  rows={8}
                  value={newContent}
                  onChange={(e) => setNewContent(e.target.value)}
                  className="input-corporate w-full font-mono text-xs"
                  required
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#e0e0e0]">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="btn-secondary-corporate text-xs py-1 px-3.5"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting || uploadingDoc}
                  className="btn-primary-corporate text-xs py-1 px-4"
                >
                  {submitting ? 'Saving...' : 'Save to Vault'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
