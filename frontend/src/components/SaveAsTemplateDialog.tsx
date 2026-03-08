import { useState } from 'react';
import {
  Button,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  Input,
  useToast,
} from '@nordlig/components';
import { Loader2 } from 'lucide-react';
import type { RunDetails } from '@/api/weekly-plan';
import { createSessionTemplate, type TemplateExercise } from '@/api/session-templates';

interface SaveAsTemplateDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  runDetails?: RunDetails;
  exercises?: TemplateExercise[];
  sessionType?: string;
  defaultName: string;
}

export function SaveAsTemplateDialog({
  open,
  onOpenChange,
  runDetails,
  exercises,
  sessionType,
  defaultName,
}: SaveAsTemplateDialogProps) {
  const { toast } = useToast();
  const [name, setName] = useState(defaultName);
  const [description, setDescription] = useState('');
  const [saving, setSaving] = useState(false);

  // Reset state when dialog opens
  const [prevOpen, setPrevOpen] = useState(false);
  if (open && !prevOpen) {
    setName(defaultName);
    setDescription('');
    setSaving(false);
  }
  if (open !== prevOpen) setPrevOpen(open);

  const handleSave = async () => {
    if (!name.trim()) return;
    setSaving(true);
    try {
      const type = sessionType ?? 'running';
      await createSessionTemplate({
        name: name.trim(),
        description: description.trim() || undefined,
        session_type: type,
        ...(type === 'running' && runDetails ? { run_details: runDetails } : {}),
        ...(type === 'strength' && exercises ? { exercises } : {}),
      });
      toast({ title: 'Vorlage erstellt', variant: 'success' });
      onOpenChange(false);
    } catch {
      toast({ title: 'Vorlage konnte nicht erstellt werden', variant: 'error' });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Als Vorlage speichern</DialogTitle>
        </DialogHeader>

        <div className="space-y-3">
          <div>
            <label
              htmlFor="template-name"
              className="text-xs font-medium text-[var(--color-text-muted)] mb-1 block"
            >
              Name *
            </label>
            <Input
              id="template-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              inputSize="sm"
              placeholder="z.B. Intervalle 4×3min"
              autoFocus
            />
          </div>

          <div>
            <label
              htmlFor="template-description"
              className="text-xs font-medium text-[var(--color-text-muted)] mb-1 block"
            >
              Beschreibung
            </label>
            <Input
              id="template-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              inputSize="sm"
              placeholder="Optional"
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="ghost" size="sm" onClick={() => onOpenChange(false)} disabled={saving}>
            Abbrechen
          </Button>
          <Button size="sm" onClick={handleSave} disabled={!name.trim() || saving}>
            {saving && <Loader2 className="w-3.5 h-3.5 animate-spin mr-1.5" />}
            Erstellen
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
