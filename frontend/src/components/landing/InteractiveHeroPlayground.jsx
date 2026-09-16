import { useState } from 'react';
import {
  Wand2,
  Sparkles,
  CheckCircle2,
  TrendingUp,
  Target,
  FileSearch,
  Layers,
  ArrowRight,
  Clock,
  DollarSign,
  Building2,
  MapPin,
  GraduationCap,
  ShieldCheck,
  RefreshCw,
} from 'lucide-react';

export default function InteractiveHeroPlayground({ onTryLiveDemo }) {
  const [activeTab, setActiveTab] = useState('bulletcraft');

  // Tab 1: BulletCraft state
  const [isTransformed, setIsTransformed] = useState(false);

  // Tab 2: ATS Matcher state
  const [selectedRole, setSelectedRole] = useState('backend');
  const [hasAdoptedSkill, setHasAdoptedSkill] = useState(false);

  // Tab 3: Scraper state
  const [scraperUrl, setScraperUrl] = useState('https://boards.greenhouse.io/stripe/jobs/5829103');

  // Tab 4: Pipeline CRM state
  const [pipelineStatus, setPipelineStatus] = useState('Applied');

  return (
    <div className="card-corporate w-full max-w-5xl mx-auto rounded-lg border border-[#e0e0e0] dark:border-[#2b313c] bg-white dark:bg-[#1a1d24] shadow-none overflow-hidden transition-all">
      {/* Interactive Tabs Header */}
      <div
        className="flex border-b border-[#e0e0e0] dark:border-[#2b313c] bg-[#f3f6f8] dark:bg-[#0f1115] overflow-x-auto scrollbar-none"
        role="tablist"
      >
        <button
          role="tab"
          aria-selected={activeTab === 'bulletcraft'}
          onClick={() => setActiveTab('bulletcraft')}
          className={`flex items-center gap-2 px-5 py-3.5 text-xs font-semibold whitespace-nowrap border-b-2 transition-all ${
            activeTab === 'bulletcraft'
              ? 'border-[#0a66c2] text-[#0a66c2] dark:text-[#70b5f9] bg-white dark:bg-[#1a1d24]'
              : 'border-transparent text-[#666666] dark:text-[#9aa1b2] hover:text-[#000000] dark:hover:text-[#f3f6f8]'
          }`}
        >
          <Wand2 size={15} />
          <span>BulletCraft Framework</span>
        </button>

        <button
          role="tab"
          aria-selected={activeTab === 'ats'}
          onClick={() => setActiveTab('ats')}
          className={`flex items-center gap-2 px-5 py-3.5 text-xs font-semibold whitespace-nowrap border-b-2 transition-all ${
            activeTab === 'ats'
              ? 'border-[#0a66c2] text-[#0a66c2] dark:text-[#70b5f9] bg-white dark:bg-[#1a1d24]'
              : 'border-transparent text-[#666666] dark:text-[#9aa1b2] hover:text-[#000000] dark:hover:text-[#f3f6f8]'
          }`}
        >
          <Target size={15} />
          <span>ATS Fit Matcher</span>
        </button>

        <button
          role="tab"
          aria-selected={activeTab === 'scraper'}
          onClick={() => setActiveTab('scraper')}
          className={`flex items-center gap-2 px-5 py-3.5 text-xs font-semibold whitespace-nowrap border-b-2 transition-all ${
            activeTab === 'scraper'
              ? 'border-[#0a66c2] text-[#0a66c2] dark:text-[#70b5f9] bg-white dark:bg-[#1a1d24]'
              : 'border-transparent text-[#666666] dark:text-[#9aa1b2] hover:text-[#000000] dark:hover:text-[#f3f6f8]'
          }`}
        >
          <FileSearch size={15} />
          <span>Job Scraper</span>
        </button>

        <button
          role="tab"
          aria-selected={activeTab === 'crm'}
          onClick={() => setActiveTab('crm')}
          className={`flex items-center gap-2 px-5 py-3.5 text-xs font-semibold whitespace-nowrap border-b-2 transition-all ${
            activeTab === 'crm'
              ? 'border-[#0a66c2] text-[#0a66c2] dark:text-[#70b5f9] bg-white dark:bg-[#1a1d24]'
              : 'border-transparent text-[#666666] dark:text-[#9aa1b2] hover:text-[#000000] dark:hover:text-[#f3f6f8]'
          }`}
        >
          <Layers size={15} />
          <span>Pipeline CRM</span>
        </button>
      </div>

      {/* Tab Panels Body */}
      <div className="p-5 sm:p-7">
        {/* TAB 1: BulletCraft Framework */}
        {activeTab === 'bulletcraft' && (
          <div className="space-y-5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-[#0a66c2] dark:text-[#70b5f9]">
                  Accomplishment Engineering
                </span>
                <h3 className="text-base sm:text-lg font-bold text-[#000000] dark:text-[#f3f6f8]">
                  Transform Generic Bullets into Quantifiable Impact
                </h3>
              </div>
              <button
                onClick={() => setIsTransformed(!isTransformed)}
                className={isTransformed ? 'btn-secondary-corporate text-xs' : 'btn-primary-corporate text-xs'}
              >
                {isTransformed ? (
                  <>
                    <RefreshCw size={13} />
                    <span>Reset Example</span>
                  </>
                ) : (
                  <>
                    <Sparkles size={13} />
                    <span>Transform with BulletCraft</span>
                  </>
                )}
              </button>
            </div>

            {/* Before / After Comparison Display */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Weak Bullet Card */}
              <div className="p-4 rounded-lg border border-[#e0e0e0] dark:border-[#2b313c] bg-[#f3f6f8] dark:bg-[#0f1115]">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-bold text-[#b24020] bg-[#fdf2f2] dark:bg-[#b24020]/20 dark:text-[#ff8162] px-2 py-0.5 rounded">
                    Weak / Generic Bullet
                  </span>
                  <span className="text-[10px] text-[#666666] dark:text-[#9aa1b2]">ATS Conversion: Low</span>
                </div>
                <p className="text-xs sm:text-sm text-[#666666] dark:text-[#9aa1b2] leading-relaxed italic">
                  &ldquo;Responsible for writing backend APIs and optimizing database queries for our services.&rdquo;
                </p>
                <div className="mt-4 pt-3 border-t border-[#e0e0e0] dark:border-[#2b313c] text-[11px] text-[#666666] dark:text-[#9aa1b2] flex items-center gap-1.5">
                  <span className="text-[#b24020] font-bold">✕</span>
                  <span>Lacks quantifiable metrics, scale, and technical depth.</span>
                </div>
              </div>

              {/* BulletCraft Transformed Card */}
              <div
                className={`p-4 rounded-lg border transition-all ${
                  isTransformed
                    ? 'border-[#0a66c2] bg-[#f0f7fe] dark:bg-[#0a66c2]/10'
                    : 'border-[#e0e0e0] dark:border-[#2b313c] bg-white dark:bg-[#1a1d24] opacity-80'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-bold text-[#0a66c2] bg-[#0a66c2]/10 dark:text-[#70b5f9] px-2 py-0.5 rounded flex items-center gap-1">
                    <Sparkles size={11} />
                    <span>BulletCraft Formula</span>
                  </span>
                  <span className="text-[10px] text-[#057642] dark:text-[#45c586] font-semibold flex items-center gap-1">
                    <TrendingUp size={11} />
                    <span>ATS Conversion: High</span>
                  </span>
                </div>

                {isTransformed ? (
                  <div className="space-y-3 animate-fade-in">
                    <p className="text-xs sm:text-sm font-medium text-[#000000] dark:text-[#f3f6f8] leading-relaxed">
                      &ldquo;Engineered 14 resilient FastAPI microservices handling 2.4M daily requests, reducing p99 latency by 38% through Redis caching and PostgreSQL query indexing.&rdquo;
                    </p>

                    {/* Structural XYZ Tags */}
                    <div className="flex flex-wrap gap-1.5 pt-2">
                      <div className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-semibold bg-[#ecfdf5] dark:bg-[#057642]/20 text-[#057642] dark:text-[#45c586] border border-[#057642]/30">
                        <CheckCircle2 size={11} />
                        <span>Accomplished [X]: Action</span>
                      </div>
                      <div className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-semibold bg-[#f0f7fe] dark:bg-[#004e99]/20 text-[#0a66c2] dark:text-[#70b5f9] border border-[#0a66c2]/30">
                        <TrendingUp size={11} />
                        <span>Measured by [Y]: 2.4M reqs &amp; -38% latency</span>
                      </div>
                      <div className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-semibold bg-[#f3f6f8] dark:bg-[#2b313c]/30 text-[#000000] dark:text-[#f3f6f8] border border-[#e0e0e0] dark:border-[#2b313c]">
                        <ShieldCheck size={11} />
                        <span>Done by [Z]: Redis &amp; PostgreSQL</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="h-28 flex flex-col items-center justify-center text-center">
                    <p className="text-xs text-[#666666] dark:text-[#9aa1b2] mb-3">
                      Click &ldquo;Transform with BulletCraft&rdquo; to see the accomplishment formula in action.
                    </p>
                    <button
                      onClick={() => setIsTransformed(true)}
                      className="btn-primary-corporate text-xs"
                    >
                      Apply BulletCraft Formula
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: ATS Fit Matcher */}
        {activeTab === 'ats' && (
          <div className="space-y-5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-[#0a66c2] dark:text-[#70b5f9]">
                  Smart Multi-Resume Scoring
                </span>
                <h3 className="text-base sm:text-lg font-bold text-[#000000] dark:text-[#f3f6f8]">
                  Match Keywords &amp; Eliminate ATS Gaps
                </h3>
              </div>
              {/* Role Switcher */}
              <div className="inline-flex rounded-lg border border-[#e0e0e0] dark:border-[#2b313c] p-1 bg-[#f3f6f8] dark:bg-[#0f1115]">
                <button
                  onClick={() => {
                    setSelectedRole('backend');
                    setHasAdoptedSkill(false);
                  }}
                  className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                    selectedRole === 'backend'
                      ? 'bg-white dark:bg-[#1a1d24] text-[#0a66c2] dark:text-[#70b5f9] shadow-sm'
                      : 'text-[#666666] dark:text-[#9aa1b2]'
                  }`}
                >
                  Backend Systems
                </button>
                <button
                  onClick={() => {
                    setSelectedRole('fullstack');
                    setHasAdoptedSkill(false);
                  }}
                  className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                    selectedRole === 'fullstack'
                      ? 'bg-white dark:bg-[#1a1d24] text-[#0a66c2] dark:text-[#70b5f9] shadow-sm'
                      : 'text-[#666666] dark:text-[#9aa1b2]'
                  }`}
                >
                  Full Stack Dev
                </button>
              </div>
            </div>

            {/* ATS Score Meter & Keywords Grid */}
            <div className="p-5 rounded-lg border border-[#e0e0e0] dark:border-[#2b313c] bg-[#f3f6f8] dark:bg-[#0f1115]">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#e0e0e0] dark:border-[#2b313c]">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-[#666666] dark:text-[#9aa1b2]">ATS Match Score</span>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#ecfdf5] text-[#057642] dark:bg-[#057642]/20 dark:text-[#45c586]">
                      Best Fit Resume
                    </span>
                  </div>
                  <div className="text-3xl font-extrabold text-[#0a66c2] dark:text-[#70b5f9] font-mono mt-1">
                    {hasAdoptedSkill ? '96%' : '88%'}
                  </div>
                </div>

                <button
                  onClick={() => setHasAdoptedSkill(!hasAdoptedSkill)}
                  className="btn-primary-corporate text-xs"
                >
                  <Sparkles size={13} />
                  <span>{hasAdoptedSkill ? 'Reset Keywords' : 'Adopt Missing Skill'}</span>
                </button>
              </div>

              {/* Keyword Pills */}
              <div className="pt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <span className="text-xs font-semibold text-[#057642] dark:text-[#45c586] flex items-center gap-1.5 mb-2">
                    <CheckCircle2 size={13} />
                    <span>Matched Keywords ({hasAdoptedSkill ? 5 : 4})</span>
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    <span className="px-2.5 py-1 rounded-md text-xs font-medium bg-[#ecfdf5] dark:bg-[#057642]/20 text-[#057642] dark:text-[#45c586] border border-[#057642]/30">
                      Python
                    </span>
                    <span className="px-2.5 py-1 rounded-md text-xs font-medium bg-[#ecfdf5] dark:bg-[#057642]/20 text-[#057642] dark:text-[#45c586] border border-[#057642]/30">
                      PostgreSQL
                    </span>
                    <span className="px-2.5 py-1 rounded-md text-xs font-medium bg-[#ecfdf5] dark:bg-[#057642]/20 text-[#057642] dark:text-[#45c586] border border-[#057642]/30">
                      Redis
                    </span>
                    <span className="px-2.5 py-1 rounded-md text-xs font-medium bg-[#ecfdf5] dark:bg-[#057642]/20 text-[#057642] dark:text-[#45c586] border border-[#057642]/30">
                      Docker
                    </span>
                    {hasAdoptedSkill && (
                      <span className="px-2.5 py-1 rounded-md text-xs font-medium bg-[#f0f7fe] dark:bg-[#0a66c2]/20 text-[#0a66c2] dark:text-[#70b5f9] border border-[#0a66c2]/40">
                        Kubernetes (Adopted)
                      </span>
                    )}
                  </div>
                </div>

                <div>
                  <span className="text-xs font-semibold text-[#b24020] dark:text-[#ff8162] flex items-center gap-1.5 mb-2">
                    <Target size={13} />
                    <span>Missing Keywords ({hasAdoptedSkill ? 1 : 2})</span>
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {!hasAdoptedSkill && (
                      <span className="px-2.5 py-1 rounded-md text-xs font-medium bg-[#fffbeb] dark:bg-[#b24020]/20 text-[#b24020] dark:text-[#ff8162] border border-[#b24020]/30">
                        Kubernetes
                      </span>
                    )}
                    <span className="px-2.5 py-1 rounded-md text-xs font-medium bg-[#fffbeb] dark:bg-[#b24020]/20 text-[#b24020] dark:text-[#ff8162] border border-[#b24020]/30">
                      gRPC
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: 1-Click Job Scraper */}
        {activeTab === 'scraper' && (
          <div className="space-y-5">
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-[#0a66c2] dark:text-[#70b5f9]">
                Structured Intelligence
              </span>
              <h3 className="text-base sm:text-lg font-bold text-[#000000] dark:text-[#f3f6f8]">
                Parse Any Job Description or ATS URL
              </h3>
            </div>

            {/* Simulated Input Bar */}
            <div className="flex items-center gap-2 p-2 rounded-lg border border-[#e0e0e0] dark:border-[#2b313c] bg-white dark:bg-[#1a1d24]">
              <FileSearch size={16} className="text-[#666666] ml-2" />
              <input
                type="text"
                readOnly
                value={scraperUrl}
                onChange={(e) => setScraperUrl(e.target.value)}
                className="w-full bg-transparent text-xs text-[#000000] dark:text-[#f3f6f8] focus:outline-none"
              />
              <span className="text-[11px] px-2.5 py-1 rounded bg-[#0a66c2] text-white font-semibold whitespace-nowrap">
                Parsed
              </span>
            </div>

            {/* Parsed Output Card */}
            <div className="p-5 rounded-lg border border-[#e0e0e0] dark:border-[#2b313c] bg-white dark:bg-[#1a1d24]">
              <div className="flex flex-wrap items-start justify-between gap-4 pb-4 border-b border-[#e0e0e0] dark:border-[#2b313c]">
                <div>
                  <h4 className="text-sm sm:text-base font-bold text-[#000000] dark:text-[#f3f6f8]">
                    Senior Software Engineer - Payments Infrastructure
                  </h4>
                  <div className="flex flex-wrap items-center gap-3 mt-1 text-xs text-[#666666] dark:text-[#9aa1b2]">
                    <span className="flex items-center gap-1">
                      <Building2 size={13} className="text-[#0a66c2]" />
                      <span>Stripe</span>
                    </span>
                    <span className="flex items-center gap-1">
                      <MapPin size={13} className="text-[#0a66c2]" />
                      <span>Hybrid (San Francisco, CA)</span>
                    </span>
                    <span className="flex items-center gap-1 font-semibold text-[#057642] dark:text-[#45c586]">
                      <DollarSign size={13} />
                      <span>$140,000 - $175,000 USD</span>
                    </span>
                  </div>
                </div>

                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#f0f7fe] dark:bg-[#0a66c2]/20 text-[#0a66c2] dark:text-[#70b5f9] border border-[#0a66c2]/30">
                  <GraduationCap size={13} />
                  <span>Eligible: 2024-2026 Graduates</span>
                </div>
              </div>

              <div className="pt-4">
                <span className="text-[11px] font-bold text-[#666666] dark:text-[#9aa1b2] uppercase tracking-wider block mb-2">
                  ATS Extracted Taxonomy
                </span>
                <div className="flex flex-wrap gap-1.5">
                  <span className="px-2 py-0.5 rounded text-xs bg-[#f3f6f8] dark:bg-[#0f1115] text-[#000000] dark:text-[#f3f6f8] border border-[#e0e0e0] dark:border-[#2b313c]">
                    Distributed Systems
                  </span>
                  <span className="px-2 py-0.5 rounded text-xs bg-[#f3f6f8] dark:bg-[#0f1115] text-[#000000] dark:text-[#f3f6f8] border border-[#e0e0e0] dark:border-[#2b313c]">
                    FastAPI
                  </span>
                  <span className="px-2 py-0.5 rounded text-xs bg-[#f3f6f8] dark:bg-[#0f1115] text-[#000000] dark:text-[#f3f6f8] border border-[#e0e0e0] dark:border-[#2b313c]">
                    PostgreSQL
                  </span>
                  <span className="px-2 py-0.5 rounded text-xs bg-[#f3f6f8] dark:bg-[#0f1115] text-[#000000] dark:text-[#f3f6f8] border border-[#e0e0e0] dark:border-[#2b313c]">
                    Kafka
                  </span>
                  <span className="px-2 py-0.5 rounded text-xs bg-[#f3f6f8] dark:bg-[#0f1115] text-[#000000] dark:text-[#f3f6f8] border border-[#e0e0e0] dark:border-[#2b313c]">
                    High Availability
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: Pipeline CRM */}
        {activeTab === 'crm' && (
          <div className="space-y-5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-[#0a66c2] dark:text-[#70b5f9]">
                  Application CRM &amp; Kanban
                </span>
                <h3 className="text-base sm:text-lg font-bold text-[#000000] dark:text-[#f3f6f8]">
                  Automate Follow-Ups &amp; Never Lose an Application Link
                </h3>
              </div>
              <button
                onClick={() => setPipelineStatus(pipelineStatus === 'Applied' ? 'Interviewing' : 'Applied')}
                className="btn-primary-corporate text-xs"
              >
                <span>{pipelineStatus === 'Applied' ? 'Advance to Interviewing' : 'Reset to Applied'}</span>
              </button>
            </div>

            {/* Kanban Preview Card */}
            <div className="p-5 rounded-lg border border-[#e0e0e0] dark:border-[#2b313c] bg-[#f3f6f8] dark:bg-[#0f1115]">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
                <div>
                  <h4 className="text-sm font-bold text-[#000000] dark:text-[#f3f6f8]">
                    Stripe - Senior Infrastructure Engineer
                  </h4>
                  <p className="text-xs text-[#666666] dark:text-[#9aa1b2]">
                    Current Status: <strong className="text-[#0a66c2] dark:text-[#70b5f9]">{pipelineStatus}</strong>
                  </p>
                </div>
                <div className="flex items-center gap-1.5 text-xs text-[#b24020] dark:text-[#ff8162] bg-[#fffbeb] dark:bg-[#b24020]/20 px-3 py-1 rounded-md border border-[#b24020]/30">
                  <Clock size={13} />
                  <span>Follow-up alert: Due in 3 days</span>
                </div>
              </div>

              {/* Progress Flow Steps */}
              <div className="grid grid-cols-4 gap-2 text-center text-xs pt-2">
                <div className="p-2 rounded-md bg-[#0a66c2] text-white font-semibold">Wishlist</div>
                <div
                  className={`p-2 rounded-md font-semibold transition-colors ${
                    pipelineStatus === 'Applied' || pipelineStatus === 'Interviewing'
                      ? 'bg-[#0a66c2] text-white'
                      : 'bg-white dark:bg-[#1a1d24] border border-[#e0e0e0] dark:border-[#2b313c] text-[#666666] dark:text-[#9aa1b2]'
                  }`}
                >
                  Applied
                </div>
                <div
                  className={`p-2 rounded-md font-semibold transition-colors ${
                    pipelineStatus === 'Interviewing'
                      ? 'bg-[#057642] text-white'
                      : 'bg-white dark:bg-[#1a1d24] border border-[#e0e0e0] dark:border-[#2b313c] text-[#666666] dark:text-[#9aa1b2]'
                  }`}
                >
                  Interviewing
                </div>
                <div className="p-2 rounded-md bg-white dark:bg-[#1a1d24] border border-[#e0e0e0] dark:border-[#2b313c] text-[#666666] dark:text-[#9aa1b2]">
                  Offer
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Playground Bottom Action Bar */}
      <div className="px-6 py-4 bg-[#f3f6f8] dark:bg-[#0f1115] border-t border-[#e0e0e0] dark:border-[#2b313c] flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-xs text-[#666666] dark:text-[#9aa1b2]">
          <Sparkles size={14} className="text-[#0a66c2]" />
          <span>Interactive preview based on real JobHelperGuru NLP capabilities.</span>
        </div>
        <button
          onClick={onTryLiveDemo}
          className="btn-primary-corporate text-xs"
        >
          <span>Launch Live in Workspace</span>
          <ArrowRight size={14} />
        </button>
      </div>
    </div>
  );
}
