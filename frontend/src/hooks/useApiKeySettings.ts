import { useState } from 'react';
import { useToast } from '@nordlig/components';
import { getUserSettings, updateUserSettings, type UserSettings } from '@/api/userSettings';

export interface ApiKeyState {
  claudeKey: string;
  openaiKey: string;
  claudeKeySet: boolean;
  openaiKeySet: boolean;
  saving: boolean;
  error: string | null;
  setClaudeKey: (v: string) => void;
  setOpenaiKey: (v: string) => void;
  setError: (v: string | null) => void;
  loadKeys: () => Promise<void>;
  saveKeys: () => Promise<void>;
  clearKey: (provider: 'claude' | 'openai') => Promise<void>;
}

export function useApiKeySettings(): ApiKeyState {
  const { toast } = useToast();

  const [claudeKey, setClaudeKey] = useState('');
  const [openaiKey, setOpenaiKey] = useState('');
  const [claudeKeySet, setClaudeKeySet] = useState(false);
  const [openaiKeySet, setOpenaiKeySet] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const applyResult = (result: UserSettings) => {
    setClaudeKeySet(result.claude_api_key_set);
    setOpenaiKeySet(result.openai_api_key_set);
  };

  const loadKeys = async () => {
    const result = await getUserSettings();
    applyResult(result);
  };

  const saveKeys = async () => {
    if (!claudeKey && !openaiKey) return;

    setSaving(true);
    setError(null);

    try {
      const params: { claude_api_key?: string; openai_api_key?: string } = {};
      if (claudeKey) params.claude_api_key = claudeKey;
      if (openaiKey) params.openai_api_key = openaiKey;

      const result = await updateUserSettings(params);
      applyResult(result);
      setClaudeKey('');
      setOpenaiKey('');
      toast({ title: 'API-Schlüssel gespeichert', variant: 'success' });
    } catch {
      setError('Speichern fehlgeschlagen');
    } finally {
      setSaving(false);
    }
  };

  const clearKey = async (provider: 'claude' | 'openai') => {
    setSaving(true);
    setError(null);

    try {
      const params = provider === 'claude' ? { claude_api_key: '' } : { openai_api_key: '' };
      const result = await updateUserSettings(params);
      applyResult(result);
      toast({ title: 'API-Schlüssel entfernt', variant: 'success' });
    } catch {
      setError('Entfernen fehlgeschlagen');
    } finally {
      setSaving(false);
    }
  };

  return {
    claudeKey,
    openaiKey,
    claudeKeySet,
    openaiKeySet,
    saving,
    error,
    setClaudeKey,
    setOpenaiKey,
    setError,
    loadKeys,
    saveKeys,
    clearKey,
  };
}
