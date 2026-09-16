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
        <span className="text-xs font-bold uppercase tracking-widest text-[#0a66c2] dark:text-[#70b5f9] bg-white dark:bg-[#1a1d24] px-3 py-1 rounded-full border border-[#e0e0e0] dark:border-[#2b313c]">
          Core Capabilities
        </span>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-[#000000] dark:text-[#f3f6f8] mt-3 tracking-tight">
          Engineered for Modern Technical Applicants
        </h2>
        <p className="text-sm text-[#666666] dark:text-[#9aa1b2] mt-3 leading-relaxed">
          Everything you need to beat automated ATS filters, tailor resumes at scale, and track your complete application journey without compromising security.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 sm:gap-8">
        {pillars.map((pillar, idx) => {
          const Icon = pillar.icon;
          return (
            <div
              key={idx}
              className="card-corporate p-6 sm:p-7 rounded-lg border border-[#e0e0e0] dark:border-[#2b313c] bg-white dark:bg-[#1a1d24] hover:border-[#c1c6d4] dark:hover:border-[#404856] flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="w-10 h-10 rounded-md bg-[#f3f6f8] dark:bg-[#0f1115] border border-[#e0e0e0] dark:border-[#2b313c] flex items-center justify-center text-[#0a66c2] dark:text-[#70b5f9] group-hover:scale-105 transition-transform">
                    <Icon size={20} />
                  </div>
                  <span className="text-[11px] font-bold text-[#0a66c2] dark:text-[#70b5f9] bg-[#f3f6f8] dark:bg-[#0f1115] border border-[#e0e0e0] dark:border-[#2b313c] px-2.5 py-0.5 rounded-full">
                    {pillar.tag}
                  </span>
                </div>

                <h3 className="text-lg font-bold text-[#000000] dark:text-[#f3f6f8] mb-2">
                  {pillar.title}
                </h3>
                <p className="text-xs sm:text-sm text-[#666666] dark:text-[#9aa1b2] leading-relaxed mb-6">
                  {pillar.description}
                </p>
              </div>

              <div className="flex flex-wrap gap-2 pt-4 border-t border-[#e0e0e0] dark:border-[#2b313c]">
                {pillar.badges.map((b, bIdx) => (
                  <span
                    key={bIdx}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-medium bg-[#f3f6f8] dark:bg-[#0f1115] text-[#666666] dark:text-[#9aa1b2] border border-[#e0e0e0] dark:border-[#2b313c]"
                  >
                    <CheckCircle2 size={11} className="text-[#057642] dark:text-[#45c586]" />
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
