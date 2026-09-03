import React from 'react';
import { CheckCircle2, Star, Wrench, Users } from 'lucide-react';

export default function SkillsMatrix({
  requiredSkills = [],
  preferredSkills = [],
  techStack = [],
  softSkills = [],
  onSelectKeyword,
}) {
  return (
    <div className="space-y-6">
      {/* Required Skills */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <CheckCircle2 size={16} className="text-rose-400" />
          <h4 className="text-sm font-semibold uppercase tracking-wider text-rose-400">
            Required Must-Haves ({requiredSkills.length})
          </h4>
        </div>
        {requiredSkills.length === 0 ? (
          <p className="text-xs text-slate-500 italic">None specifically parsed as strict must-haves.</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {requiredSkills.map((skill, i) => (
              <span
                key={i}
                onClick={() => onSelectKeyword && onSelectKeyword(skill)}
                title="Click to optimize bullet point for this skill"
                className="badge-pill badge-required cursor-pointer hover:scale-105"
              >
                {skill}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Preferred Skills */}
      {preferredSkills.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Star size={16} className="text-cyan-400" />
            <h4 className="text-sm font-semibold uppercase tracking-wider text-cyan-400">
              Preferred / Nice-to-Have ({preferredSkills.length})
            </h4>
          </div>
          <div className="flex flex-wrap gap-2">
            {preferredSkills.map((skill, i) => (
              <span
                key={i}
                onClick={() => onSelectKeyword && onSelectKeyword(skill)}
                title="Click to optimize bullet point for this skill"
                className="badge-pill badge-preferred cursor-pointer hover:scale-105"
              >
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Core Tech Stack */}
      {techStack.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Wrench size={16} className="text-emerald-400" />
            <h4 className="text-sm font-semibold uppercase tracking-wider text-emerald-400">
              Tech Stack & Tools ({techStack.length})
            </h4>
          </div>
          <div className="flex flex-wrap gap-2">
            {techStack.map((tech, i) => (
              <span
                key={i}
                onClick={() => onSelectKeyword && onSelectKeyword(tech)}
                title="Click to optimize bullet point for this tool"
                className="badge-pill badge-tech cursor-pointer hover:scale-105"
              >
                {tech}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Soft Skills */}
      {softSkills.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Users size={16} className="text-amber-400" />
            <h4 className="text-sm font-semibold uppercase tracking-wider text-amber-400">
              Soft Skills & Collaboration ({softSkills.length})
            </h4>
          </div>
          <div className="flex flex-wrap gap-2">
            {softSkills.map((item, i) => (
              <span key={i} className="badge-pill badge-soft">
                {item}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
