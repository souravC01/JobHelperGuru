import { useState } from 'react';
import { ChevronDown, HelpCircle } from 'lucide-react';

export default function FaqSection() {
  const [openIndex, setOpenIndex] = useState(null);

  const faqs = [
    {
      q: 'Is JobHelperGuru free to use?',
      a: 'Yes! JobHelperGuru includes a 100% free offline heuristic NLP mode that works immediately with zero API keys required. If you want ultra-fast cloud model inference, you can optionally bring your own API key for Groq, Nvidia NIM, OpenAI, or connect a local Ollama instance.',
    },
    {
      q: 'What is the BulletCraft Framework?',
      a: 'The BulletCraft Framework is an accomplishment engineering formula: Accomplished [X], measured by [Y], by doing [Z]. Instead of listing duties (e.g., "Worked on APIs"), it articulates measurable scale, impact, and tooling (e.g., "Engineered 14 resilient FastAPI microservices handling 2.4M daily requests, cutting p99 latency by 38% using Redis").',
    },
    {
      q: 'Are my resumes and credentials secure?',
      a: 'Absolutely. Your private API keys are encrypted at rest using AES-256 Fernet authenticated symmetric encryption. Resumes are isolated per user in private Cloudflare R2 object storage and retrieved strictly via time-limited presigned URLs. No third-party data selling or public indexing.',
    },
    {
      q: 'Can I export my pipeline data?',
      a: 'Yes. With one click, you can download a formatted, styled Excel (.xlsx) spreadsheet complete with status indicators, interview round notes, and application links for offline archiving and audit tracking.',
    },
  ];

  return (
    <section id="faq" className="py-16 sm:py-24 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="text-center mb-12">
        <span className="text-xs font-bold uppercase tracking-widest text-[#0a66c2] dark:text-[#70b5f9] bg-[#eff6ff] dark:bg-[#0a66c2]/10 px-3 py-1 rounded-full border border-[#bfdbfe] dark:border-[#0a66c2]/30">
          Frequently Asked Questions
        </span>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-[#0f172a] dark:text-white mt-3 tracking-tight">
          Got Questions? We Have Answers.
        </h2>
      </div>

      <div className="space-y-4">
        {faqs.map((faq, idx) => {
          const isOpen = openIndex === idx;
          return (
            <div
              key={idx}
              className="rounded-xl border border-[#e2e8f0] dark:border-[#334155] bg-white dark:bg-[#1a2234] overflow-hidden transition-all shadow-sm"
            >
              <button
                onClick={() => setOpenIndex(isOpen ? null : idx)}
                className="w-full px-6 py-4 text-left flex items-center justify-between gap-4 focus:outline-none"
                aria-expanded={isOpen}
              >
                <span className="text-sm sm:text-base font-bold text-[#0f172a] dark:text-white">
                  {faq.q}
                </span>
                <ChevronDown
                  size={18}
                  className={`text-[#64748b] dark:text-[#94a3b8] transition-transform duration-200 shrink-0 ${
                    isOpen ? 'rotate-180 text-[#0a66c2] dark:text-[#70b5f9]' : ''
                  }`}
                />
              </button>

              {isOpen && (
                <div className="px-6 pb-5 pt-1 text-xs sm:text-sm text-[#64748b] dark:text-[#94a3b8] leading-relaxed border-t border-[#f1f5f9] dark:border-[#334155]">
                  {faq.a}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
