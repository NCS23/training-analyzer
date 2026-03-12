import { useState, useCallback, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { getSession, getSessionTrack, getWorkingZones, getKmSplits } from '@/api/training';
import type { SessionDetail, LapDetail, HRZone, GPSTrack, KmSplit } from '@/api/training';
import { useToast } from '@nordlig/components';

export interface SessionData {
  session: SessionDetail | null;
  loading: boolean;
  error: string | null;
  setError: (error: string | null) => void;
  setSession: React.Dispatch<React.SetStateAction<SessionDetail | null>>;
  localLaps: LapDetail[];
  setLocalLaps: React.Dispatch<React.SetStateAction<LapDetail[]>>;
  gpsTrack: GPSTrack | null;
  kmSplits: KmSplit[] | null;
  sessionGap: string | null;
  workingHrZones: Record<string, HRZone> | null;
  setWorkingHrZones: React.Dispatch<React.SetStateAction<Record<string, HRZone> | null>>;
  reload: () => Promise<void>;
}

export function useSessionData(sessionId: number): SessionData {
  const location = useLocation();
  const { toast } = useToast();

  const [session, setSession] = useState<SessionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [localLaps, setLocalLaps] = useState<LapDetail[]>([]);
  const [gpsTrack, setGpsTrack] = useState<GPSTrack | null>(null);
  const [kmSplits, setKmSplits] = useState<KmSplit[] | null>(null);
  const [sessionGap, setSessionGap] = useState<string | null>(null);
  const [workingHrZones, setWorkingHrZones] = useState<Record<string, HRZone> | null>(null);

  // eslint-disable-next-line complexity -- loading multiple dependent resources
  const loadSession = useCallback(async () => {
    if (!sessionId || isNaN(sessionId)) {
      setError('Ungültige Session-ID.');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const data = await getSession(sessionId);
      setSession(data);
      const loadedLaps = data.laps || [];
      setLocalLaps(loadedLaps);

      if (data.has_gps) {
        try {
          const trackData = await getSessionTrack(sessionId);
          if (trackData.has_gps && trackData.track) {
            setGpsTrack(trackData.track);
          }
        } catch {
          // GPS track is optional
        }
        try {
          const splitsData = await getKmSplits(sessionId);
          if (splitsData.has_splits && splitsData.splits) {
            setKmSplits(splitsData.splits);
            setSessionGap(splitsData.session_gap_formatted ?? null);
          }
        } catch {
          // km splits are optional
        }
      }

      const hasLapTypes = loadedLaps.some((l) => l.user_override || l.suggested_type);
      if (hasLapTypes && loadedLaps.length > 0) {
        try {
          const result = await getWorkingZones(sessionId);
          if (result.hr_zones_working) {
            setWorkingHrZones(result.hr_zones_working);
          }
        } catch {
          // working HR zones are optional
        }
      }
    } catch {
      setError('Session konnte nicht geladen werden.');
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    loadSession();
  }, [loadSession]);

  // Show toast after upload redirect
  useEffect(() => {
    if ((location.state as { uploaded?: boolean })?.uploaded) {
      window.history.replaceState({}, '');
      toast({ title: 'Training erfolgreich hochgeladen', variant: 'success' });
    }
  }, [location.state, toast]);

  return {
    session,
    loading,
    error,
    setError,
    setSession,
    localLaps,
    setLocalLaps,
    gpsTrack,
    kmSplits,
    sessionGap,
    workingHrZones,
    setWorkingHrZones,
    reload: loadSession,
  };
}
