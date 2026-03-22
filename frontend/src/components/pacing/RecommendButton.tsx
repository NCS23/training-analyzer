import { useState } from 'react';
import { Button, Spinner, Alert, AlertDescription, useToast } from '@nordlig/components';
import { Sparkles } from 'lucide-react';
import { getPacingRecommendation } from '@/api/pacing';
import type { PacingRecommendationResponse } from '@/api/pacing';

interface RecommendButtonProps {
  raceName: string;
  distanceKm: number | null;
  targetTimeSeconds: number | null;
  disabled?: boolean;
  onRecommendation: (rec: PacingRecommendationResponse) => void;
}

export function RecommendButton({
  raceName,
  distanceKm,
  targetTimeSeconds,
  disabled,
  onRecommendation,
}: RecommendButtonProps) {
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);

  const handleClick = async () => {
    if (!distanceKm || distanceKm <= 0 || !targetTimeSeconds || targetTimeSeconds <= 0) {
      toast({ title: 'Bitte zuerst Distanz und Zielzeit eingeben', variant: 'error' });
      return;
    }
    setLoading(true);
    try {
      const rec = await getPacingRecommendation({
        race_name: raceName || null,
        distance_km: distanceKm,
        target_time_seconds: targetTimeSeconds,
      });
      onRecommendation(rec);
    } catch {
      toast({ title: 'KI-Empfehlung fehlgeschlagen', variant: 'error' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button variant="ghost" size="sm" onClick={handleClick} disabled={disabled || loading}>
      {loading ? <Spinner size="sm" aria-hidden="true" /> : <Sparkles size={14} />}
      KI-Empfehlung
    </Button>
  );
}

export function RecommendReasoning({
  reasoning,
  onClose,
}: {
  reasoning: string;
  onClose: () => void;
}) {
  return (
    <Alert variant="info" closeable onClose={onClose}>
      <AlertDescription>
        <strong>KI-Empfehlung:</strong> {reasoning}
      </AlertDescription>
    </Alert>
  );
}
