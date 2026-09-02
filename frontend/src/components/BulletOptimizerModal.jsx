import React, { useState, useEffect } from 'react';
import {
  Wand2,
  CheckCircle2,
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
  ArrowRight,
  Target,
  FileEdit,
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
  onMarkSkillsAdded = null,
}) {
  const [keywords, setKeywords] = useState([]);
  const [newSkillInput, setNewSkillInput] = useState('');
  const [sectionType, setSectionType] = useState('work_history'); // 'work_history' or 'project'
  const [existingBullet, setExistingBullet] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [showBulletPicker, setShowBulletPicker] = useState(false);
  const [addedConfirmed, setAddedConfirmed] = useState(false);

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
    setExistingBullet('');
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

  const handleGenerate = async (e, overrideBullet = null) => {
    e?.preventDefault();
    if (keywords.length === 0) {
      setError('Please add at least one target skill to incorporate.');
      return;
    }
    setLoading(true);
    setError('');
    setAddedConfirmed(false);

    const bulletToUse = overrideBullet !== null ? overrideBullet : existingBullet;

    try {
      const evidenceContext = selectedResume
        ? [selectedResume.content.slice(0, 3000)]
        : [];

      const res = await optimizeBullet({
        target_job_title: targetJobTitle || 'Software Engineer',
        section_type: sectionType,
        target_keyword: keywords.join(', '),
        target_keywords: keywords,
        existing_bullet: bulletToUse.trim(),
        evidence_context: evidenceContext,
      });

      setResult(res);
      if (res.original_bullet_to_replace && !existingBullet) {
        setExistingBullet(res.original_bullet_to_replace);
      }
    } catch (err) {
      setError(err.message || 'Failed to generate optimized bullet points.');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectDifferentBullet = (bulletObj) => {
    setExistingBullet(bulletObj.bullet);
    setShowBulletPicker(false);
    handleGenerate(null, bulletObj.bullet);
  };

  const handleCopy = (text, idx) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const handleMarkAdded = () => {
    if (onMarkSkillsAdded && keywords.length > 0) {
      onMarkSkillsAdded(keywords);
      setAddedConfirmed(true);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto">
      <div className="glass-panel bg-slate-900 border border-slate-700 w-full max-w-3xl my-8 p-6 rounded-2xl space-y-5 animate-fade-in shadow-2xl max-h-[92vh] overflow-y-auto">
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
              <p className="text-xs text-slate-300">
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
            <label className="text-xs font-semibold text-slate-200">
              Target Skills to Incorporate ({keywords.length})
            </label>
            <span className="text-[11px] text-slate-400">
              Targeting: <strong className="text-slate-200">{targetJobTitle}</strong>
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-2 pt-1">
            {keywords.map((kw, i) => (
              <span
                key={i}
                className="badge-pill bg-indigo-600/30 border border-indigo-500/50 text-indigo-200 text-xs py-1 px-2.5 flex items-center gap-1.5"
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

        {/* Section Type Switcher */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-300">Resume Section:</span>
            <div className="flex bg-slate-950/80 p-1 rounded-xl border border-slate-800 text-xs">
              <button
                type="button"
                onClick={() => {
                  setSectionType('project');
                  setResult(null);
                }}
                className={`flex items-center gap-1.5 py-1.5 px-3 rounded-lg font-semibold transition-all ${
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
                className={`flex items-center gap-1.5 py-1.5 px-3 rounded-lg font-semibold transition-all ${
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

          <button
            onClick={(e) => handleGenerate(e)}
            disabled={loading || keywords.length === 0}
            className="btn-primary text-xs self-end sm:self-auto"
          >
            {loading ? (
              <>
                <Loader2 size={13} className="animate-spin" />
                <span>Analyzing & Optimizing...</span>
              </>
            ) : (
              <>
                <Sparkles size={13} />
                <span>Regenerate Recommendations</span>
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
            {/* 🎯 Target Project & Bullet Point to Change Card */}
            <div className="p-4 rounded-xl bg-gradient-to-r from-indigo-950/60 to-slate-900 border border-indigo-500/40 space-y-3 shadow-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded-lg bg-indigo-500/20 text-indigo-300">
                    {sectionType === 'project' ? <FolderGit2 size={16} /> : <Briefcase size={16} />}
                  </div>
                  <div>
                    <h4 className="font-bold text-xs uppercase tracking-wide text-indigo-300">
                      {sectionType === 'project' ? 'Target Project in Resume' : 'Target Role / Employment in Resume'}
                    </h4>
                    <span className="text-xs font-semibold text-white">
                      {result.target_project_name || (sectionType === 'project' ? 'Primary Technical Project' : 'Professional Work Experience')}
                    </span>
                  </div>
                </div>

                {result.available_resume_bullets && result.available_resume_bullets.length > 1 && (
                  <button
                    onClick={() => setShowBulletPicker(!showBulletPicker)}
                    className="text-[11px] text-cyan-400 hover:text-cyan-300 underline font-medium"
                  >
                    {showBulletPicker ? 'Hide Bullets' : `Change Target ${sectionType === 'project' ? 'Project' : 'Job'} Bullet`}
                  </button>
                )}
              </div>

              {/* Strategic Rationale */}
              {result.replacement_rationale && (
                <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
                  <strong className="text-cyan-300">Strategy: </strong>
                  {result.replacement_rationale}
                </p>
              )}

              {/* Current Bullet in Resume to Replace */}
              {result.original_bullet_to_replace && (
                <div className="space-y-1.5 pt-1">
                  <div className="flex items-center gap-1.5 text-[11px] font-semibold text-rose-400 uppercase tracking-wider">
                    <span>
                      {sectionType === 'project'
                        ? 'Current Project Bullet in Resume to Replace:'
                        : 'Current Work History Bullet in Resume to Replace:'}
                    </span>
                  </div>
                  <div className="font-mono text-xs text-rose-200 bg-rose-950/30 p-2.5 rounded-lg border border-rose-500/30 leading-relaxed">
                    • {result.original_bullet_to_replace}
                  </div>
                </div>
              )}

              {/* Bullet Picker Dropdown */}
              {showBulletPicker && result.available_resume_bullets && (
                <div className="p-3 bg-slate-950/90 rounded-xl border border-slate-700 space-y-2 mt-2">
                  <span className="text-xs font-semibold text-slate-300 block">
                    Choose which existing {sectionType === 'project' ? 'project' : 'work history'} bullet to upgrade:
                  </span>
                  <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                    {result.available_resume_bullets.map((bObj, idx) => (
                      <div
                        key={idx}
                        onClick={() => handleSelectDifferentBullet(bObj)}
                        className={`p-2 rounded-lg cursor-pointer transition-colors text-xs font-mono border ${
                          existingBullet === bObj.bullet
                            ? 'bg-indigo-950/60 border-indigo-500 text-indigo-200'
                            : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                        }`}
                      >
                        <span className="text-[10px] font-sans font-bold text-slate-500 uppercase block">
                          {bObj.section}
                        </span>
                        • {bObj.bullet}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Header for recommended replacements */}
            <div className="flex items-center justify-between pt-1">
              <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                <Sparkles size={14} className="text-cyan-400" />
                <span>Recommended Replacement Candidates (Choose 1)</span>
              </h4>
              <span className="text-[11px] text-slate-400 font-medium">
                Framework: What + How + Result
              </span>
            </div>

            {/* Alternatives Grid */}
            <div className="space-y-3">
              {result.alternatives.map((alt, idx) => (
                <div
                  key={idx}
                  className="glass-card p-4 space-y-2.5 border-slate-800 hover:border-slate-700 transition-all text-xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-indigo-300 tracking-wide uppercase text-[11px]">
                      {alt.variant_name}
                    </span>
                    <div className="flex items-center gap-2">
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

                      {onMarkSkillsAdded && (
                        <button
                          onClick={handleMarkAdded}
                          className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-semibold transition-all ${
                            addedConfirmed
                              ? 'bg-blue-600 text-white shadow-md shadow-blue-500/30 font-bold'
                              : 'bg-blue-950/70 border border-blue-500/50 text-blue-300 hover:bg-blue-900/60 hover:text-white'
                          }`}
                          title="Marks these skills as adopted into your resume, moving them to Matched Technical Skills (Blue) and recalculating your match score!"
                        >
                          <CheckCircle2 size={12} className={addedConfirmed ? 'text-white' : 'text-blue-400'} />
                          <span>{addedConfirmed ? '✓ Added to Resume' : 'Mark Skills Added'}</span>
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Bullet text */}
                  <p className="font-mono text-xs text-emerald-300 bg-slate-950/80 p-3 rounded-lg border border-emerald-500/30 leading-relaxed">
                    • {alt.bullet}
                  </p>

                  {/* What / How / Result Breakdown */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-2 pt-1 text-[11px] text-slate-400">
                    <div className="bg-slate-900/60 p-2 rounded border border-slate-800/60">
                      <strong className="text-indigo-300 block mb-0.5">WHAT (Keyword):</strong>
                      <span className="text-slate-200">{alt.what}</span>
                    </div>
                    <div className="bg-slate-900/60 p-2 rounded border border-slate-800/60">
                      <strong className="text-indigo-300 block mb-0.5">HOW (Action):</strong>
                      <span className="text-slate-200">{alt.how}</span>
                    </div>
                    <div className="bg-slate-900/60 p-2 rounded border border-slate-800/60">
                      <strong className="text-indigo-300 block mb-0.5">RESULT / REASON:</strong>
                      <span className="text-slate-200">{alt.result_or_reason}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Added Confirmation & Recalculate Callout */}
            {addedConfirmed ? (
              <div className="p-3.5 bg-blue-950/70 border border-blue-500/50 rounded-xl flex items-center justify-between gap-3 text-xs animate-fade-in shadow-lg shadow-blue-950/50">
                <div className="flex items-center gap-2.5 text-blue-200">
                  <CheckCircle2 size={18} className="text-blue-400 shrink-0" />
                  <div>
                    <span className="font-bold text-white">Skills Adopted! </span>
                    <span>
                      <strong className="text-cyan-300 font-mono">{keywords.join(', ')}</strong> moved to <strong>Matched Technical Skills (Blue)</strong> in your comparison card. Your projected ATS score has been boosted!
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              onMarkSkillsAdded && (
                <div className="p-3.5 bg-slate-900/90 border border-blue-500/30 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                  <div className="flex items-center gap-2 text-slate-300">
                    <Sparkles size={16} className="text-blue-400 shrink-0" />
                    <span>
                      Put this bullet into your resume? Move these skills to Matched (Blue) to re-evaluate your match score.
                    </span>
                  </div>
                  <button
                    onClick={handleMarkAdded}
                    className="btn-primary bg-blue-600 hover:bg-blue-500 border-blue-400 text-xs py-1.5 px-3 flex items-center gap-1.5 self-start sm:self-auto shrink-0 shadow-md shadow-blue-600/30 font-semibold"
                  >
                    <CheckCircle2 size={13} />
                    <span>Move {keywords.length} Skill{keywords.length > 1 ? 's' : ''} to Matched (Blue)</span>
                  </button>
                </div>
              )
            )}
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
