import React, { useState, useEffect } from 'react';
import {
  Wand2,
  CheckCircle2,
  AlertTriangle,
  Copy,
  Check,
  ShieldCheck,
  HelpCircle,
  Sparkles,
  Loader2,
  Briefcase,
  FolderGit2,
  X,
  Plus,
} from 'lucide-react';
import { optimizeBullet } from '../api/client';

export default function BulletOptimizerModal({
  isOpen,
  onClose,
  initialKeyword = '',
  initialKeywords = [],
  initialSectionType = 'work_history',
  targetJobTitle = 'Software Engineer',
  selectedResume = null,
}) {
  const [keywords, setKeywords] = useState([]);
  const [newSkillInput, setNewSkillInput] = useState('');
  const [sectionType, setSectionType] = useState('work_history'); // 'work_history' or 'project'
  const [existingBullet, setExistingBullet] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [userConfirmed, setUserConfirmed] = useState(false);

  useEffect(() => {
    let kwList = [];
    if (initialKeywords && initialKeywords.length > 0) {
      kwList = [...initialKeywords];
    } else if (initialKeyword) {
      kwList = [initialKeyword];
    }
    setKeywords(kwList);
    setSectionType(initialSectionType || 'work_history');
    setResult(null);
  }, [initialKeyword, initialKeywords, initialSectionType, isOpen]);

  useEffect(() => {
    if (isOpen && keywords.length > 0 && !result && !loading) {
      handleGenerate();
    }
  }, [isOpen, keywords]);

  if (!isOpen) return null;

  const handleRemoveSkill = (skillToRemove) => {
    const updated = keywords.filter((k) => k !== skillToRemove);
    setKeywords(updated);
  };

  const handleAddSkill = (e) => {
    e.preventDefault();
    if (newSkillInput.trim() && !keywords.includes(newSkillInput.trim())) {
      setKeywords([...keywords, newSkillInput.trim()]);
      setNewSkillInput('');
    }
  };

  const handleGenerate = async (e) => {
    e?.preventDefault();
    if (keywords.length === 0) {
      setError('Please add at least one target skill to incorporate.');
      return;
    }
    setLoading(true);
    setError('');
    setUserConfirmed(false);

    try {
      const evidenceContext = selectedResume
        ? [selectedResume.content.slice(0, 2000)]
        : [];

      const res = await optimizeBullet({
        target_job_title: targetJobTitle || 'Software Engineer',
        section_type: sectionType,
        target_keyword: keywords.join(', '),
        target_keywords: keywords,
        existing_bullet: existingBullet.trim() || '',
        evidence_context: evidenceContext,
      });

      setResult(res);
    } catch (err) {
      setError(err.message || 'Failed to generate optimized bullet points.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (text, idx) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto">
      <div className="glass-panel bg-slate-900 border border-slate-700 w-full max-w-3xl my-8 p-6 rounded-2xl space-y-5 animate-fade-in shadow-2xl max-h-[90vh] overflow-y-auto">
        {/* Modal Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-indigo-500/20 text-indigo-400">
              <Wand2 size={20} />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">
                BulletSkill 2.0 Resume Optimizer
              </h3>
              <p className="text-xs text-slate-400">
                Incorporate target skills into <strong>{sectionType === 'project' ? 'Project' : 'Work History'}</strong> bullet points
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

        {/* Target Skills Pill Bank */}
        <div className="space-y-2 glass-card p-4">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold text-slate-300">
              Target Skills to Incorporate ({keywords.length})
            </label>
            <span className="text-[11px] text-slate-400">
              Targeting: <strong>{targetJobTitle}</strong>
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-2 pt-1">
            {keywords.map((kw, i) => (
              <span
                key={i}
                className="badge-pill bg-indigo-600/20 border border-indigo-500/40 text-indigo-200 text-xs py-1 px-2.5 flex items-center gap-1.5"
              >
                <span className="font-semibold">{kw}</span>
                <button
                  type="button"
                  onClick={() => handleRemoveSkill(kw)}
                  className="hover:text-rose-400 text-slate-400"
                  title="Remove skill"
                >
                  <X size={12} />
                </button>
              </span>
            ))}

            {/* Add skill input */}
            <div className="flex items-center gap-1">
              <input
                type="text"
                value={newSkillInput}
                onChange={(e) => setNewSkillInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAddSkill(e)}
                placeholder="+ Add skill..."
                className="bg-slate-950/70 border border-slate-700 rounded-lg px-2.5 py-1 text-xs text-white placeholder-slate-500 outline-none w-28 focus:w-36 transition-all"
              />
              {newSkillInput && (
                <button
                  type="button"
                  onClick={handleAddSkill}
                  className="p-1 rounded bg-indigo-600 text-white text-xs hover:bg-indigo-500"
                >
                  <Plus size={12} />
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Controls: Section Type + Optional Existing Bullet */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Resume Section
            </label>
            <div className="grid grid-cols-2 gap-2 bg-slate-950/60 p-1 rounded-xl border border-slate-800">
              <button
                type="button"
                onClick={() => {
                  setSectionType('project');
                  setResult(null);
                }}
                className={`flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-semibold transition-all ${
                  sectionType === 'project'
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <FolderGit2 size={13} />
                <span>Project Bullet</span>
              </button>
              <button
                type="button"
                onClick={() => {
                  setSectionType('work_history');
                  setResult(null);
                }}
                className={`flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-semibold transition-all ${
                  sectionType === 'work_history'
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <Briefcase size={13} />
                <span>Work History</span>
              </button>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Existing Bullet to Tweak (Optional)
            </label>
            <input
              type="text"
              placeholder="Leave blank to generate a fresh high-impact bullet..."
              value={existingBullet}
              onChange={(e) => setExistingBullet(e.target.value)}
              className="input-field text-xs py-2"
            />
          </div>
        </div>

        {/* Generate / Regenerate Button */}
        <div className="flex justify-end">
          <button
            onClick={handleGenerate}
            disabled={loading || keywords.length === 0}
            className="btn-primary text-xs"
          >
            {loading ? (
              <>
                <Loader2 size={13} className="animate-spin" />
                <span>Generating BulletSkill Candidates...</span>
              </>
            ) : (
              <>
                <Sparkles size={13} />
                <span>Generate Bullet Candidates ({keywords.length} Skills)</span>
              </>
            )}
          </button>
        </div>

        {error && (
          <div className="p-3.5 bg-rose-500/20 border border-rose-500/40 rounded-xl text-rose-300 text-xs flex items-center gap-2">
            <AlertTriangle size={15} />
            <span>{error}</span>
          </div>
        )}

        {/* Results Container */}
        {result && (
          <div className="space-y-4 pt-2 border-t border-slate-800">
            {/* Verification Gate / Warning */}
            {result.requires_confirmation && (
              <div className="p-4 rounded-xl bg-amber-950/40 border border-amber-500/40 text-amber-200 space-y-2">
                <div className="flex items-start gap-2.5">
                  <AlertTriangle size={16} className="text-amber-400 shrink-0 mt-0.5" />
                  <div>
                    <h5 className="font-bold text-xs uppercase tracking-wide text-amber-300">
                      Unverified Skill Gate (Resume Guide 2.0 Compliance)
                    </h5>
                    <p className="text-xs text-amber-200/90 mt-0.5">
                      {result.warning ||
                        `Confirm you have hands-on experience with ${keywords.join(', ')} before exporting to your resume.`}
                    </p>
                  </div>
                </div>

                <label className="flex items-center gap-2 pt-1 text-xs cursor-pointer select-none text-slate-100 font-medium">
                  <input
                    type="checkbox"
                    checked={userConfirmed}
                    onChange={(e) => setUserConfirmed(e.target.checked)}
                    className="rounded border-slate-700 text-indigo-600 focus:ring-0 w-4 h-4 bg-slate-900"
                  />
                  <span>
                    Yes, I have worked with these technologies and verify this claim is true.
                  </span>
                </label>
              </div>
            )}

            {/* Alternatives Grid */}
            <div className="space-y-3">
              {result.alternatives.map((alt, idx) => (
                <div
                  key={idx}
                  className="glass-card p-4 space-y-2.5 border-slate-800 hover:border-slate-700 transition-all text-xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-indigo-400 tracking-wide uppercase text-[11px]">
                      {alt.variant_name}
                    </span>
                    <button
                      onClick={() => handleCopy(alt.bullet, idx)}
                      className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs transition-colors"
                    >
                      {copiedIndex === idx ? (
                        <>
                          <Check size={12} className="text-emerald-400" />
                          <span className="text-emerald-400 font-semibold">Copied!</span>
                        </>
                      ) : (
                        <>
                          <Copy size={12} />
                          <span>Copy Bullet</span>
                        </>
                      )}
                    </button>
                  </div>

                  {/* Bullet text */}
                  <p className="font-mono text-xs text-slate-100 bg-slate-950/70 p-3 rounded-lg border border-slate-800/90 leading-relaxed">
                    • {alt.bullet}
                  </p>

                  {/* What / How / Result Breakdown */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-2 pt-1 text-[11px] text-slate-400">
                    <div className="bg-slate-900/50 p-2 rounded border border-slate-800/60">
                      <strong className="text-indigo-300 block mb-0.5">WHAT (Keyword):</strong>
                      <span className="text-slate-200">{alt.what}</span>
                    </div>
                    <div className="bg-slate-900/50 p-2 rounded border border-slate-800/60">
                      <strong className="text-indigo-300 block mb-0.5">HOW (Action):</strong>
                      <span className="text-slate-200">{alt.how}</span>
                    </div>
                    <div className="bg-slate-900/50 p-2 rounded border border-slate-800/60">
                      <strong className="text-indigo-300 block mb-0.5">RESULT / REASON:</strong>
                      <span className="text-slate-200">{alt.result_or_reason}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="flex justify-end pt-3 border-t border-slate-800">
          <button onClick={onClose} className="btn-secondary text-xs">
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
