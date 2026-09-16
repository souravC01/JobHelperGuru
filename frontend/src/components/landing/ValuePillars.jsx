import {
  FileSearch,
  ShieldCheck,
  Mail,
  KeyRound,
  CheckCircle2,
  Lock,
  Cpu,
  Database,
  ExternalLink,
} from 'lucide-react';

export default function ValuePillars() {
  const pillars = [
    {
      icon: FileSearch,
      tag: 'Universal Parser',
      title: 'Multi-Format Job Scraping',
      description:
        'Instant deep scraping from Workday CXS endpoints, Greenhouse, Lever, SmartRecruiters, or raw text. Automatically extracts salary ranges, required vs. preferred tech stacks, and college new-grad eligibility windows.',
      badges: ['Workday CXS', 'Greenhouse', 'Lever', 'SmartRecruiters'],
    },
    {
      icon: ShieldCheck,
      tag: 'Zero Hallucination',
      title: 'Context-Aware Fact Verification',
      description:
        'Never fabricates false experience. The engine cross-checks candidate resume history before suggesting skill additions. Unverified skills are steered into honest open-source and academic portfolio project bullets.',
      badges: ['Evidence Verification', 'BulletCraft Formula', 'Honest Matching'],
    },
    {
      icon: Mail,
      tag: 'High Conversion',
      title: 'Recruiter Outreach Generator',
      description:
        'Turns top-matching resumes and job requirements into tailored recruiter pitches: cold outreach emails with compelling subject lines, LinkedIn InMails strictly under 300 characters, and portal cover letter opening hooks.',
      badges: ['Cold Emails', 'LinkedIn InMails <300ch', 'Cover Letter Hooks'],
    },
    {
      icon: KeyRound,
      tag: 'Privacy First',
      title: 'Enterprise Security & BYOK',
      description:
        'Bring Your Own Keys (Groq, Nvidia NIM, OpenAI, Ollama) encrypted with AES-256 Fernet at rest, or use our 100% free built-in Offline Heuristic NLP Engine. Resumes are protected in private Cloudflare R2 vaults with presigned URLs.',
      badges: ['AES-256 Fernet', 'Cloudflare R2 Vault', '100% Free Offline NLP'],
    },
  ];

  return (
    <section id="features" className="py-16 sm:py-24 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="text-center max-w-3xl mx-auto mb-14">
        <span className="text-xs font-bold uppercase tracking-widest text-[#0a66c2] dark:text-[#70b5f9] bg-[#eff6ff] dark:bg-[#0a66c2]/10 px-3 py-1 rounded-full border border-[#bfdbfe] dark:border-[#0a66c2]/30">
          Core Capabilities
        </span>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-[#0f172a] dark:text-white mt-3 tracking-tight">
          Engineered for Modern Technical Applicants
        </h2>
        <p className="text-sm text-[#64748b] dark:text-[#94a3b8] mt-3 leading-relaxed">
          Everything you need to beat automated ATS filters, tailor resumes at scale, and track your complete application journey without compromising security.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 sm:gap-8">
        {pillars.map((pillar, idx) => {
          const Icon = pillar.icon;
          return (
            <div
              key={idx}
              className="p-7 rounded-2xl border border-[#e0e0e0] dark:border-[#374151] bg-white dark:bg-[#1a2234] shadow-sm hover:shadow-md transition-all hover:border-[#0a66c2]/40 group flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 rounded-xl bg-[#f0f7ff] dark:bg-[#0a66c2]/20 border border-[#bfdbfe] dark:border-[#0a66c2]/30 flex items-center justify-center text-[#0a66c2] dark:text-[#70b5f9] group-hover:scale-105 transition-transform">
                    <Icon size={22} />
                  </div>
                  <span className="text-[11px] font-bold text-[#0a66c2] dark:text-[#70b5f9] bg-[#eff6ff] dark:bg-[#0a66c2]/10 px-2.5 py-0.5 rounded-full">
                    {pillar.tag}
                  </span>
                </div>

                <h3 className="text-lg font-bold text-[#0f172a] dark:text-white mb-2">
                  {pillar.title}
                </h3>
                <p className="text-xs sm:text-sm text-[#64748b] dark:text-[#94a3b8] leading-relaxed mb-6">
                  {pillar.description}
                </p>
              </div>

              <div className="flex flex-wrap gap-2 pt-4 border-t border-[#f1f5f9] dark:border-[#334155]">
                {pillar.badges.map((b, bIdx) => (
                  <span
                    key={bIdx}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-medium bg-[#f8fafc] dark:bg-[#111827] text-[#475569] dark:text-[#cbd5e1] border border-[#e2e8f0] dark:border-[#334155]"
                  >
                    <CheckCircle2 size={11} className="text-[#057642] dark:text-[#4ade80]" />
                    <span>{b}</span>
                  </span>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
