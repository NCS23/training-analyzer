import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Spinner } from '@nordlig/components';
import { AppLayout } from './layouts/AppLayout';

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
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route element={<AppLayout />}>
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/sessions" element={<SessionsPage />} />
              <Route path="/sessions/new" element={<UploadPage />} />
              <Route path="/sessions/:id" element={<SessionDetailPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="*" element={<NotFoundPage />} />
            </Route>
          </Routes>
        </Suspense>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
