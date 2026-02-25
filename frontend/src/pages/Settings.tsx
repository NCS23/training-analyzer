import { Card, CardBody } from '@nordlig/components';

export function SettingsPage() {
  return (
    <div className="p-4 md:p-6 max-w-3xl mx-auto space-y-6">
      <h1 className="text-xl font-semibold text-[var(--color-text-base)]">Einstellungen</h1>

      <Card elevation="raised">
        <CardBody className="flex flex-col items-center py-12 text-center">
          <p className="text-sm text-[var(--color-text-muted)]">
            Einstellungen werden spaeter implementiert.
          </p>
        </CardBody>
      </Card>
    </div>
  );
}
