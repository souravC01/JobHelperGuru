import React, { useState, useRef, useEffect } from 'react';
import { User as UserIcon, LogOut, Settings as SettingsIcon, ShieldCheck, ChevronDown, Sparkles } from 'lucide-react';
import { logoutUser } from '../api/client';

export default function UserNav({ user, onOpenAuth, onOpenSettings, applicationsCount = 0, resumesCount = 0 }) {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  if (!user) {
    return (
      <button
        onClick={() => onOpenAuth('login')}
        className="px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-xs font-semibold shadow-md shadow-indigo-500/20 hover:shadow-indigo-500/30 flex items-center gap-1.5 transition-all"
      >
        <UserIcon size={14} />
        <span>Sign In</span>
      </button>
    );
  }

  const initial = (user.name || user.email || 'U')[0].toUpperCase();

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setDropdownOpen(!dropdownOpen)}
        className="flex items-center gap-2 p-1.5 pl-2 pr-2.5 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] border border-white/10 hover:border-white/20 transition-all text-left group"
        title="Account Profile & Settings"
      >
        {user.avatar_url ? (
          <img
            src={user.avatar_url}
            alt={user.name}
            className="w-7 h-7 rounded-lg object-cover ring-1 ring-white/20"
          />
        ) : (
          <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-indigo-600 to-purple-500 text-white flex items-center justify-center font-bold text-xs ring-1 ring-white/20 shadow-inner">
            {initial}
          </div>
        )}
        <div className="hidden sm:flex flex-col text-left">
          <span className="text-[11px] font-semibold text-white leading-tight max-w-[100px] truncate">
            {user.name || user.email.split('@')[0]}
          </span>
          <span className="text-[9px] text-zinc-400 capitalize flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            {user.provider || 'email'}
          </span>
        </div>
        <ChevronDown size={13} className="text-zinc-400 group-hover:text-white transition-colors" />
      </button>

      {dropdownOpen && (
        <div className="absolute right-0 mt-2 w-64 rounded-2xl bg-zinc-900 border border-white/15 shadow-2xl p-2 z-50 backdrop-blur-xl animate-scale-up">
          {/* User Details Header */}
          <div className="p-3 bg-white/[0.03] border border-white/5 rounded-xl mb-2">
            <div className="flex items-center gap-2.5 mb-1.5">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-600 to-purple-500 text-white flex items-center justify-center font-bold text-sm shadow-inner shrink-0">
                {initial}
              </div>
              <div className="overflow-hidden">
                <p className="text-xs font-semibold text-white truncate">{user.name}</p>
                <p className="text-[10px] text-zinc-400 truncate">{user.email}</p>
              </div>
            </div>
            <div className="pt-2 mt-2 border-t border-white/5 flex items-center justify-between text-[10px] text-zinc-400">
              <span>Tenant Pipeline:</span>
              <span className="font-semibold text-indigo-300">
                {applicationsCount} apps &bull; {resumesCount} resumes
              </span>
            </div>
          </div>

          {/* Menu Items */}
          <div className="space-y-1">
            <button
              onClick={() => {
                setDropdownOpen(false);
                if (onOpenSettings) onOpenSettings();
              }}
              className="w-full flex items-center gap-2.5 px-3 py-2 text-xs text-zinc-300 hover:text-white hover:bg-white/10 rounded-xl transition-colors text-left"
            >
              <SettingsIcon size={14} className="text-zinc-400" />
              <span>Personal AI & API Settings</span>
            </button>

            <button
              onClick={() => {
                setDropdownOpen(false);
                logoutUser();
              }}
              className="w-full flex items-center gap-2.5 px-3 py-2 text-xs text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-xl transition-colors text-left"
            >
              <LogOut size={14} />
              <span>Log Out</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
