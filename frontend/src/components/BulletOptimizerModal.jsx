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
} from 'lucide-react';
import { optimizeBullet } from '../api/client';

export default function BulletOptimizerModal({
  isOpen,
  onClose,
  initialKeyword = '',
  targetJobTitle = 'Software Engineer',
  selectedResume = null,
}) {
  const [keyword, setKeyword] = useState(initialKeyword);
  const [sectionType, setSectionType] = useState('work_history'); // 'work_history' or 'project'
  const [existingBullet, setExistingBullet] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [userConfirmed, setUserConfirmed] = useState(false);

  useEffect(() => {
    if (initialKeyword) {
      setKeyword(initialKeyword);
    }
  }, [initialKeyword]);

  if (!isOpen) return null;

  const handleGenerate = async (e) => {
    e?.preventDefault();
    if (!keyword.trim()) {
      setError('Please provide a target keyword or skill.');
      return;
    }
    setLoading(true);
    setError('');
    setUserConfirmed(false);

    try {
      const evidenceContext = selectedResume
        ? [selectedResume.content.slice(0, 1500)]
        : [];

      const res = await optimizeBullet({
        target_job_title: targetJobTitle || 'Software Engineer',
        section_type: sectionType,
        target_keyword: keyword.trim(),
        existing_bullet: existingBullet.trim() || `Contributed to backend development and feature delivery.`,
        evidence_context: evidenceContext,
      });
      setResult(res);
    } catch (err) {
      setError(err.message || 'Failed to optimize bullet.');
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
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-indigo-500/20 text-indigo-400">
              <Wand2 size={20} />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <span>Resume Bullet Optimizer</span>
                <span className="text-xs px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 font-mono font-normal border border-indigo-800/60">
                  BulletSkill 2.0
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Rewrites bullets to incorporate missing skills using the{' '}
                <strong className="text-slate-200">What + How + Result/Reason</strong> framework.
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

        {/* Input Form */}
        <form onSubmit={handleGenerate} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Target Missing Keyword
              </label>
              <input
                type="text"
                placeholder="e.g. Kafka, Docker, Kubernetes, GraphQL"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                className="input-field font-medium text-indigo-300"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Resume Section Type
              </label>
              <div className="grid grid-cols-2 gap-2 bg-slate-950/70 p-1 rounded-xl border border-slate-800">
                <button
                  type="button"
                  onClick={() => setSectionType('work_history')}
                  className={`flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-lg text-xs font-medium transition-all ${
                    sectionType === 'work_history'
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <Briefcase size={13} />
                  <span>Work History</span>
                </button>
                <button
                  type="button"
                  onClick={() => setSectionType('project')}
                  className={`flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-lg text-xs font-medium transition-all ${
                    sectionType === 'project'
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <FolderGit2 size={13} />
                  <span>Project</span>
                </button>
              </div>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Existing Bullet Point to Revise (or brief context)
            </label>
            <textarea
              placeholder="e.g. Developed backend services and managed database queries for order workflows."
              rows={2}
              value={existingBullet}
              onChange={(e) => setExistingBullet(e.target.value)}
              className="input-field text-xs font-mono"
            />
          </div>

          {error && (
            <div className="p-3 bg-rose-500/20 border border-rose-500/40 rounded-lg text-rose-300 text-xs flex items-center gap-2">
              <AlertTriangle size={14} />
              <span>{error}</span>
            </div>
          )}

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={loading}
              className="btn-primary text-xs"
            >
              {loading ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  <span>Optimizing with BulletSkill...</span>
                </>
              ) : (
                <>
                  <Sparkles size={14} />
                  <span>Generate Tailored Alternatives</span>
                </>
              )}
            </button>
          </div>
        </form>

        {/* Results Area */}
        {result && (
          <div className="space-y-5 pt-4 border-t border-slate-800 animate-fade-in">
            {/* Claim Status Banner */}
            <div
              className={`p-4 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                result.claim_status === 'verified' || userConfirmed
                  ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300'
                  : 'bg-amber-950/40 border-amber-500/40 text-amber-300'
              }`}
            >
              <div className="flex items-start gap-2.5">
                {result.claim_status === 'verified' || userConfirmed ? (
                  <ShieldCheck size={20} className="text-emerald-400 mt-0.5 shrink-0" />
                ) : (
                  <AlertTriangle size={20} className="text-amber-400 mt-0.5 shrink-0" />
                )}
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-xs uppercase tracking-wide">
                      {userConfirmed
                        ? 'User Confirmed (Verified for Export)'
                        : result.claim_status === 'verified'
                        ? 'Verified Claim'
                        : 'Unverified Skill Suggestion'}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 mt-0.5 leading-relaxed">
                    {userConfirmed
                      ? `You confirmed using ${result.target_keyword}. This bullet is now ready for resume export.`
                      : result.warning ||
                        `Target skill "${result.target_keyword}" matches verified evidence from your resume context.`}
                  </p>
                </div>
              </div>

              {/* Confirmation Button for Unverified Skills */}
              {result.claim_status !== 'verified' && !userConfirmed && (
                <button
                  type="button"
                  onClick={() => setUserConfirmed(true)}
                  className="btn-secondary text-xs border-amber-500/50 hover:bg-amber-500/20 text-amber-200 whitespace-nowrap"
                >
                  <CheckCircle2 size={14} className="text-emerald-400" />
                  <span>Yes, I used this!</span>
                </button>
              )}
            </div>

            {/* 3 Alternatives */}
            <div className="space-y-4">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Bullet Alternatives (3 Variants)
              </h4>

              {result.alternatives.map((alt, idx) => (
                <div
                  key={idx}
                  className="glass-card p-4 space-y-3 border-slate-700/80 hover:border-indigo-500/50 transition-all"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-indigo-300 flex items-center gap-1.5">
                      <Sparkles size={13} />
                      <span>{alt.variant_name}</span>
                    </span>

                    <button
                      onClick={() => handleCopy(alt.bullet, idx)}
                      className="text-xs flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
                    >
                      {copiedIndex === idx ? (
                        <>
                          <Check size={12} className="text-emerald-400" />
                          <span className="text-emerald-400 font-medium">Copied!</span>
                        </>
                      ) : (
                        <>
                          <Copy size={12} />
                          <span>Copy</span>
                        </>
                      )}
                    </button>
                  </div>

                  {/* The Bullet text */}
                  <p className="text-xs font-mono text-slate-100 bg-slate-950/70 p-3 rounded-lg border border-slate-800 leading-relaxed">
                    • {alt.bullet}
                  </p>

                  {/* Breakdown Grid: What + How + Result/Reason */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-[11px] pt-1">
                    <div className="bg-slate-900/60 p-2 rounded border border-slate-800">
                      <span className="font-semibold text-rose-400 block mb-0.5">WHAT / Keyword:</span>
                      <span className="text-slate-300">{alt.what}</span>
                    </div>
                    <div className="bg-slate-900/60 p-2 rounded border border-slate-800">
                      <span className="font-semibold text-sky-400 block mb-0.5">HOW it was used:</span>
                      <span className="text-slate-300">{alt.how}</span>
                    </div>
                    <div className="bg-slate-900/60 p-2 rounded border border-slate-800">
                      <span className="font-semibold text-emerald-400 block mb-0.5">RESULT / Reason:</span>
                      <span className="text-slate-300">{alt.result_or_reason}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
