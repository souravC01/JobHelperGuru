import React, { useState, useEffect } from 'react';
import {
  Crown,
  CheckCircle,
  AlertTriangle,
  Wand2,
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
} from 'lucide-react';
import { matchResumes } from '../api/client';

export default function ResumeFitRanker({
  currentJob,
  resumes = [],
  onSelectKeywordForOptimization,
  onBestResumeSelected,
}) {
  const [rankedResumes, setRankedResumes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [expandedId, setExpandedId] = useState(null);
  // Track selected missing skills per resume: { [resumeId]: string[] }
  const [selectedSkillsMap, setSelectedSkillsMap] = useState({});

  const runRanking = async () => {
    if (!currentJob || resumes.length === 0) return;
    setLoading(true);
    try {
      const results = await matchResumes(currentJob);
      setRankedResumes(results);
      if (results.length > 0) {
        setExpandedId(results[0].resume_id);
        if (onBestResumeSelected) {
          onBestResumeSelected(results[0]);
        }
      }
    } catch (err) {
      console.error('Failed to rank resumes:', err);
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
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Crown className="text-amber-400" size={20} />
            <span>Best-Fit Resume Comparison</span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Evaluates your uploaded resumes against this job's required qualifications and ATS keywords.
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
        <div className="py-8 text-center text-xs text-slate-400 flex items-center justify-center gap-2">
          <Loader2 size={16} className="animate-spin text-indigo-400" />
          <span>Ranking resumes and calculating keyword matches...</span>
        </div>
      ) : (
        <div className="space-y-4">
          {rankedResumes.map((rank, idx) => {
            const isBest = rank.is_best_fit;
            const isExpanded = expandedId === rank.resume_id;
            const selectedSkills = selectedSkillsMap[rank.resume_id] || [];
            const nonSkillTerms = ['new grad', 'new graduate', 'entry level', 'recent grad', 'degree'];
            const displayMissing = (rank.missing_keywords || []).filter(
              (k) => !nonSkillTerms.some((ns) => k.toLowerCase().includes(ns))
            );

            return (
              <div
                key={rank.resume_id}
                className={`glass-card p-5 transition-all ${
                  isBest
                    ? 'border-indigo-500/60 bg-indigo-950/20 shadow-lg shadow-indigo-950/40'
                    : 'border-slate-800'
                }`}
              >
                {/* Header Row */}
                <div
                  onClick={() => setExpandedId(isExpanded ? null : rank.resume_id)}
                  className="flex items-center justify-between gap-4 cursor-pointer select-none"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
                        isBest
                          ? 'bg-amber-400 text-slate-950 shadow-md shadow-amber-400/30'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {idx + 1}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-slate-100">{rank.resume_name}</span>
                        {isBest && (
                          <span className="badge-pill bg-amber-400/20 border border-amber-400/40 text-amber-300 text-[10px] py-0.5">
                            ★ Recommended Fit
                          </span>
                        )}
                      </div>

                      {/* New Grad Eligibility Status Badge */}
                      {rank.is_new_grad_role && (
                        <div className="flex items-center gap-1.5 mt-1">
                          {rank.new_grad_eligible ? (
                            <span className="badge-pill bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 text-[10px] py-0.5 px-2 flex items-center gap-1 font-medium">
                              <GraduationCap size={12} className="text-emerald-400" />
                              <span>🎓 New Grad Eligible ({rank.graduation_status})</span>
                            </span>
                          ) : (
                            <span className="badge-pill bg-amber-950/60 border border-amber-500/40 text-amber-300 text-[10px] py-0.5 px-2 flex items-center gap-1 font-medium">
                              <AlertTriangle size={12} className="text-amber-400" />
                              <span>🎓 New Grad Check: {rank.graduation_status || 'Graduation date not detected'}</span>
                            </span>
                          )}
                        </div>
                      )}

                      <p className="text-[11px] text-slate-400 line-clamp-1 mt-0.5">
                        {rank.fit_summary || 'Evaluated against required job skills'}
                      </p>
                    </div>
                  </div>

                  {/* Match Score Gauge */}
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className="text-sm font-extrabold text-white">{rank.match_score}%</div>
                      <div className="w-24 bg-slate-800 rounded-full h-1.5 overflow-hidden mt-1">
                        <div
                          className={`h-full rounded-full ${
                            rank.match_score >= 75
                              ? 'bg-emerald-400'
                              : rank.match_score >= 50
                              ? 'bg-indigo-400'
                              : 'bg-amber-400'
                          }`}
                          style={{ width: `${rank.match_score}%` }}
                        />
                      </div>
                    </div>

                    <button className="text-slate-400 hover:text-white p-1">
                      {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </button>
                  </div>
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="mt-4 pt-4 border-t border-slate-800/80 space-y-4 animate-fade-in text-xs">
                    {/* Education & Graduation Status Verification */}
                    {rank.graduation_status && (
                      <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                        <div className="flex items-center gap-2">
                          <GraduationCap size={16} className={rank.new_grad_eligible ? "text-emerald-400" : "text-amber-400"} />
                          <div>
                            <span className="font-semibold text-slate-200">Education & Graduation: </span>
                            <span className="text-slate-300">{rank.graduation_status}</span>
                          </div>
                        </div>
                        {rank.is_new_grad_role && (
                          <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded shrink-0 self-start sm:self-auto ${
                            rank.new_grad_eligible
                              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                              : 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                          }`}>
                            {rank.new_grad_eligible ? '✓ Meets 4mo/6mo Rule' : 'Verify Timeline'}
                          </span>
                        )}
                      </div>
                    )}

                    {/* Fit explanation */}
                    {rank.fit_summary && (
                      <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-slate-300 leading-relaxed">
                        <strong className="text-indigo-300">Why this score: </strong>
                        {rank.fit_summary}
                      </div>
                    )}

                    {/* Matched Keywords */}
                    <div>
                      <h5 className="font-semibold text-emerald-400 flex items-center gap-1.5 mb-2">
                        <CheckCircle size={14} />
                        <span>Matched Technical Skills ({rank.matched_keywords.length})</span>
                      </h5>
                      {rank.matched_keywords.length === 0 ? (
                        <span className="text-slate-500 italic">No direct matches found.</span>
                      ) : (
                        <div className="flex flex-wrap gap-1.5">
                          {rank.matched_keywords.map((kw, i) => (
                            <span key={i} className="badge-pill badge-tech text-[11px] py-0.5">
                              {kw} ✓
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Missing Keywords Multi-Select */}
                    <div className="space-y-3">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <h5 className="font-semibold text-rose-400 flex items-center gap-1.5">
                          <AlertTriangle size={14} />
                          <span>Missing Skills ({displayMissing.length})</span>
                          <span className="text-[11px] text-slate-400 font-normal">
                            — Click skills to select for bullet generation
                          </span>
                        </h5>

                        {displayMissing.length > 0 && (
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => selectAllSkills(rank.resume_id, displayMissing)}
                              className="text-[11px] text-indigo-400 hover:text-indigo-300 font-medium"
                            >
                              Select All
                            </button>
                            <span className="text-slate-600">|</span>
                            <button
                              onClick={() => clearSkills(rank.resume_id)}
                              className="text-[11px] text-slate-400 hover:text-slate-200"
                            >
                              Clear
                            </button>
                          </div>
                        )}
                      </div>

                      {displayMissing.length === 0 ? (
                        <span className="text-emerald-400 italic">All key target qualifications covered!</span>
                      ) : (
                        <div className="flex flex-wrap gap-2">
                          {displayMissing.map((kw, i) => {
                            const isSelected = selectedSkills.includes(kw);

                            return (
                              <button
                                key={i}
                                type="button"
                                onClick={() => toggleSkillSelection(rank.resume_id, kw)}
                                className={`badge-pill text-xs py-1 px-3 flex items-center gap-1.5 transition-all cursor-pointer ${
                                  isSelected
                                    ? 'bg-indigo-600 text-white border-indigo-400 shadow-md shadow-indigo-600/30 font-bold scale-[1.03]'
                                    : 'bg-rose-500/15 border border-rose-500/30 text-rose-300 hover:bg-rose-500/25 hover:border-rose-400'
                                }`}
                              >
                                {isSelected ? (
                                  <Check size={13} className="text-white stroke-[3]" />
                                ) : (
                                  <Plus size={12} className="text-rose-400" />
                                )}
                                <span>{kw}</span>
                              </button>
                            );
                          })}
                        </div>
                      )}

                      {/* Action Bar when 1 or more skills selected */}
                      {selectedSkills.length > 0 && (
                        <div className="p-3.5 rounded-xl bg-indigo-950/50 border border-indigo-500/40 flex flex-col sm:flex-row sm:items-center justify-between gap-3 animate-fade-in shadow-lg">
                          <div className="flex items-center gap-2">
                            <Sparkles size={16} className="text-cyan-400 shrink-0" />
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
                            <button
                              onClick={() => handleIncorporate(rank, 'project')}
                              className="btn-primary text-xs py-1.5 px-3 flex items-center gap-1.5"
                            >
                              <FolderGit2 size={13} />
                              <span>Incorporate into Project</span>
                            </button>

                            <button
                              onClick={() => handleIncorporate(rank, 'work_history')}
                              className="btn-secondary text-xs py-1.5 px-3 flex items-center gap-1.5 bg-slate-900 border-indigo-400/40 text-indigo-200 hover:text-white"
                            >
                              <Briefcase size={13} />
                              <span>Incorporate into Work History</span>
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
