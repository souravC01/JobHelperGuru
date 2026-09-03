import React, { useState, useEffect } from 'react';
import {
  Wand2,
  Copy,
  Check,
  Sparkles,
  Loader2,
  Briefcase,
  FolderGit2,
  X,
  Plus,
  AlertTriangle,
  CheckCircle2,
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
  onAiError = null,
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
      if (onAiError && (err.canSwitchOffline || err.status === 502)) {
        onAiError(err, () => handleGenerate(null, bulletToUse));
      }
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
    <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
      <div className="card-corporate bg-white border border-[#e0e0e0] w-full max-w-4xl my-8 p-6 rounded-xl space-y-5 animate-fade-in shadow-xl max-h-[92vh] overflow-y-auto text-[#000000]">
        {/* Modal Header */}
        <div className="flex items-center justify-between pb-3 border-b border-[#e0e0e0]">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-full bg-[#0a66c2]/10 text-[#0a66c2]">
              <Wand2 size={18} />
            </div>
            <div>
              <h3 className="text-base font-bold text-[#000000] tracking-tight">
                BulletSkill 2.0 Resume Bullet Optimizer
              </h3>
              <p className="text-xs text-[#666666]">
                Incorporate target skills into <strong>{sectionType === 'project' ? 'Project' : 'Work History'}</strong> bullet points
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-[#666666] hover:text-[#000000] p-1 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Target Skills Pill Bank */}
        <div className="space-y-2 p-4 bg-[#f3f6f8] border border-[#e0e0e0] rounded-lg">
          <div className="flex items-center justify-between">
            <label className="text-xs font-bold text-[#000000]">
              Target Skills to Incorporate ({keywords.length})
            </label>
            <span className="text-[11px] text-[#666666]">
              Targeting: <strong className="text-[#000000]">{targetJobTitle}</strong>
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-2 pt-1">
            {keywords.map((kw, i) => (
              <span
                key={i}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#b24020]/10 text-[#b24020] border border-[#b24020]/25"
              >
                <span>{kw}</span>
                <button
                  type="button"
                  onClick={() => handleRemoveSkill(kw)}
                  className="hover:text-[#b24020] text-[#666666] transition-colors"
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
                className="input-corporate px-2.5 py-1 text-xs w-28 focus:w-36 transition-all"
              />
              {newSkillInput && (
                <button
                  type="button"
                  onClick={handleAddSkill}
                  className="p-1 rounded-full bg-[#0a66c2] text-white text-xs hover:bg-[#004e99]"
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
            <span className="text-xs font-semibold text-[#000000]">Resume Section:</span>
            <div className="flex bg-[#f3f6f8] p-1 rounded-full border border-[#e0e0e0] text-xs">
              <button
                type="button"
                onClick={() => {
                  setSectionType('project');
                  setResult(null);
                }}
                className={`flex items-center gap-1.5 py-1 px-3.5 rounded-full font-semibold transition-all ${
                  sectionType === 'project'
                    ? 'bg-[#0a66c2] text-white shadow-sm'
                    : 'text-[#666666] hover:text-[#000000]'
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
                className={`flex items-center gap-1.5 py-1 px-3.5 rounded-full font-semibold transition-all ${
                  sectionType === 'work_history'
                    ? 'bg-[#0a66c2] text-white shadow-sm'
                    : 'text-[#666666] hover:text-[#000000]'
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
            className="btn-primary-corporate text-xs self-end sm:self-auto"
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
          <div className="p-3 bg-[#b24020]/10 border border-[#b24020]/25 rounded-lg text-[#b24020] text-xs flex items-center gap-2">
            <AlertTriangle size={15} />
            <span>{error}</span>
          </div>
        )}

        {/* Results Container */}
        {result && (
          <div className="space-y-4 pt-2 border-t border-[#e0e0e0]">
            {/* Target Role & Current Bullet Card */}
            <div className="p-4 rounded-lg bg-[#f3f6f8] border border-[#e0e0e0] space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded-full bg-[#0a66c2]/10 text-[#0a66c2]">
                    {sectionType === 'project' ? <FolderGit2 size={16} /> : <Briefcase size={16} />}
                  </div>
                  <div>
                    <h4 className="font-bold text-xs uppercase tracking-wide text-[#0a66c2]">
                      {sectionType === 'project' ? 'Target Project in Resume' : 'Target Role / Employment in Resume'}
                    </h4>
                    <span className="text-xs font-semibold text-[#000000]">
                      {result.target_project_name || (sectionType === 'project' ? 'Primary Technical Project' : 'Professional Work Experience')}
                    </span>
                  </div>
                </div>

                {result.available_resume_bullets && result.available_resume_bullets.length > 1 && (
                  <button
                    onClick={() => setShowBulletPicker(!showBulletPicker)}
                    className="text-[11px] text-[#0a66c2] hover:underline font-semibold"
                  >
                    {showBulletPicker ? 'Hide Bullets' : `Change Target ${sectionType === 'project' ? 'Project' : 'Job'} Bullet`}
                  </button>
                )}
              </div>

              {/* Strategic Rationale */}
              {result.replacement_rationale && (
                <p className="text-xs text-[#000000] leading-relaxed bg-white p-3 rounded-lg border border-[#e0e0e0]">
                  <strong className="text-[#0a66c2]">Strategy: </strong>
                  {result.replacement_rationale}
                </p>
              )}

              {/* Current Bullet in Resume to Replace */}
              {result.original_bullet_to_replace && (
                <div className="space-y-1.5 pt-1">
                  <div className="flex items-center gap-1.5 text-[11px] font-bold text-[#b24020] uppercase tracking-wider">
                    <span>
                      {sectionType === 'project'
                        ? 'Current Project Bullet in Resume to Replace:'
                        : 'Current Work History Bullet in Resume to Replace:'}
                    </span>
                  </div>
                  <div className="font-mono text-xs text-[#b24020] bg-[#b24020]/5 p-2.5 rounded border border-[#b24020]/25 leading-relaxed">
                    &bull; {result.original_bullet_to_replace}
                  </div>
                </div>
              )}

              {/* Bullet Picker Dropdown */}
              {showBulletPicker && result.available_resume_bullets && (
                <div className="p-3 bg-white rounded-lg border border-[#e0e0e0] space-y-2 mt-2">
                  <span className="text-xs font-semibold text-[#000000] block">
                    Choose which existing {sectionType === 'project' ? 'project' : 'work history'} bullet to upgrade:
                  </span>
                  <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                    {result.available_resume_bullets.map((bObj, idx) => (
                      <div
                        key={idx}
                        onClick={() => handleSelectDifferentBullet(bObj)}
                        className={`p-2 rounded cursor-pointer transition-colors text-xs font-mono border ${
                          existingBullet === bObj.bullet
                            ? 'bg-[#0a66c2]/10 border-[#0a66c2] text-[#0a66c2] font-semibold'
                            : 'bg-[#f3f6f8] border-[#e0e0e0] text-[#666666] hover:bg-[#eef3f8] hover:text-[#000000]'
                        }`}
                      >
                        <span className="text-[10px] font-sans font-bold text-[#666666] uppercase block">
                          {bObj.section}
                        </span>
                        &bull; {bObj.bullet}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Header for recommended replacements */}
            <div className="flex items-center justify-between pt-1">
              <h4 className="text-xs font-bold text-[#000000] uppercase tracking-wider flex items-center gap-1.5">
                <Sparkles size={14} className="text-[#0a66c2]" />
                <span>Recommended Replacement Candidates (Choose 1)</span>
              </h4>
              <span className="text-[11px] text-[#666666] font-medium">
                Framework: What + How + Result
              </span>
            </div>

            {/* Alternatives Grid */}
            <div className="space-y-3">
              {result.alternatives.map((alt, idx) => (
                <div
                  key={idx}
                  className="card-corporate p-4 space-y-2.5 bg-white border border-[#e0e0e0] hover:border-[#c1c6d4] transition-all text-xs rounded-lg shadow-none"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-[#0a66c2] tracking-wide uppercase text-[11px]">
                      {alt.variant_name}
                    </span>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleCopy(alt.bullet, idx)}
                        className="btn-secondary-corporate text-xs py-1 px-3"
                      >
                        {copiedIndex === idx ? (
                          <>
                            <Check size={12} className="text-[#057642]" />
                            <span className="text-[#057642] font-semibold">Copied!</span>
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
                          className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold transition-all ${
                            addedConfirmed
                              ? 'bg-[#057642] text-white'
                              : 'btn-primary-corporate text-xs py-1 px-3'
                          }`}
                          title="Marks these skills as adopted into your resume, moving them to Matched Technical Skills and recalculating your match score!"
                        >
                          <CheckCircle2 size={12} className="text-white" />
                          <span>{addedConfirmed ? 'Added to Resume' : 'Mark Skills Added'}</span>
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Bullet text */}
                  <p className="font-mono text-xs text-[#000000] bg-[#f3f6f8] p-3 rounded-lg border border-[#e0e0e0] leading-relaxed">
                    &bull; {alt.bullet}
                  </p>

                  {/* What / How / Result Breakdown */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-2 pt-1 text-[11px]">
                    <div className="bg-white p-2.5 rounded border border-[#e0e0e0]">
                      <strong className="text-[#0a66c2] block mb-0.5 font-bold">WHAT (Keyword):</strong>
                      <span className="text-[#000000]">{alt.what}</span>
                    </div>
                    <div className="bg-white p-2.5 rounded border border-[#e0e0e0]">
                      <strong className="text-[#0a66c2] block mb-0.5 font-bold">HOW (Action):</strong>
                      <span className="text-[#000000]">{alt.how}</span>
                    </div>
                    <div className="bg-white p-2.5 rounded border border-[#e0e0e0]">
                      <strong className="text-[#0a66c2] block mb-0.5 font-bold">RESULT / REASON:</strong>
                      <span className="text-[#000000]">{alt.result_or_reason}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Added Confirmation & Recalculate Callout */}
            {addedConfirmed ? (
              <div className="p-3.5 bg-[#057642]/10 border border-[#057642]/25 rounded-lg flex items-center justify-between gap-3 text-xs animate-fade-in text-[#057642]">
                <div className="flex items-center gap-2.5">
                  <CheckCircle2 size={18} className="text-[#057642] shrink-0" />
                  <div>
                    <span className="font-bold">Skills Adopted! </span>
                    <span>
                      <strong className="font-mono">{keywords.join(', ')}</strong> moved to <strong>Matched Technical Skills</strong> in your comparison card. Your projected ATS score has been boosted!
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              onMarkSkillsAdded && (
                <div className="p-3.5 bg-[#f3f6f8] border border-[#e0e0e0] rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                  <div className="flex items-center gap-2 text-[#000000]">
                    <Sparkles size={16} className="text-[#0a66c2] shrink-0" />
                    <span>
                      Put this bullet into your resume? Move these skills to Matched to re-evaluate your match score.
                    </span>
                  </div>
                  <button
                    onClick={handleMarkAdded}
                    className="btn-primary-corporate text-xs py-1.5 px-3 flex items-center gap-1.5 self-start sm:self-auto shrink-0"
                  >
                    <CheckCircle2 size={13} />
                    <span>Move {keywords.length} Skill{keywords.length > 1 ? 's' : ''} to Matched</span>
                  </button>
                </div>
              )
            )}
          </div>
        )}

        <div className="flex justify-end pt-3 border-t border-[#e0e0e0]">
          <button onClick={onClose} className="btn-secondary-corporate text-xs py-1 px-4">
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
