import React from 'react';
import { Bell, Calendar } from 'lucide-react';

export default function FollowUpBanner({ applications = [], onSelectApp }) {
  const today = new Date().toISOString().slice(0, 10);

  const dueApps = applications.filter((app) => {
    if (!app.follow_up_date) return false;
    return app.follow_up_date <= today && app.status !== 'Rejected' && app.status !== 'Archived' && app.status !== 'Offered';
  });

  if (dueApps.length === 0) return null;

  return (
    <div className="card-corporate p-4 bg-white border border-[#e0e0e0] rounded-lg text-[#000000] flex flex-col sm:flex-row sm:items-center justify-between gap-3 animate-fade-in shadow-none">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-full bg-[#b24020]/10 text-[#b24020] border border-[#b24020]/25 shrink-0">
          <Bell size={18} />
        </div>
        <div>
          <h4 className="font-bold text-xs uppercase tracking-wide text-[#b24020]">
            Follow-Up Reminder ({dueApps.length} Action{dueApps.length > 1 ? 's' : ''} Needed)
          </h4>
          <p className="text-xs text-[#666666] mt-0.5">
            You have {dueApps.length} application{dueApps.length > 1 ? 's' : ''} scheduled for follow-up today or overdue.
          </p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {dueApps.map((app) => (
          <button
            key={app.id}
            onClick={() => onSelectApp && onSelectApp(app)}
            className="text-xs px-3 py-1 rounded-full bg-[#f3f6f8] hover:bg-[#b24020]/10 border border-[#e0e0e0] hover:border-[#b24020]/30 text-[#000000] hover:text-[#b24020] flex items-center gap-1.5 transition-colors font-medium"
          >
            <Calendar size={12} className="text-[#666666]" />
            <span className="font-semibold">{app.company}</span>
            <span className="text-[#666666] font-mono">({app.follow_up_date})</span>
          </button>
        ))}
      </div>
    </div>
  );
}
