import { FileSearch, Sparkles, FileSpreadsheet, ArrowRight } from 'lucide-react';

export default function HowItWorks() {
  const steps = [
    {
      number: '01',
      icon: FileSearch,
      title: 'Parse the True Requirements',
      description:
        'Drop in a job posting URL or raw description. JobHelperGuru automatically extracts standardized job titles, compensation packages, required vs. preferred tech stacks, and hidden ATS keyword indexes.',
    },
    {
      number: '02',
      icon: Sparkles,
      title: 'Optimize Bullets & Pick the Best Resume',
      description:
        'Audit your resume library to select the highest-scoring resume. Use the BulletCraft Framework to transform weak bullet points into quantifiable achievements, and generate tailored outreach pitches in seconds.',
    },
    {
      number: '03',
      icon: FileSpreadsheet,
      title: 'Track Deadlines & Export to Excel',
      description:
        'Seamlessly progress applications across Kanban stages (Wishlist, Applied, Interviewing, Offered). Get automatic follow-up reminders and export clean, styled Excel spreadsheets for offline recordkeeping.',
    },
  ];

  return (
    <section id="how-it-works" className="py-16 sm:py-24 bg-[#f3f6f8] dark:bg-[#0f1115] border-y border-[#e0e0e0] dark:border-[#2b313c] transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-14">
          <span className="text-xs font-bold uppercase tracking-widest text-[#0a66c2] dark:text-[#70b5f9] bg-white dark:bg-[#1a1d24] px-3 py-1 rounded-full border border-[#e0e0e0] dark:border-[#2b313c]">
            3-Step Workflow
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-[#000000] dark:text-[#f3f6f8] mt-3 tracking-tight">
            How JobHelperGuru Accelerates Your Hunt
          </h2>
          <p className="text-sm text-[#666666] dark:text-[#9aa1b2] mt-3 leading-relaxed">
            From discovering a posting to negotiating an offer, streamline every phase of your job search in minutes.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {steps.map((step, idx) => {
            const Icon = step.icon;
            return (
              <div
                key={idx}
                className="card-corporate relative p-6 sm:p-7 rounded-lg bg-white dark:bg-[#1a1d24] border border-[#e0e0e0] dark:border-[#2b313c] flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-5">
                    <span className="text-3xl font-black text-[#c1c6d4] dark:text-[#404856] font-mono">
                      {step.number}
                    </span>
                    <div className="w-10 h-10 rounded-md bg-[#f3f6f8] dark:bg-[#0f1115] border border-[#e0e0e0] dark:border-[#2b313c] text-[#0a66c2] dark:text-[#70b5f9] flex items-center justify-center">
                      <Icon size={18} />
                    </div>
                  </div>

                  <h3 className="text-base font-bold text-[#000000] dark:text-[#f3f6f8] mb-2">
                    {step.title}
                  </h3>
                  <p className="text-xs sm:text-sm text-[#666666] dark:text-[#9aa1b2] leading-relaxed">
                    {step.description}
                  </p>
                </div>

                {idx < steps.length - 1 && (
                  <div className="hidden lg:block absolute -right-4 top-1/2 -translate-y-1/2 text-[#c1c6d4] dark:text-[#404856] z-10">
                    <ArrowRight size={20} />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
