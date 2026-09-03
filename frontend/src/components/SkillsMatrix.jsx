import React, { useState } from 'react';
import { CheckCircle2, Star, Wrench, Users } from 'lucide-react';

export default function SkillsMatrix({
  requiredSkills = [],
  preferredSkills = [],
  techStack = [],
  softSkills = [],
  onSelectKeyword,
}) {
  const [activeTab, setActiveTab] = useState('all'); // 'all', 'required', 'preferred', 'tech', 'soft'

  const totalSkills = requiredSkills.length + preferredSkills.length + techStack.length + softSkills.length;

  return (
    <div className="space-y-5">
      {/* Category Filter Tabs */}
      <div className="flex flex-wrap items-center gap-1.5 border-b border-[#e0e0e0] pb-2 text-xs">
        <button
          type="button"
          onClick={() => setActiveTab('all')}
          className={`px-3 py-1 rounded-full font-semibold transition-colors ${
            activeTab === 'all'
              ? 'bg-[#0a66c2] text-white'
              : 'text-[#666666] hover:text-[#000000] hover:bg-[#f3f6f8]'
          }`}
        >
          All Categories ({totalSkills})
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('required')}
          className={`px-3 py-1 rounded-full font-semibold transition-colors ${
            activeTab === 'required'
              ? 'bg-[#b24020] text-white'
              : 'text-[#666666] hover:text-[#000000] hover:bg-[#f3f6f8]'
          }`}
        >
          Must-Haves ({requiredSkills.length})
        </button>
        {preferredSkills.length > 0 && (
          <button
            type="button"
            onClick={() => setActiveTab('preferred')}
            className={`px-3 py-1 rounded-full font-semibold transition-colors ${
              activeTab === 'preferred'
                ? 'bg-[#0a66c2] text-white'
                : 'text-[#666666] hover:text-[#000000] hover:bg-[#f3f6f8]'
            }`}
          >
            Preferred ({preferredSkills.length})
          </button>
        )}
        {techStack.length > 0 && (
          <button
            type="button"
            onClick={() => setActiveTab('tech')}
            className={`px-3 py-1 rounded-full font-semibold transition-colors ${
              activeTab === 'tech'
                ? 'bg-[#057642] text-white'
                : 'text-[#666666] hover:text-[#000000] hover:bg-[#f3f6f8]'
            }`}
          >
            Tech Stack ({techStack.length})
          </button>
        )}
        {softSkills.length > 0 && (
          <button
            type="button"
            onClick={() => setActiveTab('soft')}
            className={`px-3 py-1 rounded-full font-semibold transition-colors ${
              activeTab === 'soft'
                ? 'bg-[#000000] text-white'
                : 'text-[#666666] hover:text-[#000000] hover:bg-[#f3f6f8]'
            }`}
          >
            Soft Skills ({softSkills.length})
          </button>
        )}
      </div>

      {/* Required Must-Haves */}
      {(activeTab === 'all' || activeTab === 'required') && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <CheckCircle2 size={15} className="text-[#b24020]" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#b24020]">
              Required Must-Haves ({requiredSkills.length})
            </h4>
          </div>
          {requiredSkills.length === 0 ? (
            <p className="text-xs text-[#666666] italic">None specifically parsed as strict must-haves.</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {requiredSkills.map((skill, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => onSelectKeyword && onSelectKeyword(skill)}
                  title="Click to optimize resume bullet for this skill"
                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#b24020]/10 text-[#b24020] border border-[#b24020]/25 hover:bg-[#b24020]/20 hover:border-[#b24020] transition-all cursor-pointer"
                >
                  <span>{skill}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Preferred Skills */}
      {(activeTab === 'all' || activeTab === 'preferred') && preferredSkills.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Star size={15} className="text-[#0a66c2]" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#0a66c2]">
              Preferred Qualifications ({preferredSkills.length})
            </h4>
          </div>
          <div className="flex flex-wrap gap-2">
            {preferredSkills.map((skill, i) => (
              <button
                key={i}
                type="button"
                onClick={() => onSelectKeyword && onSelectKeyword(skill)}
                title="Click to optimize resume bullet for this skill"
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#0a66c2]/10 text-[#0a66c2] border border-[#0a66c2]/25 hover:bg-[#0a66c2]/20 hover:border-[#0a66c2] transition-all cursor-pointer"
              >
                <span>{skill}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Core Tech Stack */}
      {(activeTab === 'all' || activeTab === 'tech') && techStack.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Wrench size={15} className="text-[#057642]" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#057642]">
              Tech Stack & Tools ({techStack.length})
            </h4>
          </div>
          <div className="flex flex-wrap gap-2">
            {techStack.map((tech, i) => (
              <button
                key={i}
                type="button"
                onClick={() => onSelectKeyword && onSelectKeyword(tech)}
                title="Click to optimize resume bullet for this tool"
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#057642]/10 text-[#057642] border border-[#057642]/25 hover:bg-[#057642]/20 hover:border-[#057642] transition-all cursor-pointer"
              >
                <span>{tech}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Soft Skills */}
      {(activeTab === 'all' || activeTab === 'soft') && softSkills.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Users size={15} className="text-[#000000]" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#000000]">
              Soft Skills & Collaboration ({softSkills.length})
            </h4>
          </div>
          <div className="flex flex-wrap gap-2">
            {softSkills.map((item, i) => (
              <span
                key={i}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-[#f3f6f8] text-[#000000] border border-[#e0e0e0]"
              >
                {item}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
