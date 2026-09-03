import React, { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon,
  Key,
  Globe,
  Cpu,
  Check,
  AlertCircle,
  Loader2,
  Sparkles,
  Trash2,
  Edit2,
  PlusCircle,
  ShieldCheck,
  Tag,
  Zap,
} from 'lucide-react';
import { getSettings, updateSettings, testAISettings } from '../api/client';

export default function SettingsModal({ isOpen, onClose }) {
  // Form fields
  const [keyName, setKeyName] = useState('');
  const [baseUrl, setBaseUrl] = useState('');
  const [modelName, setModelName] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [editingId, setEditingId] = useState(null);

  // Saved Keys List & Offline Status
  const [savedKeys, setSavedKeys] = useState([]);
  const [activeKeyId, setActiveKeyId] = useState(null);
  const [isOfflineActive, setIsOfflineActive] = useState(false);

  // UI States
  const [showKey, setShowKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadSettingsAndKeys();
    }
  }, [isOpen]);

  // Helper to deduplicate an array of key profiles
  const deduplicateKeys = (keysList) => {
    const seen = new Set();
    return keysList.filter((k) => {
      const sig = `${(k.api_base_url || '').trim()}::${(k.model_name || '').trim()}::${(k.api_key || '').trim()}`;
      if (seen.has(sig)) return false;
      seen.add(sig);
      return true;
    });
  };

  const loadSettingsAndKeys = async () => {
    try {
      const data = await getSettings();
      let parsedSavedKeys = [];

      setIsOfflineActive(Boolean(data.use_offline_mode));

      if (data.saved_keys) {
        try {
          parsedSavedKeys = JSON.parse(data.saved_keys);
        } catch (e) {
          parsedSavedKeys = [];
        }
      }

      // Fallback to localStorage if backend saved_keys is empty
      if (!parsedSavedKeys || parsedSavedKeys.length === 0) {
        const local = localStorage.getItem('jobhelperguru_saved_keys');
        if (local) {
          try {
            parsedSavedKeys = JSON.parse(local);
          } catch (e) {
            parsedSavedKeys = [];
          }
        }
      }

      // If still empty but an active key exists, auto-populate the first saved profile
      if (parsedSavedKeys.length === 0 && (data.api_base_url || data.api_key)) {
        const initialProfile = {
          id: 'key-' + Date.now(),
          name: data.model_name || 'Active AI Key',
          api_base_url: data.api_base_url || 'https://generativelanguage.googleapis.com/v1beta/openai/',
          model_name: data.model_name || 'gemini-2.0-flash',
          api_key: data.api_key || '',
          created_at: new Date().toISOString(),
        };
        parsedSavedKeys = [initialProfile];
      }

      // Clean up any duplicates from earlier saves
      parsedSavedKeys = deduplicateKeys(parsedSavedKeys);
      setSavedKeys(parsedSavedKeys);

      // Find active key
      let currentActiveId = null;
      if (!data.use_offline_mode) {
        const activeMatch = parsedSavedKeys.find(
          (k) =>
            (k.api_base_url || '').trim() === (data.api_base_url || '').trim() &&
            (k.model_name || '').trim() === (data.model_name || '').trim() &&
            (k.api_key || '').trim() === (data.api_key || '').trim()
        );

        if (activeMatch) {
          currentActiveId = activeMatch.id;
        } else if (parsedSavedKeys.length > 0) {
          currentActiveId = parsedSavedKeys[0].id;
        }
      }

      setActiveKeyId(currentActiveId);

      // Populate form with current active or first profile
      const target = parsedSavedKeys.find((k) => k.id === currentActiveId) || parsedSavedKeys[0];
      if (target) {
        setEditingId(target.id);
        setKeyName(target.name || '');
        setBaseUrl(target.api_base_url || '');
        setModelName(target.model_name || '');
        setApiKey(target.api_key || '');
      } else {
        setEditingId(null);
        setBaseUrl(data.api_base_url || '');
        setModelName(data.model_name || '');
        setApiKey(data.api_key || '');
      }

      setTestResult(null);
    } catch (err) {
      console.error('Failed to load settings:', err);
    }
  };

  if (!isOpen) return null;

  const maskKey = (key) => {
    if (!key) return 'No Key (Public / Local Endpoint)';
    if (key.length <= 8) return '••••••••';
    return `${key.slice(0, 4)}••••••••${key.slice(-4)}`;
  };

  const handleSwitchToOffline = async () => {
    setSaving(true);
    try {
      await updateSettings({
        use_offline_mode: true,
      });
      setIsOfflineActive(true);
      setActiveKeyId(null);
      setTestResult({
        success: true,
        message: 'Active engine switched to Built-in Offline Heuristic. Zero API keys used.',
      });
    } catch (err) {
      alert('Failed to switch to offline engine: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleActivateKey = async (profile) => {
    setSaving(true);
    try {
      await updateSettings({
        api_base_url: profile.api_base_url.trim(),
        api_key: profile.api_key.trim(),
        model_name: profile.model_name.trim(),
        use_offline_mode: false,
        saved_keys: JSON.stringify(savedKeys),
      });

      setIsOfflineActive(false);
      setActiveKeyId(profile.id);
      setEditingId(profile.id);
      setKeyName(profile.name);
      setBaseUrl(profile.api_base_url);
      setModelName(profile.model_name);
      setApiKey(profile.api_key);
      setTestResult({
        success: true,
        message: `Active provider switched to ${profile.name} (${profile.model_name})!`,
      });
    } catch (err) {
      alert('Failed to activate key: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleEditKey = (profile) => {
    setEditingId(profile.id);
    setKeyName(profile.name || '');
    setBaseUrl(profile.api_base_url || '');
    setModelName(profile.model_name || '');
    setApiKey(profile.api_key || '');
    setTestResult(null);
  };

  const handleDeleteKey = async (idToDelete) => {
    const updated = savedKeys.filter((k) => k.id !== idToDelete);
    setSavedKeys(updated);
    localStorage.setItem('jobhelperguru_saved_keys', JSON.stringify(updated));

    try {
      await updateSettings({
        saved_keys: JSON.stringify(updated),
      });
    } catch (e) {
      console.error('Failed to update saved keys after delete:', e);
    }

    if (editingId === idToDelete) {
      handleAddNewKey();
    }
  };

  const handleAddNewKey = () => {
    setEditingId(null);
    setKeyName('');
    setBaseUrl('');
    setModelName('');
    setApiKey('');
    setTestResult(null);
  };

  const handleSaveForm = async (e) => {
    e?.preventDefault();
    if (!baseUrl.trim() || !modelName.trim()) {
      alert('Please provide both an API Base URL and Model Name.');
      return;
    }

    setSaving(true);
    const trimmedUrl = baseUrl.trim();
    const trimmedModel = modelName.trim();
    const trimmedKey = apiKey.trim();
    const nameToUse = keyName.trim() || trimmedModel || 'Custom AI Provider';

    let updatedList = [...savedKeys];

    // Check if we are updating by editingId OR if this exact key combination already exists
    let targetIndex = -1;
    if (editingId) {
      targetIndex = updatedList.findIndex((item) => item.id === editingId);
    }

    // If not found by ID, look for existing entry with identical credentials to prevent duplicate!
    if (targetIndex === -1) {
      targetIndex = updatedList.findIndex(
        (item) =>
          item.api_base_url.trim() === trimmedUrl &&
          item.model_name.trim() === trimmedModel &&
          item.api_key.trim() === trimmedKey
      );
    }

    let savedId;
    if (targetIndex !== -1) {
      // UPDATE existing key without duplicating
      savedId = updatedList[targetIndex].id;
      updatedList[targetIndex] = {
        ...updatedList[targetIndex],
        name: nameToUse,
        api_base_url: trimmedUrl,
        model_name: trimmedModel,
        api_key: trimmedKey,
        updated_at: new Date().toISOString(),
      };
    } else {
      // Create genuinely new key profile
      savedId = 'key-' + Date.now();
      const newProfile = {
        id: savedId,
        name: nameToUse,
        api_base_url: trimmedUrl,
        model_name: trimmedModel,
        api_key: trimmedKey,
        created_at: new Date().toISOString(),
      };
      updatedList.unshift(newProfile);
    }

    // Deduplicate entire list by signature to ensure zero duplicates
    updatedList = deduplicateKeys(updatedList);

    setSavedKeys(updatedList);
    localStorage.setItem('jobhelperguru_saved_keys', JSON.stringify(updatedList));

    try {
      // Save to backend, disable offline mode, and set as active
      await updateSettings({
        api_base_url: trimmedUrl,
        api_key: trimmedKey,
        model_name: trimmedModel,
        use_offline_mode: false,
        saved_keys: JSON.stringify(updatedList),
      });

      setActiveKeyId(savedId);
      setEditingId(savedId);
      setIsOfflineActive(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2000);
    } catch (err) {
      alert('Failed to save settings: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleTestConnection = async () => {
    if (!baseUrl.trim() || !modelName.trim()) {
      setTestResult({ success: false, message: 'Please enter API Base URL and Model Name to test.' });
      return;
    }

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

  const isEditingExisting = editingId && savedKeys.some((k) => k.id === editingId);

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto">
      <div className="glass-panel bg-[#0e0e11] border border-white/[0.12] w-full max-w-xl my-8 p-6 rounded-2xl space-y-5 animate-fade-in shadow-2xl max-h-[92vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <SettingsIcon size={18} />
            </div>
            <div>
              <h3 className="text-base font-bold text-white tracking-tight">AI Engine & API Keys</h3>
              <p className="text-xs text-zinc-400">
                Choose a saved API key profile or switch to the built-in offline heuristic
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-zinc-500 hover:text-white p-1 transition-colors"
          >
            ✕
          </button>
        </div>

        {/* 1. Built-in Offline Heuristic Engine Option */}
        <div
          className={`p-3.5 rounded-xl border transition-all text-xs flex items-center justify-between gap-3 ${
            isOfflineActive
              ? 'bg-emerald-950/40 border-emerald-500/80 shadow-md shadow-emerald-950/40'
              : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
          }`}
        >
          <div className="min-w-0 flex-1 space-y-1">
            <div className="flex items-center gap-2">
              <Zap size={16} className={isOfflineActive ? 'text-emerald-400' : 'text-slate-400'} />
              <span className="font-bold text-slate-100 text-sm">Built-in Offline Heuristic Engine</span>
              {isOfflineActive && (
                <span className="badge-pill bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-[10px] py-0.2 px-1.5 font-bold flex items-center gap-1">
                  <Check size={10} className="stroke-[3]" />
                  <span>Active</span>
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-400">
              Zero API keys required, zero network dependencies. Runs locally on your machine with high accuracy rule-based ATS matching and BulletSkill templates.
            </p>
          </div>

          {!isOfflineActive ? (
            <button
              type="button"
              onClick={handleSwitchToOffline}
              disabled={saving}
              className="px-3 py-1.5 rounded-lg bg-emerald-700 hover:bg-emerald-600 text-white text-xs font-bold shrink-0 transition-all shadow-sm flex items-center gap-1.5"
            >
              <Zap size={13} />
              <span>Use Offline</span>
            </button>
          ) : (
            <div className="text-[11px] font-bold text-emerald-400 shrink-0">
              Currently Selected ✓
            </div>
          )}
        </div>

        {/* 2. Saved Keys Section */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <ShieldCheck size={14} className="text-indigo-400" />
              <span>Saved API Keys ({savedKeys.length})</span>
            </label>
            <button
              type="button"
              onClick={handleAddNewKey}
              className="text-[11px] text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-medium"
            >
              <PlusCircle size={12} />
              <span>+ Add New Key</span>
            </button>
          </div>

          {savedKeys.length === 0 ? (
            <div className="p-4 rounded-xl border border-dashed border-slate-800 text-center text-xs text-slate-400">
              No saved keys yet. Enter your API URL, Model Name, and API Key below to save your first profile.
            </div>
          ) : (
            <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
              {savedKeys.map((item) => {
                const isActive = !isOfflineActive && activeKeyId === item.id;
                const isBeingEdited = editingId === item.id;

                return (
                  <div
                    key={item.id}
                    className={`p-3 rounded-xl border transition-all text-xs flex items-center justify-between gap-3 ${
                      isActive
                        ? 'bg-indigo-950/50 border-indigo-500/80 shadow-md shadow-indigo-950/40'
                        : isBeingEdited
                        ? 'bg-slate-800/80 border-cyan-500/60'
                        : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <div className="min-w-0 flex-1 space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-100 truncate">{item.name}</span>
                        {isActive && (
                          <span className="badge-pill bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-[10px] py-0.2 px-1.5 font-bold flex items-center gap-1">
                            <Check size={10} className="stroke-[3]" />
                            <span>Active</span>
                          </span>
                        )}
                        {isBeingEdited && (
                          <span className="badge-pill bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 text-[10px] py-0.2 px-1.5 font-semibold">
                            Loaded in Form
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-2 text-[11px] text-slate-400 truncate">
                        <span className="font-mono text-cyan-300">{item.model_name}</span>
                        <span>•</span>
                        <span className="font-mono text-slate-400 truncate">{item.api_base_url}</span>
                      </div>

                      <div className="font-mono text-[10px] text-slate-500">
                        Key: {maskKey(item.api_key)}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-1.5 shrink-0">
                      {!isActive && (
                        <button
                          type="button"
                          onClick={() => handleActivateKey(item)}
                          className="px-2.5 py-1 rounded bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm transition-all"
                          title="Use this saved key as active AI provider"
                        >
                          Activate
                        </button>
                      )}

                      <button
                        type="button"
                        onClick={() => handleEditKey(item)}
                        className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
                        title="Edit this saved key in form"
                      >
                        <Edit2 size={13} />
                      </button>

                      <button
                        type="button"
                        onClick={() => handleDeleteKey(item.id)}
                        className="p-1.5 rounded hover:bg-rose-950/40 text-slate-400 hover:text-rose-400 transition-colors"
                        title="Delete this saved key"
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* 3. Input Form */}
        <form onSubmit={handleSaveForm} className="space-y-4 pt-3 border-t border-slate-800">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
              {isEditingExisting ? 'Edit Selected Key Profile' : 'Configure New Key'}
            </h4>
            {isEditingExisting && (
              <button
                type="button"
                onClick={handleAddNewKey}
                className="text-[11px] text-slate-400 hover:text-slate-200 flex items-center gap-1"
              >
                <PlusCircle size={11} />
                <span>Switch to New Key</span>
              </button>
            )}
          </div>

          {/* Profile Name */}
          <div>
            <label className="block text-xs font-semibold text-slate-200 mb-1 flex items-center gap-1.5">
              <Tag size={13} className="text-indigo-400" />
              <span>Profile Name (Optional)</span>
            </label>
            <input
              type="text"
              value={keyName}
              onChange={(e) => setKeyName(e.target.value)}
              placeholder="e.g. My Google Gemini, OpenAI Work, Groq Fast"
              className="input-field text-xs"
            />
          </div>

          {/* API Base URL */}
          <div>
            <label className="block text-xs font-semibold text-slate-200 mb-1 flex items-center gap-1.5">
              <Globe size={13} className="text-indigo-400" />
              <span>API Base URL</span>
            </label>
            <input
              type="text"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="e.g. https://generativelanguage.googleapis.com/v1beta/openai/ or https://api.openai.com/v1"
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
              placeholder="Paste your API key here (AIzaSy... or sk-...)"
              className="input-field font-mono text-xs"
            />
          </div>

          {/* Test Connection Result */}
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
                Close
              </button>

              <button
                type="submit"
                disabled={saving}
                className="btn-primary text-xs"
              >
                {saving
                  ? 'Saving...'
                  : saveSuccess
                  ? 'Saved & Active! ✓'
                  : isEditingExisting
                  ? 'Update Saved Key'
                  : 'Save Key'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
