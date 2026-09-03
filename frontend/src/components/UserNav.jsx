import React, { useState, useRef, useEffect } from 'react';
import { User as UserIcon, LogOut, Settings as SettingsIcon, ChevronDown } from 'lucide-react';
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
        className="btn-primary-corporate text-xs"
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
        className="flex items-center gap-2 p-1 pl-1.5 pr-2.5 rounded-full bg-white hover:bg-[#f3f6f8] border border-[#e0e0e0] hover:border-[#c1c6d4] transition-all text-left group"
        title="Account Profile & Settings"
      >
        {user.avatar_url ? (
          <img
            src={user.avatar_url}
            alt={user.name}
            className="w-7 h-7 rounded-full object-cover border border-[#e0e0e0]"
          />
        ) : (
          <div className="w-7 h-7 rounded-full bg-[#0a66c2] text-white flex items-center justify-center font-bold text-xs">
            {initial}
          </div>
        )}
        <div className="hidden sm:flex flex-col text-left">
          <span className="text-xs font-semibold text-[#000000] leading-tight max-w-[100px] truncate">
            {user.name || user.email.split('@')[0]}
          </span>
          <span className="text-[10px] text-[#666666] capitalize flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-[#057642]" />
            {user.provider || 'email'}
          </span>
        </div>
        <ChevronDown size={13} className="text-[#666666] group-hover:text-[#000000] transition-colors" />
      </button>

      {dropdownOpen && (
        <div className="absolute right-0 mt-2 w-64 rounded-lg bg-white border border-[#e0e0e0] shadow-lg p-2 z-50 animate-fade-in text-[#000000]">
          {/* User Details Header */}
          <div className="p-3 bg-[#f3f6f8] border border-[#e0e0e0] rounded-md mb-2">
            <div className="flex items-center gap-2.5 mb-1.5">
              <div className="w-8 h-8 rounded-full bg-[#0a66c2] text-white flex items-center justify-center font-bold text-sm shrink-0">
                {initial}
              </div>
              <div className="overflow-hidden">
                <p className="text-xs font-bold text-[#000000] truncate">{user.name}</p>
                <p className="text-[11px] text-[#666666] truncate">{user.email}</p>
              </div>
            </div>
            <div className="pt-2 mt-2 border-t border-[#e0e0e0] flex items-center justify-between text-[11px] text-[#666666]">
              <span>Tenant Pipeline:</span>
              <span className="font-semibold text-[#0a66c2]">
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
              className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-medium text-[#000000] hover:bg-[#f3f6f8] rounded-md transition-colors text-left"
            >
              <SettingsIcon size={14} className="text-[#666666]" />
              <span>Personal AI & API Settings</span>
            </button>

            <button
              onClick={() => {
                setDropdownOpen(false);
                logoutUser();
              }}
              className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-medium text-[#b24020] hover:bg-[#b24020]/10 rounded-md transition-colors text-left"
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
