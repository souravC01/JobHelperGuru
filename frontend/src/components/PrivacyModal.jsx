import React from 'react';
import { ShieldCheck, Lock, Key, Trash2, Database, X } from 'lucide-react';

export default function PrivacyModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm animate-fade-in">
      <div className="relative max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl border border-[#e0e0e0] bg-white p-6 shadow-2xl dark:border-[#374151] dark:bg-[#1f2937]">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#e0e0e0] pb-4 dark:border-[#374151]">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#0a66c2]/10 text-[#0a66c2] dark:bg-[#0a66c2]/20 dark:text-[#70b5f9]">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-[#191919] dark:text-white">Privacy & Data Policy</h2>
              <p className="text-xs text-[#666666] dark:text-[#9ca3af]">How your resumes, keys, and job data are protected</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-[#666666] hover:bg-[#f3f3f3] hover:text-[#191919] dark:text-[#9ca3af] dark:hover:bg-[#374151] dark:hover:text-white"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="mt-5 space-y-4 text-sm text-[#333333] dark:text-[#d1d5db]">
          <div className="rounded-lg border border-[#e5e7eb] bg-[#f9fafb] p-4 dark:border-[#374151] dark:bg-[#111827]/50">
            <div className="flex items-start gap-3">
              <Lock className="mt-0.5 h-5 w-5 shrink-0 text-[#0a66c2] dark:text-[#70b5f9]" />
              <div>
                <h3 className="font-semibold text-[#191919] dark:text-white">Zero Tracking & Strict Account Isolation</h3>
                <p className="mt-1 text-xs leading-relaxed text-[#555555] dark:text-[#9ca3af]">
                  Your uploaded resumes, job applications, and tailored materials are strictly isolated to your authenticated account.
                  We do not sell, license, or monetize your resume data, and we do not run third-party tracking or advertising scripts.
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-[#e5e7eb] bg-[#f9fafb] p-4 dark:border-[#374151] dark:bg-[#111827]/50">
            <div className="flex items-start gap-3">
              <Key className="mt-0.5 h-5 w-5 shrink-0 text-[#057642] dark:text-[#34d399]" />
              <div>
                <h3 className="font-semibold text-[#191919] dark:text-white">BYOK (Bring Your Own Key) & Offline AI</h3>
                <p className="mt-1 text-xs leading-relaxed text-[#555555] dark:text-[#9ca3af]">
                  By default, resume matching and skill extraction use a fast, offline heuristic NLP rule engine that costs $0.00.
                  If you configure your own external AI provider key, it is encrypted server-side with Fernet authenticated encryption
                  and is only ever decrypted to dispatch your specific requests directly to your chosen provider.
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-[#e5e7eb] bg-[#f9fafb] p-4 dark:border-[#374151] dark:bg-[#111827]/50">
            <div className="flex items-start gap-3">
              <Database className="mt-0.5 h-5 w-5 shrink-0 text-[#b24020] dark:text-[#f87171]" />
              <div>
                <h3 className="font-semibold text-[#191919] dark:text-white">Storage Quotas</h3>
                <p className="mt-1 text-xs leading-relaxed text-[#555555] dark:text-[#9ca3af]">
                  To guarantee reliability and maintain free access for all users, accounts are permitted up to 10 stored resumes
                  and 50MB of binary document storage.
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-[#e5e7eb] bg-[#f9fafb] p-4 dark:border-[#374151] dark:bg-[#111827]/50">
            <div className="flex items-start gap-3">
              <Trash2 className="mt-0.5 h-5 w-5 shrink-0 text-[#666666] dark:text-[#9ca3af]" />
              <div>
                <h3 className="font-semibold text-[#191919] dark:text-white">User Control & Permanent Deletion</h3>
                <p className="mt-1 text-xs leading-relaxed text-[#555555] dark:text-[#9ca3af]">
                  You have full ownership of your data. You can delete any resume, document attachment, job record, or configured AI profile
                  at any time from your dashboard. Deleted items are permanently unlinked immediately.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-6 flex justify-end border-t border-[#e0e0e0] pt-4 dark:border-[#374151]">
          <button
            onClick={onClose}
            className="rounded-lg bg-[#0a66c2] px-5 py-2 text-xs font-semibold text-white transition hover:bg-[#004182] focus:outline-none focus:ring-2 focus:ring-[#0a66c2]/50"
          >
            Understood
          </button>
        </div>
      </div>
    </div>
  );
}
