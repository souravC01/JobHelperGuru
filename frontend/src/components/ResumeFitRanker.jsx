import React, { useState, useEffect } from 'react';
import {
  Crown,
  CheckCircle,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Loader2,
  Check,
  FolderGit2,
  Briefcase,
  Plus,
  GraduationCap,
  CheckCircle2,
  X,
  TrendingUp,
} from 'lucide-react';
import { matchResumes } from '../api/client';

export default function ResumeFitRanker({
  currentJob,
  resumes = [],
  adoptedSkillsMap = {},
  onAdoptSkills = null,
  onRemoveAdoptedSkill = null,
  onSelectKeywordForOptimization,
  onBestResumeSelected,
  onAiError,
}) {
  const [rankedResumes, setRankedResumes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [expandedId, setExpandedId] = useState(null);
  const [selectedSkillsMap, setSelectedSkillsMap] = useState({});

  const runRanking = async () => {
    if (!currentJob || resumes.length === 0) return;
    setLoading(true);
    try {
      const jobPayload = currentJob?.analysis || currentJob;
      const results = await matchResumes({ job: jobPayload, resumes });
      setRankedResumes(results);
      if (results.length > 0) {
        setExpandedId(results[0].resume_id);
        if (onBestResumeSelected) {
          onBestResumeSelected(results[0]);
        }
      }
    } catch (err) {
      console.error('Failed to rank resumes:', err);
      if (onAiError && (err.canSwitchOffline || err.status === 502)) {
        onAiError(err, () => runRanking());
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (currentJob && resumes.length > 0) {
      runRanking();
    }
  }, [currentJob, resumes.length]);

  if (!currentJob || resumes.length === 0) {
    return null;
  }

  const toggleSkillSelection = (resumeId, skill) => {
    setSelectedSkillsMap((prev) => {
      const currentList = prev[resumeId] || [];
      const isSelected = currentList.includes(skill);
      const updatedList = isSelected
        ? currentList.filter((s) => s !== skill)
        : [...currentList, skill];

      return {
        ...prev,
        [resumeId]: updatedList,
      };
    });
  };

  const selectAllSkills = (resumeId, allSkills) => {
    setSelectedSkillsMap((prev) => ({
      ...prev,
      [resumeId]: [...allSkills],
    }));
  };

  const clearSkills = (resumeId) => {
    setSelectedSkillsMap((prev) => ({
      ...prev,
      [resumeId]: [],
    }));
  };

  const handleIncorporate = (resume, sectionType) => {
    const selected = selectedSkillsMap[resume.resume_id] || [];
    if (selected.length === 0) return;
    if (onSelectKeywordForOptimization) {
      onSelectKeywordForOptimization(selected, resume, sectionType);
    }
  };

  return (
    <div className="glass-panel p-6 space-y-5 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-white flex items-center gap-2 tracking-tight">
            <Crown className="text-amber-400" size={18} />
            <span>Resume Best-Fit & ATS Alignment</span>
          </h3>
          <p className="text-xs text-zinc-400 mt-0.5">
            Evaluates candidate resumes against ATS keywords and required qualifications.
          </p>
        </div>

        <button
          onClick={runRanking}
          disabled={loading}
          className="btn-secondary text-xs"
        >
          {loading ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}
          <span>Re-evaluate</span>
        </button>
      </div>

      {loading ? (
        <div className="py-12 text-center text-xs text-zinc-400 flex flex-col items-center justify-center gap-3">
          <Loader2 size={22} className="animate-spin text-indigo-400" />
          <span className="font-mono">Analyzing resume keywords and scoring ATS alignment...</span>
        </div>
      ) : (
        <div className="space-y-4">
          {rankedResumes.map((rank, idx) => {
            const isBest = rank.is_best_fit;
            const isExpanded = expandedId === rank.resume_id;
            const selectedSkills = selectedSkillsMap[rank.resume_id] || [];
            const adoptedSkills = (adoptedSkillsMap && adoptedSkillsMap[rank.resume_id]) || [];

            const nonSkillTerms = ['new grad', 'new graduate', 'entry level', 'recent grad', 'degree'];
            const displayMissing = (rank.missing_keywords || []).filter(
              (k) => !nonSkillTerms.some((ns) => k.toLowerCase().includes(ns)) && !adoptedSkills.includes(k)
            );

            // Dynamically recalculate projected match score with adopted skills
            const totalKeywords = (rank.matched_keywords.length + (rank.missing_keywords?.length || 0)) || 1;
            const baseScore = rank.match_score;
            const hasAdopted = adoptedSkills.length > 0;
            const projectedScore = hasAdopted
              ? Math.min(100, Math.max(baseScore, Math.round(((rank.matched_keywords.length + adoptedSkills.length) / totalKeywords) * 100)))
              : baseScore;
            const scoreDiff = projectedScore - baseScore;

            return (
              <div
                key={rank.resume_id}
                className={`glass-card p-5 transition-all ${
                  isBest
                    ? 'border-indigo-500/40 bg-gradient-to-b from-indigo-950/20 to-transparent shadow-lg shadow-indigo-950/30'
                    : 'border-white/[0.06]'
                }`}
              >
                {/* Header Row */}
                <div
                  onClick={() => setExpandedId(isExpanded ? null : rank.resume_id)}
                  className="flex items-center justify-between gap-4 cursor-pointer select-none"
                >
                  <div className="flex items-center gap-3.5">
                    <div
                      className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-mono font-bold ${
                        isBest
                          ? 'bg-gradient-to-tr from-amber-500 to-amber-400 text-slate-950 shadow-md shadow-amber-400/20'
                          : 'bg-white/[0.04] text-zinc-400 border border-white/10'
                      }`}
                    >
                      {idx + 1}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm text-zinc-100">{rank.resume_name}</span>
                        {isBest && (
                          <span className="badge-pill bg-amber-500/10 border border-amber-500/30 text-amber-300 text-[10px] py-0.5">
                            ★ Top Fit
                          </span>
                        )}
                      </div>

                      {/* New Grad Eligibility Status Badge */}
                      {rank.is_new_grad_role && (
                        <div className="flex items-center gap-1.5 mt-1">
                          {rank.new_grad_eligible ? (
                            <span className="badge-pill bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-[10px] py-0.5 px-2 flex items-center gap-1 font-medium">
                              <GraduationCap size={12} className="text-emerald-400" />
                              <span>New Grad Eligible ({rank.graduation_status})</span>
                            </span>
                          ) : (
                            <span className="badge-pill bg-amber-500/10 border border-amber-500/30 text-amber-300 text-[10px] py-0.5 px-2 flex items-center gap-1 font-medium">
                              <AlertTriangle size={12} className="text-amber-400" />
                              <span>Timeline Check: {rank.graduation_status || 'Date not found'}</span>
                            </span>
                          )}
                        </div>
                      )}

                      <p className="text-[11px] text-zinc-400 line-clamp-1 mt-0.5">
                        {rank.fit_summary || 'Evaluated against required job skills'}
                      </p>
                    </div>
                  </div>

                  {/* Radial / Progress Score Gauge with JetBrains Mono */}
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className="flex items-center justify-end gap-1.5 font-mono">
                        <span className={`text-base font-bold ${
                          projectedScore >= 80 ? 'text-emerald-400' : projectedScore >= 60 ? 'text-cyan-400' : 'text-amber-400'
                        }`}>
                          {projectedScore}%
                        </span>
                        {hasAdopted && scoreDiff > 0 && (
                          <span className="badge-pill bg-blue-500/15 border border-blue-400/40 text-blue-300 text-[10px] py-0.2 px-1.5 font-bold animate-pulse">
                            +{scoreDiff}% Boost
                          </span>
                        )}
                      </div>
                      <div className="w-28 bg-white/[0.06] rounded-full h-1.5 overflow-hidden mt-1.5 relative flex">
                        <div
                          className="h-full bg-emerald-400 transition-all duration-500 rounded-full"
                          style={{ width: `${baseScore}%` }}
                        />
                        {hasAdopted && scoreDiff > 0 && (
                          <div
                            className="h-full bg-blue-500 transition-all duration-500 rounded-full"
                            style={{ width: `${scoreDiff}%` }}
                          />
                        )}
                      </div>
                    </div>

                    <button className="text-zinc-400 hover:text-white p-1 transition-colors">
                      {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </button>
                  </div>
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="mt-4 pt-4 border-t border-white/[0.06] space-y-4 animate-fade-in text-xs">
                    {/* Education & Graduation Status */}
                    {rank.graduation_status && (
                      <div className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.06] flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                        <div className="flex items-center gap-2">
                          <GraduationCap size={15} className={rank.new_grad_eligible ? "text-emerald-400" : "text-amber-400"} />
                          <div>
                            <span className="font-semibold text-zinc-200">Education & Timeline: </span>
                            <span className="text-zinc-400">{rank.graduation_status}</span>
                          </div>
                        </div>
                        {rank.is_new_grad_role && (
                          <span className={`text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded-full shrink-0 self-start sm:self-auto ${
                            rank.new_grad_eligible
                              ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/30'
                              : 'bg-amber-500/10 text-amber-300 border border-amber-500/30'
                          }`}>
                            {rank.new_grad_eligible ? '✓ Meets 4mo/6mo Rule' : 'Verify Timeline'}
                          </span>
                        )}
                      </div>
                    )}

                    {/* Fit Explanation */}
                    {rank.fit_summary && (
                      <div className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.06] text-zinc-300 leading-relaxed">
                        <strong className="text-indigo-400">Match Insights: </strong>
                        {rank.fit_summary}
                      </div>
                    )}

                    {/* Matched Keywords (Verified Emerald & Potentially Added Blue) */}
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <h5 className="font-semibold text-emerald-400 flex items-center gap-1.5 text-xs">
                          <CheckCircle size={13} />
                          <span>Matched Technical Skills ({rank.matched_keywords.length + adoptedSkills.length})</span>
                        </h5>
                        {adoptedSkills.length > 0 && (
                          <span className="text-[10px] text-blue-300 font-semibold bg-blue-500/10 border border-blue-500/30 px-2 py-0.5 rounded-full flex items-center gap-1">
                            <Sparkles size={10} className="text-blue-400" />
                            <span>{adoptedSkills.length} Potentially Added (Blue)</span>
                          </span>
                        )}
                      </div>

                      {rank.matched_keywords.length === 0 && adoptedSkills.length === 0 ? (
                        <span className="text-zinc-500 italic">No direct matches found.</span>
                      ) : (
                        <div className="flex flex-wrap gap-1.5">
                          {/* Verified matches from original resume text */}
                          {rank.matched_keywords.map((kw, i) => (
                            <span key={i} className="badge-pill bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 text-[11px] py-0.5 font-mono">
                              {kw} ✓
                            </span>
                          ))}

                          {/* Potentially added skills (Electric Blue) */}
                          {adoptedSkills.map((kw, i) => (
                            <span
                              key={`adopted-${i}`}
                              className="badge-pill bg-blue-500/10 border border-blue-400/40 text-blue-200 text-[11px] py-0.5 px-2.5 flex items-center gap-1.5 font-mono animate-fade-in"
                              title="Potentially added to resume — re-evaluated and counting towards score!"
                            >
                              <Sparkles size={11} className="text-blue-400" />
                              <span>{kw}</span>
                              <span className="text-[9px] uppercase font-bold text-blue-300 bg-blue-900/50 px-1 py-0.2 rounded border border-blue-500/30">
                                Added
                              </span>
                              {onRemoveAdoptedSkill && (
                                <button
                                  type="button"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    onRemoveAdoptedSkill(kw, rank.resume_id);
                                  }}
                                  className="text-blue-400 hover:text-rose-400 hover:bg-rose-950/40 rounded p-0.5 transition-colors ml-0.5"
                                  title="Remove from added and return to missing"
                                >
                                  <X size={10} />
                                </button>
                              )}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Missing Skills Multi-Select */}
                    <div className="space-y-3">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <h5 className="font-semibold text-rose-400 flex items-center gap-1.5 text-xs">
                          <AlertTriangle size={13} />
                          <span>Missing Skills ({displayMissing.length})</span>
                          <span className="text-[11px] text-zinc-500 font-normal">
                            — Click skills to select for bullet generation
                          </span>
                        </h5>

                        {displayMissing.length > 0 && (
                          <div className="flex items-center gap-2 text-xs">
                            <button
                              onClick={() => selectAllSkills(rank.resume_id, displayMissing)}
                              className="text-indigo-400 hover:text-indigo-300 font-medium"
                            >
                              Select All
                            </button>
                            <span className="text-zinc-600">|</span>
                            <button
                              onClick={() => clearSkills(rank.resume_id)}
                              className="text-zinc-500 hover:text-zinc-300"
                            >
                              Clear
                            </button>
                          </div>
                        )}
                      </div>

                      {displayMissing.length === 0 ? (
                        <span className="text-emerald-400 italic">All key target qualifications covered!</span>
                      ) : (
                        <div className="flex flex-wrap gap-1.5">
                          {displayMissing.map((kw, i) => {
                            const isSelected = selectedSkills.includes(kw);

                            return (
                              <button
                                key={i}
                                type="button"
                                onClick={() => toggleSkillSelection(rank.resume_id, kw)}
                                className={`badge-pill text-xs py-1 px-3 flex items-center gap-1.5 transition-all cursor-pointer font-mono ${
                                  isSelected
                                    ? 'bg-indigo-600 text-white border-indigo-400 shadow-md shadow-indigo-600/30 font-bold scale-[1.02]'
                                    : 'bg-rose-500/10 border border-rose-500/25 text-rose-300 hover:bg-rose-500/20'
                                }`}
                              >
                                {isSelected ? (
                                  <Check size={12} className="text-white stroke-[3]" />
                                ) : (
                                  <Plus size={11} className="text-rose-400" />
                                )}
                                <span>{kw}</span>
                              </button>
                            );
                          })}
                        </div>
                      )}

                      {/* Action Bar when 1 or more skills selected */}
                      {selectedSkills.length > 0 && (
                        <div className="p-3.5 rounded-xl bg-indigo-950/40 border border-indigo-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-3 animate-fade-in shadow-xl">
                          <div className="flex items-center gap-2">
                            <Sparkles size={15} className="text-cyan-400 shrink-0" />
                            <div>
                              <span className="text-xs font-bold text-white">
                                {selectedSkills.length} Skill{selectedSkills.length > 1 ? 's' : ''} Selected:{' '}
                              </span>
                              <span className="text-xs font-mono text-cyan-300">
                                {selectedSkills.join(', ')}
                              </span>
                            </div>
                          </div>

                          <div className="flex items-center gap-2 flex-wrap">
                            {onAdoptSkills && (
                              <button
                                onClick={() => {
                                  onAdoptSkills(selectedSkills, rank.resume_id);
                                  clearSkills(rank.resume_id);
                                }}
                                className="btn-secondary text-xs py-1.5 px-3 flex items-center gap-1.5 bg-blue-950/60 border-blue-400/40 text-blue-200 hover:bg-blue-900/80"
                                title="Move selected skills to Matched (Blue) and re-evaluate score immediately"
                              >
                                <CheckCircle2 size={12} className="text-blue-400" />
                                <span>Mark Added (Blue)</span>
                              </button>
                            )}

                            <button
                              onClick={() => handleIncorporate(rank, 'project')}
                              className="btn-gradient text-xs py-1.5 px-3 flex items-center gap-1.5"
                            >
                              <FolderGit2 size={12} />
                              <span>Incorporate in Project</span>
                            </button>

                            <button
                              onClick={() => handleIncorporate(rank, 'work_history')}
                              className="btn-secondary text-xs py-1.5 px-3 flex items-center gap-1.5 text-indigo-300 hover:text-white"
                            >
                              <Briefcase size={12} />
                              <span>Incorporate in Work</span>
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
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
