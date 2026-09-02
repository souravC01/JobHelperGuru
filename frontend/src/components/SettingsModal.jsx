import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Key, Globe, Cpu, Check, AlertCircle, Loader2, Sparkles, ExternalLink } from 'lucide-react';
import { getSettings, updateSettings, testAISettings } from '../api/client';

const PRESETS = [
  {
    name: '⭐ Google Gemini (AI Studio / Free)',
    url: 'https://generativelanguage.googleapis.com/v1beta/openai/',
    model: 'gemini-2.0-flash',
    keyHelp: 'Get free key from aistudio.google.com with your Google account',
    link: 'https://aistudio.google.com/app/apikey',
  },
  {
    name: 'OpenAI (GPT-4o Mini / GPT-4o)',
    url: 'https://api.openai.com/v1',
    model: 'gpt-4o-mini',
    keyHelp: 'Get key from platform.openai.com',
    link: 'https://platform.openai.com/api-keys',
  },
  {
    name: 'Groq (Free Llama 3.3 70B)',
    url: 'https://api.groq.com/openai/v1',
    model: 'llama-3.3-70b-versatile',
    keyHelp: 'Free high-speed key from console.groq.com',
    link: 'https://console.groq.com/keys',
  },
  {
    name: 'OpenRouter (Claude 3.5 & GPT-4o)',
    url: 'https://openrouter.ai/api/v1',
    model: 'anthropic/claude-3.5-sonnet',
    keyHelp: 'Get key from openrouter.ai',
    link: 'https://openrouter.ai/keys',
  },
  {
    name: 'NVIDIA NIM (Nemotron)',
    url: 'https://integrate.api.nvidia.com/v1',
    model: 'nvidia/nemotron-4-340b-instruct',
    keyHelp: 'Free credits at build.nvidia.com',
    link: 'https://build.nvidia.com',
  },
  {
    name: 'Local Ollama',
    url: 'http://localhost:11434/v1',
    model: 'llama3.2',
    keyHelp: 'Runs locally on your machine via Ollama',
    link: 'https://ollama.com',
  },
];

export default function SettingsModal({ isOpen, onClose }) {
  const [baseUrl, setBaseUrl] = useState('https://generativelanguage.googleapis.com/v1beta/openai/');
  const [apiKey, setApiKey] = useState('');
  const [modelName, setModelName] = useState('gemini-2.0-flash');
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
      if (data.api_base_url) setBaseUrl(data.api_base_url);
      if (data.api_key) setApiKey(data.api_key);
      if (data.model_name) setModelName(data.model_name);
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
      <div className="glass-panel bg-slate-900 border border-slate-700 w-full max-w-xl my-8 p-6 rounded-2xl space-y-5 animate-fade-in shadow-2xl max-h-[92vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-indigo-500/20 text-indigo-400">
              <SettingsIcon size={20} />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">AI Model Provider Settings</h3>
              <p className="text-xs text-slate-300">
                Connect Google Gemini, OpenAI, Groq, or OpenRouter for highest quality parsing
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
            Recommended AI Providers (Click to Select)
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {PRESETS.map((preset, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => applyPreset(preset)}
                className={`text-left p-2.5 rounded-xl border transition-all text-xs ${
                  baseUrl === preset.url && modelName === preset.model
                    ? 'bg-indigo-950/60 border-indigo-500/80 shadow-md shadow-indigo-950/30'
                    : 'bg-slate-950/50 hover:bg-slate-800/80 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="font-bold text-slate-100 flex items-center justify-between">
                  <span>{preset.name}</span>
                  {baseUrl === preset.url && modelName === preset.model && (
                    <span className="text-[10px] text-indigo-400 font-bold uppercase">Active</span>
                  )}
                </div>
                <div className="text-[11px] font-mono text-slate-400 truncate mt-0.5">{preset.model}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSave} className="space-y-4">
          {/* Base URL */}
          <div>
            <label className="block text-xs font-semibold text-slate-200 mb-1 flex items-center gap-1.5">
              <Globe size={13} className="text-indigo-400" />
              <span>API Base URL</span>
            </label>
            <input
              type="text"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="e.g. https://generativelanguage.googleapis.com/v1beta/openai/"
              className="input-field font-mono text-xs"
              required
            />
          </div>

          {/* Model Name */}
          <div>
            <label className="block text-xs font-semibold text-slate-200 mb-1 flex items-center gap-1.5">
              <Cpu size={13} className="text-indigo-400" />
              <span>Model Name</span>
            </label>
            <input
              type="text"
              value={modelName}
              onChange={(e) => setModelName(e.target.value)}
              placeholder="e.g. gemini-2.0-flash, gpt-4o-mini, or anthropic/claude-3.5-sonnet"
              className="input-field font-mono text-xs"
              required
            />
          </div>

          {/* API Key */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
                <Key size={13} className="text-indigo-400" />
                <span>API Key</span>
              </label>
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="text-[11px] text-indigo-400 hover:text-indigo-300 font-semibold"
              >
                {showKey ? 'Hide' : 'Reveal'}
              </button>
            </div>
            <input
              type={showKey ? 'text' : 'password'}
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Paste your API key here (AIzaSy... for Gemini, or sk-...)"
              className="input-field font-mono text-xs"
            />

            {/* Quick Link to Google AI Studio Key */}
            <div className="mt-2.5 p-3 rounded-xl bg-indigo-950/40 border border-indigo-500/30 text-xs text-indigo-200 space-y-1">
              <div className="font-semibold text-white flex items-center gap-1.5">
                <Sparkles size={14} className="text-cyan-400" />
                <span>Need a high-quality key with a generous free tier?</span>
              </div>
              <p className="text-[11px] text-slate-300">
                You can get a free <strong>Google Gemini API Key</strong> in 30 seconds using your regular Google account (no credit card required):
              </p>
              <a
                href="https://aistudio.google.com/app/apikey"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-cyan-400 hover:text-cyan-300 font-bold text-xs underline mt-1"
              >
                <span>Get Free Gemini API Key at Google AI Studio</span>
                <ExternalLink size={12} />
              </a>
            </div>
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
