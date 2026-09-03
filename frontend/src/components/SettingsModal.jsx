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

    let targetIndex = -1;
    if (editingId) {
      targetIndex = updatedList.findIndex((item) => item.id === editingId);
    }

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

    updatedList = deduplicateKeys(updatedList);
    setSavedKeys(updatedList);
    localStorage.setItem('jobhelperguru_saved_keys', JSON.stringify(updatedList));

    try {
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
    <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
      <div className="card-corporate bg-white border border-[#e0e0e0] w-full max-w-xl my-8 p-6 rounded-xl space-y-5 animate-fade-in shadow-xl max-h-[92vh] overflow-y-auto text-[#000000]">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-[#e0e0e0]">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-full bg-[#0a66c2]/10 text-[#0a66c2]">
              <SettingsIcon size={18} />
            </div>
            <div>
              <h3 className="text-base font-bold text-[#000000] tracking-tight">AI Engine & API Keys</h3>
              <p className="text-xs text-[#666666]">
                Choose a saved API key profile or switch to the built-in offline heuristic
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-[#666666] hover:text-[#000000] p-1 transition-colors text-base"
          >
            ✕
          </button>
        </div>

        {/* 1. Built-in Offline Heuristic Engine Option */}
        <div
          className={`p-3.5 rounded-lg border transition-all text-xs flex items-center justify-between gap-3 ${
            isOfflineActive
              ? 'bg-[#057642]/10 border-2 border-[#057642]'
              : 'bg-[#f3f6f8] border border-[#e0e0e0] hover:border-[#c1c6d4]'
          }`}
        >
          <div className="min-w-0 flex-1 space-y-1">
            <div className="flex items-center gap-2">
              <Zap size={16} className={isOfflineActive ? 'text-[#057642]' : 'text-[#666666]'} />
              <span className="font-bold text-[#000000] text-sm">Built-in Offline Heuristic Engine</span>
              {isOfflineActive && (
                <span className="badge-corporate bg-[#057642]/10 border border-[#057642]/25 text-[#057642] text-[10px] py-0.2 px-1.5 font-bold flex items-center gap-1">
                  <Check size={10} className="stroke-[3]" />
                  <span>Active</span>
                </span>
              )}
            </div>
            <p className="text-[11px] text-[#666666]">
              Zero API keys required, zero network dependencies. Runs locally on your machine with high accuracy rule-based ATS matching and BulletSkill templates.
            </p>
          </div>

          {!isOfflineActive ? (
            <button
              type="button"
              onClick={handleSwitchToOffline}
              disabled={saving}
              className="btn-secondary-corporate text-xs py-1 px-3 shrink-0 flex items-center gap-1.5"
            >
              <Zap size={13} />
              <span>Use Offline</span>
            </button>
          ) : (
            <div className="text-[11px] font-bold text-[#057642] shrink-0">
              Currently Selected ✓
            </div>
          )}
        </div>

        {/* 2. Saved Keys Section */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-xs font-bold text-[#000000] uppercase tracking-wider flex items-center gap-1.5">
              <ShieldCheck size={14} className="text-[#0a66c2]" />
              <span>Saved API Keys ({savedKeys.length})</span>
            </label>
            <button
              type="button"
              onClick={handleAddNewKey}
              className="text-[11px] text-[#0a66c2] hover:underline flex items-center gap-1 font-semibold"
            >
              <PlusCircle size={12} />
              <span>+ Add New Key</span>
            </button>
          </div>

          {savedKeys.length === 0 ? (
            <div className="p-4 rounded-lg border border-dashed border-[#e0e0e0] bg-[#f3f6f8] text-center text-xs text-[#666666]">
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
                    className={`p-3 rounded-lg border transition-all text-xs flex items-center justify-between gap-3 ${
                      isActive
                        ? 'bg-[#0a66c2]/5 border-2 border-[#0a66c2]'
                        : isBeingEdited
                        ? 'bg-[#f3f6f8] border border-[#0a66c2]'
                        : 'bg-[#f3f6f8] border border-[#e0e0e0] hover:border-[#c1c6d4]'
                    }`}
                  >
                    <div className="min-w-0 flex-1 space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-[#000000] truncate">{item.name}</span>
                        {isActive && (
                          <span className="badge-corporate bg-[#057642]/10 border border-[#057642]/25 text-[#057642] text-[10px] py-0.2 px-1.5 font-bold flex items-center gap-1">
                            <Check size={10} className="stroke-[3]" />
                            <span>Active</span>
                          </span>
                        )}
                        {isBeingEdited && (
                          <span className="badge-corporate bg-[#0a66c2]/10 border border-[#0a66c2]/25 text-[#0a66c2] text-[10px] py-0.2 px-1.5 font-semibold">
                            Loaded in Form
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-2 text-[11px] text-[#666666] truncate">
                        <span className="font-mono text-[#0a66c2] font-semibold">{item.model_name}</span>
                        <span>-</span>
                        <span className="font-mono text-[#666666] truncate">{item.api_base_url}</span>
                      </div>

                      <div className="font-mono text-[10px] text-[#666666]">
                        Key: {maskKey(item.api_key)}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-1.5 shrink-0">
                      {!isActive && (
                        <button
                          type="button"
                          onClick={() => handleActivateKey(item)}
                          className="btn-primary-corporate text-xs py-1 px-3"
                          title="Use this saved key as active AI provider"
                        >
                          Activate
                        </button>
                      )}

                      <button
                        type="button"
                        onClick={() => handleEditKey(item)}
                        className="p-1.5 rounded hover:bg-white text-[#666666] hover:text-[#000000] transition-colors"
                        title="Edit this saved key in form"
                      >
                        <Edit2 size={13} />
                      </button>

                      <button
                        type="button"
                        onClick={() => handleDeleteKey(item.id)}
                        className="p-1.5 rounded hover:bg-white text-[#666666] hover:text-[#b24020] transition-colors"
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
        <form onSubmit={handleSaveForm} className="space-y-4 pt-3 border-t border-[#e0e0e0]">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold text-[#000000] uppercase tracking-wider">
              {isEditingExisting ? 'Edit Selected Key Profile' : 'Configure New Key'}
            </h4>
            {isEditingExisting && (
              <button
                type="button"
                onClick={handleAddNewKey}
                className="text-[11px] text-[#666666] hover:text-[#000000] flex items-center gap-1 font-semibold"
              >
                <PlusCircle size={11} />
                <span>Switch to New Key</span>
              </button>
            )}
          </div>

          {/* Profile Name */}
          <div>
            <label className="block text-xs font-semibold text-[#000000] mb-1 flex items-center gap-1.5">
              <Tag size={13} className="text-[#0a66c2]" />
              <span>Profile Name (Optional)</span>
            </label>
            <input
              type="text"
              value={keyName}
              onChange={(e) => setKeyName(e.target.value)}
              placeholder="e.g. My Google Gemini, OpenAI Work, Groq Fast"
              className="input-corporate w-full text-xs"
            />
          </div>

          {/* API Base URL */}
          <div>
            <label className="block text-xs font-semibold text-[#000000] mb-1 flex items-center gap-1.5">
              <Globe size={13} className="text-[#0a66c2]" />
              <span>API Base URL</span>
            </label>
            <input
              type="text"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="e.g. https://generativelanguage.googleapis.com/v1beta/openai/ or https://api.openai.com/v1"
              className="input-corporate w-full font-mono text-xs"
              required
            />
          </div>

          {/* Model Name */}
          <div>
            <label className="block text-xs font-semibold text-[#000000] mb-1 flex items-center gap-1.5">
              <Cpu size={13} className="text-[#0a66c2]" />
              <span>Model Name</span>
            </label>
            <input
              type="text"
              value={modelName}
              onChange={(e) => setModelName(e.target.value)}
              placeholder="e.g. gemini-2.0-flash, gpt-4o-mini, or anthropic/claude-3.5-sonnet"
              className="input-corporate w-full font-mono text-xs"
              required
            />
          </div>

          {/* API Key */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-semibold text-[#000000] flex items-center gap-1.5">
                <Key size={13} className="text-[#0a66c2]" />
                <span>API Key</span>
              </label>
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="text-[11px] text-[#0a66c2] hover:underline font-semibold"
              >
                {showKey ? 'Hide' : 'Reveal'}
              </button>
            </div>
            <input
              type={showKey ? 'text' : 'password'}
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Paste your API key here (AIzaSy... or sk-...)"
              className="input-corporate w-full font-mono text-xs"
            />
          </div>

          {/* Test Connection Result */}
          {testResult && (
            <div
              className={`p-3 rounded-lg border text-xs flex items-start gap-2 ${
                testResult.success
                  ? 'bg-[#057642]/10 border-[#057642]/25 text-[#057642]'
                  : 'bg-[#b24020]/10 border-[#b24020]/25 text-[#b24020]'
              }`}
            >
              {testResult.success ? (
                <Check size={16} className="text-[#057642] shrink-0 mt-0.5" />
              ) : (
                <AlertCircle size={16} className="text-[#b24020] shrink-0 mt-0.5" />
              )}
              <span className="leading-relaxed">{testResult.message}</span>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center justify-between pt-3 border-t border-[#e0e0e0]">
            <button
              type="button"
              onClick={handleTestConnection}
              disabled={testing}
              className="btn-secondary-corporate text-xs py-1 px-3"
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
                className="btn-secondary-corporate text-xs py-1 px-3.5"
              >
                Close
              </button>

              <button
                type="submit"
                disabled={saving}
                className="btn-primary-corporate text-xs py-1 px-4"
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
