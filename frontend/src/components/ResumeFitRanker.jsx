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
    <div className="card-corporate p-6 bg-white border border-[#e0e0e0] rounded-lg space-y-5 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold text-[#000000] flex items-center gap-2 tracking-tight">
            <Crown className="text-[#0a66c2]" size={18} />
            <span>Resume Best-Fit & ATS Alignment</span>
          </h3>
          <p className="text-xs text-[#666666] mt-0.5">
            Evaluates candidate resumes against ATS keywords and required qualifications.
          </p>
        </div>

        <button
          onClick={runRanking}
          disabled={loading}
          className="btn-secondary-corporate text-xs"
        >
          {loading ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}
          <span>Re-evaluate</span>
        </button>
      </div>

      {loading ? (
        <div className="py-12 text-center text-xs text-[#666666] flex flex-col items-center justify-center gap-3">
          <Loader2 size={22} className="animate-spin text-[#0a66c2]" />
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
                className={`card-corporate p-5 transition-all bg-white rounded-lg ${
                  isBest
                    ? 'border-2 border-[#0a66c2] shadow-sm'
                    : 'border border-[#e0e0e0]'
                }`}
              >
                {/* Header Row */}
                <div
                  onClick={() => setExpandedId(isExpanded ? null : rank.resume_id)}
                  className="flex items-center justify-between gap-4 cursor-pointer select-none"
                >
                  <div className="flex items-center gap-3.5">
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-mono font-bold ${
                        isBest
                          ? 'bg-[#0a66c2] text-white shadow-sm'
                          : 'bg-[#f3f6f8] text-[#000000] border border-[#e0e0e0]'
                      }`}
                    >
                      {idx + 1}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-[#000000]">{rank.resume_name}</span>
                        {isBest && (
                          <span className="badge-corporate bg-[#057642]/10 border border-[#057642]/25 text-[#057642] text-[10px] py-0.5 font-bold">
                            Top Fit
                          </span>
                        )}
                      </div>

                      {/* New Grad Eligibility Status Badge */}
                      {rank.is_new_grad_role && (
                        <div className="flex items-center gap-1.5 mt-1">
                          {rank.new_grad_eligible ? (
                            <span className="badge-corporate bg-[#057642]/10 border border-[#057642]/25 text-[#057642] text-[10px] py-0.5 px-2 flex items-center gap-1 font-semibold">
                              <GraduationCap size={12} className="text-[#057642]" />
                              <span>New Grad Eligible ({rank.graduation_status})</span>
                            </span>
                          ) : (
                            <span className="badge-corporate bg-[#b24020]/10 border border-[#b24020]/25 text-[#b24020] text-[10px] py-0.5 px-2 flex items-center gap-1 font-semibold">
                              <AlertTriangle size={12} className="text-[#b24020]" />
                              <span>Timeline Check: {rank.graduation_status || 'Date not found'}</span>
                            </span>
                          )}
                        </div>
                      )}

                      <p className="text-[11px] text-[#666666] line-clamp-1 mt-0.5">
                        {rank.fit_summary || 'Evaluated against required job skills'}
                      </p>
                    </div>
                  </div>

                  {/* Progress Score Gauge */}
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className="flex items-center justify-end gap-1.5 font-mono">
                        <span className={`text-base font-bold ${
                          projectedScore >= 80 ? 'text-[#057642]' : projectedScore >= 60 ? 'text-[#0a66c2]' : 'text-[#b24020]'
                        }`}>
                          {projectedScore}%
                        </span>
                        {hasAdopted && scoreDiff > 0 && (
                          <span className="badge-corporate bg-[#0a66c2]/10 border border-[#0a66c2]/30 text-[#0a66c2] text-[10px] py-0.2 px-1.5 font-bold">
                            +{scoreDiff}% Boost
                          </span>
                        )}
                      </div>
                      <div className="w-28 bg-[#e0e0e0] rounded-full h-1.5 overflow-hidden mt-1.5 relative flex">
                        <div
                          className="h-full bg-[#057642] transition-all duration-500 rounded-full"
                          style={{ width: `${baseScore}%` }}
                        />
                        {hasAdopted && scoreDiff > 0 && (
                          <div
                            className="h-full bg-[#0a66c2] transition-all duration-500 rounded-full"
                            style={{ width: `${scoreDiff}%` }}
                          />
                        )}
                      </div>
                    </div>

                    <button className="text-[#666666] hover:text-[#000000] p-1 transition-colors">
                      {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </button>
                  </div>
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="mt-4 pt-4 border-t border-[#e0e0e0] space-y-4 animate-fade-in text-xs">
                    {/* Education & Graduation Status */}
                    {rank.graduation_status && (
                      <div className="p-3 rounded-lg bg-[#f3f6f8] border border-[#e0e0e0] flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                        <div className="flex items-center gap-2">
                          <GraduationCap size={15} className={rank.new_grad_eligible ? "text-[#057642]" : "text-[#b24020]"} />
                          <div>
                            <span className="font-semibold text-[#000000]">Education & Timeline: </span>
                            <span className="text-[#666666]">{rank.graduation_status}</span>
                          </div>
                        </div>
                        {rank.is_new_grad_role && (
                          <span className={`text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded-full shrink-0 self-start sm:self-auto ${
                            rank.new_grad_eligible
                              ? 'bg-[#057642]/10 text-[#057642] border border-[#057642]/30'
                              : 'bg-[#b24020]/10 text-[#b24020] border border-[#b24020]/30'
                          }`}>
                            {rank.new_grad_eligible ? 'Meets Timeline' : 'Verify Timeline'}
                          </span>
                        )}
                      </div>
                    )}

                    {/* Fit Explanation */}
                    {rank.fit_summary && (
                      <div className="p-3 rounded-lg bg-[#f3f6f8] border border-[#e0e0e0] text-[#000000] leading-relaxed">
                        <strong className="text-[#0a66c2]">Match Insights: </strong>
                        {rank.fit_summary}
                      </div>
                    )}

                    {/* Matched Keywords */}
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <h5 className="font-bold text-[#057642] flex items-center gap-1.5 text-xs">
                          <CheckCircle size={13} />
                          <span>Matched Technical Skills ({rank.matched_keywords.length + adoptedSkills.length})</span>
                        </h5>
                        {adoptedSkills.length > 0 && (
                          <span className="text-[10px] text-[#0a66c2] font-semibold bg-[#0a66c2]/10 border border-[#0a66c2]/30 px-2 py-0.5 rounded-full flex items-center gap-1">
                            <Sparkles size={10} className="text-[#0a66c2]" />
                            <span>{adoptedSkills.length} Potentially Added</span>
                          </span>
                        )}
                      </div>

                      {rank.matched_keywords.length === 0 && adoptedSkills.length === 0 ? (
                        <span className="text-[#666666] italic">No direct matches found.</span>
                      ) : (
                        <div className="flex flex-wrap gap-1.5">
                          {/* Verified matches from original resume text */}
                          {rank.matched_keywords.map((kw, i) => (
                            <span key={i} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-[#057642]/10 text-[#057642] border border-[#057642]/20 text-[11px] font-mono font-semibold">
                              {kw} ✓
                            </span>
                          ))}

                          {/* Potentially added skills */}
                          {adoptedSkills.map((kw, i) => (
                            <span
                              key={`adopted-${i}`}
                              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#0a66c2]/10 border border-[#0a66c2]/30 text-[#0a66c2] text-[11px] font-mono font-semibold animate-fade-in"
                              title="Potentially added to resume - re-evaluated and counting towards score!"
                            >
                              <Sparkles size={11} className="text-[#0a66c2]" />
                              <span>{kw}</span>
                              <span className="text-[9px] uppercase font-bold text-[#0a66c2] bg-[#0a66c2]/15 px-1 py-0.2 rounded">
                                Added
                              </span>
                              {onRemoveAdoptedSkill && (
                                <button
                                  type="button"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    onRemoveAdoptedSkill(kw, rank.resume_id);
                                  }}
                                  className="text-[#0a66c2] hover:text-[#b24020] rounded p-0.5 transition-colors ml-0.5"
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
                        <h5 className="font-bold text-[#b24020] flex items-center gap-1.5 text-xs">
                          <AlertTriangle size={13} />
                          <span>Missing Skills ({displayMissing.length})</span>
                          <span className="text-[11px] text-[#666666] font-normal">
                            - Click skills to select for bullet generation
                          </span>
                        </h5>

                        {displayMissing.length > 0 && (
                          <div className="flex items-center gap-2 text-xs">
                            <button
                              onClick={() => selectAllSkills(rank.resume_id, displayMissing)}
                              className="text-[#0a66c2] hover:underline font-semibold"
                            >
                              Select All
                            </button>
                            <span className="text-[#e0e0e0]">|</span>
                            <button
                              onClick={() => clearSkills(rank.resume_id)}
                              className="text-[#666666] hover:text-[#000000]"
                            >
                              Clear
                            </button>
                          </div>
                        )}
                      </div>

                      {displayMissing.length === 0 ? (
                        <span className="text-[#057642] font-semibold italic">All key target qualifications covered!</span>
                      ) : (
                        <div className="flex flex-wrap gap-1.5">
                          {displayMissing.map((kw, i) => {
                            const isSelected = selectedSkills.includes(kw);

                            return (
                              <button
                                key={i}
                                type="button"
                                onClick={() => toggleSkillSelection(rank.resume_id, kw)}
                                className={`inline-flex items-center gap-1.5 text-xs py-1 px-3 rounded-full transition-all cursor-pointer font-mono ${
                                  isSelected
                                    ? 'bg-[#0a66c2] text-white border border-[#0a66c2] font-bold shadow-sm'
                                    : 'bg-[#b24020]/10 border border-[#b24020]/25 text-[#b24020] hover:bg-[#b24020]/20 font-semibold'
                                }`}
                              >
                                {isSelected ? (
                                  <Check size={12} className="text-white stroke-[3]" />
                                ) : (
                                  <Plus size={11} className="text-[#b24020]" />
                                )}
                                <span>{kw}</span>
                              </button>
                            );
                          })}
                        </div>
                      )}

                      {/* Action Bar when 1 or more skills selected */}
                      {selectedSkills.length > 0 && (
                        <div className="p-3.5 rounded-lg bg-[#f3f6f8] border border-[#0a66c2]/30 flex flex-col sm:flex-row sm:items-center justify-between gap-3 animate-fade-in shadow-sm">
                          <div className="flex items-center gap-2">
                            <Sparkles size={15} className="text-[#0a66c2] shrink-0" />
                            <div>
                              <span className="text-xs font-bold text-[#000000]">
                                {selectedSkills.length} Skill{selectedSkills.length > 1 ? 's' : ''} Selected:{' '}
                              </span>
                              <span className="text-xs font-mono text-[#0a66c2] font-semibold">
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
                                className="btn-secondary-corporate text-xs py-1 px-3"
                                title="Move selected skills to Matched and re-evaluate score immediately"
                              >
                                <CheckCircle2 size={12} className="text-[#0a66c2]" />
                                <span>Mark Added</span>
                              </button>
                            )}

                            <button
                              onClick={() => handleIncorporate(rank, 'project')}
                              className="btn-primary-corporate text-xs py-1 px-3"
                            >
                              <FolderGit2 size={12} />
                              <span>Incorporate in Project</span>
                            </button>

                            <button
                              onClick={() => handleIncorporate(rank, 'work_history')}
                              className="btn-secondary-corporate text-xs py-1 px-3"
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
