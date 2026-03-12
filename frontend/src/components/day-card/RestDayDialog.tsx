import { useState } from 'react';
import {
  Button,
  Input,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@nordlig/components';
import { ArrowRightLeft, CircleSlash, EllipsisVertical, Moon, Pencil, Trash2 } from 'lucide-react';
import { MoveSessionDialog } from '../MoveSessionDialog';

export interface RestDayDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  notes: string | null;
  dayOfWeek: number;
  onSaveNotes: (notes: string | null) => void;
  onRemoveRestDay: () => void;
  onMoveRestDay?: (targetDay: number) => void;
}

// eslint-disable-next-line max-lines-per-function -- Dialog mit Read/Edit-Modus + Kebab-Menü
export function RestDayDialog({
  open,
  onOpenChange,
  notes,
  dayOfWeek,
  onSaveNotes,
  onRemoveRestDay,
  onMoveRestDay,
}: RestDayDialogProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [localNotes, setLocalNotes] = useState(notes ?? '');
  const [showMoveDialog, setShowMoveDialog] = useState(false);

  const [prevOpen, setPrevOpen] = useState(false);
  if (open && !prevOpen) {
    setLocalNotes(notes ?? '');
    setIsEditing(false);
  }
  if (open !== prevOpen) setPrevOpen(open);

  const handleSave = () => {
    onSaveNotes(localNotes.trim() || null);
    setIsEditing(false);
    onOpenChange(false);
  };

  const handleRemove = () => {
    onRemoveRestDay();
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle>
              <span className="flex items-center gap-2">
                <Moon className="w-4 h-4 text-[var(--color-text-muted)]" />
                Ruhetag
              </span>
            </DialogTitle>
            {!isEditing && (
              <DropdownMenu>
                <DropdownMenuTrigger>
                  <Button variant="ghost" size="sm" aria-label="Ruhetag Optionen">
                    <EllipsisVertical className="w-4 h-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem icon={<Pencil />} onSelect={() => setIsEditing(true)}>
                    Bearbeiten
                  </DropdownMenuItem>
                  <DropdownMenuItem icon={<CircleSlash />} onSelect={handleRemove}>
                    Ausfallen lassen
                  </DropdownMenuItem>
                  {onMoveRestDay && (
                    <DropdownMenuItem
                      icon={<ArrowRightLeft />}
                      onSelect={() => setShowMoveDialog(true)}
                    >
                      Verschieben
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuItem icon={<Trash2 />} onSelect={handleRemove}>
                    Entfernen
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </div>
        </DialogHeader>

        <div className="space-y-3">
          {!isEditing && (
            <p className="text-sm text-[var(--color-text-muted)]">
              {notes ? notes : 'Keine Notizen.'}
            </p>
          )}

          {isEditing && (
            <Input
              type="text"
              value={localNotes}
              onChange={(e) => setLocalNotes(e.target.value)}
              inputSize="sm"
              placeholder="Notizen (z.B. Regeneration, Stretching)"
              aria-label="Ruhetag Notizen"
            />
          )}
        </div>

        {isEditing && (
          <DialogFooter>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setLocalNotes(notes ?? '');
                setIsEditing(false);
              }}
            >
              Abbrechen
            </Button>
            <Button size="sm" onClick={handleSave}>
              Speichern
            </Button>
          </DialogFooter>
        )}
      </DialogContent>

      {onMoveRestDay && (
        <MoveSessionDialog
          open={showMoveDialog}
          onOpenChange={setShowMoveDialog}
          currentDay={dayOfWeek}
          sessionLabel="Ruhetag"
          onSelectDay={(targetDay) => {
            setShowMoveDialog(false);
            onOpenChange(false);
            onMoveRestDay(targetDay);
          }}
        />
      )}
    </Dialog>
  );
}
