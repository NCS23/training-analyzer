import {
  Card,
  CardHeader,
  CardBody,
  CardFooter,
  Button,
  Label,
  Alert,
  AlertDescription,
  Spinner,
  PasswordInput,
} from '@nordlig/components';
import type { ApiKeyState } from '@/hooks/useApiKeySettings';

interface ApiKeyFieldProps {
  id: string;
  label: string;
  placeholder: string;
  isSet: boolean;
  value: string;
  onChange: (v: string) => void;
  onClear: () => void;
  disabled: boolean;
}

function ApiKeyField({
  id,
  label,
  placeholder,
  isSet,
  value,
  onChange,
  onClear,
  disabled,
}: ApiKeyFieldProps) {
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>{label}</Label>
      {isSet && (
        <div className="flex items-center gap-2">
          <span className="text-xs text-[var(--color-text-success)]">Konfiguriert</span>
          <Button variant="ghost" size="sm" onClick={onClear} disabled={disabled}>
            Entfernen
          </Button>
        </div>
      )}
      <PasswordInput
        id={id}
        placeholder={isSet ? 'Neuen Schlüssel eingeben...' : placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}

export function ApiKeyCard({ keys }: { keys: ApiKeyState }) {
  return (
    <Card elevation="raised" padding="spacious">
      <CardHeader>
        <h2 className="text-sm font-semibold text-[var(--color-text-base)]">API-Schlüssel</h2>
      </CardHeader>
      <CardBody>
        <p className="text-xs text-[var(--color-text-muted)] mb-4">
          Eigene API-Schlüssel für die KI-Analyse. Ohne Schlüssel wird der serverseitige Fallback
          verwendet.
        </p>
        <div className="space-y-4">
          <ApiKeyField
            id="claude-key"
            label="Anthropic (Claude)"
            placeholder="sk-ant-..."
            isSet={keys.claudeKeySet}
            value={keys.claudeKey}
            onChange={keys.setClaudeKey}
            onClear={() => keys.clearKey('claude')}
            disabled={keys.saving}
          />
          <ApiKeyField
            id="openai-key"
            label="OpenAI"
            placeholder="sk-..."
            isSet={keys.openaiKeySet}
            value={keys.openaiKey}
            onChange={keys.setOpenaiKey}
            onClear={() => keys.clearKey('openai')}
            disabled={keys.saving}
          />
        </div>

        {keys.error && (
          <Alert variant="error" closeable onClose={() => keys.setError(null)} className="mt-4">
            <AlertDescription>{keys.error}</AlertDescription>
          </Alert>
        )}
      </CardBody>
      <CardFooter className="justify-end pt-4">
        <Button
          variant="primary"
          onClick={keys.saveKeys}
          disabled={keys.saving || (!keys.claudeKey && !keys.openaiKey)}
        >
          {keys.saving ? <Spinner size="sm" aria-hidden="true" /> : 'Speichern'}
        </Button>
      </CardFooter>
    </Card>
  );
}
