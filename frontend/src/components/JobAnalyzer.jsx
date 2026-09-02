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
} from 'lucide-react';
import SkillsMatrix from './SkillsMatrix';
import ATSKeywordBank from './ATSKeywordBank';
import { analyzeJob, addApplication } from '../api/client';

export default function JobAnalyzer({
  onJobAnalyzed,
  currentJob,
  onOpenBulletOptimizer,
  onOpenCoverLetter,
  onApplicationSaved,
}) {
  const [mode, setMode] = useState('url'); // 'url' or 'text'
  const [urlInput, setUrlInput] = useState('');
  const [textInput, setTextInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [saveSuccess, setSaveSuccess] = useState(false);

  const handleAnalyze = async (e) => {
    e?.preventDefault();
    setError('');
    setSaveSuccess(false);

    if (mode === 'url' && !urlInput.trim()) {
      setError('Please enter a valid job URL.');
      return;
    }
    if (mode === 'text' && !textInput.trim()) {
      setError('Please paste job description text.');
      return;
    }

    setLoading(true);
    try {
      const data = await analyzeJob({
        url: mode === 'url' ? urlInput.trim() : null,
        text: mode === 'text' ? textInput.trim() : null,
      });
      if (onJobAnalyzed) {
        onJobAnalyzed(data);
      }
    } catch (err) {
      setError(err.message || 'Error parsing job description.');
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
      {/* Search / Input Box */}
      <div className="glass-panel p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Sparkles className="text-indigo-400" size={20} />
            <h2 className="text-lg font-bold text-slate-100">Job Ingestion & Analyzer</h2>
          </div>
          <div className="flex bg-slate-900/80 p-1 rounded-lg border border-slate-800 text-xs">
            <button
              onClick={() => setMode('url')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium transition-all ${
                mode === 'url'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Link2 size={13} />
              Job URL
            </button>
            <button
              onClick={() => setMode('text')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium transition-all ${
                mode === 'text'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <FileText size={13} />
              Paste Text
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-rose-500/15 border border-rose-500/30 rounded-lg flex items-center gap-2 text-rose-300 text-xs">
            <AlertCircle size={15} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleAnalyze}>
          {mode === 'url' ? (
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="relative flex-1">
                <input
                  type="url"
                  placeholder="Paste job link (LinkedIn, Greenhouse, Lever, Indeed, etc.)..."
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  className="input-field pl-10"
                  disabled={loading}
                />
                <Link2 className="absolute left-3.5 top-3 text-slate-500" size={16} />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="btn-primary whitespace-nowrap"
              >
                {loading ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    <span>Extracting & Analyzing...</span>
                  </>
                ) : (
                  <>
                    <Sparkles size={16} />
                    <span>Fetch & Analyze</span>
                  </>
                )}
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              <textarea
                placeholder="Paste the full job description text here..."
                rows={5}
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                className="input-field resize-y font-sans"
                disabled={loading}
              />
              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={loading}
                  className="btn-primary"
                >
                  {loading ? (
                    <>
                      <Loader2 size={16} className="animate-spin" />
                      <span>Analyzing...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles size={16} />
                      <span>Analyze Text</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </form>
      </div>

      {/* Analysis Result Display */}
      {currentJob && (
        <div className="space-y-6 animate-fade-in">
          {/* Header Card */}
          <div className="glass-panel p-6 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-6 border-b border-slate-800/80">
              <div>
                <div className="flex items-center gap-2 text-indigo-400 font-semibold text-xs tracking-wider uppercase mb-1">
                  <Building2 size={14} />
                  <span>{currentJob.company}</span>
                </div>
                <h1 className="text-2xl font-bold text-white tracking-tight">
                  {currentJob.title}
                </h1>

                <div className="flex flex-wrap items-center gap-3 mt-3 text-xs text-slate-300">
                  <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-800/90 border border-slate-700/60">
                    <MapPin size={13} className="text-slate-400" />
                    <span>{currentJob.location}</span>
                    {currentJob.work_mode && (
                      <span className="text-indigo-300 font-medium">({currentJob.work_mode})</span>
                    )}
                  </div>

                  {currentJob.salary_range && currentJob.salary_range !== 'Not specified' && (
                    <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-950/40 border border-emerald-800/50 text-emerald-300 font-medium">
                      <DollarSign size={13} />
                      <span>{currentJob.salary_range}</span>
                    </div>
                  )}

                  {currentJob.experience_level && currentJob.experience_level !== 'Not specified' && (
                    <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-purple-950/40 border border-purple-800/50 text-purple-300 font-medium">
                      <Briefcase size={13} />
                      <span>{currentJob.experience_level}</span>
                    </div>
                  )}

                  {currentJob.is_new_grad_role && (
                    <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-cyan-950/50 border border-cyan-700/60 text-cyan-300 font-medium">
                      <GraduationCap size={14} className="text-cyan-400" />
                      <span>🎓 New Grad Role (4mo prior / 6mo post rule)</span>
                    </div>
                  )}

                  {currentJob.source_url && currentJob.source_url !== 'manual_paste' && (
                    <a
                      href={currentJob.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-indigo-400 hover:text-indigo-300 transition-colors"
                    >
                      <ExternalLink size={13} />
                      <span>Original Posting</span>
                    </a>
                  )}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center gap-2 pt-2 lg:pt-0">
                <button
                  onClick={() => onOpenBulletOptimizer && onOpenBulletOptimizer(currentJob.required_skills[0] || 'Target Skill')}
                  className="btn-secondary text-xs"
                >
                  <Wand2 size={14} className="text-indigo-400" />
                  <span>Optimize Bullet</span>
                </button>

                <button
                  onClick={() => onOpenCoverLetter && onOpenCoverLetter()}
                  className="btn-secondary text-xs"
                >
                  <Mail size={14} className="text-cyan-400" />
                  <span>Cover Letter</span>
                </button>

                <button
                  onClick={() => handleSaveToTracker('Wishlist')}
                  className="btn-primary text-xs"
                >
                  <PlusCircle size={14} />
                  <span>{saveSuccess ? 'Saved to Tracker! ✓' : 'Save to Tracker'}</span>
                </button>
              </div>
            </div>

            {/* Role Summary */}
            {currentJob.summary && (
              <div className="mt-4 pt-4 text-xs text-slate-300 leading-relaxed bg-slate-900/50 p-3.5 rounded-lg border border-slate-800/60">
                <span className="font-semibold text-indigo-300">Executive Summary: </span>
                {currentJob.summary}
              </div>
            )}
          </div>

          {/* Grid: Skills Matrix + ATS Keyword Bank */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 glass-panel p-6">
              <h3 className="text-base font-bold text-slate-100 mb-4 flex items-center gap-2">
                <Briefcase size={18} className="text-indigo-400" />
                <span>Skills & Qualifications Matrix</span>
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
