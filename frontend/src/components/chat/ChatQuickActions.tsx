import { Button } from '@nordlig/components';

interface ChatQuickActionsProps {
  onSelect: (question: string) => void;
  disabled?: boolean;
}

const QUICK_QUESTIONS = [
  'Wie war meine Trainingswoche?',
  'Kann ich morgen schneller laufen?',
  'Wann ist der naechste Ruhetag?',
  'Soll ich den Trainingsplan anpassen?',
  'Wie steht es um mein Wettkampfziel?',
  'Was soll ich heute trainieren?',
];

export function ChatQuickActions({ onSelect, disabled }: ChatQuickActionsProps) {
  return (
    <div className="space-y-3">
      <p className="text-sm text-[var(--color-text-muted)] text-center">
        Frag mich etwas zu deinem Training:
      </p>
      <div className="flex flex-wrap justify-center gap-2">
        {QUICK_QUESTIONS.map((q) => (
          <Button
            key={q}
            variant="secondary"
            size="sm"
            onClick={() => onSelect(q)}
            disabled={disabled}
          >
            {q}
          </Button>
        ))}
      </div>
    </div>
  );
}
