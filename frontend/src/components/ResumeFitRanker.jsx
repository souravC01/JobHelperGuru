import { useState, useEffect, useRef } from 'react';
import {
  Crown,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Wand2,
  Loader2,
  AlertCircle,
  GraduationCap,
} from 'lucide-react';
import { evaluateResumes, matchResumes } from '../api/client';
import MatchEvidenceDetails from './MatchEvidenceDetails';

export default function ResumeFitRanker({
  currentJob,
  resumes = [],
  adoptedSkillsMap = {},
  refreshKey = 0,
  onAdoptSkills = null,
  onRemoveAdoptedSkill = null,
  onSelectKeywordForOptimization,
  onBestResumeSelected,
  onOpenBulletOptimizer,
  onAiError,
}) {
  const [evaluations, setEvaluations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedId, setExpandedId] = useState(null);
  const [needsJobReanalysis, setNeedsJobReanalysis] = useState(false);

  const requestIdRef = useRef(0);
  const abortControllerRef = useRef(null);

  const runEvaluation = async (isFresh = false) => {
    if (!currentJob || resumes.length === 0) return;

    const jobText = currentJob?.raw_text || currentJob?.text || (typeof currentJob === 'string' ? currentJob : '');

    // Fall back to legacy matchResumes if no full job text is present but analysis fields exist
    if (!jobText || !jobText.trim()) {
      if (currentJob?.analysis || currentJob?.title || currentJob?.required_skills) {
        return runLegacyMatch();
      }
      setNeedsJobReanalysis(true);
      return;
    }
    setNeedsJobReanalysis(false);

    // Cancel prior in-flight request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    const currentRequestId = ++requestIdRef.current;
    setLoading(true);
    setError(null);

    try {
      const resumeIds = resumes.map((r) => r.id);
      const batch = await evaluateResumes(jobText, resumeIds, {
        fresh: isFresh,
        signal: abortController.signal,
      });

      // Guard against race conditions and out-of-order responses
      if (currentRequestId !== requestIdRef.current) return;

      const evals = batch?.evaluations || [];
      setEvaluations(evals);

      // Downstream best resume selection
      if (evals.length > 0) {
        // Select stable first tied top-match
        const topEval = evals.find((e) => e.rank === 1 && (e.match_score || 0) > 0);
        if (topEval) {
          const matching = resumes.find((r) => r.id === topEval.resume_id) || null;
          if (onBestResumeSelected) onBestResumeSelected(matching);
        } else {
          // Zero-scores or unscorable batches clear stale selection
          if (onBestResumeSelected) onBestResumeSelected(null);
        }
        // Expand first resume by default
        if (evals[0]?.resume_id) {
          setExpandedId(evals[0].resume_id);
        }
      } else {
        if (onBestResumeSelected) onBestResumeSelected(null);
      }
    } catch (err) {
      if (err.name === 'AbortError') return;
      if (currentRequestId !== requestIdRef.current) return;
      console.error('Failed to evaluate resumes:', err);
      setError(err.message || 'Evaluation failed.');
      if (onBestResumeSelected) onBestResumeSelected(null);
      if (onAiError && (err.canSwitchOffline || err.status === 502)) {
        onAiError(err, () => runEvaluation(true));
      }
    } finally {
      if (currentRequestId === requestIdRef.current) {
        setLoading(false);
      }
    }
  };

  const runLegacyMatch = async () => {
    const currentRequestId = ++requestIdRef.current;
    setLoading(true);
    setError(null);

    try {
      const jobPayload = currentJob?.analysis || currentJob;
      const results = await matchResumes({ job: jobPayload, resumes });
      if (currentRequestId !== requestIdRef.current) return;

      // Adapt legacy response to evaluation format
      const adapted = (results || []).map((r, idx) => ({
        resume_id: r.resume_id,
        resume_name: r.resume_name,
        match_score: r.match_score,
        rank: idx + 1,
        is_top_match: !!(r.is_best_fit && r.match_score > 0),
        status: 'complete',
        category_scores: {
          required_skills: {
            weight: 100,
            credited_weight: `${r.match_score}.00`,
            coverage_ratio: `${r.match_score / 100}`,
          },
        },
        requirement_results: (r.matched_keywords || []).map((k) => ({
          requirement: { id: k, text: k, category: 'required_skills' },
          evidence: [{ level: 'demonstrated', source_quote: k }],
        })).concat(
          (r.missing_keywords || []).map((k) => ({
            requirement: { id: k, text: k, category: 'required_skills' },
            evidence: [{ level: 'not_evidenced', source_quote: '' }],
          }))
        ),
        eligibility: {
          is_new_grad_role: r.is_new_grad_role,
          eligible: r.new_grad_eligible,
          status: r.graduation_status,
          graduation_date: r.graduation_date,
        },
        is_legacy: true,
        fit_summary: r.fit_summary,
      }));

      setEvaluations(adapted);
      if (adapted.length > 0) {
        setExpandedId(adapted[0].resume_id);
        if (onBestResumeSelected) {
          const matching = resumes.find((res) => res.id === adapted[0].resume_id) || null;
          onBestResumeSelected(matching);
        }
      }
    } catch (err) {
      if (currentRequestId !== requestIdRef.current) return;
      console.error('Failed to rank resumes (legacy fallback):', err);
      setError(err.message || 'Legacy match failed.');
      if (onAiError && (err.canSwitchOffline || err.status === 502)) {
        onAiError(err, () => runLegacyMatch());
      }
    } finally {
      if (currentRequestId === requestIdRef.current) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    if (currentJob && resumes.length > 0) {
      runEvaluation();
    }
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [
    currentJob?.raw_text,
    currentJob?.text,
    currentJob?.id,
    currentJob?.title,
    resumes.map((r) => `${r.id}:${r.updated_at || r.content?.length || 0}`).join(','),
    refreshKey,
  ]);

  if (!currentJob || resumes.length === 0) {
    return null;
  }

  // Count rank frequency to display tie badges
  const rankCounts = {};
  evaluations.forEach((e) => {
    if (e.rank != null) {
      rankCounts[e.rank] = (rankCounts[e.rank] || 0) + 1;
    }
  });

  // Sort displayed cards according to evaluations, placing unranked/missing at the end
  const sortedResumes = [...resumes].sort((a, b) => {
    const evalA = evaluations.find((e) => e.resume_id === a.id);
    const evalB = evaluations.find((e) => e.resume_id === b.id);
    const rankA = evalA?.rank ?? 9999;
    const rankB = evalB?.rank ?? 9999;
    if (rankA !== rankB) return rankA - rankB;
    return a.id.localeCompare(b.id);
  });

  return (
    <div className="card-corporate p-6 bg-white dark:bg-[#1a1d24] border border-[#e0e0e0] dark:border-[#2b313c] rounded-lg space-y-5 animate-fade-in" data-testid="resume-fit-ranker">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
        <div>
          <h3 className="text-base font-bold text-[#000000] dark:text-[#f3f6f8] flex items-center gap-2 tracking-tight">
            <Crown className="text-[#0a66c2]" size={18} />
            <span>Resume Best-Fit & Evidence-Based Alignment</span>
          </h3>
          <p className="text-xs text-[#666666] dark:text-[#9aa1b2] mt-0.5">
            Scores candidate resumes deterministically from verified job requirements and candidate evidence.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={() => {
              if (!onOpenBulletOptimizer) return;
              const job = currentJob.analysis || currentJob;
              const skills = job.required_skills?.length > 0
                ? job.required_skills
                : (job.ats_keywords?.length > 0 ? job.ats_keywords.slice(0, 3) : ['Key Qualification']);
              onOpenBulletOptimizer(skills);
            }}
            className="btn-secondary-corporate text-xs"
            title="Craft high-impact resume bullets with BulletCraft"
          >
            <Wand2 size={13} />
            <span>BulletCraft</span>
          </button>
          <button
            type="button"
            onClick={() => runEvaluation(true)}
            disabled={loading}
            className="btn-secondary-corporate text-xs"
          >
            {loading ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}
            <span>Re-evaluate</span>
          </button>
        </div>
      </div>

      {needsJobReanalysis && (
        <div className="p-3.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-800 dark:text-amber-300 text-xs flex items-center gap-2">
          <AlertCircle size={16} className="shrink-0 text-amber-600 dark:text-amber-400" />
          <span>
            The current job record has no source text available for requirement evidence matching. Please re-analyze the job description.
          </span>
        </div>
      )}

      {error && (
        <div className="p-3.5 rounded-lg bg-[#b24020]/10 border border-[#b24020]/30 text-[#b24020] dark:text-[#ff8162] text-xs flex items-center gap-2">
          <AlertCircle size={16} className="shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="py-12 text-center text-xs text-[#666666] dark:text-[#9aa1b2] flex flex-col items-center justify-center gap-3">
          <Loader2 size={22} className="animate-spin text-[#0a66c2]" />
          <span className="font-mono">Extracting requirements, matching evidence quotes, and scoring alignment...</span>
        </div>
      ) : (
        <div className="space-y-4">
          {sortedResumes.map((resume) => {
            const evaluation = evaluations.find((e) => e.resume_id === resume.id);
            const isExpanded = expandedId === resume.id;
            const adoptedSkills = (adoptedSkillsMap && adoptedSkillsMap[resume.id]) || [];

            const isUnranked = !evaluation || evaluation.status !== 'complete' || evaluation.match_score == null;
            const isTie = evaluation?.rank != null && (rankCounts[evaluation.rank] > 1);
            const isTopMatch = !isUnranked && evaluation.is_top_match && (evaluation.match_score || 0) > 0;
            const score = evaluation?.match_score;

            return (
              <div
                key={resume.id}
                className={`card-corporate p-5 transition-all bg-white dark:bg-[#1a1d24] rounded-lg ${
                  isTopMatch
                    ? 'border-2 border-[#0a66c2] shadow-sm'
                    : 'border border-[#e0e0e0] dark:border-[#2b313c]'
                }`}
                data-testid={`resume-card-${resume.id}`}
              >
                {/* Header Row */}
                <div
                  onClick={() => setExpandedId(isExpanded ? null : resume.id)}
                  className="flex items-center justify-between gap-4 cursor-pointer select-none"
                >
                  <div className="flex items-center gap-3.5">
                    {/* Rank Badge */}
                    <div
                      className={`min-w-8 h-8 px-2 rounded-full flex items-center justify-center text-xs font-mono font-bold ${
                        isTopMatch
                          ? 'bg-[#0a66c2] text-white shadow-sm'
                          : isUnranked
                          ? 'bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/30'
                          : 'bg-[#f3f6f8] dark:bg-[#12141a] text-[#000000] dark:text-[#f3f6f8] border border-[#e0e0e0] dark:border-[#2b313c]'
                      }`}
                    >
                      {isUnranked
                        ? 'Unranked'
                        : isTie
                        ? `Rank #${evaluation.rank} Tie`
                        : `#${evaluation.rank}`}
                    </div>

                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-bold text-sm text-[#000000] dark:text-[#f3f6f8]">
                          {resume.name}
                        </span>
                        {isTopMatch && (
                          <span className="badge-corporate bg-[#057642]/10 dark:bg-[#057642]/20 border border-[#057642]/25 text-[#057642] dark:text-[#45c586] text-[10px] py-0.5 font-bold">
                            {isTie ? 'Rank #1 Tie - Top Fit' : 'Top Fit'}
                          </span>
                        )}
                        {adoptedSkills.length > 0 && (
                          <span
                            className="badge-corporate bg-[#0a66c2]/10 border border-[#0a66c2]/30 text-[#0a66c2] dark:text-[#70b5f9] text-[10px] py-0.5 px-1.5 font-semibold"
                            title="Adopted in BulletCraft preview. Save resume to update backend score."
                          >
                            +{adoptedSkills.length} in preview
                          </span>
                        )}
                      </div>

                      {/* Eligibility Summary in Header */}
                      {evaluation?.eligibility?.is_new_grad_role && (
                        <div className="flex items-center gap-1.5 mt-1">
                          {evaluation.eligibility.eligible === true && (
                            <span className="badge-corporate bg-[#057642]/10 border border-[#057642]/25 text-[#057642] dark:text-[#45c586] text-[10px] py-0.5 px-2 flex items-center gap-1 font-semibold">
                              <GraduationCap size={12} className="text-[#057642] dark:text-[#45c586]" />
                              <span>New Grad Eligible ({evaluation.eligibility.status})</span>
                            </span>
                          )}
                          {evaluation.eligibility.eligible === false && (
                            <span className="badge-corporate bg-[#b24020]/10 border border-[#b24020]/25 text-[#b24020] dark:text-[#ff8162] text-[10px] py-0.5 px-2 flex items-center gap-1 font-semibold">
                              <AlertTriangle size={12} className="text-[#b24020] dark:text-[#ff8162]" />
                              <span>Timeline Ineligible ({evaluation.eligibility.status || 'Outside window'})</span>
                            </span>
                          )}
                          {(evaluation.eligibility.eligible === null || evaluation.eligibility.eligible === undefined) && (
                            <span className="badge-corporate bg-[#555555]/10 border border-[#555555]/25 text-[#555555] dark:text-[#9aa1b2] text-[10px] py-0.5 px-2 flex items-center gap-1 font-semibold">
                              <GraduationCap size={12} className="text-[#666666] dark:text-[#9aa1b2]" />
                              <span>Timeline Unknown ({evaluation.eligibility.status || 'Graduation date not detected'})</span>
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Progress Gauge */}
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className="flex items-center justify-end gap-1.5 font-mono">
                        {isUnranked ? (
                          <span className="text-xs text-amber-700 dark:text-amber-300 font-semibold">
                            Needs Review
                          </span>
                        ) : (
                          <span
                            className={`text-base font-bold ${
                              score >= 80
                                ? 'text-[#057642] dark:text-[#45c586]'
                                : score >= 60
                                ? 'text-[#0a66c2] dark:text-[#70b5f9]'
                                : 'text-[#b24020] dark:text-[#ff8162]'
                            }`}
                          >
                            {score}%
                          </span>
                        )}
                      </div>

                      {!isUnranked && (
                        <div className="w-28 bg-[#e0e0e0] dark:bg-[#2b313c] rounded-full h-1.5 overflow-hidden mt-1.5">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${
                              score >= 80
                                ? 'bg-[#057642] dark:bg-[#45c586]'
                                : score >= 60
                                ? 'bg-[#0a66c2] dark:bg-[#70b5f9]'
                                : 'bg-[#b24020] dark:bg-[#ff8162]'
                            }`}
                            style={{ width: `${score}%` }}
                          />
                        </div>
                      )}
                    </div>

                    <button
                      type="button"
                      className="text-[#666666] dark:text-[#9aa1b2] hover:text-[#000000] dark:hover:text-[#f3f6f8] p-1 transition-colors"
                      aria-label="Toggle details"
                    >
                      {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </button>
                  </div>
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="mt-4 pt-4 border-t border-[#e0e0e0] dark:border-[#2b313c]">
                    {isUnranked ? (
                      <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/30 text-xs space-y-2 text-amber-900 dark:text-amber-200">
                        <div className="flex items-center gap-2 font-bold">
                          <AlertTriangle size={15} className="text-amber-600 dark:text-amber-400" />
                          <span>Evaluation Incomplete</span>
                        </div>
                        <p>
                          This resume could not be scored automatically against the job requirements.
                        </p>
                        {evaluation?.warnings?.length > 0 && (
                          <ul className="list-disc list-inside space-y-1 text-[11px] opacity-90">
                            {evaluation.warnings.map((w, i) => (
                              <li key={i}>{w}</li>
                            ))}
                          </ul>
                        )}
                      </div>
                    ) : (
                      <MatchEvidenceDetails
                        evaluation={evaluation}
                        resume={resume}
                        adoptedSkills={adoptedSkills}
                        onRemoveAdoptedSkill={onRemoveAdoptedSkill}
                        onSelectKeywordForOptimization={onSelectKeywordForOptimization}
                      />
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
