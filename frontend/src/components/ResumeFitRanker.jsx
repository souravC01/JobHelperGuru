import React, { useState, useEffect } from 'react';
import { Crown, CheckCircle, AlertTriangle, Wand2, ChevronDown, ChevronUp, Sparkles, Loader2 } from 'lucide-react';
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

  const runRanking = async () => {
    if (!currentJob || resumes.length === 0) return;
    setLoading(true);
    try {
      const data = await matchResumes({ job: currentJob, resumes });
      setRankedResumes(data);
      if (data.length > 0) {
        setExpandedId(data[0].resume_id);
        if (onBestResumeSelected) {
          onBestResumeSelected(data[0]);
        }
      }
    } catch (err) {
      console.error('Failed to match resumes:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (currentJob && resumes.length > 0) {
      runRanking();
    }
  }, [currentJob, resumes]);

  if (!currentJob) return null;

  if (resumes.length === 0) {
    return (
      <div className="glass-panel p-6 text-center space-y-2">
        <Sparkles className="mx-auto text-indigo-400" size={28} />
        <h4 className="font-semibold text-slate-200 text-sm">Compare Multiple Resumes</h4>
        <p className="text-xs text-slate-400 max-w-md mx-auto">
          You haven't added any resumes yet. Add your resumes in the <strong>Resume Library</strong> tab to see which version fits this job best!
        </p>
      </div>
    );
  }

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
        <div className="space-y-3">
          {rankedResumes.map((rank, idx) => {
            const isBest = rank.is_best_fit;
            const isExpanded = expandedId === rank.resume_id;

            return (
              <div
                key={rank.resume_id}
                className={`glass-card p-4 transition-all ${
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
                        <span>Matched Keywords ({rank.matched_keywords.length})</span>
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

                    {/* Missing Keywords */}
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <h5 className="font-semibold text-rose-400 flex items-center gap-1.5">
                          <AlertTriangle size={14} />
                          <span>Missing Skills to Incorporate ({rank.missing_keywords.length})</span>
                        </h5>
                        <span className="text-[10px] text-slate-500">Click a keyword to generate revised bullets</span>
                      </div>

                      {rank.missing_keywords.length === 0 ? (
                        <span className="text-emerald-400 italic">All key target qualifications covered!</span>
                      ) : (
                        <div className="flex flex-wrap gap-1.5">
                          {rank.missing_keywords.map((kw, i) => (
                            <button
                              key={i}
                              onClick={() => onSelectKeywordForOptimization && onSelectKeywordForOptimization(kw, rank)}
                              className="badge-pill bg-rose-500/15 border border-rose-500/30 text-rose-300 hover:bg-rose-500/25 hover:border-rose-400 text-[11px] py-0.5 flex items-center gap-1 transition-all"
                              title={`Click to optimize bullet point for "${kw}"`}
                            >
                              <span>{kw}</span>
                              <Wand2 size={11} className="text-indigo-400" />
                            </button>
                          ))}
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
