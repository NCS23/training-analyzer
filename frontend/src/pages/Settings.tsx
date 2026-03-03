import { useNavigate } from 'react-router-dom';
import { Card, CardBody, List, ListItem } from '@nordlig/components';
import {
  ChevronRight,
  ClipboardList,
  Dumbbell,
  Target,
  HeartPulse,
  CalendarRange,
} from 'lucide-react';

const tiles = [
  {
    title: 'Trainingspläne',
    description: 'Periodisierte Trainingspläne erstellen und verwalten',
    icon: CalendarRange,
    route: '/settings/plans',
  },
  {
    title: 'Session-Templates',
    description: 'Vorlagen fuer Kraft- und Lauftraining erstellen und verwalten',
    icon: ClipboardList,
    route: '/settings/templates',
  },
  {
    title: 'Übungsbibliothek',
    description: 'Übungen verwalten, Favoriten und Kategorien pflegen',
    icon: Dumbbell,
    route: '/settings/exercises',
  },
  {
    title: 'Wettkampf-Ziele',
    description: 'Ziele definieren und Fortschritt verfolgen',
    icon: Target,
    route: '/settings/goals',
  },
  {
    title: 'Athletenprofil',
    description: 'Herzfrequenz-Zonen und Höhenkorrektur',
    icon: HeartPulse,
    route: '/settings/athlete',
  },
];

export function SettingsPage() {
  const navigate = useNavigate();

  return (
    <div className="p-4 pt-8 md:p-6 md:pt-10 max-w-5xl mx-auto space-y-6">
      <header className="pb-2">
        <h1 className="text-2xl md:text-3xl font-semibold text-[var(--color-text-base)]">
          Einstellungen
        </h1>
        <p className="text-xs text-[var(--color-text-muted)] mt-1">
          App-Einstellungen und persönliche Daten verwalten.
        </p>
      </header>

      <Card elevation="raised" padding="spacious">
        <CardBody>
          <List variant="none" gap="xs">
            {tiles.map((tile) => (
              <ListItem
                key={tile.route}
                interactive
                icon={<tile.icon className="w-5 h-5" />}
                description={tile.description}
                action={<ChevronRight className="w-4 h-4 text-[var(--color-text-muted)]" />}
                onClick={() => navigate(tile.route)}
              >
                {tile.title}
              </ListItem>
            ))}
          </List>
        </CardBody>
      </Card>
    </div>
  );
}
