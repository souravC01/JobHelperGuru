import React from 'react';
import { Sun, Moon } from 'lucide-react';

export default function ThemeToggle({ theme = 'light', onToggle }) {
  const isDark = theme === 'dark';

  return (
    <button
      type="button"
      onClick={onToggle}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      className="p-2 rounded-full bg-white hover:bg-[#f3f6f8] border border-[#e0e0e0] hover:border-[#c1c6d4] text-[#666666] hover:text-[#000000] transition-all flex items-center justify-center cursor-pointer shadow-none"
    >
      {isDark ? (
        <Sun size={17} className="text-[#f59e0b] transition-transform duration-200 hover:rotate-45" />
      ) : (
        <Moon size={17} className="text-[#666666] transition-transform duration-200 hover:-rotate-12" />
      )}
    </button>
  );
}
