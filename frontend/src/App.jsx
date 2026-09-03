import React, { useState, useEffect } from 'react';
import {
  Briefcase,
  Sparkles,
  FileText,
  Table as TableIcon,
  Settings as SettingsIcon,
  FileSpreadsheet,
  Layers,
  CheckCircle2,
  TrendingUp,
} from 'lucide-react';
import JobAnalyzer from './components/JobAnalyzer';
import ResumeFitRanker from './components/ResumeFitRanker';
import ResumeLibrary from './components/ResumeLibrary';
import ApplicationsTracker from './components/ApplicationsTracker';
import BulletOptimizerModal from './components/BulletOptimizerModal';
import CoverLetterModal from './components/CoverLetterModal';
import SettingsModal from './components/SettingsModal';
import OfflineSwitchModal from './components/OfflineSwitchModal';
import { getResumes, getApplications, getExcelExportUrl } from './api/client';

export default function App() {
  const [activeTab, setActiveTab] = useState('analyzer'); // 'analyzer', 'resumes', 'tracker'
  const [currentJob, setCurrentJob] = useState(null);
  const [resumes, setResumes] = useState([]);
  const [applications, setApplications] = useState([]);
  const [refreshTrackerTrigger, setRefreshTrackerTrigger] = useState(0);

  // Modals state
  const [isOptimizerOpen, setIsOptimizerOpen] = useState(false);
  const [optimizerKeywords, setOptimizerKeywords] = useState([]);
  const [optimizerSectionType, setOptimizerSectionType] = useState('work_history');
  const [isCoverLetterOpen, setIsCoverLetterOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [selectedResumeForJob, setSelectedResumeForJob] = useState(null);
  // Potentially added skills: { [resumeId]: string[] }
  const [adoptedSkillsMap, setAdoptedSkillsMap] = useState({});

  // Offline / AI Error Popup State
  const [aiErrorState, setAiErrorState] = useState({
    isOpen: false,
    errorMsg: '',
    modelName: '',
    retryAction: null,
  });

  const handleAiError = (err, retryFn = null) => {
    setAiErrorState({
      isOpen: true,
      errorMsg: err.message || 'The configured AI model failed to respond.',
      modelName: err.modelName || '',
      retryAction: retryFn,
    });
  };

  const handleAdoptSkills = (skills, resumeId = null) => {
    const targetId = resumeId || selectedResumeForJob?.id;
    if (!targetId || !skills || skills.length === 0) return;
    const skillsList = Array.isArray(skills) ? skills : [skills];
    setAdoptedSkillsMap((prev) => {
      const existing = prev[targetId] || [];
      const combined = Array.from(new Set([...existing, ...skillsList]));
      return { ...prev, [targetId]: combined };
    });
  };

  const handleRemoveAdoptedSkill = (skill, resumeId) => {
    setAdoptedSkillsMap((prev) => {
      const existing = prev[resumeId] || [];
      return { ...prev, [resumeId]: existing.filter((s) => s !== skill) };
    });
  };

  const loadInitialData = async () => {
    try {
      const [resumesData, appsData] = await Promise.all([
        getResumes(),
        getApplications(),
      ]);
      setResumes(resumesData);
      setApplications(appsData);
      if (resumesData.length > 0) {
        setSelectedResumeForJob(resumesData[0]);
      }
    } catch (err) {
      console.error('Failed to load initial data:', err);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  const handleJobAnalyzed = (data) => {
    setCurrentJob(data);
  };

  const handleOpenOptimizer = (keywordsArg = '', targetResume = null, sectionType = 'work_history') => {
    let kwList = [];
    if (Array.isArray(keywordsArg)) {
      kwList = keywordsArg;
    } else if (typeof keywordsArg === 'string' && keywordsArg.trim()) {
      kwList = [keywordsArg.trim()];
    } else {
      kwList = [currentJob?.required_skills?.[0] || 'Target Qualification'];
    }
    setOptimizerKeywords(kwList);
    setOptimizerSectionType(sectionType || 'work_history');
    if (targetResume) {
      setSelectedResumeForJob(targetResume);
    }
    setIsOptimizerOpen(true);
  };

  const handleApplicationSaved = async () => {
    setRefreshTrackerTrigger((prev) => prev + 1);
    const updatedApps = await getApplications().catch(() => []);
    setApplications(updatedApps);
  };

  // Stats
  const totalCount = applications.length;
  const appliedCount = applications.filter((a) => a.status === 'Applied').length;
  const interviewCount = applications.filter((a) => a.status === 'Interviewing').length;
  const offerCount = applications.filter((a) => a.status === 'Offered').length;

  return (
    <div className="min-h-screen flex flex-col text-slate-100">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-40 bg-[#09090b]/80 backdrop-blur-xl border-b border-white/[0.06]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Brand */}
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => setActiveTab('analyzer')}>
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 to-violet-600 flex items-center justify-center text-white shadow-lg shadow-indigo-500/20 ring-1 ring-white/20">
              <Sparkles size={18} className="animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-base tracking-tight text-white">
                  JobHelper<span className="text-indigo-400">Guru</span>
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 font-mono border border-indigo-500/20 font-semibold">
                  v2.0
                </span>
              </div>
              <p className="text-[11px] text-zinc-400 tracking-tight">AI & Offline Resume Optimizer</p>
            </div>
          </div>

          {/* Centered Pill Nav Tabs */}
          <nav className="hidden md:flex items-center gap-1 bg-white/[0.03] p-1 rounded-full border border-white/[0.08] text-xs">
            <button
              onClick={() => setActiveTab('analyzer')}
              className={`flex items-center gap-2 px-4 py-1.5 rounded-full font-medium transition-all ${
                activeTab === 'analyzer'
                  ? 'bg-white/[0.1] text-white shadow-sm font-semibold'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              <Briefcase size={13} />
              <span>Job Analyzer</span>
            </button>

            <button
              onClick={() => setActiveTab('resumes')}
              className={`flex items-center gap-2 px-4 py-1.5 rounded-full font-medium transition-all ${
                activeTab === 'resumes'
                  ? 'bg-white/[0.1] text-white shadow-sm font-semibold'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              <FileText size={13} />
              <span>Resume Vault ({resumes.length})</span>
            </button>

            <button
              onClick={() => setActiveTab('tracker')}
              className={`flex items-center gap-2 px-4 py-1.5 rounded-full font-medium transition-all ${
                activeTab === 'tracker'
                  ? 'bg-white/[0.1] text-white shadow-sm font-semibold'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              <TableIcon size={13} />
              <span>Application Pipeline ({totalCount})</span>
            </button>
          </nav>

          {/* Right Header Actions */}
          <div className="flex items-center gap-2.5">
            <a
              href={getExcelExportUrl()}
              download="job_tracker.xlsx"
              className="btn-excel text-xs hidden sm:flex"
              title="Download full styled Excel spreadsheet tracking your jobs"
            >
              <FileSpreadsheet size={14} />
              <span>Export .xlsx</span>
            </a>

            <button
              onClick={() => setIsSettingsOpen(true)}
              className="p-2 rounded-xl bg-white/[0.03] hover:bg-white/[0.08] border border-white/[0.08] hover:border-white/[0.2] text-zinc-400 hover:text-white transition-all shadow-sm"
              title="AI & API Settings"
            >
              <SettingsIcon size={17} />
            </button>
          </div>
        </div>

        {/* Mobile Tab bar */}
        <div className="flex md:hidden px-4 pb-2 pt-1 gap-1 border-t border-white/[0.06] overflow-x-auto text-xs">
          <button
            onClick={() => setActiveTab('analyzer')}
            className={`px-3 py-1 rounded-full font-medium whitespace-nowrap ${
              activeTab === 'analyzer' ? 'bg-indigo-600 text-white' : 'text-zinc-400'
            }`}
          >
            Analyzer
          </button>
          <button
            onClick={() => setActiveTab('resumes')}
            className={`px-3 py-1 rounded-full font-medium whitespace-nowrap ${
              activeTab === 'resumes' ? 'bg-indigo-600 text-white' : 'text-zinc-400'
            }`}
          >
            Resumes ({resumes.length})
          </button>
          <button
            onClick={() => setActiveTab('tracker')}
            className={`px-3 py-1 rounded-full font-medium whitespace-nowrap ${
              activeTab === 'tracker' ? 'bg-indigo-600 text-white' : 'text-zinc-400'
            }`}
          >
            Pipeline ({totalCount})
          </button>
        </div>
      </header>

      {/* Pipeline Quick Stats Bar */}
      <section className="bg-white/[0.015] border-b border-white/[0.06] py-2.5 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4 text-xs">
          <div className="flex items-center gap-6 flex-wrap">
            <div className="flex items-center gap-2 text-zinc-400">
              <Layers size={13} className="text-zinc-500" />
              <span>Tracked: <strong className="text-white font-mono">{totalCount}</strong></span>
            </div>
            <div className="flex items-center gap-2 text-zinc-400">
              <div className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
              <span>Applied: <strong className="text-indigo-300 font-mono">{appliedCount}</strong></span>
            </div>
            <div className="flex items-center gap-2 text-zinc-400">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span>Interviewing: <strong className="text-emerald-300 font-mono">{interviewCount}</strong></span>
            </div>
            <div className="flex items-center gap-2 text-zinc-400">
              <div className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
              <span>Offers: <strong className="text-cyan-300 font-mono">{offerCount}</strong></span>
            </div>
          </div>

          <div className="text-[11px] text-zinc-400 flex items-center gap-1.5">
            <TrendingUp size={12} className="text-indigo-400" />
            <span>Targeting high-match roles accelerates interview conversion</span>
          </div>
        </div>
      </section>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full">
        {activeTab === 'analyzer' && (
          <div className="space-y-8">
            <JobAnalyzer
              currentJob={currentJob}
              applications={applications}
              onJobAnalyzed={handleJobAnalyzed}
              onOpenBulletOptimizer={(kw) => handleOpenOptimizer(kw)}
              onOpenCoverLetter={() => setIsCoverLetterOpen(true)}
              onApplicationSaved={handleApplicationSaved}
              onAiError={handleAiError}
            />

            {/* Resume Best Fit Ranker */}
            {currentJob && (
              <ResumeFitRanker
                currentJob={currentJob}
                resumes={resumes}
                adoptedSkillsMap={adoptedSkillsMap}
                onAdoptSkills={handleAdoptSkills}
                onRemoveAdoptedSkill={handleRemoveAdoptedSkill}
                onSelectKeywordForOptimization={(skills, rank, sectionType) => {
                  const matchingResume = resumes.find((r) => r.id === rank.resume_id);
                  handleOpenOptimizer(skills, matchingResume, sectionType);
                }}
                onBestResumeSelected={(best) => {
                  const matchingResume = resumes.find((r) => r.id === best.resume_id);
                  if (matchingResume) setSelectedResumeForJob(matchingResume);
                }}
                onAiError={handleAiError}
              />
            )}
          </div>
        )}

        {activeTab === 'resumes' && (
          <ResumeLibrary
            onResumesUpdated={(updated) => setResumes(updated)}
          />
        )}

        {activeTab === 'tracker' && (
          <ApplicationsTracker refreshTrigger={refreshTrackerTrigger} />
        )}
      </main>

      {/* Modals */}
      <BulletOptimizerModal
        isOpen={isOptimizerOpen}
        onClose={() => setIsOptimizerOpen(false)}
        initialKeywords={optimizerKeywords}
        initialSectionType={optimizerSectionType}
        targetJobTitle={currentJob?.title || 'Software Engineer'}
        selectedResume={selectedResumeForJob}
        onMarkSkillsAdded={(skills) => handleAdoptSkills(skills, selectedResumeForJob?.id)}
        onAiError={handleAiError}
      />

      <CoverLetterModal
        isOpen={isCoverLetterOpen}
        onClose={() => setIsCoverLetterOpen(false)}
        currentJob={currentJob}
        selectedResume={selectedResumeForJob}
        onAiError={handleAiError}
      />

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />

      <OfflineSwitchModal
        isOpen={aiErrorState.isOpen}
        onClose={() => setAiErrorState((prev) => ({ ...prev, isOpen: false }))}
        errorMessage={aiErrorState.errorMsg}
        modelName={aiErrorState.modelName}
        onSwitchToOffline={async () => {
          if (aiErrorState.retryAction) {
            await aiErrorState.retryAction();
          }
        }}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-6 text-center text-xs text-slate-500">
        <p>JobHelperGuru — Built for smarter, tailored job applications & ATS optimization.</p>
      </footer>
    </div>
  );
}
