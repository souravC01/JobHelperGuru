import { Briefcase, ArrowRight } from 'lucide-react';
import ThemeToggle from '../ThemeToggle';

export default function LandingNav({
  currentUser,
  onSignIn,
  onGetStarted,
  onGoToDashboard,
  theme,
  onToggleTheme,
}) {
  return (
    <header className="sticky top-0 z-40 bg-white dark:bg-[#1a1d24] border-b border-[#e0e0e0] dark:border-[#2b313c] transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Brand Logo */}
        <a
          href="#"
          className="flex items-center gap-3 group focus:outline-none"
          aria-label="JobHelperGuru Home"
        >
          <div className="w-9 h-9 rounded-md bg-[#0a66c2] flex items-center justify-center shadow-sm group-hover:scale-105 transition-transform">
            <Briefcase size={20} className="text-white" />
          </div>
          <div>
            <span className="font-bold text-base tracking-tight text-[#000000] dark:text-[#f3f6f8]">
              JobHelperGuru
            </span>
            <p className="text-[11px] text-[#666666] dark:text-[#9aa1b2] hidden sm:block">
              AI Job Tailoring &amp; BulletCraft Engine
            </p>
          </div>
        </a>

        {/* Anchor Links (Desktop) */}
        <nav className="hidden md:flex items-center gap-6 text-xs font-semibold text-[#666666] dark:text-[#9aa1b2]">
          <a href="#demo" className="hover:text-[#000000] dark:hover:text-[#f3f6f8] transition-colors">
            Interactive Demo
          </a>
          <a href="#features" className="hover:text-[#000000] dark:hover:text-[#f3f6f8] transition-colors">
            Features
          </a>
          <a href="#how-it-works" className="hover:text-[#000000] dark:hover:text-[#f3f6f8] transition-colors">
            How It Works
          </a>
          <a href="#security" className="hover:text-[#000000] dark:hover:text-[#f3f6f8] transition-colors">
            Security &amp; BYOK
          </a>
          <a href="#faq" className="hover:text-[#000000] dark:hover:text-[#f3f6f8] transition-colors">
            FAQ
          </a>
        </nav>

        {/* Action Controls */}
        <div className="flex items-center gap-2.5">
          <ThemeToggle theme={theme} onToggle={onToggleTheme} />

          {currentUser ? (
            <button
              onClick={onGoToDashboard}
              className="btn-primary-corporate text-xs"
            >
              <span>Go to Dashboard</span>
              <ArrowRight size={14} />
            </button>
          ) : (
            <div className="flex items-center gap-2">
              <button
                onClick={onSignIn}
                className="px-3.5 py-2 text-xs font-semibold text-[#0a66c2] dark:text-[#70b5f9] hover:bg-[#f3f6f8] dark:hover:bg-[#2b313c] rounded-full transition-colors"
              >
                Sign In
              </button>
              <button
                onClick={onGetStarted}
                className="btn-primary-corporate text-xs"
              >
                <span>Get Started Free</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
