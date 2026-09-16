import { Briefcase } from 'lucide-react';

export default function LandingFooter({ onOpenPrivacy }) {
  return (
    <footer className="border-t border-[#e0e0e0] dark:border-[#374151] bg-white dark:bg-[#111827] py-12 text-xs text-[#64748b] dark:text-[#94a3b8] transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-6">
        {/* Brand info */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-md bg-[#0a66c2] flex items-center justify-center shadow-sm text-white">
            <Briefcase size={18} />
          </div>
          <div>
            <span className="font-bold text-sm text-[#0f172a] dark:text-white">JobHelperGuru</span>
            <p className="text-[11px] text-[#64748b] dark:text-[#94a3b8]">
              Built for smarter, tailored job applications &amp; ATS optimization.
            </p>
          </div>
        </div>

        {/* Links and privacy */}
        <div className="flex flex-wrap items-center justify-center gap-4 text-xs">
          <a href="#demo" className="hover:text-[#0a66c2] dark:hover:text-[#70b5f9] transition-colors">
            Interactive Demo
          </a>
          <span className="text-[#cbd5e1] dark:text-[#475569]">•</span>
          <a href="#features" className="hover:text-[#0a66c2] dark:hover:text-[#70b5f9] transition-colors">
            Features
          </a>
          <span className="text-[#cbd5e1] dark:text-[#475569]">•</span>
          <a href="#how-it-works" className="hover:text-[#0a66c2] dark:hover:text-[#70b5f9] transition-colors">
            How It Works
          </a>
          <span className="text-[#cbd5e1] dark:text-[#475569]">•</span>
          <button
            onClick={onOpenPrivacy}
            className="font-semibold text-[#0a66c2] dark:text-[#70b5f9] hover:underline"
          >
            Privacy &amp; Terms
          </button>
        </div>
      </div>

      <div className="mt-8 pt-6 border-t border-[#f1f5f9] dark:border-[#1f2937] text-center text-[11px] text-[#94a3b8]">
        &copy; {new Date().getFullYear()} JobHelperGuru. All rights reserved.
      </div>
    </footer>
  );
}
