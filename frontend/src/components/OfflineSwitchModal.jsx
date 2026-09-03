import React, { useState } from 'react';
import { AlertTriangle, Zap, Settings as SettingsIcon, X, Loader2 } from 'lucide-react';
import { updateSettings } from '../api/client';

export default function OfflineSwitchModal({
  isOpen,
  onClose,
  errorMessage,
  modelName,
  onSwitchToOffline,
  onOpenSettings,
}) {
  const [switching, setSwitching] = useState(false);

  if (!isOpen) return null;

  const handleSwitch = async () => {
    setSwitching(true);
    try {
      await updateSettings({ use_offline_mode: true });
      if (onSwitchToOffline) {
        await onSwitchToOffline();
      }
      onClose();
    } catch (err) {
      alert('Failed to switch to offline mode: ' + err.message);
    } finally {
      setSwitching(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="glass-panel bg-[#0e0e11] border border-amber-500/30 w-full max-w-lg p-6 rounded-2xl space-y-5 animate-fade-in shadow-2xl shadow-amber-950/20">
        {/* Header */}
        <div className="flex items-start justify-between pb-3 border-b border-white/[0.06]">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 shrink-0">
              <AlertTriangle size={20} />
            </div>
            <div>
              <h3 className="text-base font-bold text-white tracking-tight">AI API Provider Error</h3>
              <p className="text-xs text-zinc-400">
                The online model failed to respond.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-zinc-500 hover:text-white p-1 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Error Details */}
        <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/30 text-xs text-rose-200 space-y-1">
          <div className="font-semibold text-rose-300 flex items-center gap-1.5">
            <span>Provider Error {modelName ? `(${modelName})` : ''}:</span>
          </div>
          <p className="font-mono text-[11px] leading-relaxed break-words text-rose-100">
            {errorMessage || 'API call failed with network or configuration error.'}
          </p>
        </div>

        {/* Value Prop for Offline Mode */}
        <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-300 space-y-2">
          <div className="font-semibold text-white flex items-center gap-2">
            <Zap size={15} className="text-emerald-400" />
            <span>Built-in Offline Heuristic Engine Available</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            You can immediately switch to the built-in offline engine. It requires zero API keys, no network calls, and delivers instant, reliable ATS parsing and bullet point optimization.
          </p>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-2.5 pt-2 border-t border-slate-800">
          <button
            type="button"
            onClick={() => {
              onClose();
              if (onOpenSettings) onOpenSettings();
            }}
            className="btn-secondary text-xs w-full sm:w-auto flex items-center justify-center gap-1.5"
          >
            <SettingsIcon size={14} />
            <span>Open Settings</span>
          </button>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary text-xs w-full sm:w-auto"
            >
              Dismiss
            </button>
            <button
              type="button"
              onClick={handleSwitch}
              disabled={switching}
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-bold shadow-lg shadow-emerald-950/50 flex items-center justify-center gap-1.5 w-full sm:w-auto transition-all"
            >
              {switching ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  <span>Switching...</span>
                </>
              ) : (
                <>
                  <Zap size={14} />
                  <span>Switch to Offline & Retry</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
