import React, { useState } from 'react';
import {
  Link2,
  FileText,
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
      {/* Corporate Ingestion Card */}
      <div className="max-w-4xl mx-auto w-full">
        <form onSubmit={handleAnalyze} className="card-corporate p-3 sm:p-4 bg-white border border-[#e0e0e0] rounded-lg shadow-none flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          <div className="text-[#0a66c2] pl-2 hidden sm:block shrink-0">
            <Link2 size={18} />
          </div>

          <input
            type="url"
            placeholder="Paste LinkedIn, Greenhouse, Workday, Dayforce, or Lever job URL..."
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            disabled={loading}
            className="input-corporate flex-1 text-sm text-[#000000] placeholder:text-[#666666] h-11"
          />

          <button
            type="submit"
            disabled={loading}
            className="btn-primary-corporate whitespace-nowrap h-11 px-6 shrink-0"
          >
            {loading ? (
              <>
                <Loader2 size={14} className="animate-spin" />
                <span>Analyzing...</span>
              </>
            ) : (
              <span>Analyze Job</span>
            )}
          </button>
        </form>

        {/* Toggle for manual paste */}
        <div className="flex items-center justify-between px-3 mt-2 text-xs text-[#666666]">
          <span>Supported: LinkedIn, Greenhouse, Workday, Dayforce, Lever, Indeed</span>
          <button
            type="button"
            onClick={() => setShowPasteText(!showPasteText)}
            className="text-[#0a66c2] hover:underline flex items-center gap-1 font-semibold transition-colors"
          >
            <FileText size={12} />
            <span>{showPasteText ? 'Hide Text Area' : 'Or Paste Job Text Directly'}</span>
            {showPasteText ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          </button>
        </div>

        {/* Expandable Text Paste Drawer */}
        {showPasteText && (
          <div className="card-corporate p-4 mt-3 space-y-3 bg-white border border-[#e0e0e0] rounded-lg animate-fade-in">
            <textarea
              placeholder="Paste full job description text here..."
              rows={6}
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              disabled={loading}
              className="input-corporate w-full text-xs font-mono resize-y"
            />
            <div className="flex justify-end">
              <button
                type="button"
                onClick={handleAnalyze}
                disabled={loading}
                className="btn-primary-corporate text-xs"
              >
                {loading ? 'Analyzing Text...' : 'Analyze Raw Text'}
              </button>
            </div>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="mt-3 p-3 bg-[#b24020]/10 border border-[#b24020]/25 rounded-lg flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2.5 text-[#b24020] text-xs animate-fade-in">
            <div className="flex items-center gap-2">
              <AlertCircle size={15} className="shrink-0 text-[#b24020]" />
              <span>{error}</span>
            </div>
            {mode === 'url' && (
              <button
                type="button"
                onClick={() => {
                  setMode('text');
                  setShowPasteText(true);
                  setError('');
                }}
                className="btn-secondary-corporate text-[11px] py-1 px-3 border-[#b24020] text-[#b24020] hover:bg-[#b24020]/10 shrink-0"
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
          <div className="card-corporate p-6 bg-white border border-[#e0e0e0] rounded-lg">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-6 border-b border-[#e0e0e0]">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="badge-corporate bg-[#f3f6f8] text-[#000000] border border-[#e0e0e0] font-semibold text-xs">
                    <Building2 size={13} className="text-[#0a66c2]" />
                    <span>{currentJob.company || 'Unknown Company'}</span>
                  </span>
                  {currentJob.work_mode && (
                    <span className="badge-corporate bg-[#f3f6f8] text-[#666666] border border-[#e0e0e0] text-xs">
                      {currentJob.work_mode}
                    </span>
                  )}
                </div>

                <h1 className="text-2xl font-bold text-[#000000] tracking-tight">
                  {currentJob.title || 'Open Position'}
                </h1>

                <div className="flex flex-wrap items-center gap-2 pt-1 text-xs text-[#000000]">
                  <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#f3f6f8] border border-[#e0e0e0]">
                    <MapPin size={13} className="text-[#666666]" />
                    <span>{currentJob.location || 'Unknown'}</span>
                  </div>

                  {currentJob.salary_range && currentJob.salary_range !== 'Not specified' && (
                    <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#057642]/10 border border-[#057642]/20 text-[#057642] font-mono font-semibold">
                      <DollarSign size={13} />
                      <span>{currentJob.salary_range}</span>
                    </div>
                  )}

                  {/* Required Professional Work Experience Badge */}
                  <div
                    className={`flex items-center gap-1.5 px-3 py-1 rounded-full font-medium border text-xs transition-colors ${
                      (currentJob.experience_required === 'New Grad' || currentJob.is_new_grad_role)
                        ? 'bg-[#0a66c2]/10 border-[#0a66c2]/25 text-[#0a66c2]'
                        : currentJob.experience_required && currentJob.experience_required !== 'Not specified'
                        ? 'bg-[#b24020]/10 border-[#b24020]/25 text-[#b24020] font-mono font-semibold'
                        : 'bg-[#f3f6f8] border-[#e0e0e0] text-[#666666]'
                    }`}
                    title="Required Professional Work Experience"
                  >
                    <Clock
                      size={13}
                      className={
                        (currentJob.experience_required === 'New Grad' || currentJob.is_new_grad_role)
                          ? 'text-[#0a66c2]'
                          : currentJob.experience_required && currentJob.experience_required !== 'Not specified'
                          ? 'text-[#b24020]'
                          : 'text-[#666666]'
                      }
                    />
                    <span>
                      Exp: {currentJob.experience_required || currentJob.experience_level || 'Not specified'}
                    </span>
                  </div>

                  {currentJob.experience_level && currentJob.experience_level !== 'Not specified' && currentJob.experience_level !== currentJob.experience_required && (
                    <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#004e99]/10 border border-[#004e99]/20 text-[#004e99] font-medium">
                      <Briefcase size={13} />
                      <span>{currentJob.experience_level}</span>
                    </div>
                  )}

                  {currentJob.is_new_grad_role && (
                    <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#0a66c2]/10 border border-[#0a66c2]/20 text-[#0a66c2] font-medium">
                      <GraduationCap size={13} className="text-[#0a66c2]" />
                      <span>New Grad Eligibility</span>
                    </div>
                  )}

                  {currentJob.source_url && currentJob.source_url !== 'manual_paste' && (
                    <a
                      href={currentJob.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-[#0a66c2] hover:underline transition-colors ml-1 font-semibold"
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
                  className="btn-secondary-corporate text-xs"
                >
                  <Wand2 size={13} />
                  <span>Bullet Optimizer</span>
                </button>

                <button
                  onClick={() => onOpenCoverLetter && onOpenCoverLetter()}
                  className="btn-secondary-corporate text-xs"
                >
                  <Mail size={13} />
                  <span>Cover Letter</span>
                </button>

                <button
                  onClick={() => handleSaveToTracker('Wishlist')}
                  className={`text-xs flex items-center gap-1.5 transition-all ${
                    isAlreadyInPipeline
                      ? 'btn-secondary-corporate text-[#057642] border-[#057642] hover:bg-[#057642]/10'
                      : 'btn-primary-corporate'
                  }`}
                  title={isAlreadyInPipeline ? 'Job is already in your application pipeline. Click to refresh details.' : 'Save to your application pipeline'}
                >
                  {saveSuccess ? (
                    <>
                      <Check size={13} className="stroke-[3]" />
                      <span>{isAlreadyInPipeline ? 'Updated in Pipeline!' : 'Saved to Pipeline!'}</span>
                    </>
                  ) : isAlreadyInPipeline ? (
                    <>
                      <Check size={13} className="stroke-[2.5]" />
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
              <div className="mt-4 pt-3 text-xs text-[#000000] leading-relaxed bg-[#f3f6f8] p-3.5 rounded-lg border border-[#e0e0e0]">
                <span className="font-bold text-[#0a66c2]">Executive Summary: </span>
                {currentJob.summary}
              </div>
            )}
          </div>

          {/* Grid: Skills Matrix + ATS Keyword Bank */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 card-corporate p-6 bg-white border border-[#e0e0e0] rounded-lg">
              <h3 className="text-sm font-bold text-[#000000] mb-4 flex items-center gap-2 tracking-tight">
                <Briefcase size={16} className="text-[#0a66c2]" />
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
