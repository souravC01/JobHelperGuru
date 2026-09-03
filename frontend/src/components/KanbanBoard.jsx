import React from 'react';
import { MapPin, DollarSign, Calendar, ExternalLink, ArrowRight, ArrowLeft } from 'lucide-react';

const COLUMNS = [
  { id: 'Wishlist', label: 'Wishlist', badge: 'status-wishlist' },
  { id: 'Applied', label: 'Applied', badge: 'status-applied' },
  { id: 'Interviewing', label: 'Interviewing', badge: 'status-interviewing' },
  { id: 'Offered', label: 'Offered', badge: 'status-offered' },
  { id: 'Rejected', label: 'Rejected', badge: 'status-rejected' },
];

export default function KanbanBoard({ applications = [], onUpdateStatus }) {
  const getNextStatus = (current) => {
    const idx = COLUMNS.findIndex((c) => c.id === current);
    if (idx !== -1 && idx < COLUMNS.length - 1) {
      return COLUMNS[idx + 1].id;
    }
    return null;
  };

  const getPrevStatus = (current) => {
    const idx = COLUMNS.findIndex((c) => c.id === current);
    if (idx > 0) {
      return COLUMNS[idx - 1].id;
    }
    return null;
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 overflow-x-auto pb-4">
      {COLUMNS.map((col) => {
        const columnApps = applications.filter((app) => app.status === col.id);

        return (
          <div
            key={col.id}
            className="flex flex-col bg-[#f3f6f8] rounded-lg border border-[#e0e0e0] p-3 min-w-[260px]"
          >
            {/* Column Header */}
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-[#e0e0e0]">
              <div className="flex items-center gap-2">
                <span className={`badge-corporate ${col.badge} text-[11px] py-0.5 font-bold`}>
                  {col.label}
                </span>
              </div>
              <span className="text-xs font-bold text-[#000000] bg-white border border-[#e0e0e0] px-2.5 py-0.5 rounded-full">
                {columnApps.length}
              </span>
            </div>

            {/* Column Cards */}
            <div className="space-y-3 flex-1 overflow-y-auto max-h-[70vh] pr-1">
              {columnApps.length === 0 ? (
                <div className="py-8 text-center text-[#666666] text-xs italic">
                  No applications
                </div>
              ) : (
                columnApps.map((app) => {
                  const nextStatus = getNextStatus(app.status);
                  const prevStatus = getPrevStatus(app.status);

                  return (
                    <div
                      key={app.id}
                      className="card-corporate p-3.5 space-y-2.5 bg-white border border-[#e0e0e0] hover:border-[#c1c6d4] transition-all text-xs rounded-lg shadow-none"
                    >
                      <div>
                        <div className="flex items-start justify-between gap-1">
                          <h4 className="font-bold text-[#000000] line-clamp-1">{app.company}</h4>
                          {app.url && (
                            <a
                              href={app.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-[#666666] hover:text-[#0a66c2] p-0.5"
                            >
                              <ExternalLink size={12} />
                            </a>
                          )}
                        </div>
                        <p className="text-[#666666] font-medium line-clamp-1">{app.role}</p>
                      </div>

                      <div className="space-y-1 text-[11px] text-[#666666]">
                        {app.location && app.location !== 'Unknown' && (
                          <div className="flex items-center gap-1">
                            <MapPin size={11} className="text-[#666666]" />
                            <span className="line-clamp-1">{app.location}</span>
                          </div>
                        )}
                        {app.salary && app.salary !== 'Not specified' && (
                          <div className="flex items-center gap-1 text-[#057642] font-mono font-semibold">
                            <DollarSign size={11} />
                            <span className="line-clamp-1">{app.salary}</span>
                          </div>
                        )}
                        {app.follow_up_date && (
                          <div className="flex items-center gap-1 text-[#b24020] font-semibold">
                            <Calendar size={11} />
                            <span>Follow-up: {app.follow_up_date}</span>
                          </div>
                        )}
                      </div>

                      {/* Card Move Actions */}
                      <div className="pt-2 border-t border-[#e0e0e0] flex items-center justify-between">
                        {prevStatus ? (
                          <button
                            onClick={() => onUpdateStatus(app.id, prevStatus)}
                            title={`Move back to ${prevStatus}`}
                            className="text-[11px] text-[#666666] hover:text-[#000000] flex items-center gap-0.5 p-1 rounded hover:bg-[#f3f6f8] font-medium"
                          >
                            <ArrowLeft size={11} />
                            <span>Back</span>
                          </button>
                        ) : (
                          <span />
                        )}

                        {nextStatus && (
                          <button
                            onClick={() => onUpdateStatus(app.id, nextStatus)}
                            title={`Advance to ${nextStatus}`}
                            className="text-[11px] text-[#0a66c2] hover:underline font-semibold flex items-center gap-0.5 p-1 rounded hover:bg-[#0a66c2]/5"
                          >
                            <span>{nextStatus}</span>
                            <ArrowRight size={11} />
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
