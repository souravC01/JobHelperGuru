import React, { useState } from 'react';
import {
  Link2,
  FileText,
  Sparkles,
  Building2,
  MapPin,
  DollarSign,
  Briefcase,
  ExternalLink,
  PlusCircle,
  Wand2,
  Mail,
  Loader2,
  AlertCircle,
  GraduationCap,
  ChevronDown,
  ChevronUp,
  Check,
  Clock,
} from 'lucide-react';
import SkillsMatrix from './SkillsMatrix';
import ATSKeywordBank from './ATSKeywordBank';
import { analyzeJob, addApplication } from '../api/client';

export default function JobAnalyzer({
  onJobAnalyzed,
  currentJob,
  applications = [],
  onOpenBulletOptimizer,
  onOpenCoverLetter,
  onApplicationSaved,
  onAiError,
}) {
  const [mode, setMode] = useState('url'); // 'url' or 'text'
  const [urlInput, setUrlInput] = useState('');
  const [textInput, setTextInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [showPasteText, setShowPasteText] = useState(false);

  const isAlreadyInPipeline = Boolean(
    currentJob &&
    applications &&
    applications.some((app) => {
      const jobUrl = (currentJob.source_url || urlInput || '').trim().replace(/\/+$/, '');
      const appUrl = (app.url || '').trim().replace(/\/+$/, '');
      const matchUrl = jobUrl && jobUrl !== 'manual_paste' && appUrl && appUrl === jobUrl;
      const matchCompanyRole = (
        app.company && currentJob.company &&
        app.company.trim().toLowerCase() === currentJob.company.trim().toLowerCase() &&
        app.role && currentJob.title &&
        app.role.trim().toLowerCase() === currentJob.title.trim().toLowerCase()
      );
      return matchUrl || matchCompanyRole;
    })
  );

  const handleAnalyze = async (e) => {
    e?.preventDefault();
    setError('');
    setSaveSuccess(false);

    const activeMode = showPasteText ? 'text' : mode;

    if (activeMode === 'url' && !urlInput.trim()) {
      setError('Please enter a valid job URL.');
      return;
    }
    if (activeMode === 'text' && !textInput.trim()) {
      setError('Please paste the job description text.');
      return;
    }

    setLoading(true);
    try {
      const data = await analyzeJob({
        url: activeMode === 'url' ? urlInput.trim() : null,
        text: activeMode === 'text' ? textInput.trim() : null,
      });
      if (onJobAnalyzed) {
        onJobAnalyzed(data);
      }
    } catch (err) {
      setError(err.message || 'Error parsing job description.');
      if (onAiError && (err.canSwitchOffline || err.status === 502)) {
        onAiError(err, () => handleAnalyze());
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSaveToTracker = async (defaultStatus = 'Wishlist') => {
    if (!currentJob) return;
    try {
      const appData = {
        company: currentJob.company || 'Unknown Company',
        role: currentJob.title || 'Open Position',
        status: defaultStatus,
        location: currentJob.location || 'Unknown',
        salary: currentJob.salary_range || 'Not specified',
        url: currentJob.source_url || urlInput || '',
        required_skills: currentJob.required_skills || [],
        ats_keywords: currentJob.ats_keywords || [],
        notes: currentJob.summary || '',
      };
      await addApplication(appData);
      setSaveSuccess(true);
      if (onApplicationSaved) onApplicationSaved();
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      setError('Failed to save to application tracker.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Floating Raycast-Style Command Bar */}
      <div className="max-w-4xl mx-auto w-full">
        <form onSubmit={handleAnalyze} className="glass-command-bar p-2 pl-4 flex items-center gap-3">
          <div className="text-indigo-400 shrink-0">
            <Sparkles size={18} className="animate-pulse" />
          </div>

          <input
            type="url"
            placeholder="Paste LinkedIn, Workday, Dayforce, or Greenhouse job URL..."
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            disabled={loading}
            className="bg-transparent border-none outline-none text-sm text-white placeholder:text-zinc-500 font-mono tracking-tight flex-1"
          />

          <button
            type="submit"
            disabled={loading}
            className="btn-gradient whitespace-nowrap text-xs px-4 py-2 flex items-center gap-1.5 shrink-0"
          >
            {loading ? (
              <>
                <Loader2 size={14} className="animate-spin" />
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <span>⚡ Analyze Role</span>
              </>
            )}
          </button>
        </form>

        {/* Toggle for manual paste */}
        <div className="flex items-center justify-between px-3 mt-2 text-xs text-zinc-500">
          <span>Supported: LinkedIn, Greenhouse, Workday, Dayforce, Lever, Indeed</span>
          <button
            type="button"
            onClick={() => setShowPasteText(!showPasteText)}
            className="text-zinc-400 hover:text-indigo-400 flex items-center gap-1 transition-colors font-medium"
          >
            <FileText size={12} />
            <span>{showPasteText ? 'Hide Text Area' : 'Or Paste Text Directly'}</span>
            {showPasteText ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          </button>
        </div>

        {/* Expandable Text Paste Drawer */}
        {showPasteText && (
          <div className="glass-panel p-4 mt-3 space-y-3 animate-fade-in border-white/10">
            <textarea
              placeholder="Paste full job description text here..."
              rows={5}
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              disabled={loading}
              className="input-field text-xs font-mono resize-y"
            />
            <div className="flex justify-end">
              <button
                type="button"
                onClick={handleAnalyze}
                disabled={loading}
                className="btn-primary text-xs"
              >
                {loading ? 'Analyzing Text...' : 'Analyze Raw Text'}
              </button>
            </div>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="mt-3 p-3 bg-rose-500/10 border border-rose-500/25 rounded-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2.5 text-rose-300 text-xs animate-fade-in">
            <div className="flex items-center gap-2">
              <AlertCircle size={15} className="shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
            {mode === 'url' && (
              <button
                type="button"
                onClick={() => {
                  setMode('text');
                  setError('');
                }}
                className="shrink-0 px-3 py-1 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 font-medium text-[11px] border border-rose-500/30 transition-colors"
              >
                Switch to Paste Job Text &rarr;
              </button>
            )}
          </div>
        )}
      </div>

      {/* Analysis Result Display */}
      {currentJob && (
        <div className="space-y-6 animate-fade-in">
          {/* Header Card */}
          <div className="glass-panel p-6 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-80 h-80 bg-indigo-500/[0.07] rounded-full blur-3xl pointer-events-none" />

            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-6 border-b border-white/[0.06]">
              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <span className="badge-pill bg-indigo-500/10 text-indigo-300 border border-indigo-500/25 font-mono text-[11px]">
                    <Building2 size={12} />
                    <span>{currentJob.company || 'Unknown Company'}</span>
                  </span>
                  {currentJob.work_mode && (
                    <span className="badge-pill bg-white/[0.04] text-zinc-300 border border-white/10 text-[11px]">
                      {currentJob.work_mode}
                    </span>
                  )}
                </div>

                <h1 className="text-2xl font-bold text-white tracking-tight">
                  {currentJob.title || 'Open Position'}
                </h1>

                <div className="flex flex-wrap items-center gap-2.5 pt-1 text-xs text-zinc-300">
                  <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/[0.03] border border-white/[0.08]">
                    <MapPin size={13} className="text-zinc-400" />
                    <span>{currentJob.location || 'Unknown'}</span>
                  </div>

                  {currentJob.salary_range && currentJob.salary_range !== 'Not specified' && (
                    <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 font-mono font-medium">
                      <DollarSign size={13} />
                      <span>{currentJob.salary_range}</span>
                    </div>
                  )}

                  {/* Required Professional Work Experience Badge */}
                  <div
                    className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg font-medium border text-xs transition-colors ${
                      (currentJob.experience_required === 'New Grad' || currentJob.is_new_grad_role)
                        ? 'bg-cyan-500/10 border-cyan-500/25 text-cyan-300'
                        : currentJob.experience_required && currentJob.experience_required !== 'Not specified'
                        ? 'bg-amber-500/10 border-amber-500/25 text-amber-300 font-mono'
                        : 'bg-white/[0.03] border-white/[0.08] text-zinc-400'
                    }`}
                    title="Required Professional Work Experience"
                  >
                    <Clock
                      size={13}
                      className={
                        (currentJob.experience_required === 'New Grad' || currentJob.is_new_grad_role)
                          ? 'text-cyan-400'
                          : currentJob.experience_required && currentJob.experience_required !== 'Not specified'
                          ? 'text-amber-400'
                          : 'text-zinc-500'
                      }
                    />
                    <span>
                      Exp: {currentJob.experience_required || currentJob.experience_level || 'Not specified'}
                    </span>
                  </div>

                  {currentJob.experience_level && currentJob.experience_level !== 'Not specified' && currentJob.experience_level !== currentJob.experience_required && (
                    <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-violet-500/10 border border-violet-500/20 text-violet-300 font-medium">
                      <Briefcase size={13} />
                      <span>{currentJob.experience_level}</span>
                    </div>
                  )}

                  {currentJob.is_new_grad_role && (
                    <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 font-medium">
                      <GraduationCap size={13} className="text-cyan-400" />
                      <span>New Grad Eligibility</span>
                    </div>
                  )}

                  {currentJob.source_url && currentJob.source_url !== 'manual_paste' && (
                    <a
                      href={currentJob.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-indigo-400 hover:text-indigo-300 transition-colors ml-1 font-medium"
                    >
                      <ExternalLink size={12} />
                      <span>Original Link</span>
                    </a>
                  )}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center gap-2 pt-2 lg:pt-0">
                <button
                  onClick={() => onOpenBulletOptimizer && onOpenBulletOptimizer(currentJob.required_skills?.[0] || 'Target Skill')}
                  className="btn-secondary text-xs"
                >
                  <Wand2 size={13} className="text-indigo-400" />
                  <span>Bullet Optimizer</span>
                </button>

                <button
                  onClick={() => onOpenCoverLetter && onOpenCoverLetter()}
                  className="btn-secondary text-xs"
                >
                  <Mail size={13} className="text-cyan-400" />
                  <span>Cover Letter</span>
                </button>

                <button
                  onClick={() => handleSaveToTracker('Wishlist')}
                  className={`text-xs flex items-center gap-1.5 transition-all ${
                    isAlreadyInPipeline
                      ? 'btn-secondary text-emerald-300 border-emerald-500/30 hover:bg-emerald-500/10'
                      : 'btn-gradient'
                  }`}
                  title={isAlreadyInPipeline ? 'Job is already in your application pipeline. Click to refresh details.' : 'Save to your application pipeline'}
                >
                  {saveSuccess ? (
                    <>
                      <Check size={13} className="text-emerald-400 stroke-[3]" />
                      <span>{isAlreadyInPipeline ? 'Updated in Pipeline! ✓' : 'Saved to Pipeline! ✓'}</span>
                    </>
                  ) : isAlreadyInPipeline ? (
                    <>
                      <Check size={13} className="text-emerald-400 stroke-[2.5]" />
                      <span>In Pipeline (Update)</span>
                    </>
                  ) : (
                    <>
                      <PlusCircle size={13} />
                      <span>Add to Pipeline</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Role Executive Summary */}
            {currentJob.summary && (
              <div className="mt-4 pt-3 text-xs text-zinc-300 leading-relaxed bg-white/[0.02] p-3.5 rounded-xl border border-white/[0.06]">
                <span className="font-semibold text-indigo-300">Executive Summary: </span>
                {currentJob.summary}
              </div>
            )}
          </div>

          {/* Grid: Skills Matrix + ATS Keyword Bank */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 glass-panel p-6">
              <h3 className="text-sm font-bold text-zinc-100 mb-4 flex items-center gap-2 tracking-tight">
                <Briefcase size={16} className="text-indigo-400" />
                <span>Skills & Requirements Matrix</span>
              </h3>
              <SkillsMatrix
                requiredSkills={currentJob.required_skills}
                preferredSkills={currentJob.preferred_skills}
                techStack={currentJob.tech_stack}
                softSkills={currentJob.soft_skills}
                onSelectKeyword={(kw) => onOpenBulletOptimizer && onOpenBulletOptimizer(kw)}
              />
            </div>

            <div className="lg:col-span-1">
              <ATSKeywordBank
                keywords={currentJob.ats_keywords}
                onSelectKeyword={(kw) => onOpenBulletOptimizer && onOpenBulletOptimizer(kw)}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
