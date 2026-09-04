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
  Pencil,
  Eye,
  Check,
  Copy,
  Download,
} from 'lucide-react';
import {
  getResumes,
  addResume,
  deleteResume,
  uploadResumeFile,
  parseResumeFile,
  updateResume,
} from '../api/client';

export default function ResumeLibrary({ onResumesUpdated }) {
  const [resumes, setResumes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newName, setNewName] = useState('');
  const [newContent, setNewContent] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [uploadingDoc, setUploadingDoc] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  // Inline editing state
  const [editingId, setEditingId] = useState(null);
  const [editingName, setEditingName] = useState('');
  const [renaming, setRenaming] = useState(false);

  // Quick View modal state
  const [viewingResume, setViewingResume] = useState(null);
  const [copied, setCopied] = useState(false);

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

  const handleCloseAddModal = () => {
    setShowAddModal(false);
    setNewName('');
    setNewContent('');
    setSelectedFile(null);
    setError('');
  };

  const handleCreate = async (e) => {
    if (e) e.preventDefault();
    if (!newName.trim() || !newContent.trim()) {
      setError('Both resume title and content are required.');
      return;
    }
    setSubmitting(true);
    setError('');
    try {
      if (selectedFile) {
        // Upload the actual binary with the user's custom title
        await uploadResumeFile(selectedFile, newName.trim());
      } else {
        // Plain text entry
        await addResume({ name: newName.trim(), content: newContent.trim() });
      }
      handleCloseAddModal();
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

    // Only set newName if user hasn't already typed a custom title
    if (!newName.trim()) {
      setNewName(suggestedTitle);
    }
    setSelectedFile(file);

    try {
      if (file.name.endsWith('.txt') || file.name.endsWith('.md')) {
        const text = await file.text();
        setNewContent(text);
      } else {
        // Parse document on the fly without creating a record in the database yet
        const parsed = await parseResumeFile(file);
        setNewContent(parsed.text);
        if (!newName.trim()) {
          setNewName(parsed.suggested_title || suggestedTitle);
        }
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

  // Inline editing handlers
  const handleStartEdit = (resume) => {
    setEditingId(resume.id);
    setEditingName(resume.name);
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditingName('');
  };

  const handleSaveEdit = async (id) => {
    if (!editingName.trim()) return;
    setRenaming(true);
    try {
      const updated = await updateResume(id, { name: editingName.trim() });
      setResumes((prev) =>
        prev.map((r) => (r.id === id ? { ...r, name: updated.name } : r))
      );
      if (onResumesUpdated) {
        onResumesUpdated(
          resumes.map((r) => (r.id === id ? { ...r, name: updated.name } : r))
        );
      }
      setEditingId(null);
      setEditingName('');
    } catch (err) {
      alert(err.message || 'Failed to rename resume');
    } finally {
      setRenaming(false);
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
            <div
              key={resume.id}
              className="card-corporate p-5 bg-white border border-[#e0e0e0] hover:border-[#c1c6d4] transition-all rounded-lg flex flex-col justify-between space-y-4 shadow-none"
            >
              <div>
                {/* Header with Title and Action Icons */}
                <div className="flex items-start justify-between gap-2 mb-1.5">
                  {editingId === resume.id ? (
                    <div className="flex items-center gap-1.5 flex-1 mr-2">
                      <input
                        type="text"
                        value={editingName}
                        onChange={(e) => setEditingName(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleSaveEdit(resume.id);
                          if (e.key === 'Escape') handleCancelEdit();
                        }}
                        className="input-corporate py-1 px-2 text-xs font-semibold w-full"
                        autoFocus
                        disabled={renaming}
                      />
                      <button
                        onClick={() => handleSaveEdit(resume.id)}
                        disabled={renaming}
                        className="p-1 text-[#057642] hover:bg-[#057642]/10 rounded transition-colors"
                        title="Save title"
                      >
                        <Check size={14} />
                      </button>
                      <button
                        onClick={handleCancelEdit}
                        disabled={renaming}
                        className="p-1 text-[#666666] hover:bg-[#e0e0e0] rounded transition-colors"
                        title="Cancel"
                      >
                        <X size={14} />
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center gap-1.5 min-w-0 flex-1">
                      <h3
                        className="font-bold text-[#000000] text-sm truncate"
                        title={resume.name}
                      >
                        {resume.name}
                      </h3>
                      <button
                        onClick={() => handleStartEdit(resume)}
                        className="text-[#666666] hover:text-[#0a66c2] p-1 rounded hover:bg-[#f3f6f8] transition-colors shrink-0"
                        title="Rename resume title"
                      >
                        <Pencil size={13} />
                      </button>
                    </div>
                  )}

                  <div className="flex items-center gap-1 shrink-0">
                    <button
                      onClick={() => setViewingResume(resume)}
                      title="Quick View full resume"
                      className="text-[#666666] hover:text-[#0a66c2] p-1 rounded hover:bg-[#f3f6f8] transition-colors"
                    >
                      <Eye size={14} />
                    </button>
                    <button
                      onClick={() => handleDelete(resume.id)}
                      title="Delete resume"
                      className="text-[#666666] hover:text-[#b24020] p-1 rounded hover:bg-[#b24020]/10 transition-colors"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
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
                <span className="font-mono text-[10px] text-[#666666]">
                  {resume.content.split(/\s+/).length} words
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Resume Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="card-corporate bg-white border border-[#e0e0e0] w-full max-w-3xl max-h-[88vh] rounded-xl flex flex-col animate-fade-in shadow-2xl text-[#000000] overflow-hidden">
            {/* Modal Header (Fixed) */}
            <div className="flex items-center justify-between p-5 border-b border-[#e0e0e0] shrink-0 bg-white">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-full bg-[#0a66c2]/10 text-[#0a66c2]">
                  <FileText size={18} />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#000000] tracking-tight">Add Resume Profile</h3>
                  <p className="text-[11px] text-[#666666]">Add a tailored resume to your vault for ATS matching</p>
                </div>
              </div>
              <button
                onClick={handleCloseAddModal}
                className="text-[#666666] hover:text-[#000000] p-1.5 rounded-full hover:bg-[#f3f6f8] transition-colors"
                title="Close"
              >
                <X size={16} />
              </button>
            </div>

            {/* Modal Body (Scrollable if needed) */}
            <div className="p-6 overflow-y-auto space-y-4 flex-1">
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
                className={`border border-dashed rounded-lg p-5 text-center cursor-pointer transition-all ${
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
                  <div className="space-y-2 py-1">
                    <Loader2 size={20} className="animate-spin text-[#0a66c2] mx-auto" />
                    <p className="text-xs text-[#0a66c2] font-semibold font-mono">
                      Extracting text from document...
                    </p>
                  </div>
                ) : (
                  <div className="space-y-1">
                    <div className="flex items-center justify-center gap-2 text-[#000000] text-xs font-semibold">
                      <Upload size={14} className="text-[#0a66c2]" />
                      <span>
                        {selectedFile
                          ? `Document Selected: ${selectedFile.name} (${(selectedFile.size / 1024).toFixed(1)} KB)`
                          : 'Drop your resume file here or click to browse'}
                      </span>
                    </div>
                    <p className="text-[11px] text-[#666666]">
                      Supports <strong>.PDF</strong>, <strong>.DOCX (Word)</strong>, <strong>.TXT</strong>, <strong>.MD</strong>
                    </p>
                  </div>
                )}
              </div>

              <form id="add-resume-form" onSubmit={handleCreate} className="space-y-4">
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
                  <p className="text-[10px] text-[#666666] mt-1">
                    This custom title identifies this resume profile across the application.
                  </p>
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
                    rows={7}
                    value={newContent}
                    onChange={(e) => setNewContent(e.target.value)}
                    className="input-corporate w-full font-mono text-xs"
                    required
                  />
                </div>
              </form>
            </div>

            {/* Modal Footer (Fixed & Sticky) */}
            <div className="p-4 border-t border-[#e0e0e0] bg-[#fcfdfe] flex items-center justify-between shrink-0">
              <span className="text-[11px] text-[#666666]">
                {selectedFile ? (
                  <span className="text-[#057642] font-medium flex items-center gap-1">
                    <CheckCircle size={12} /> Document binary ready for vault storage
                  </span>
                ) : (
                  'Manual text entry'
                )}
              </span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleCloseAddModal}
                  className="btn-secondary-corporate text-xs py-1.5 px-4"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  form="add-resume-form"
                  disabled={submitting || uploadingDoc}
                  className="btn-primary-corporate text-xs py-1.5 px-5 flex items-center gap-1.5"
                >
                  {submitting && <Loader2 size={13} className="animate-spin" />}
                  <span>{submitting ? 'Saving...' : 'Save to Vault'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Quick View Modal */}
      {viewingResume && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="card-corporate bg-white border border-[#e0e0e0] w-full max-w-3xl max-h-[90vh] rounded-xl flex flex-col animate-fade-in shadow-2xl text-[#000000] overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between p-5 border-b border-[#e0e0e0] shrink-0 bg-white">
              <div className="flex items-center gap-2.5 min-w-0 flex-1 mr-4">
                <div className="p-2 rounded-full bg-[#0a66c2]/10 text-[#0a66c2] shrink-0">
                  <FileText size={18} />
                </div>
                <div className="min-w-0">
                  <h3 className="text-sm font-bold text-[#000000] tracking-tight truncate">
                    {viewingResume.name}
                  </h3>
                  <div className="flex items-center gap-2 mt-0.5 text-[11px] text-[#666666]">
                    <span>Added: {new Date(viewingResume.created_at).toLocaleDateString()}</span>
                    <span>•</span>
                    <span className="font-mono">{viewingResume.content.split(/\s+/).length} words</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(viewingResume.content);
                    setCopied(true);
                    setTimeout(() => setCopied(false), 2000);
                  }}
                  className="btn-secondary-corporate text-xs py-1 px-3 flex items-center gap-1.5"
                  title="Copy full resume text"
                >
                  {copied ? <Check size={13} className="text-[#057642]" /> : <Copy size={13} />}
                  <span>{copied ? 'Copied!' : 'Copy Text'}</span>
                </button>

                {viewingResume.download_url && (
                  <a
                    href={viewingResume.download_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-secondary-corporate text-xs py-1 px-3 flex items-center gap-1.5"
                    title="Download original uploaded file"
                  >
                    <Download size={13} />
                    <span>Download File</span>
                  </a>
                )}

                <button
                  onClick={() => setViewingResume(null)}
                  className="text-[#666666] hover:text-[#000000] p-1.5 rounded-full hover:bg-[#f3f6f8] transition-colors"
                  title="Close"
                >
                  <X size={16} />
                </button>
              </div>
            </div>

            {/* Scrollable Document Reader Body */}
            <div className="p-6 overflow-y-auto flex-1 bg-[#f8fafc]">
              <div className="bg-white border border-[#e0e0e0] rounded-lg p-5 font-mono text-xs text-[#000000] whitespace-pre-wrap leading-relaxed shadow-sm selection:bg-[#0a66c2]/20">
                {viewingResume.content}
              </div>
            </div>

            {/* Footer */}
            <div className="p-3.5 border-t border-[#e0e0e0] bg-[#fcfdfe] flex items-center justify-between shrink-0 text-xs text-[#666666]">
              <span className="flex items-center gap-1.5 text-[#057642] font-semibold text-[11px]">
                <CheckCircle size={13} /> Active in ATS Optimizer & Tailored Outreach
              </span>
              <button
                type="button"
                onClick={() => setViewingResume(null)}
                className="btn-secondary-corporate text-xs py-1 px-4"
              >
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
