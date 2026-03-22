import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getRaceReport,
  triggerRaceAnalysis,
  type RaceReportData,
  type RaceAnalysis,
} from '@/api/training';

export function useRaceReport(sessionId: number) {
  const queryClient = useQueryClient();

  const reportQuery = useQuery<RaceReportData>({
    queryKey: ['race-report', sessionId],
    queryFn: () => getRaceReport(sessionId),
  });

  const analysisMutation = useMutation<RaceAnalysis>({
    mutationFn: () => triggerRaceAnalysis(sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['race-report', sessionId] });
    },
  });

  return {
    report: reportQuery.data ?? null,
    isLoading: reportQuery.isLoading,
    error: reportQuery.error,
    analysis: analysisMutation.data ?? null,
    isAnalyzing: analysisMutation.isPending,
    triggerAnalysis: analysisMutation.mutate,
  };
}
