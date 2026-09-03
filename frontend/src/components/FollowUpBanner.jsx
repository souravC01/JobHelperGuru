import React from 'react';
import { Bell, AlertCircle, Calendar } from 'lucide-react';

export default function FollowUpBanner({ applications = [], onSelectApp }) {
  const today = new Date().toISOString().slice(0, 10);

  const dueApps = applications.filter((app) => {
    if (!app.follow_up_date) return false;
    return app.follow_up_date <= today && app.status !== 'Rejected' && app.status !== 'Archived' && app.status !== 'Offered';
  });

  if (dueApps.length === 0) return null;

  return (
    <div className="p-4 rounded-xl bg-amber-950/40 border border-amber-500/40 text-amber-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 animate-fade-in shadow-lg shadow-amber-950/20">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-amber-500/20 text-amber-400">
          <Bell size={18} className="animate-bounce" />
        </div>
        <div>
          <h4 className="font-bold text-xs uppercase tracking-wide text-amber-300">
            Follow-Up Reminder ({dueApps.length} Action{dueApps.length > 1 ? 's' : ''} Needed)
          </h4>
          <p className="text-xs text-amber-200/80 mt-0.5">
            You have {dueApps.length} application{dueApps.length > 1 ? 's' : ''} scheduled for follow-up today or overdue.
          </p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {dueApps.map((app) => (
          <button
            key={app.id}
            onClick={() => onSelectApp && onSelectApp(app)}
            className="text-xs px-2.5 py-1 rounded bg-amber-900/60 hover:bg-amber-800/80 border border-amber-600/50 text-amber-100 flex items-center gap-1.5 transition-colors"
          >
            <Calendar size={12} />
            <span>{app.company}</span>
            <span className="opacity-70">({app.follow_up_date})</span>
          </button>
        ))}
      </div>
    </div>
  );
}
