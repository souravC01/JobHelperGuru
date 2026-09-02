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
      <header className="sticky top-0 z-40 bg-slate-950/80 backdrop-blur-xl border-b border-slate-800/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Brand */}
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => setActiveTab('analyzer')}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 flex items-center justify-center text-white shadow-lg shadow-indigo-500/25">
              <Briefcase size={20} />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-extrabold text-base tracking-tight text-white">
                  JobHelper<span className="text-indigo-400">Guru</span>
                </span>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-indigo-500/20 text-indigo-300 font-mono border border-indigo-500/30">
                  v1.0
                </span>
              </div>
              <p className="text-[10px] text-slate-400">AI Job Parsing • Skills • ATS Optimizer • Excel Tracker</p>
            </div>
          </div>

          {/* Nav Tabs */}
          <nav className="hidden md:flex items-center gap-1 bg-slate-900/90 p-1 rounded-xl border border-slate-800/90 text-xs">
            <button
              onClick={() => setActiveTab('analyzer')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg font-semibold transition-all ${
                activeTab === 'analyzer'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Sparkles size={14} />
              <span>Job Analyzer</span>
            </button>

            <button
              onClick={() => setActiveTab('resumes')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg font-semibold transition-all ${
                activeTab === 'resumes'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <FileText size={14} />
              <span>My Resumes ({resumes.length})</span>
            </button>

            <button
              onClick={() => setActiveTab('tracker')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg font-semibold transition-all ${
                activeTab === 'tracker'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <TableIcon size={14} />
              <span>Application Tracker ({totalCount})</span>
            </button>
          </nav>

          {/* Right Header Actions */}
          <div className="flex items-center gap-2">
            <a
              href={getExcelExportUrl()}
              download="job_tracker.xlsx"
              className="btn-excel text-xs hidden sm:flex"
              title="Download full styled Excel spreadsheet tracking your jobs"
            >
              <FileSpreadsheet size={15} />
              <span>Excel Export</span>
            </a>

            <button
              onClick={() => setIsSettingsOpen(true)}
              className="p-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-white transition-colors"
              title="AI & API Settings"
            >
              <SettingsIcon size={18} />
            </button>
          </div>
        </div>

        {/* Mobile Tab bar */}
        <div className="flex md:hidden px-4 pb-2 pt-1 gap-1 border-t border-slate-800/60 overflow-x-auto text-xs">
          <button
            onClick={() => setActiveTab('analyzer')}
            className={`px-3 py-1 rounded-md font-medium whitespace-nowrap ${
              activeTab === 'analyzer' ? 'bg-indigo-600 text-white' : 'text-slate-400'
            }`}
          >
            Analyzer
          </button>
          <button
            onClick={() => setActiveTab('resumes')}
            className={`px-3 py-1 rounded-md font-medium whitespace-nowrap ${
              activeTab === 'resumes' ? 'bg-indigo-600 text-white' : 'text-slate-400'
            }`}
          >
            Resumes ({resumes.length})
          </button>
          <button
            onClick={() => setActiveTab('tracker')}
            className={`px-3 py-1 rounded-md font-medium whitespace-nowrap ${
              activeTab === 'tracker' ? 'bg-indigo-600 text-white' : 'text-slate-400'
            }`}
          >
            Tracker ({totalCount})
          </button>
        </div>
      </header>

      {/* Pipeline Quick Stats Bar */}
      <section className="bg-slate-900/40 border-b border-slate-800/50 py-2.5 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4 text-xs">
          <div className="flex items-center gap-6 flex-wrap">
            <div className="flex items-center gap-2 text-slate-400">
              <Layers size={14} className="text-slate-500" />
              <span>Tracked: <strong className="text-white">{totalCount}</strong></span>
            </div>
            <div className="flex items-center gap-2 text-slate-400">
              <div className="w-2 h-2 rounded-full bg-blue-400" />
              <span>Applied: <strong className="text-blue-300">{appliedCount}</strong></span>
            </div>
            <div className="flex items-center gap-2 text-slate-400">
              <div className="w-2 h-2 rounded-full bg-amber-400" />
              <span>Interviewing: <strong className="text-amber-300">{interviewCount}</strong></span>
            </div>
            <div className="flex items-center gap-2 text-slate-400">
              <div className="w-2 h-2 rounded-full bg-emerald-400" />
              <span>Offers: <strong className="text-emerald-300">{offerCount}</strong></span>
            </div>
          </div>

          <div className="text-[11px] text-slate-500 flex items-center gap-1.5">
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
              onJobAnalyzed={handleJobAnalyzed}
              onOpenBulletOptimizer={(kw) => handleOpenOptimizer(kw)}
              onOpenCoverLetter={() => setIsCoverLetterOpen(true)}
              onApplicationSaved={handleApplicationSaved}
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
      />

      <CoverLetterModal
        isOpen={isCoverLetterOpen}
        onClose={() => setIsCoverLetterOpen(false)}
        currentJob={currentJob}
        selectedResume={selectedResumeForJob}
      />

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-6 text-center text-xs text-slate-500">
        <p>JobHelperGuru — Built for smarter, tailored job applications & ATS optimization.</p>
      </footer>
    </div>
  );
}
