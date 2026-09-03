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
  Lock,
  User as UserIcon,
} from 'lucide-react';
import JobAnalyzer from './components/JobAnalyzer';
import ResumeFitRanker from './components/ResumeFitRanker';
import ResumeLibrary from './components/ResumeLibrary';
import ApplicationsTracker from './components/ApplicationsTracker';
import BulletOptimizerModal from './components/BulletOptimizerModal';
import CoverLetterModal from './components/CoverLetterModal';
import SettingsModal from './components/SettingsModal';
import OfflineSwitchModal from './components/OfflineSwitchModal';
import AuthModal from './components/AuthModal';
import UserNav from './components/UserNav';
import {
  getResumes,
  getApplications,
  downloadExcelReport,
  getCurrentUser,
  getMe,
  getToken,
} from './api/client';

export default function App() {
  const [currentUser, setCurrentUser] = useState(getCurrentUser());
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [authMode, setAuthMode] = useState('login');

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
    if (!getToken()) {
      setResumes([]);
      setApplications([]);
      return;
    }
    try {
      const me = await getMe().catch(() => null);
      if (me) setCurrentUser(me);

      const [resumesData, appsData] = await Promise.all([
        getResumes().catch(() => []),
        getApplications().catch(() => []),
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
    const handleUnauthorized = () => {
      setCurrentUser(null);
      setResumes([]);
      setApplications([]);
      setAuthMode('login');
      setIsAuthOpen(true);
    };

    const handleLogout = () => {
      setCurrentUser(null);
      setResumes([]);
      setApplications([]);
      setCurrentJob(null);
    };

    window.addEventListener('jh_auth_unauthorized', handleUnauthorized);
    window.addEventListener('jh_auth_logout', handleLogout);

    loadInitialData();

    return () => {
      window.removeEventListener('jh_auth_unauthorized', handleUnauthorized);
      window.removeEventListener('jh_auth_logout', handleLogout);
    };
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

  const appliedCount = applications.filter((a) => a.status === 'Applied').length;
  const interviewCount = applications.filter((a) => a.status === 'Interviewing').length;
  const offerCount = applications.filter((a) => a.status === 'Offered').length;
  const totalCount = applications.length;

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      {/* Top Navbar */}
      <header className="sticky top-0 z-40 bg-zinc-950/80 backdrop-blur-xl border-b border-white/[0.08]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
          {/* Brand Logo */}
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => setActiveTab('analyzer')}>
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-purple-600 p-[1px] shadow-lg shadow-indigo-500/20">
              <div className="w-full h-full bg-zinc-950 rounded-[15px] flex items-center justify-center">
                <Briefcase size={20} className="text-indigo-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-base tracking-tight text-white">JobHelperGuru</span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 tracking-wide uppercase">
                  Multi-User Cloud
                </span>
              </div>
              <p className="text-[11px] text-zinc-400 hidden sm:block">
                AI Job Tailoring, Best-Fit Resumes & Personal Pipeline
              </p>
            </div>
          </div>

          {/* Desktop Navigation Tabs */}
          <nav className="hidden md:flex items-center gap-1.5 p-1 bg-white/[0.04] border border-white/[0.08] rounded-2xl">
            <button
              onClick={() => setActiveTab('analyzer')}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-medium transition-all ${
                activeTab === 'analyzer'
                  ? 'bg-white/[0.1] text-white shadow-sm font-semibold'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              <Sparkles size={13} className={activeTab === 'analyzer' ? 'text-indigo-400' : ''} />
              <span>Job Analyzer</span>
            </button>

            <button
              onClick={() => {
                if (!currentUser) {
                  setAuthMode('login');
                  setIsAuthOpen(true);
                }
                setActiveTab('resumes');
              }}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-medium transition-all ${
                activeTab === 'resumes'
                  ? 'bg-white/[0.1] text-white shadow-sm font-semibold'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              <FileText size={13} />
              <span>Resumes ({resumes.length})</span>
            </button>

            <button
              onClick={() => {
                if (!currentUser) {
                  setAuthMode('login');
                  setIsAuthOpen(true);
                }
                setActiveTab('tracker');
              }}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-medium transition-all ${
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
            <button
              onClick={() => {
                if (!currentUser) {
                  setAuthMode('login');
                  setIsAuthOpen(true);
                  return;
                }
                downloadExcelReport().catch((err) => alert(err.message));
              }}
              className="btn-excel text-xs hidden sm:flex items-center gap-1.5"
              title="Download full styled Excel spreadsheet tracking your jobs"
            >
              <FileSpreadsheet size={14} />
              <span>Export .xlsx</span>
            </button>

            <button
              onClick={() => {
                if (!currentUser) {
                  setAuthMode('login');
                  setIsAuthOpen(true);
                  return;
                }
                setIsSettingsOpen(true);
              }}
              className="p-2 rounded-xl bg-white/[0.03] hover:bg-white/[0.08] border border-white/[0.08] hover:border-white/[0.2] text-zinc-400 hover:text-white transition-all shadow-sm"
              title="AI & API Settings"
            >
              <SettingsIcon size={17} />
            </button>

            <UserNav
              user={currentUser}
              onOpenAuth={(mode) => {
                setAuthMode(mode);
                setIsAuthOpen(true);
              }}
              onOpenSettings={() => setIsSettingsOpen(true)}
              applicationsCount={applications.length}
              resumesCount={resumes.length}
            />
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
            onClick={() => {
              if (!currentUser) {
                setAuthMode('login');
                setIsAuthOpen(true);
              }
              setActiveTab('resumes');
            }}
            className={`px-3 py-1 rounded-full font-medium whitespace-nowrap ${
              activeTab === 'resumes' ? 'bg-indigo-600 text-white' : 'text-zinc-400'
            }`}
          >
            Resumes ({resumes.length})
          </button>
          <button
            onClick={() => {
              if (!currentUser) {
                setAuthMode('login');
                setIsAuthOpen(true);
              }
              setActiveTab('tracker');
            }}
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
              onOpenBulletOptimizer={(kw) => {
                if (!currentUser) {
                  setAuthMode('login');
                  setIsAuthOpen(true);
                  return;
                }
                handleOpenOptimizer(kw);
              }}
              onOpenCoverLetter={() => {
                if (!currentUser) {
                  setAuthMode('login');
                  setIsAuthOpen(true);
                  return;
                }
                setIsCoverLetterOpen(true);
              }}
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
                  if (!currentUser) {
                    setAuthMode('login');
                    setIsAuthOpen(true);
                    return;
                  }
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
          currentUser ? (
            <ResumeLibrary
              onResumesUpdated={(updated) => setResumes(updated)}
            />
          ) : (
            <div className="max-w-xl mx-auto my-12 p-8 rounded-3xl bg-white/[0.02] border border-white/10 text-center backdrop-blur-xl">
              <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 mx-auto flex items-center justify-center mb-4">
                <Lock size={28} />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">Personal Resume Library</h3>
              <p className="text-xs text-zinc-400 mb-6 leading-relaxed">
                Sign in to upload, store, and manage your private resumes with encrypted Cloudflare R2 object storage.
              </p>
              <button
                onClick={() => {
                  setAuthMode('login');
                  setIsAuthOpen(true);
                }}
                className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-xs font-semibold shadow-lg shadow-indigo-500/20 transition-all"
              >
                Sign In to View Resumes
              </button>
            </div>
          )
        )}

        {activeTab === 'tracker' && (
          currentUser ? (
            <ApplicationsTracker refreshTrigger={refreshTrackerTrigger} />
          ) : (
            <div className="max-w-xl mx-auto my-12 p-8 rounded-3xl bg-white/[0.02] border border-white/10 text-center backdrop-blur-xl">
              <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 mx-auto flex items-center justify-center mb-4">
                <TableIcon size={28} />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">Personal Job Pipeline</h3>
              <p className="text-xs text-zinc-400 mb-6 leading-relaxed">
                Sign in to view and manage your private job application pipeline, interview stages, and follow-up deadlines.
              </p>
              <button
                onClick={() => {
                  setAuthMode('login');
                  setIsAuthOpen(true);
                }}
                className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-xs font-semibold shadow-lg shadow-indigo-500/20 transition-all"
              >
                Sign In to View Pipeline
              </button>
            </div>
          )
        )}
      </main>

      {/* Modals */}
      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        initialMode={authMode}
        onSuccess={(user) => {
          setCurrentUser(user);
          loadInitialData();
        }}
      />

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
