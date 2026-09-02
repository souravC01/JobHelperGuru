import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Key, Globe, Cpu, Check, AlertCircle, Loader2, Sparkles } from 'lucide-react';
import { getSettings, updateSettings, testAISettings } from '../api/client';

const PRESETS = [
  {
    name: 'Nemotron 3 / 4 (NVIDIA NIM)',
    url: 'https://integrate.api.nvidia.com/v1',
    model: 'nvidia/nemotron-4-340b-instruct',
  },
  {
    name: 'MiniMax M3 / M01',
    url: 'https://api.minimax.chat/v1',
    model: 'minimax/minimax-01',
  },
  {
    name: 'Local Ollama',
    url: 'http://localhost:11434/v1',
    model: 'nemotron-mini',
  },
  {
    name: 'OpenRouter (Universal)',
    url: 'https://openrouter.ai/api/v1',
    model: 'nvidia/nemotron-4-340b-instruct',
  },
];

export default function SettingsModal({ isOpen, onClose }) {
  const [baseUrl, setBaseUrl] = useState('https://integrate.api.nvidia.com/v1');
  const [apiKey, setApiKey] = useState('');
  const [modelName, setModelName] = useState('nvidia/nemotron-4-340b-instruct');
  const [defaultFollowUpDays, setDefaultFollowUpDays] = useState(7);
  const [showKey, setShowKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadCurrentSettings();
    }
  }, [isOpen]);

  const loadCurrentSettings = async () => {
    try {
      const data = await getSettings();
      setBaseUrl(data.api_base_url || 'https://integrate.api.nvidia.com/v1');
      setApiKey(data.api_key || '');
      setModelName(data.model_name || 'nvidia/nemotron-4-340b-instruct');
      setDefaultFollowUpDays(data.default_follow_up_days || 7);
      setTestResult(null);
    } catch (err) {
      console.error('Failed to load settings:', err);
    }
  };

  if (!isOpen) return null;

  const handleSave = async (e) => {
    e?.preventDefault();
    setSaving(true);
    try {
      await updateSettings({
        api_base_url: baseUrl.trim(),
        api_key: apiKey.trim(),
        model_name: modelName.trim(),
        default_follow_up_days: parseInt(defaultFollowUpDays, 10) || 7,
      });
      setSaveSuccess(true);
      setTimeout(() => {
        setSaveSuccess(false);
        onClose();
      }, 1200);
    } catch (err) {
      alert('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await testAISettings({
        api_base_url: baseUrl.trim(),
        api_key: apiKey.trim(),
        model_name: modelName.trim(),
      });
      setTestResult(res);
    } catch (err) {
      setTestResult({ success: false, message: err.message || 'Connection test failed' });
    } finally {
      setTesting(false);
    }
  };

  const applyPreset = (preset) => {
    setBaseUrl(preset.url);
    setModelName(preset.model);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto">
      <div className="glass-panel bg-slate-900 border border-slate-700 w-full max-w-xl my-8 p-6 rounded-2xl space-y-5 animate-fade-in shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-indigo-500/20 text-indigo-400">
              <SettingsIcon size={20} />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">AI Model & App Settings</h3>
              <p className="text-xs text-slate-400">
                Configure your OpenAI-compatible endpoint (MiniMax, Nemotron, Ollama, etc.)
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white text-lg font-bold p-1"
          >
            ✕
          </button>
        </div>

        {/* Presets */}
        <div>
          <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Quick Provider Presets
          </label>
          <div className="grid grid-cols-2 gap-2">
            {PRESETS.map((preset, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => applyPreset(preset)}
                className="text-left p-2 rounded-lg bg-slate-950/60 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 text-xs text-slate-300 transition-colors"
              >
                <div className="font-semibold text-indigo-300 text-[11px]">{preset.name}</div>
                <div className="text-[10px] text-slate-500 truncate">{preset.model}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSave} className="space-y-4">
          {/* Base URL */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
              <Globe size={13} className="text-indigo-400" />
              <span>API Base URL</span>
            </label>
            <input
              type="text"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="e.g. https://integrate.api.nvidia.com/v1"
              className="input-field font-mono text-xs"
              required
            />
          </div>

          {/* Model Name */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
              <Cpu size={13} className="text-indigo-400" />
              <span>Model Name</span>
            </label>
            <input
              type="text"
              value={modelName}
              onChange={(e) => setModelName(e.target.value)}
              placeholder="e.g. nvidia/nemotron-4-340b-instruct or minimax/minimax-01"
              className="input-field font-mono text-xs"
              required
            />
          </div>

          {/* API Key */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                <Key size={13} className="text-indigo-400" />
                <span>API Key</span>
              </label>
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="text-[11px] text-indigo-400 hover:text-indigo-300 font-medium"
              >
                {showKey ? 'Hide' : 'Reveal'}
              </button>
            </div>
            <input
              type={showKey ? 'text' : 'password'}
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="nvapi-... or your MiniMax / Ollama / OpenRouter key"
              className="input-field font-mono text-xs"
            />
            <p className="text-[11px] text-slate-500 mt-1">
              Leave blank to use the built-in offline NLP heuristic parser (no internet/API needed).
            </p>
          </div>

          {/* Test connection result */}
          {testResult && (
            <div
              className={`p-3 rounded-xl border text-xs flex items-start gap-2 ${
                testResult.success
                  ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300'
                  : 'bg-rose-950/40 border-rose-500/40 text-rose-300'
              }`}
            >
              {testResult.success ? (
                <Check size={16} className="text-emerald-400 shrink-0 mt-0.5" />
              ) : (
                <AlertCircle size={16} className="text-rose-400 shrink-0 mt-0.5" />
              )}
              <span className="leading-relaxed">{testResult.message}</span>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center justify-between pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={handleTestConnection}
              disabled={testing}
              className="btn-secondary text-xs"
            >
              {testing ? (
                <>
                  <Loader2 size={13} className="animate-spin" />
                  <span>Testing Connection...</span>
                </>
              ) : (
                <>
                  <Sparkles size={13} />
                  <span>Test Connection</span>
                </>
              )}
            </button>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onClose}
                className="btn-secondary text-xs"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={saving}
                className="btn-primary text-xs"
              >
                {saving ? 'Saving...' : saveSuccess ? 'Saved! ✓' : 'Save Settings'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
