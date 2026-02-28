import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  DashboardLayout,
  Sidebar as DSSidebar,
  SidebarContent,
  SidebarGroup,
  SidebarItem,
  Icon,
  Text,
} from '@nordlig/components';
import { LayoutDashboard, Dumbbell, TrendingUp, Weight, Settings } from 'lucide-react';
import { BottomNav } from './BottomNav';

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/sessions', label: 'Sessions', icon: Dumbbell },
  { to: '/trends', label: 'Trends', icon: TrendingUp },
  { to: '/strength/progression', label: 'Kraft', icon: Weight },
  { to: '/settings', label: 'Einstellungen', icon: Settings },
];

function HeaderContent() {
  return (
    <>
      <Dumbbell className="w-5 h-5 text-[color:var(--color-interactive-primary)]" />
      <Text as="span" className="font-semibold text-sm tracking-tight">
        Training Analyzer
      </Text>
      <div className="ml-auto" />
    </>
  );
}

function SidebarNav() {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <DSSidebar>
      <SidebarContent>
        <SidebarGroup>
          {navItems.map(({ to, label, icon }) => (
            <SidebarItem
              key={to}
              icon={<Icon icon={icon} size="sm" />}
              label={label}
              active={location.pathname.startsWith(to)}
              onClick={() => navigate(to)}
            />
          ))}
        </SidebarGroup>
      </SidebarContent>
    </DSSidebar>
  );
}

export function AppLayout() {
  return (
    <DashboardLayout>
      <DashboardLayout.Header>
        <HeaderContent />
      </DashboardLayout.Header>
      <DashboardLayout.Body>
        <DashboardLayout.Sidebar>
          <SidebarNav />
        </DashboardLayout.Sidebar>
        <DashboardLayout.Content noPadding>
          <div className="pb-16 md:pb-0">
            <Outlet />
          </div>
        </DashboardLayout.Content>
      </DashboardLayout.Body>
      <BottomNav />
    </DashboardLayout>
  );
}
