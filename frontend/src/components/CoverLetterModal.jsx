import React, { useState, useEffect } from 'react';
import { Mail, Copy, Check, Sparkles, Loader2, MessageSquare, Send } from 'lucide-react';
import { generateOutreach } from '../api/client';

export default function CoverLetterModal({
  isOpen,
  onClose,
  currentJob,
  selectedResume,
  onAiError,
}) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [copiedPitch, setCopiedPitch] = useState(false);
  const [copiedNote, setCopiedNote] = useState(false);

  useEffect(() => {
    if (isOpen && currentJob) {
      handleGenerate();
    }
  }, [isOpen, currentJob]);

  if (!isOpen || !currentJob) return null;

  const handleGenerate = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await generateOutreach({
        job: currentJob,
        resume_id: selectedResume?.id || null,
        resume_content: selectedResume?.content || null,
      });
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to generate tailored outreach.');
      if (onAiError && (err.canSwitchOffline || err.status === 502)) {
        onAiError(err, () => handleGenerate());
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (text, type) => {
    navigator.clipboard.writeText(text);
    if (type === 'pitch') {
      setCopiedPitch(true);
      setTimeout(() => setCopiedPitch(false), 2000);
    } else {
      setCopiedNote(true);
      setTimeout(() => setCopiedNote(false), 2000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto">
      <div className="glass-panel bg-slate-900 border border-slate-700 w-full max-w-3xl my-8 p-6 rounded-2xl space-y-5 animate-fade-in shadow-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-cyan-500/20 text-cyan-400">
              <Mail size={20} />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">
                Tailored Outreach & Cover Letter Pitch
              </h3>
              <p className="text-xs text-slate-400">
                Customized for <strong>{currentJob.title}</strong> at <strong>{currentJob.company}</strong>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white text-lg font-bold p-1 transition-colors"
          >
            ✕
          </button>
        </div>

        {loading ? (
          <div className="py-16 text-center space-y-3">
            <Loader2 size={24} className="animate-spin text-cyan-400 mx-auto" />
            <p className="text-xs text-slate-400">Crafting high-impact outreach and cover letter pitch...</p>
          </div>
        ) : error ? (
          <div className="p-4 bg-rose-500/20 border border-rose-500/40 rounded-xl text-rose-300 text-xs">
            {error}
          </div>
        ) : data ? (
          <div className="space-y-6">
            {/* Subject Line */}
            <div className="glass-card p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Suggested Email Subject Line
                </span>
                <button
                  onClick={() => handleCopy(data.subject_line, 'subject')}
                  className="text-[11px] text-indigo-400 hover:text-indigo-300"
                >
                  Copy Subject
                </button>
              </div>
              <p className="font-mono text-xs text-slate-200 bg-slate-950/70 p-2.5 rounded border border-slate-800">
                {data.subject_line}
              </p>
            </div>

            {/* 3-Paragraph Cover Letter Pitch */}
            <div className="glass-card p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Send size={13} className="text-cyan-400" />
                  <span>3-Paragraph Application Pitch</span>
                </span>
                <button
                  onClick={() => handleCopy(data.cover_letter_pitch, 'pitch')}
                  className="text-xs flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-300 transition-colors"
                >
                  {copiedPitch ? (
                    <>
                      <Check size={12} className="text-emerald-400" />
                      <span className="text-emerald-400 font-medium">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy size={12} />
                      <span>Copy Pitch</span>
                    </>
                  )}
                </button>
              </div>
              <div className="text-xs text-slate-200 bg-slate-950/70 p-4 rounded-lg border border-slate-800 whitespace-pre-line leading-relaxed font-sans">
                {data.cover_letter_pitch}
              </div>
            </div>

            {/* LinkedIn Connection Note */}
            <div className="glass-card p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                  <MessageSquare size={13} className="text-amber-400" />
                  <span>LinkedIn / Recruiter InMail Note (&lt;300 chars)</span>
                </span>
                <button
                  onClick={() => handleCopy(data.connection_note, 'note')}
                  className="text-xs flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-amber-300 transition-colors"
                >
                  {copiedNote ? (
                    <>
                      <Check size={12} className="text-emerald-400" />
                      <span className="text-emerald-400 font-medium">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy size={12} />
                      <span>Copy Note</span>
                    </>
                  )}
                </button>
              </div>
              <div className="text-xs text-slate-200 bg-slate-950/70 p-3 rounded-lg border border-slate-800 font-sans">
                {data.connection_note}
              </div>
            </div>
          </div>
        ) : null}

        <div className="flex justify-between items-center pt-2 border-t border-slate-800">
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="btn-secondary text-xs"
          >
            <Sparkles size={13} />
            <span>Regenerate Pitch</span>
          </button>
          <button onClick={onClose} className="btn-primary text-xs">
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
