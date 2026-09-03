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
    <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="card-corporate bg-white border border-[#e0e0e0] w-full max-w-lg p-6 rounded-xl space-y-5 animate-fade-in shadow-xl text-[#000000]">
        {/* Header */}
        <div className="flex items-start justify-between pb-3 border-b border-[#e0e0e0]">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-full bg-[#b24020]/10 border border-[#b24020]/25 text-[#b24020] shrink-0">
              <AlertTriangle size={20} />
            </div>
            <div>
              <h3 className="text-base font-bold text-[#000000] tracking-tight">AI API Provider Error</h3>
              <p className="text-xs text-[#666666]">
                The online model failed to respond.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-[#666666] hover:text-[#000000] p-1 transition-colors text-base"
          >
            <X size={18} />
          </button>
        </div>

        {/* Error Details */}
        <div className="p-3.5 rounded-lg bg-[#b24020]/10 border border-[#b24020]/25 text-xs text-[#b24020] space-y-1">
          <div className="font-bold text-[#b24020] flex items-center gap-1.5">
            <span>Provider Error {modelName ? `(${modelName})` : ''}:</span>
          </div>
          <p className="font-mono text-[11px] leading-relaxed break-words text-[#b24020]">
            {errorMessage || 'API call failed with network or configuration error.'}
          </p>
        </div>

        {/* Value Prop for Offline Mode */}
        <div className="p-3.5 rounded-lg bg-[#f3f6f8] border border-[#e0e0e0] text-xs text-[#000000] space-y-2">
          <div className="font-bold text-[#000000] flex items-center gap-2">
            <Zap size={15} className="text-[#057642]" />
            <span>Built-in Offline Heuristic Engine Available</span>
          </div>
          <p className="text-[11px] text-[#666666] leading-relaxed">
            You can immediately switch to the built-in offline engine. It requires zero API keys, no network calls, and delivers instant, reliable ATS parsing and bullet point optimization.
          </p>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-2.5 pt-2 border-t border-[#e0e0e0]">
          <button
            type="button"
            onClick={() => {
              onClose();
              if (onOpenSettings) onOpenSettings();
            }}
            className="btn-secondary-corporate text-xs w-full sm:w-auto flex items-center justify-center gap-1.5 py-1 px-3"
          >
            <SettingsIcon size={14} />
            <span>Open Settings</span>
          </button>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary-corporate text-xs w-full sm:w-auto py-1 px-3"
            >
              Dismiss
            </button>
            <button
              type="button"
              onClick={handleSwitch}
              disabled={switching}
              className="btn-primary-corporate text-xs w-full sm:w-auto py-1 px-4 flex items-center justify-center gap-1.5"
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
