import { useState } from 'react';
import {
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Info,
  Sparkles,
  Plus,
  Quote,
  GraduationCap,
  Check,
  FolderGit2,
  Briefcase,
  X,
  AlertTriangle,
} from 'lucide-react';

const CATEGORY_LABELS = {
  required_skills: 'Required Skills',
  responsibilities: 'Responsibilities',
  relevant_experience: 'Relevant Experience',
  preferred_qualifications: 'Preferred Qualifications',
};

const EVIDENCE_LEVEL_CONFIG = {
  demonstrated: {
    bg: 'bg-[#057642]/10 dark:bg-[#057642]/20',
    border: 'border-[#057642]/30',
    text: 'text-[#057642] dark:text-[#45c586]',
    label: 'Demonstrated (100%)',
    icon: CheckCircle2,
  },
  listed: {
    bg: 'bg-[#0a66c2]/10 dark:bg-[#0a66c2]/20',
    border: 'border-[#0a66c2]/30',
    text: 'text-[#0a66c2] dark:text-[#70b5f9]',
    label: 'Listed (50%)',
    icon: Info,
  },
  learning: {
    bg: 'bg-amber-500/10 dark:bg-amber-500/20',
    border: 'border-amber-500/30',
    text: 'text-amber-600 dark:text-amber-400',
    label: 'Learning (25%)',
    icon: HelpCircle,
  },
  contradicted: {
    bg: 'bg-[#b24020]/10 dark:bg-[#b24020]/20',
    border: 'border-[#b24020]/30',
    text: 'text-[#b24020] dark:text-[#ff8162]',
    label: 'Contradicted (0%)',
    icon: AlertCircle,
  },
  not_evidenced: {
    bg: 'bg-[#666666]/10 dark:bg-[#666666]/20',
    border: 'border-[#666666]/30',
    text: 'text-[#666666] dark:text-[#9aa1b2]',
    label: 'Not evidenced in this resume',
    icon: AlertCircle,
  },
};

