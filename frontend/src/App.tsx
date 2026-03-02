import { Component, lazy, Suspense } from 'react';
import type { ReactNode, ErrorInfo } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Spinner, ToastProvider } from '@nordlig/components';
import { AppLayout } from './layouts/AppLayout';

/* ------------------------------------------------------------------ */
/*  Global Error Boundary                                              */
/* ------------------------------------------------------------------ */

class ErrorBoundary extends Component<
  { children: ReactNode },
  { hasError: boolean; error: Error | null }
> {
  state = { hasError: false, error: null as Error | null };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[ErrorBoundary]', error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-6 max-w-2xl mx-auto mt-12 space-y-4">
          <h1 className="text-xl font-semibold text-[var(--color-text-error)]">
            Etwas ist schiefgelaufen
          </h1>
          <pre className="text-sm bg-[var(--color-bg-subtle)] rounded-[var(--radius-component-sm)] p-4 overflow-auto whitespace-pre-wrap text-[var(--color-text-base)]">
            {this.state.error?.message}
            {'\n\n'}
            {this.state.error?.stack}
          </pre>
          <button
            onClick={() => {
              this.setState({ hasError: false, error: null });
              window.location.reload();
            }}
            className="px-4 py-2 bg-[var(--color-interactive-primary)] text-[var(--color-text-on-primary)] rounded-[var(--radius-component-sm)] text-sm"
          >
            Seite neu laden
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

/* ------------------------------------------------------------------ */
/*  App                                                                */
/* ------------------------------------------------------------------ */

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const DashboardPage = lazy(() =>
  import('./pages/Dashboard').then((m) => ({ default: m.DashboardPage })),
);
const SessionsPage = lazy(() =>
  import('./pages/Sessions').then((m) => ({ default: m.SessionsPage })),
);
const SessionDetailPage = lazy(() =>
  import('./pages/SessionDetail').then((m) => ({ default: m.SessionDetailPage })),
);
const UploadPage = lazy(() => import('./pages/Upload'));
const SettingsPage = lazy(() =>
  import('./pages/Settings').then((m) => ({ default: m.SettingsPage })),
);
const StrengthSessionPage = lazy(() =>
  import('./pages/StrengthSession').then((m) => ({ default: m.StrengthSessionPage })),
);
const AnalysePage = lazy(() =>
  import('./pages/Analyse').then((m) => ({ default: m.AnalysePage })),
);
const ExerciseLibraryPage = lazy(() =>
  import('./pages/ExerciseLibrary').then((m) => ({ default: m.ExerciseLibraryPage })),
);
const ExerciseDetailPage = lazy(() =>
  import('./pages/ExerciseDetail').then((m) => ({ default: m.ExerciseDetailPage })),
);
const SessionTemplatesPage = lazy(() =>
  import('./pages/SessionTemplates').then((m) => ({ default: m.SessionTemplatesPage })),
);
const SessionTemplateEditorPage = lazy(() =>
  import('./pages/SessionTemplateEditor').then((m) => ({ default: m.SessionTemplateEditorPage })),
);
const TrainingPlansPage = lazy(() =>
  import('./pages/TrainingPlans').then((m) => ({ default: m.TrainingPlansPage })),
);
const TrainingPlanEditorPage = lazy(() =>
  import('./pages/TrainingPlanEditor').then((m) => ({ default: m.TrainingPlanEditorPage })),
);
const WeeklyPlanPage = lazy(() =>
  import('./pages/WeeklyPlan').then((m) => ({ default: m.WeeklyPlanPage })),
);
const GoalsPage = lazy(() => import('./pages/Goals').then((m) => ({ default: m.GoalsPage })));
const AthleteProfilePage = lazy(() =>
  import('./pages/AthleteProfile').then((m) => ({ default: m.AthleteProfilePage })),
);
const NotFoundPage = lazy(() =>
  import('./pages/NotFound').then((m) => ({ default: m.NotFoundPage })),
);

function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-[50vh]">
      <Spinner size="lg" />
    </div>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <ToastProvider position="bottom-right">
            <Suspense fallback={<PageLoader />}>
              <Routes>
                <Route element={<AppLayout />}>
                  <Route index element={<Navigate to="/dashboard" replace />} />
                  <Route path="/dashboard" element={<DashboardPage />} />
                  <Route path="/sessions" element={<SessionsPage />} />
                  <Route path="/sessions/new" element={<UploadPage />} />
                  <Route path="/sessions/new/strength" element={<StrengthSessionPage />} />
                  <Route path="/sessions/:id" element={<SessionDetailPage />} />
                  <Route path="/analyse" element={<AnalysePage />} />
                  <Route path="/trends" element={<Navigate to="/analyse" replace />} />
                  <Route path="/strength/progression" element={<Navigate to="/analyse" replace />} />
                  <Route path="/balance" element={<Navigate to="/analyse" replace />} />
                  <Route path="/plan" element={<WeeklyPlanPage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                  <Route path="/settings/exercises" element={<ExerciseLibraryPage />} />
                  <Route path="/settings/exercises/:exerciseId" element={<ExerciseDetailPage />} />
                  <Route path="/settings/plans" element={<TrainingPlansPage />} />
                  <Route path="/settings/plans/new" element={<TrainingPlanEditorPage />} />
                  <Route path="/settings/plans/:planId" element={<TrainingPlanEditorPage />} />
                  <Route path="/settings/templates" element={<SessionTemplatesPage />} />
                  <Route path="/settings/templates/new" element={<SessionTemplateEditorPage />} />
                  <Route
                    path="/settings/templates/:templateId"
                    element={<SessionTemplateEditorPage />}
                  />
                  <Route path="/settings/goals" element={<GoalsPage />} />
                  <Route path="/settings/athlete" element={<AthleteProfilePage />} />
                  <Route path="*" element={<NotFoundPage />} />
                </Route>
              </Routes>
            </Suspense>
          </ToastProvider>
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
