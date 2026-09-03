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
    <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
      <div className="card-corporate bg-white border border-[#e0e0e0] w-full max-w-3xl my-8 p-6 rounded-xl space-y-5 animate-fade-in shadow-xl max-h-[90vh] overflow-y-auto text-[#000000]">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-[#e0e0e0]">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-full bg-[#0a66c2]/10 text-[#0a66c2]">
              <Mail size={18} />
            </div>
            <div>
              <h3 className="text-base font-bold text-[#000000] tracking-tight">
                Tailored Outreach & Cover Letter Pitch
              </h3>
              <p className="text-xs text-[#666666]">
                Customized for <strong>{currentJob.title}</strong> at <strong>{currentJob.company}</strong>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-[#666666] hover:text-[#000000] p-1 transition-colors text-base"
          >
            ✕
          </button>
        </div>

        {loading ? (
          <div className="py-16 text-center space-y-3">
            <Loader2 size={24} className="animate-spin text-[#0a66c2] mx-auto" />
            <p className="text-xs text-[#666666]">Crafting high-impact outreach and cover letter pitch...</p>
          </div>
        ) : error ? (
          <div className="p-4 bg-[#b24020]/10 border border-[#b24020]/25 rounded-lg text-[#b24020] text-xs">
            {error}
          </div>
        ) : data ? (
          <div className="space-y-6">
            {/* Subject Line */}
            <div className="p-4 rounded-lg bg-[#f3f6f8] border border-[#e0e0e0] space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[#666666] uppercase tracking-wider">
                  Suggested Email Subject Line
                </span>
                <button
                  onClick={() => handleCopy(data.subject_line, 'subject')}
                  className="text-[11px] text-[#0a66c2] hover:underline font-semibold"
                >
                  Copy Subject
                </button>
              </div>
              <p className="font-mono text-xs text-[#000000] bg-white p-2.5 rounded border border-[#e0e0e0]">
                {data.subject_line}
              </p>
            </div>

            {/* 3-Paragraph Cover Letter Pitch */}
            <div className="p-4 rounded-lg bg-[#f3f6f8] border border-[#e0e0e0] space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[#666666] uppercase tracking-wider flex items-center gap-1.5">
                  <Send size={13} className="text-[#0a66c2]" />
                  <span>3-Paragraph Application Pitch</span>
                </span>
                <button
                  onClick={() => handleCopy(data.cover_letter_pitch, 'pitch')}
                  className="btn-secondary-corporate text-xs py-1 px-3"
                >
                  {copiedPitch ? (
                    <>
                      <Check size={12} className="text-[#057642]" />
                      <span className="text-[#057642] font-semibold">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy size={12} />
                      <span>Copy Pitch</span>
                    </>
                  )}
                </button>
              </div>
              <div className="text-xs text-[#000000] bg-white p-4 rounded-lg border border-[#e0e0e0] whitespace-pre-line leading-relaxed font-sans">
                {data.cover_letter_pitch}
              </div>
            </div>

            {/* LinkedIn Connection Note */}
            <div className="p-4 rounded-lg bg-[#f3f6f8] border border-[#e0e0e0] space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[#666666] uppercase tracking-wider flex items-center gap-1.5">
                  <MessageSquare size={13} className="text-[#0a66c2]" />
                  <span>LinkedIn / Recruiter InMail Note (&lt;300 chars)</span>
                </span>
                <button
                  onClick={() => handleCopy(data.connection_note, 'note')}
                  className="btn-secondary-corporate text-xs py-1 px-3"
                >
                  {copiedNote ? (
                    <>
                      <Check size={12} className="text-[#057642]" />
                      <span className="text-[#057642] font-semibold">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy size={12} />
                      <span>Copy Note</span>
                    </>
                  )}
                </button>
              </div>
              <div className="text-xs text-[#000000] bg-white p-3 rounded-lg border border-[#e0e0e0] font-sans">
                {data.connection_note}
              </div>
            </div>
          </div>
        ) : null}

        <div className="flex justify-between items-center pt-2 border-t border-[#e0e0e0]">
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="btn-secondary-corporate text-xs py-1 px-3.5"
          >
            <Sparkles size={13} />
            <span>Regenerate Pitch</span>
          </button>
          <button onClick={onClose} className="btn-primary-corporate text-xs py-1 px-4">
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
