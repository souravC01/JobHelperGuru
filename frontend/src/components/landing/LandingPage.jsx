import {
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Zap,
  Lock,
  Cpu,
  Database,
  BarChart3,
  CheckCircle,
} from 'lucide-react';
import LandingNav from './LandingNav';
import InteractiveHeroPlayground from './InteractiveHeroPlayground';
import ValuePillars from './ValuePillars';
import HowItWorks from './HowItWorks';
import FaqSection from './FaqSection';
import LandingFooter from './LandingFooter';

export default function LandingPage({
  currentUser,
  theme,
  onToggleTheme,
  onSignIn,
  onGetStarted,
  onGoToDashboard,
  onExploreGuest,
  onOpenPrivacy,
}) {
  return (
    <div className="min-h-screen bg-[#f8fafc] dark:bg-[#0f172a] text-[#0f172a] dark:text-[#f8fafc] flex flex-col font-sans selection:bg-[#0a66c2] selection:text-white transition-colors">
      {/* Navigation */}
      <LandingNav
        currentUser={currentUser}
        onSignIn={onSignIn}
        onGetStarted={onGetStarted}
        onGoToDashboard={onGoToDashboard}
        theme={theme}
        onToggleTheme={onToggleTheme}
      />

      {/* Hero Section */}
      <section className="relative pt-12 pb-16 sm:pt-20 sm:pb-24 overflow-hidden">
        {/* Subtle background glow */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-[#0a66c2]/10 dark:bg-[#0a66c2]/15 blur-[120px] rounded-full pointer-events-none -z-10" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          {/* Eyebrow badge */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-bold bg-white dark:bg-[#1a2234] border border-[#e2e8f0] dark:border-[#334155] text-[#0a66c2] dark:text-[#70b5f9] shadow-sm mb-6 animate-fade-in">
            <Sparkles size={14} />
            <span>BulletCraft Framework &bull; ATS Fit Ranker &bull; 100% Free Heuristic NLP Option</span>
          </div>

          {/* Main Headline */}
          <h1 className="text-3xl sm:text-5xl lg:text-6xl font-black tracking-tight text-[#0f172a] dark:text-white max-w-4xl mx-auto leading-tight sm:leading-tight">
            Turn Job Postings into Interview Calls with{' '}
            <span className="text-[#0a66c2] dark:text-[#70b5f9]">AI-Tailored Resumes</span>
          </h1>

          {/* Subtitle */}
          <p className="mt-5 sm:mt-6 text-sm sm:text-lg text-[#64748b] dark:text-[#94a3b8] max-w-2xl mx-auto leading-relaxed">
            Extract ATS keywords from any job posting, score your resume portfolio against ATS filters,
            engineer quantifiable accomplishment bullets using the BulletCraft Framework, and organize
            your entire pipeline in one secure workspace.
          </p>

          {/* Dual CTAs */}
          <div className="mt-8 sm:mt-10 flex flex-col sm:flex-row items-center justify-center gap-3.5">
            {currentUser ? (
              <button
                onClick={onGoToDashboard}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl text-sm font-bold bg-[#0a66c2] text-white hover:bg-[#084e96] shadow-md hover:shadow-lg transition-all"
              >
                <span>Go to Dashboard</span>
                <ArrowRight size={16} />
              </button>
            ) : (
              <button
                onClick={onGetStarted}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl text-sm font-bold bg-[#0a66c2] text-white hover:bg-[#084e96] shadow-md hover:shadow-lg transition-all"
              >
                <span>Get Started Free</span>
                <ArrowRight size={16} />
              </button>
            )}

            <button
              onClick={onExploreGuest}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl text-sm font-bold bg-white dark:bg-[#1a2234] text-[#334155] dark:text-[#f8fafc] border border-[#cbd5e1] dark:border-[#475569] hover:border-[#0a66c2] dark:hover:border-[#70b5f9] hover:bg-[#f8fafc] dark:hover:bg-[#232d42] shadow-sm transition-all"
            >
              <span>Try Guest Workspace</span>
              <span className="text-xs text-[#64748b] dark:text-[#94a3b8] font-normal">(No Sign-Up)</span>
            </button>
          </div>

          {/* Impact Stats Strip */}
          <div className="mt-12 sm:mt-16 pt-8 border-t border-[#e2e8f0] dark:border-[#334155] grid grid-cols-1 sm:grid-cols-3 gap-6 max-w-4xl mx-auto text-center">
            <div className="p-3">
              <div className="text-2xl sm:text-3xl font-extrabold text-[#0a66c2] dark:text-[#70b5f9] font-mono">
                75%
              </div>
              <p className="text-xs text-[#64748b] dark:text-[#94a3b8] mt-1 font-medium">
                Resumes filtered by automated ATS algorithms before human review
              </p>
            </div>
            <div className="p-3">
              <div className="text-2xl sm:text-3xl font-extrabold text-[#057642] dark:text-[#4ade80] font-mono">
                3x
              </div>
              <p className="text-xs text-[#64748b] dark:text-[#94a3b8] mt-1 font-medium">
                Higher interview callbacks with quantifiable BulletCraft metrics
              </p>
            </div>
            <div className="p-3">
              <div className="text-2xl sm:text-3xl font-extrabold text-[#7e22ce] dark:text-[#c084fc] font-mono">
                100%
              </div>
              <p className="text-xs text-[#64748b] dark:text-[#94a3b8] mt-1 font-medium">
                Private with AES-256 Fernet encryption and Cloudflare R2 vaults
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Interactive Micro-Demo Section */}
      <section id="demo" className="py-8 sm:py-12 px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-8">
          <span className="text-xs font-bold uppercase tracking-widest text-[#0a66c2] dark:text-[#70b5f9] bg-[#eff6ff] dark:bg-[#0a66c2]/10 px-3 py-1 rounded-full border border-[#bfdbfe] dark:border-[#0a66c2]/30">
            Interactive Playground
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-[#0f172a] dark:text-white mt-2 tracking-tight">
            Test the Core Engine Live
          </h2>
          <p className="text-xs sm:text-sm text-[#64748b] dark:text-[#94a3b8] mt-2">
            Try our accomplishment engineering formula, keyword matcher, and job parser below.
          </p>
        </div>

        <InteractiveHeroPlayground onTryLiveDemo={onExploreGuest} />
      </section>

      {/* Core Capabilities */}
      <ValuePillars />

      {/* 3-Step Workflow */}
      <HowItWorks />

      {/* Security Architecture Callout */}
      <section id="security" className="py-16 sm:py-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="rounded-3xl p-8 sm:p-12 border border-[#cbd5e1] dark:border-[#334155] bg-gradient-to-br from-white to-[#f1f5f9] dark:from-[#1a2234] dark:to-[#0f172a] shadow-lg">
          <div className="max-w-3xl">
            <span className="text-xs font-bold uppercase tracking-widest text-[#0a66c2] dark:text-[#70b5f9] bg-[#eff6ff] dark:bg-[#0a66c2]/10 px-3 py-1 rounded-full border border-[#bfdbfe] dark:border-[#0a66c2]/30">
              Enterprise Data Protection &amp; BYOK
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-[#0f172a] dark:text-white mt-3 tracking-tight">
              Your Credentials and Resumes Never Leak
            </h2>
            <p className="text-xs sm:text-sm text-[#64748b] dark:text-[#94a3b8] mt-3 leading-relaxed">
              Unlike commercial job assistants that monetize candidate data or force proprietary subscriptions,
              JobHelperGuru is built with privacy-first isolation from day one.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mt-8 pt-8 border-t border-[#e2e8f0] dark:border-[#334155]">
            <div className="flex items-start gap-3">
              <div className="w-9 h-9 rounded-lg bg-[#eff6ff] dark:bg-[#0a66c2]/20 text-[#0a66c2] dark:text-[#70b5f9] flex items-center justify-center shrink-0">
                <Lock size={18} />
              </div>
              <div>
                <h4 className="text-xs sm:text-sm font-bold text-[#0f172a] dark:text-white">
                  AES-256 Fernet Encryption
                </h4>
                <p className="text-xs text-[#64748b] dark:text-[#94a3b8] mt-1">
                  API keys for Groq, Nvidia NIM, OpenAI, and Ollama are encrypted at rest with symmetric keys.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="w-9 h-9 rounded-lg bg-[#eff6ff] dark:bg-[#0a66c2]/20 text-[#0a66c2] dark:text-[#70b5f9] flex items-center justify-center shrink-0">
                <Database size={18} />
              </div>
              <div>
                <h4 className="text-xs sm:text-sm font-bold text-[#0f172a] dark:text-white">
                  Cloudflare R2 Secure Vault
                </h4>
                <p className="text-xs text-[#64748b] dark:text-[#94a3b8] mt-1">
                  Resumes are stored in private user-partitioned object storage with zero egress fees and presigned URLs.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="w-9 h-9 rounded-lg bg-[#eff6ff] dark:bg-[#0a66c2]/20 text-[#0a66c2] dark:text-[#70b5f9] flex items-center justify-center shrink-0">
                <Cpu size={18} />
              </div>
              <div>
                <h4 className="text-xs sm:text-sm font-bold text-[#0f172a] dark:text-white">
                  100% Free Offline Mode
                </h4>
                <p className="text-xs text-[#64748b] dark:text-[#94a3b8] mt-1">
                  Use our built-in heuristic NLP engine for job parsing, keyword audits, and scoring without any API costs.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <FaqSection />

      {/* Bottom CTA Banner */}
      <section className="py-16 sm:py-20 bg-gradient-to-r from-[#0a66c2] to-[#004e99] text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-2xl sm:text-4xl font-extrabold tracking-tight">
            Ready to Stop Getting Filtered by ATS?
          </h2>
          <p className="text-sm sm:text-base text-blue-100 mt-3 max-w-xl mx-auto leading-relaxed">
            Create your free account in seconds or launch the guest workspace with no sign-up required.
          </p>

          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3.5">
            {currentUser ? (
              <button
                onClick={onGoToDashboard}
                className="w-full sm:w-auto px-6 py-3.5 rounded-xl text-sm font-bold bg-white text-[#0a66c2] hover:bg-blue-50 shadow-md transition-all flex items-center justify-center gap-2"
              >
                <span>Go to Dashboard</span>
                <ArrowRight size={16} />
              </button>
            ) : (
              <button
                onClick={onGetStarted}
                className="w-full sm:w-auto px-6 py-3.5 rounded-xl text-sm font-bold bg-white text-[#0a66c2] hover:bg-blue-50 shadow-md transition-all flex items-center justify-center gap-2"
              >
                <span>Get Started Free</span>
                <ArrowRight size={16} />
              </button>
            )}

            <button
              onClick={onExploreGuest}
              className="w-full sm:w-auto px-6 py-3.5 rounded-xl text-sm font-bold bg-transparent text-white border border-white/40 hover:bg-white/10 transition-all flex items-center justify-center gap-2"
            >
              <span>Try Guest Workspace</span>
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <LandingFooter onOpenPrivacy={onOpenPrivacy} />
    </div>
  );
}
