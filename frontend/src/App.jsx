import React, { useState, useEffect } from 'react';
import {
  Briefcase,
  Sparkles,
  FileText,
  Table as TableIcon,
  Settings as SettingsIcon,
  FileSpreadsheet,
  Layers,
  TrendingUp,
  Lock,
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
import ThemeToggle from './components/ThemeToggle';
import {
  getResumes,
  getApplications,
  downloadExcelReport,
  getCurrentUser,
  getMe,
  getToken,
  getSettings,
} from './api/client';

export default function App() {
  const [currentUser, setCurrentUser] = useState(getCurrentUser());
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [authMode, setAuthMode] = useState('login');

  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('jobhelperguru_theme') || 'light';
  });

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('jobhelperguru_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

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
  const [isOnboardingSettings, setIsOnboardingSettings] = useState(false);
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
    <div className="min-h-screen bg-[#f3f6f8] text-[#000000] flex flex-col font-sans selection:bg-[#0a66c2] selection:text-white">
      {/* Top Corporate Navbar */}
      <header className="sticky top-0 z-40 bg-white border-b border-[#e0e0e0]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
          {/* Brand Logo */}
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => setActiveTab('analyzer')}>
            <div className="w-9 h-9 rounded-md bg-[#0a66c2] flex items-center justify-center shadow-sm">
              <Briefcase size={20} className="text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-base tracking-tight text-[#000000]">JobHelperGuru</span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#f3f6f8] text-[#0a66c2] border border-[#e0e0e0] tracking-wide uppercase">
                  Cloud
                </span>
              </div>
              <p className="text-[11px] text-[#666666] hidden sm:block">
                AI Job Tailoring, Best-Fit Resumes & Personal Pipeline
              </p>
            </div>
          </div>

          {/* Desktop Navigation Tabs */}
          <nav className="hidden md:flex items-center gap-1 h-16">
            <button
              onClick={() => setActiveTab('analyzer')}
              className={`flex items-center gap-2 px-4 h-full text-xs transition-all border-b-2 ${
                activeTab === 'analyzer'
                  ? 'border-[#0a66c2] text-[#0a66c2] font-semibold'
                  : 'border-transparent text-[#666666] hover:text-[#000000] font-medium'
              }`}
            >
              <Sparkles size={14} className={activeTab === 'analyzer' ? 'text-[#0a66c2]' : 'text-[#666666]'} />
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
              className={`flex items-center gap-2 px-4 h-full text-xs transition-all border-b-2 ${
                activeTab === 'resumes'
                  ? 'border-[#0a66c2] text-[#0a66c2] font-semibold'
                  : 'border-transparent text-[#666666] hover:text-[#000000] font-medium'
              }`}
            >
              <FileText size={14} className={activeTab === 'resumes' ? 'text-[#0a66c2]' : 'text-[#666666]'} />
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
              className={`flex items-center gap-2 px-4 h-full text-xs transition-all border-b-2 ${
                activeTab === 'tracker'
                  ? 'border-[#0a66c2] text-[#0a66c2] font-semibold'
                  : 'border-transparent text-[#666666] hover:text-[#000000] font-medium'
              }`}
            >
              <TableIcon size={14} className={activeTab === 'tracker' ? 'text-[#0a66c2]' : 'text-[#666666]'} />
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

            <ThemeToggle theme={theme} onToggle={toggleTheme} />

            <button
              onClick={() => {
                if (!currentUser) {
                  setAuthMode('login');
                  setIsAuthOpen(true);
                  return;
                }
                setIsOnboardingSettings(false);
                setIsSettingsOpen(true);
              }}
              className="p-2 rounded-full bg-white hover:bg-[#f3f6f8] border border-[#e0e0e0] hover:border-[#c1c6d4] text-[#666666] hover:text-[#000000] transition-all"
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
              onOpenSettings={() => {
                setIsOnboardingSettings(false);
                setIsSettingsOpen(true);
              }}
              applicationsCount={applications.length}
              resumesCount={resumes.length}
            />
          </div>
        </div>

        {/* Mobile Tab bar */}
        <div className="flex md:hidden px-4 pb-2 pt-1 gap-1 border-t border-[#e0e0e0] bg-white overflow-x-auto text-xs">
          <button
            onClick={() => setActiveTab('analyzer')}
            className={`px-3 py-1.5 rounded-full font-medium whitespace-nowrap transition-colors ${
              activeTab === 'analyzer' ? 'bg-[#0a66c2] text-white' : 'text-[#666666] hover:text-[#000000]'
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
            className={`px-3 py-1.5 rounded-full font-medium whitespace-nowrap transition-colors ${
              activeTab === 'resumes' ? 'bg-[#0a66c2] text-white' : 'text-[#666666] hover:text-[#000000]'
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
            className={`px-3 py-1.5 rounded-full font-medium whitespace-nowrap transition-colors ${
              activeTab === 'tracker' ? 'bg-[#0a66c2] text-white' : 'text-[#666666] hover:text-[#000000]'
            }`}
          >
            Pipeline ({totalCount})
          </button>
        </div>
      </header>

      {/* Pipeline Quick Stats Bar */}
      <section className="bg-white border-b border-[#e0e0e0] py-2.5 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4 text-xs">
          <div className="flex items-center gap-6 flex-wrap">
            <div className="flex items-center gap-2 text-[#666666]">
              <Layers size={14} className="text-[#666666]" />
              <span>Tracked: <strong className="text-[#000000] font-mono">{totalCount}</strong></span>
            </div>
            <div className="flex items-center gap-2 text-[#666666]">
              <div className="w-2 h-2 rounded-full bg-[#0a66c2]" />
              <span>Applied: <strong className="text-[#0a66c2] font-mono">{appliedCount}</strong></span>
            </div>
            <div className="flex items-center gap-2 text-[#666666]">
              <div className="w-2 h-2 rounded-full bg-[#004e99]" />
              <span>Interviewing: <strong className="text-[#004e99] font-mono">{interviewCount}</strong></span>
            </div>
            <div className="flex items-center gap-2 text-[#666666]">
              <div className="w-2 h-2 rounded-full bg-[#057642]" />
              <span>Offers: <strong className="text-[#057642] font-mono">{offerCount}</strong></span>
            </div>
          </div>

          <div className="text-[11px] text-[#666666] flex items-center gap-1.5">
            <TrendingUp size={12} className="text-[#0a66c2]" />
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
            <div className="max-w-xl mx-auto my-12 p-8 rounded-lg bg-white border border-[#e0e0e0] text-center">
              <div className="w-14 h-14 rounded-full bg-[#0a66c2]/10 border border-[#0a66c2]/20 text-[#0a66c2] mx-auto flex items-center justify-center mb-4">
                <Lock size={24} />
              </div>
              <h3 className="text-xl font-bold text-[#000000] mb-2">Personal Resume Library</h3>
              <p className="text-xs text-[#666666] mb-6 leading-relaxed">
                Sign in to upload, store, and manage your private resumes with encrypted Cloudflare R2 object storage.
              </p>
              <button
                onClick={() => {
                  setAuthMode('login');
                  setIsAuthOpen(true);
                }}
                className="btn-primary-corporate"
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
            <div className="max-w-xl mx-auto my-12 p-8 rounded-lg bg-white border border-[#e0e0e0] text-center">
              <div className="w-14 h-14 rounded-full bg-[#0a66c2]/10 border border-[#0a66c2]/20 text-[#0a66c2] mx-auto flex items-center justify-center mb-4">
                <TableIcon size={24} />
              </div>
              <h3 className="text-xl font-bold text-[#000000] mb-2">Personal Job Pipeline</h3>
              <p className="text-xs text-[#666666] mb-6 leading-relaxed">
                Sign in to view and manage your private job application pipeline, interview stages, and follow-up deadlines.
              </p>
              <button
                onClick={() => {
                  setAuthMode('login');
                  setIsAuthOpen(true);
                }}
                className="btn-primary-corporate"
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
        onSuccess={async (user, isNewUser = false) => {
          setCurrentUser(user);
          await loadInitialData();
          try {
            const settings = await getSettings();
            if (isNewUser || (!settings?.api_key?.trim() && !settings?.use_offline_mode)) {
              setIsOnboardingSettings(true);
              setIsSettingsOpen(true);
            }
          } catch (e) {
            if (isNewUser) {
              setIsOnboardingSettings(true);
              setIsSettingsOpen(true);
            }
          }
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
        onClose={() => {
          setIsSettingsOpen(false);
          setIsOnboardingSettings(false);
        }}
        currentUser={currentUser}
        isOnboarding={isOnboardingSettings}
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

      {/* Corporate Footer (Zero Em-Dash) */}
      <footer className="border-t border-[#e0e0e0] bg-white py-6 text-center text-xs text-[#666666]">
        <p>JobHelperGuru - Built for smarter, tailored job applications & ATS optimization.</p>
      </footer>
    </div>
  );
}
