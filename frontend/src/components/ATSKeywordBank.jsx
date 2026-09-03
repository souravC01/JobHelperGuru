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
    <div className="card-corporate p-5 bg-white border border-[#e0e0e0] rounded-lg">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Tag size={16} className="text-[#0a66c2]" />
          <h3 className="font-bold text-sm text-[#000000]">
            High-Value ATS Keywords ({keywords.length})
          </h3>
        </div>
        {keywords.length > 0 && (
          <button
            onClick={handleCopyAll}
            className="btn-secondary-corporate text-xs py-1 px-3"
            title="Copy all ATS keywords to clipboard"
          >
            {copied ? (
              <>
                <Check size={13} className="text-[#057642]" />
                <span className="text-[#057642] font-semibold">Copied!</span>
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

      <p className="text-xs text-[#666666] mb-4 leading-relaxed">
        Ranked keywords from this job posting. Click any keyword to target it in the resume bullet optimizer.
      </p>

      {keywords.length === 0 ? (
        <p className="text-xs text-[#666666] italic">No ATS keywords extracted yet. Paste a link or description above.</p>
      ) : (
        <div className="flex flex-wrap gap-2">
          {keywords.map((kw, i) => (
            <button
              key={i}
              type="button"
              onClick={() => handleCopyOne(kw)}
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#f3f6f8] text-[#000000] border border-[#e0e0e0] hover:border-[#0a66c2] hover:bg-[#eef3f8] hover:text-[#0a66c2] transition-colors cursor-pointer group"
              title={`Click to target "${kw}" in resume bullet optimizer`}
            >
              <span>{kw}</span>
              <span className="text-[10px] text-[#666666] group-hover:text-[#0a66c2] font-normal transition-colors">&bull;</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
