import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { BottomNav } from './BottomNav';

export function AppLayout() {
  return (
    <div className="flex min-h-screen bg-[var(--color-bg-paper)]">
      <Sidebar />

      <main className="flex-1 overflow-y-auto h-screen pb-16 md:pb-0">
        <Outlet />
      </main>

      <BottomNav />
    </div>
  );
}
