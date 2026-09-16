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
    <div className="w-full max-w-5xl mx-auto rounded-2xl border border-[#e0e0e0] dark:border-[#374151] bg-white dark:bg-[#1a2234] shadow-xl overflow-hidden transition-all">
      {/* Interactive Tabs Header */}
      <div className="flex border-b border-[#e0e0e0] dark:border-[#374151] bg-[#f8fafc] dark:bg-[#111827] overflow-x-auto scrollbar-none" role="tablist">
        <button
          role="tab"
          aria-selected={activeTab === 'bulletcraft'}
          onClick={() => setActiveTab('bulletcraft')}
          className={`flex items-center gap-2 px-5 py-3.5 text-xs font-semibold whitespace-nowrap border-b-2 transition-all ${
            activeTab === 'bulletcraft'
              ? 'border-[#0a66c2] text-[#0a66c2] dark:text-[#70b5f9] bg-white dark:bg-[#1a2234]'
              : 'border-transparent text-[#64748b] dark:text-[#94a3b8] hover:text-[#0f172a] dark:hover:text-white'
          }`}
        >
          <Wand2 size={16} />
          <span>BulletCraft Framework</span>
        </button>

        <button
          role="tab"
          aria-selected={activeTab === 'ats'}
          onClick={() => setActiveTab('ats')}
          className={`flex items-center gap-2 px-5 py-3.5 text-xs font-semibold whitespace-nowrap border-b-2 transition-all ${
            activeTab === 'ats'
              ? 'border-[#0a66c2] text-[#0a66c2] dark:text-[#70b5f9] bg-white dark:bg-[#1a2234]'
              : 'border-transparent text-[#64748b] dark:text-[#94a3b8] hover:text-[#0f172a] dark:hover:text-white'
          }`}
        >
          <Target size={16} />
          <span>ATS Fit Matcher</span>
        </button>

        <button
          role="tab"
          aria-selected={activeTab === 'scraper'}
          onClick={() => setActiveTab('scraper')}
          className={`flex items-center gap-2 px-5 py-3.5 text-xs font-semibold whitespace-nowrap border-b-2 transition-all ${
            activeTab === 'scraper'
              ? 'border-[#0a66c2] text-[#0a66c2] dark:text-[#70b5f9] bg-white dark:bg-[#1a2234]'
              : 'border-transparent text-[#64748b] dark:text-[#94a3b8] hover:text-[#0f172a] dark:hover:text-white'
          }`}
        >
          <FileSearch size={16} />
          <span>1-Click Job Scraper</span>
        </button>

        <button
          role="tab"
          aria-selected={activeTab === 'crm'}
          onClick={() => setActiveTab('crm')}
          className={`flex items-center gap-2 px-5 py-3.5 text-xs font-semibold whitespace-nowrap border-b-2 transition-all ${
            activeTab === 'crm'
              ? 'border-[#0a66c2] text-[#0a66c2] dark:text-[#70b5f9] bg-white dark:bg-[#1a2234]'
              : 'border-transparent text-[#64748b] dark:text-[#94a3b8] hover:text-[#0f172a] dark:hover:text-white'
          }`}
        >
          <Layers size={16} />
          <span>Pipeline CRM</span>
        </button>
      </div>

      {/* Tab Panels Body */}
      <div className="p-6 sm:p-8">
        {/* TAB 1: BulletCraft Framework */}
        {activeTab === 'bulletcraft' && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-[#0a66c2] dark:text-[#70b5f9]">
                  Accomplishment Engineering
                </span>
                <h3 className="text-lg font-bold text-[#0f172a] dark:text-white">
                  Transform Generic Bullets into Quantifiable Impact
                </h3>
              </div>
              <button
                onClick={() => setIsTransformed(!isTransformed)}
                className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold shadow-sm transition-all ${
                  isTransformed
                    ? 'bg-[#f1f5f9] text-[#334155] dark:bg-[#334155] dark:text-[#f8fafc] hover:bg-[#e2e8f0]'
                    : 'bg-[#0a66c2] text-white hover:bg-[#084e96] hover:shadow'
                }`}
              >
                {isTransformed ? (
                  <>
                    <RefreshCw size={14} />
                    <span>Reset Example</span>
                  </>
                ) : (
                  <>
                    <Sparkles size={14} />
                    <span>Transform with BulletCraft</span>
                  </>
                )}
              </button>
            </div>

            {/* Before / After Comparison Display */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Weak Bullet Card */}
              <div className="p-5 rounded-xl border border-[#e2e8f0] dark:border-[#334155] bg-[#f8fafc] dark:bg-[#0f172a]/60">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-bold text-[#ef4444] bg-[#fef2f2] dark:bg-[#ef4444]/10 dark:text-[#fca5a5] px-2 py-0.5 rounded">
                    Weak / Generic Bullet
                  </span>
                  <span className="text-[10px] text-[#64748b] dark:text-[#94a3b8]">ATS Conversion: Low</span>
                </div>
                <p className="text-xs sm:text-sm text-[#475569] dark:text-[#cbd5e1] leading-relaxed italic">
                  &ldquo;Responsible for writing backend APIs and optimizing database queries for our services.&rdquo;
                </p>
                <div className="mt-4 pt-3 border-t border-[#e2e8f0] dark:border-[#334155] text-[11px] text-[#64748b] dark:text-[#94a3b8] flex items-center gap-1.5">
                  <span className="text-[#ef4444] font-bold">✕</span>
                  <span>Lacks quantifiable metrics, scale, and technical depth.</span>
                </div>
              </div>

              {/* BulletCraft Transformed Card */}
              <div
                className={`p-5 rounded-xl border transition-all ${
                  isTransformed
                    ? 'border-[#0a66c2]/40 bg-[#f0f7ff] dark:bg-[#0a66c2]/10 ring-2 ring-[#0a66c2]/20'
                    : 'border-[#e2e8f0] dark:border-[#334155] bg-white dark:bg-[#1a2234] opacity-80'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-bold text-[#0a66c2] bg-[#e0f2fe] dark:bg-[#0a66c2]/20 dark:text-[#70b5f9] px-2 py-0.5 rounded flex items-center gap-1">
                    <Sparkles size={11} />
                    <span>BulletCraft Formula</span>
                  </span>
                  <span className="text-[10px] text-[#057642] dark:text-[#4ade80] font-semibold flex items-center gap-1">
                    <TrendingUp size={11} />
                    <span>ATS Conversion: High</span>
                  </span>
                </div>

                {isTransformed ? (
                  <div className="space-y-4 animate-fade-in">
                    <p className="text-xs sm:text-sm font-medium text-[#0f172a] dark:text-white leading-relaxed">
                      &ldquo;Engineered 14 resilient FastAPI microservices handling 2.4M daily requests, reducing p99 latency by 38% through Redis caching and PostgreSQL query indexing.&rdquo;
                    </p>

                    {/* Structural XYZ Tags */}
                    <div className="flex flex-wrap gap-2 pt-2">
                      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-semibold bg-[#ecfdf5] dark:bg-[#064e3b]/40 text-[#057642] dark:text-[#6ee7b7] border border-[#a7f3d0] dark:border-[#059669]/30">
                        <CheckCircle2 size={12} />
                        <span>Accomplished [X]: Action</span>
                      </div>
                      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-semibold bg-[#eff6ff] dark:bg-[#1e3a8a]/40 text-[#0a66c2] dark:text-[#93c5fd] border border-[#bfdbfe] dark:border-[#3b82f6]/30">
                        <TrendingUp size={12} />
                        <span>Measured by [Y]: 2.4M reqs & -38% latency</span>
                      </div>
                      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-semibold bg-[#faf5ff] dark:bg-[#581c87]/40 text-[#7e22ce] dark:text-[#d8b4fe] border border-[#e9d5ff] dark:border-[#9333ea]/30">
                        <ShieldCheck size={12} />
                        <span>Done by [Z]: Redis & PostgreSQL</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="h-28 flex flex-col items-center justify-center text-center">
                    <p className="text-xs text-[#64748b] dark:text-[#94a3b8] mb-3">
                      Click &ldquo;Transform with BulletCraft&rdquo; to see the accomplishment formula in action.
                    </p>
                    <button
                      onClick={() => setIsTransformed(true)}
                      className="px-3 py-1.5 rounded-lg bg-[#0a66c2] text-white text-xs font-medium hover:bg-[#084e96]"
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
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-[#0a66c2] dark:text-[#70b5f9]">
                  Smart Multi-Resume Scoring
                </span>
                <h3 className="text-lg font-bold text-[#0f172a] dark:text-white">
                  Match Keywords & Eliminate ATS Gaps
                </h3>
              </div>
              {/* Role Switcher */}
              <div className="inline-flex rounded-lg border border-[#e2e8f0] dark:border-[#334155] p-1 bg-[#f8fafc] dark:bg-[#111827]">
                <button
                  onClick={() => {
                    setSelectedRole('backend');
                    setHasAdoptedSkill(false);
                  }}
                  className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                    selectedRole === 'backend'
                      ? 'bg-white dark:bg-[#1a2234] text-[#0a66c2] dark:text-[#70b5f9] shadow-sm'
                      : 'text-[#64748b] dark:text-[#94a3b8]'
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
                      ? 'bg-white dark:bg-[#1a2234] text-[#0a66c2] dark:text-[#70b5f9] shadow-sm'
                      : 'text-[#64748b] dark:text-[#94a3b8]'
                  }`}
                >
                  Full Stack Dev
                </button>
              </div>
            </div>

            {/* ATS Score Meter & Keywords Grid */}
            <div className="p-6 rounded-xl border border-[#e2e8f0] dark:border-[#334155] bg-[#f8fafc] dark:bg-[#0f172a]/60">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-[#e2e8f0] dark:border-[#334155]">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-[#64748b] dark:text-[#94a3b8]">ATS Match Score</span>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#ecfdf5] text-[#057642] dark:bg-[#064e3b]/50 dark:text-[#6ee7b7]">
                      Best Fit Resume
                    </span>
                  </div>
                  <div className="text-3xl font-extrabold text-[#0a66c2] dark:text-[#70b5f9] font-mono mt-1">
                    {hasAdoptedSkill ? '96%' : '88%'}
                  </div>
                </div>

                <button
                  onClick={() => setHasAdoptedSkill(!hasAdoptedSkill)}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold bg-[#0a66c2] text-white hover:bg-[#084e96] shadow-sm transition-all"
                >
                  <Sparkles size={13} />
                  <span>{hasAdoptedSkill ? 'Reset Keywords' : 'Adopt Missing Skill'}</span>
                </button>
              </div>

              {/* Keyword Pills */}
              <div className="pt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <span className="text-xs font-semibold text-[#057642] dark:text-[#4ade80] flex items-center gap-1.5 mb-2">
                    <CheckCircle2 size={13} />
                    <span>Matched Keywords ({hasAdoptedSkill ? 5 : 4})</span>
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    <span className="px-2.5 py-1 rounded-md text-xs font-medium bg-[#ecfdf5] dark:bg-[#064e3b]/30 text-[#057642] dark:text-[#6ee7b7] border border-[#a7f3d0] dark:border-[#059669]/40">
                      Python
                    </span>
                    <span className="px-2.5 py-1 rounded-md text-xs font-medium bg-[#ecfdf5] dark:bg-[#064e3b]/30 text-[#057642] dark:text-[#6ee7b7] border border-[#a7f3d0] dark:border-[#059669]/40">
                      PostgreSQL
                    </span>
                    <span className="px-2.5 py-1 rounded-md text-xs font-medium bg-[#ecfdf5] dark:bg-[#064e3b]/30 text-[#057642] dark:text-[#6ee7b7] border border-[#a7f3d0] dark:border-[#059669]/40">
                      Redis
                    </span>
                    <span className="px-2.5 py-1 rounded-md text-xs font-medium bg-[#ecfdf5] dark:bg-[#064e3b]/30 text-[#057642] dark:text-[#6ee7b7] border border-[#a7f3d0] dark:border-[#059669]/40">
                      Docker
                    </span>
                    {hasAdoptedSkill && (
                      <span className="px-2.5 py-1 rounded-md text-xs font-medium bg-[#dbeafe] dark:bg-[#1e3a8a]/50 text-[#1d4ed8] dark:text-[#93c5fd] border border-[#93c5fd] animate-pulse">
                        Kubernetes (Adopted)
                      </span>
                    )}
                  </div>
                </div>

                <div>
                  <span className="text-xs font-semibold text-[#b45309] dark:text-[#fbbf24] flex items-center gap-1.5 mb-2">
                    <Target size={13} />
                    <span>Missing Keywords ({hasAdoptedSkill ? 1 : 2})</span>
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {!hasAdoptedSkill && (
                      <span className="px-2.5 py-1 rounded-md text-xs font-medium bg-[#fffbeb] dark:bg-[#78350f]/30 text-[#b45309] dark:text-[#fde68a] border border-[#fde68a] dark:border-[#d97706]/40">
                        Kubernetes
                      </span>
                    )}
                    <span className="px-2.5 py-1 rounded-md text-xs font-medium bg-[#fffbeb] dark:bg-[#78350f]/30 text-[#b45309] dark:text-[#fde68a] border border-[#fde68a] dark:border-[#d97706]/40">
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
          <div className="space-y-6">
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-[#0a66c2] dark:text-[#70b5f9]">
                Structured Intelligence
              </span>
              <h3 className="text-lg font-bold text-[#0f172a] dark:text-white">
                Parse Any Job Description or ATS URL
              </h3>
            </div>

            {/* Simulated Input Bar */}
            <div className="flex items-center gap-2 p-2 rounded-xl border border-[#cbd5e1] dark:border-[#475569] bg-[#f8fafc] dark:bg-[#111827]">
              <FileSearch size={16} className="text-[#64748b] ml-2" />
              <input
                type="text"
                readOnly
                value={scraperUrl}
                onChange={(e) => setScraperUrl(e.target.value)}
                className="w-full bg-transparent text-xs text-[#334155] dark:text-[#cbd5e1] focus:outline-none"
              />
              <span className="text-[11px] px-2.5 py-1 rounded bg-[#0a66c2] text-white font-semibold whitespace-nowrap">
                Parsed
              </span>
            </div>

            {/* Parsed Output Card */}
            <div className="p-5 rounded-xl border border-[#e2e8f0] dark:border-[#334155] bg-white dark:bg-[#1a2234] shadow-sm">
              <div className="flex flex-wrap items-start justify-between gap-4 pb-4 border-b border-[#e2e8f0] dark:border-[#334155]">
                <div>
                  <h4 className="text-base font-bold text-[#0f172a] dark:text-white">
                    Senior Software Engineer - Payments Infrastructure
                  </h4>
                  <div className="flex flex-wrap items-center gap-3 mt-1 text-xs text-[#64748b] dark:text-[#94a3b8]">
                    <span className="flex items-center gap-1">
                      <Building2 size={13} className="text-[#0a66c2]" />
                      <span>Stripe</span>
                    </span>
                    <span className="flex items-center gap-1">
                      <MapPin size={13} className="text-[#0a66c2]" />
                      <span>Hybrid (San Francisco, CA)</span>
                    </span>
                    <span className="flex items-center gap-1 font-semibold text-[#057642] dark:text-[#4ade80]">
                      <DollarSign size={13} />
                      <span>$140,000 - $175,000 USD</span>
                    </span>
                  </div>
                </div>

                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#eff6ff] text-[#1d4ed8] dark:bg-[#1e3a8a]/40 dark:text-[#93c5fd] border border-[#bfdbfe]">
                  <GraduationCap size={13} />
                  <span>Eligible: 2024-2026 Graduates</span>
                </div>
              </div>

              <div className="pt-4">
                <span className="text-[11px] font-bold text-[#64748b] dark:text-[#94a3b8] uppercase tracking-wider block mb-2">
                  ATS Extracted Taxonomy
                </span>
                <div className="flex flex-wrap gap-1.5">
                  <span className="px-2 py-0.5 rounded text-xs bg-[#f1f5f9] dark:bg-[#334155] text-[#334155] dark:text-[#e2e8f0]">
                    Distributed Systems
                  </span>
                  <span className="px-2 py-0.5 rounded text-xs bg-[#f1f5f9] dark:bg-[#334155] text-[#334155] dark:text-[#e2e8f0]">
                    FastAPI
                  </span>
                  <span className="px-2 py-0.5 rounded text-xs bg-[#f1f5f9] dark:bg-[#334155] text-[#334155] dark:text-[#e2e8f0]">
                    PostgreSQL
                  </span>
                  <span className="px-2 py-0.5 rounded text-xs bg-[#f1f5f9] dark:bg-[#334155] text-[#334155] dark:text-[#e2e8f0]">
                    Kafka
                  </span>
                  <span className="px-2 py-0.5 rounded text-xs bg-[#f1f5f9] dark:bg-[#334155] text-[#334155] dark:text-[#e2e8f0]">
                    High Availability
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: Pipeline CRM */}
        {activeTab === 'crm' && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-[#0a66c2] dark:text-[#70b5f9]">
                  Application CRM & Kanban
                </span>
                <h3 className="text-lg font-bold text-[#0f172a] dark:text-white">
                  Automate Follow-Ups & Never Lose an Application Link
                </h3>
              </div>
              <button
                onClick={() => setPipelineStatus(pipelineStatus === 'Applied' ? 'Interviewing' : 'Applied')}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-[#0a66c2] text-white hover:bg-[#084e96] transition-all"
              >
                <span>{pipelineStatus === 'Applied' ? 'Advance to Interviewing' : 'Reset to Applied'}</span>
              </button>
            </div>

            {/* Kanban Preview Card */}
            <div className="p-5 rounded-xl border border-[#e2e8f0] dark:border-[#334155] bg-[#f8fafc] dark:bg-[#0f172a]/60">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
                <div>
                  <h4 className="text-sm font-bold text-[#0f172a] dark:text-white">
                    Stripe - Senior Infrastructure Engineer
                  </h4>
                  <p className="text-xs text-[#64748b] dark:text-[#94a3b8]">
                    Current Status:{' '}
                    <strong className="text-[#0a66c2] dark:text-[#70b5f9]">{pipelineStatus}</strong>
                  </p>
                </div>
                <div className="flex items-center gap-1.5 text-xs text-[#d97706] dark:text-[#fde68a] bg-[#fffbeb] dark:bg-[#78350f]/30 px-3 py-1 rounded-md border border-[#fef3c7] dark:border-[#d97706]/30">
                  <Clock size={13} />
                  <span>Follow-up alert: Due in 3 days</span>
                </div>
              </div>

              {/* Progress Flow Steps */}
              <div className="grid grid-cols-4 gap-2 text-center text-xs pt-2">
                <div className="p-2 rounded bg-[#0a66c2] text-white font-semibold">Wishlist</div>
                <div
                  className={`p-2 rounded font-semibold transition-colors ${
                    pipelineStatus === 'Applied' || pipelineStatus === 'Interviewing'
                      ? 'bg-[#0a66c2] text-white'
                      : 'bg-[#e2e8f0] dark:bg-[#334155] text-[#64748b] dark:text-[#94a3b8]'
                  }`}
                >
                  Applied
                </div>
                <div
                  className={`p-2 rounded font-semibold transition-colors ${
                    pipelineStatus === 'Interviewing'
                      ? 'bg-[#057642] text-white'
                      : 'bg-[#e2e8f0] dark:bg-[#334155] text-[#64748b] dark:text-[#94a3b8]'
                  }`}
                >
                  Interviewing
                </div>
                <div className="p-2 rounded bg-[#e2e8f0] dark:bg-[#334155] text-[#64748b] dark:text-[#94a3b8]">
                  Offer
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Playground Bottom Action Bar */}
      <div className="px-6 py-4 bg-[#f8fafc] dark:bg-[#111827] border-t border-[#e0e0e0] dark:border-[#374151] flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-xs text-[#64748b] dark:text-[#94a3b8]">
          <Sparkles size={14} className="text-[#0a66c2]" />
          <span>Interactive preview based on real JobHelperGuru NLP capabilities.</span>
        </div>
        <button
          onClick={onTryLiveDemo}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold bg-[#0a66c2] text-white hover:bg-[#084e96] shadow-sm transition-all"
        >
          <span>Launch Live in Workspace</span>
          <ArrowRight size={14} />
        </button>
      </div>
    </div>
  );
}
