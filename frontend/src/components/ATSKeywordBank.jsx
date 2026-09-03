import React, { useState } from 'react';
import { Tag, Copy, Check } from 'lucide-react';

export default function ATSKeywordBank({ keywords = [], onSelectKeyword }) {
  const [copied, setCopied] = useState(false);

  const handleCopyAll = () => {
    if (!keywords.length) return;
    navigator.clipboard.writeText(keywords.join(', '));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCopyOne = (kw) => {
    navigator.clipboard.writeText(kw);
    if (onSelectKeyword) {
      onSelectKeyword(kw);
    }
  };

  return (
    <div className="glass-panel p-5">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Tag size={18} className="text-indigo-400" />
          <h3 className="font-semibold text-sm text-slate-200">
            High-Value ATS Keywords ({keywords.length})
          </h3>
        </div>
        {keywords.length > 0 && (
          <button
            onClick={handleCopyAll}
            className="text-xs flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-indigo-300 transition-colors"
          >
            {copied ? (
              <>
                <Check size={13} className="text-emerald-400" />
                <span className="text-emerald-400 font-medium">Copied!</span>
              </>
            ) : (
              <>
                <Copy size={13} />
                <span>Copy All</span>
              </>
            )}
          </button>
        )}
      </div>

      <p className="text-xs text-slate-400 mb-4">
        Ranked keywords from this job posting. Click any keyword to optimize a resume bullet point for it.
      </p>

      {keywords.length === 0 ? (
        <p className="text-xs text-slate-500 italic">No ATS keywords extracted yet. Paste a link or description above.</p>
      ) : (
        <div className="flex flex-wrap gap-2">
          {keywords.map((kw, i) => (
            <button
              key={i}
              onClick={() => handleCopyOne(kw)}
              className="badge-pill badge-keyword group"
              title={`Click to target "${kw}" in resume bullet optimizer`}
            >
              <span>{kw}</span>
              <span className="text-[10px] opacity-40 group-hover:opacity-100 transition-opacity">⚡</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