export default function MatchEvidenceDetails({
  evaluation,
  resume,
  adoptedSkills = [],
  onRemoveAdoptedSkill = null,
  onSelectKeywordForOptimization = null,
}) {
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedSkills, setSelectedSkills] = useState([]);

  if (!evaluation) {
    return null;
  }

  const categoryScores = evaluation.category_scores || {};
  const requirementResults = evaluation.requirement_results || [];
  const warnings = evaluation.warnings || [];
  const eligibility = evaluation.eligibility;

  // Filtered requirements
  const filteredRequirements = selectedCategory === 'all'
    ? requirementResults
    : requirementResults.filter((rr) => rr.requirement?.category === selectedCategory);

  // Missing requirements (not evidenced or contradicted)
  const missingRequirements = requirementResults.filter((rr) => {
    const ev = rr.evidence?.[0];
    const level = ev?.level?.toLowerCase();
    return !ev || level === 'not_evidenced' || level === 'contradicted';
  });

  const toggleSkill = (skillText) => {
    setSelectedSkills((prev) =>
      prev.includes(skillText) ? prev.filter((s) => s !== skillText) : [...prev, skillText]
    );
  };

  const handleIncorporate = (sectionType) => {
    if (selectedSkills.length === 0 || !onSelectKeywordForOptimization) return;
    onSelectKeywordForOptimization(selectedSkills, resume, sectionType);
  };

  return (
    <div className="space-y-4 pt-2 animate-fade-in text-xs" data-testid="match-evidence-details">
      {/* Processing Warnings Banner */}
      {warnings.length > 0 && (
        <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-800 dark:text-amber-300 space-y-1">
          <div className="flex items-center gap-1.5 font-bold">
            <AlertTriangle size={14} className="text-amber-600 dark:text-amber-400 shrink-0" />
            <span>Processing Notice</span>
          </div>
          <ul className="list-disc list-inside space-y-0.5 text-[11px]">
            {warnings.map((w, idx) => (
              <li key={idx}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Graduation / Education Eligibility */}
      {eligibility && eligibility.is_new_grad_role && (
        <div className="p-3 rounded-lg bg-[#f3f6f8] dark:bg-[#12141a] border border-[#e0e0e0] dark:border-[#2b313c] flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <GraduationCap
              size={15}
              className={
                eligibility.eligible === true
                  ? 'text-[#057642] dark:text-[#45c586]'
                  : eligibility.eligible === false
                  ? 'text-[#b24020] dark:text-[#ff8162]'
                  : 'text-[#666666] dark:text-[#9aa1b2]'
              }
            />
            <div>
              <span className="font-semibold text-[#000000] dark:text-[#f3f6f8]">Education Timeline: </span>
              <span className="text-[#666666] dark:text-[#9aa1b2]">
                {eligibility.status || 'Graduation timeline not detected'}
              </span>
            </div>
          </div>
          <span
            className={`text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded-full shrink-0 self-start sm:self-auto ${
              eligibility.eligible === true
                ? 'bg-[#057642]/10 text-[#057642] dark:text-[#45c586] border border-[#057642]/30'
                : eligibility.eligible === false
                ? 'bg-[#b24020]/10 text-[#b24020] dark:text-[#ff8162] border border-[#b24020]/30'
                : 'bg-[#555555]/10 text-[#555555] dark:text-[#9aa1b2] border border-[#555555]/30'
            }`}
          >
            {eligibility.eligible === true
              ? 'Meets Timeline'
              : eligibility.eligible === false
              ? 'Ineligible'
              : 'Timeline Unknown'}
          </span>
        </div>
      )}

      {/* Category Breakdown Score Bars */}
      {Object.keys(categoryScores).length > 0 && (
        <div className="p-3.5 rounded-lg bg-[#f3f6f8] dark:bg-[#12141a] border border-[#e0e0e0] dark:border-[#2b313c] space-y-2.5">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-[#000000] dark:text-[#f3f6f8]">Category Breakdown</span>
            {evaluation.raw_score && (
              <span className="font-mono text-[11px] text-[#666666] dark:text-[#9aa1b2]">
                Raw: {evaluation.raw_score}%
              </span>
            )}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {Object.entries(categoryScores).map(([catKey, catScore]) => {
              const label = CATEGORY_LABELS[catKey] || catKey;
              const ratio = parseFloat(catScore.coverage_ratio || '0');
              const percent = Math.round(ratio * 100);
              return (
                <div key={catKey} className="space-y-1">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-[#666666] dark:text-[#9aa1b2]">{label}</span>
                    <span className="font-mono font-semibold text-[#000000] dark:text-[#f3f6f8]">
                      {catScore.credited_weight} / {catScore.weight} pts ({percent}%)
                    </span>
                  </div>
                  <div className="w-full bg-[#e0e0e0] dark:bg-[#2b313c] rounded-full h-1.5 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        percent >= 75
                          ? 'bg-[#057642] dark:bg-[#45c586]'
                          : percent >= 40
                          ? 'bg-[#0a66c2] dark:bg-[#70b5f9]'
                          : 'bg-[#b24020] dark:bg-[#ff8162]'
                      }`}
                      style={{ width: `${percent}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* BulletCraft Adopted Skills Preview Alert (does NOT inflate score) */}
      {adoptedSkills.length > 0 && (
        <div className="p-3 rounded-lg bg-[#0a66c2]/10 border border-[#0a66c2]/30 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
          <div className="flex items-center gap-2">
            <Sparkles size={14} className="text-[#0a66c2] shrink-0" />
            <div>
              <span className="font-bold text-[#0a66c2]">BulletCraft Preview ({adoptedSkills.length}): </span>
              <span className="text-[#666666] dark:text-[#9aa1b2]">
                Drafted bullet skills are shown for editing. Save resume to incorporate into score.
              </span>
            </div>
          </div>
          <div className="flex flex-wrap gap-1">
            {adoptedSkills.map((s, idx) => (
              <span
                key={idx}
                className="inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded-full bg-white dark:bg-[#1a1d24] border border-[#0a66c2]/40 text-[#0a66c2]"
              >
                <span>{s}</span>
                {onRemoveAdoptedSkill && (
                  <button
                    type="button"
                    onClick={() => onRemoveAdoptedSkill(s, resume.id)}
                    className="hover:text-[#b24020]"
                    title="Remove preview skill"
                  >
                    <X size={10} />
                  </button>
                )}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Category Filter Tabs */}
      <div className="flex items-center justify-between gap-2 border-b border-[#e0e0e0] dark:border-[#2b313c] pb-2 overflow-x-auto">
        <div className="flex items-center gap-1.5 shrink-0">
          <button
            type="button"
            onClick={() => setSelectedCategory('all')}
            className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
              selectedCategory === 'all'
                ? 'bg-[#0a66c2] text-white'
                : 'text-[#666666] dark:text-[#9aa1b2] hover:bg-[#f3f6f8] dark:hover:bg-[#12141a]'
            }`}
          >
            All Evidence ({requirementResults.length})
          </button>
          {Object.keys(categoryScores).map((catKey) => {
            const count = requirementResults.filter((rr) => rr.requirement?.category === catKey).length;
            if (count === 0) return null;
            return (
              <button
                key={catKey}
                type="button"
                onClick={() => setSelectedCategory(catKey)}
                className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
                  selectedCategory === catKey
                    ? 'bg-[#0a66c2] text-white'
                    : 'text-[#666666] dark:text-[#9aa1b2] hover:bg-[#f3f6f8] dark:hover:bg-[#12141a]'
                }`}
              >
                {CATEGORY_LABELS[catKey] || catKey} ({count})
              </button>
            );
          })}
        </div>

        {missingRequirements.length > 0 && (
          <div className="text-[11px] text-[#666666] dark:text-[#9aa1b2] shrink-0">
            {missingRequirements.length} missing qualifications
          </div>
        )}
      </div>

      {/* Requirement & Evidence Items */}
      {filteredRequirements.length === 0 ? (
        <div className="py-4 text-center text-[#666666] dark:text-[#9aa1b2] italic">
          No requirements in this category.
        </div>
      ) : (
        <div className="space-y-2">
          {filteredRequirements.map((rr, idx) => {
            const req = rr.requirement || {};
            const ev = rr.evidence?.[0];
            const level = (ev?.level || 'not_evidenced').toLowerCase();
            const config = EVIDENCE_LEVEL_CONFIG[level] || EVIDENCE_LEVEL_CONFIG.not_evidenced;
            const LevelIcon = config.icon;
            const isMissing = level === 'not_evidenced' || level === 'contradicted';
            const isSelected = selectedSkills.includes(req.text);

            return (
              <div
                key={req.id || idx}
                className={`p-3 rounded-lg border transition-all ${
                  isMissing
                    ? 'border-[#e0e0e0] dark:border-[#2b313c] bg-white dark:bg-[#1a1d24]'
                    : 'border-[#e0e0e0] dark:border-[#2b313c] bg-[#f3f6f8]/50 dark:bg-[#12141a]/50'
                }`}
              >
                {/* Header: Requirement text + Level Badge */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1.5 mb-1.5">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-xs text-[#000000] dark:text-[#f3f6f8]">
                      {req.text}
                    </span>
                    <span className="text-[10px] text-[#666666] dark:text-[#9aa1b2] font-mono">
                      [{CATEGORY_LABELS[req.category] || req.category}]
                    </span>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold border ${config.bg} ${config.border} ${config.text}`}
                    >
                      <LevelIcon size={11} />
                      <span>{config.label}</span>
                    </span>

                    {/* Button to select for BulletCraft if missing */}
                    {isMissing && onSelectKeywordForOptimization && (
                      <button
                        type="button"
                        onClick={() => toggleSkill(req.text)}
                        className={`inline-flex items-center gap-1 text-[11px] py-0.5 px-2 rounded-full transition-all font-mono ${
                          isSelected
                            ? 'bg-[#0a66c2] text-white border border-[#0a66c2] font-bold'
                            : 'bg-[#b24020]/10 text-[#b24020] dark:text-[#ff8162] border border-[#b24020]/30 hover:bg-[#b24020]/20'
                        }`}
                        title="Select skill to generate high-impact bullet"
                      >
                        {isSelected ? <Check size={10} /> : <Plus size={10} />}
                        <span>{isSelected ? 'Selected' : 'Craft Bullet'}</span>
                      </button>
                    )}
                  </div>
                </div>

                {/* Job Requirement Source Quote */}
                {req.source_quote && (
                  <div className="flex items-start gap-1.5 text-[11px] text-[#666666] dark:text-[#9aa1b2] mt-1 pl-1">
                    <Quote size={11} className="shrink-0 mt-0.5 opacity-60" />
                    <span className="italic">Job requirement: &ldquo;{req.source_quote}&rdquo;</span>
                  </div>
                )}

                {/* Candidate Evidence Quote or Missing Notice */}
                {ev && ev.source_quote && level !== 'not_evidenced' ? (
                  <div className="flex items-start gap-1.5 text-[11px] text-[#057642] dark:text-[#45c586] mt-1 pl-1 font-mono">
                    <Quote size={11} className="shrink-0 mt-0.5 text-[#057642] dark:text-[#45c586]" />
                    <span>Resume evidence: &ldquo;{ev.source_quote}&rdquo;</span>
                  </div>
                ) : (
                  <div className="text-[11px] text-[#666666] dark:text-[#9aa1b2] italic mt-1 pl-1">
                    Not evidenced in this resume
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Bottom Action Bar for Multi-Selected Missing Skills */}
      {selectedSkills.length > 0 && (
        <div className="p-3.5 rounded-lg bg-[#f3f6f8] dark:bg-[#12141a] border border-[#0a66c2]/30 flex flex-col sm:flex-row sm:items-center justify-between gap-3 animate-fade-in shadow-sm">
          <div className="flex items-center gap-2">
            <Sparkles size={15} className="text-[#0a66c2] shrink-0" />
            <div>
              <span className="text-xs font-bold text-[#000000] dark:text-[#f3f6f8]">
                {selectedSkills.length} Missing Skill{selectedSkills.length > 1 ? 's' : ''} Selected:{' '}
              </span>
              <span className="text-xs font-mono text-[#0a66c2] font-semibold">
                {selectedSkills.join(', ')}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <button
              type="button"
              onClick={() => handleIncorporate('project')}
              className="btn-primary-corporate text-xs py-1 px-3"
            >
              <FolderGit2 size={12} />
              <span>Incorporate in Project</span>
            </button>
            <button
              type="button"
              onClick={() => handleIncorporate('work_history')}
              className="btn-secondary-corporate text-xs py-1 px-3"
            >
              <Briefcase size={12} />
              <span>Incorporate in Work</span>
            </button>
            <button
              type="button"
              onClick={() => setSelectedSkills([])}
              className="text-xs text-[#666666] dark:text-[#9aa1b2] hover:text-[#000000] dark:hover:text-[#f3f6f8] px-1"
            >
              Clear
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
