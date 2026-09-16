import { Briefcase } from 'lucide-react';

export default function LandingFooter({ onOpenPrivacy }) {
  return (
    <footer className="border-t border-[#e0e0e0] dark:border-[#2b313c] bg-white dark:bg-[#1a1d24] py-10 text-xs text-[#666666] dark:text-[#9aa1b2] transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-6">
        {/* Brand info */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-md bg-[#0a66c2] flex items-center justify-center shadow-sm text-white">
            <Briefcase size={18} />
          </div>
          <div>
            <span className="font-bold text-sm text-[#000000] dark:text-[#f3f6f8]">JobHelperGuru</span>
            <p className="text-[11px] text-[#666666] dark:text-[#9aa1b2]">
              Built for smarter, tailored job applications &amp; ATS optimization.
            </p>
          </div>
        </div>

        {/* Links and privacy */}
        <div className="flex flex-wrap items-center justify-center gap-4 text-xs">
          <a href="#demo" className="hover:text-[#000000] dark:hover:text-[#f3f6f8] transition-colors">
            Interactive Demo
          </a>
          <span className="text-[#e0e0e0] dark:text-[#2b313c]">•</span>
          <a href="#features" className="hover:text-[#000000] dark:hover:text-[#f3f6f8] transition-colors">
            Features
          </a>
          <span className="text-[#e0e0e0] dark:text-[#2b313c]">•</span>
          <a href="#how-it-works" className="hover:text-[#000000] dark:hover:text-[#f3f6f8] transition-colors">
            How It Works
          </a>
          <span className="text-[#e0e0e0] dark:text-[#2b313c]">•</span>
          <button
            onClick={onOpenPrivacy}
            className="font-semibold text-[#0a66c2] dark:text-[#70b5f9] hover:underline"
          >
            Privacy &amp; Terms
          </button>
        </div>
      </div>

      <div className="mt-8 pt-6 border-t border-[#e0e0e0] dark:border-[#2b313c] text-center text-[11px] text-[#666666] dark:text-[#9aa1b2]">
        &copy; {new Date().getFullYear()} JobHelperGuru. All rights reserved.
      </div>
    </footer>
  );
}
