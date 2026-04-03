import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, Button, Spinner, Badge, Breadcrumbs, BreadcrumbItem } from '@nordlig/components';
import { Link } from 'react-router-dom';
import { getUsers, updateUser, deactivateUser } from '@/api/admin';
import type { AdminUser } from '@/api/admin';
import { useAuth } from '@/hooks/useAuth';

/* ------------------------------------------------------------------ */
/*  Role badge helpers                                                  */
/* ------------------------------------------------------------------ */

const roleBadgeVariant: Record<string, 'warning' | 'success' | 'info' | 'neutral'> = {
  pending: 'warning',
  admin: 'success',
  user: 'info',
};

const roleLabel: Record<string, string> = {
  pending: 'Ausstehend',
  admin: 'Admin',
  user: 'Nutzer',
};

/* ------------------------------------------------------------------ */
/*  Action hooks                                                        */
/* ------------------------------------------------------------------ */

function useUserActions(adminUser: AdminUser) {
  const queryClient = useQueryClient();
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });

  const approve = useMutation({
    mutationFn: () => updateUser(adminUser.id, { role: 'user', is_active: true }),
    onSuccess: invalidate,
  });
  const reject = useMutation({
    mutationFn: () => deactivateUser(adminUser.id),
    onSuccess: invalidate,
  });
  const toggleRole = useMutation({
    mutationFn: () =>
      updateUser(adminUser.id, { role: adminUser.role === 'admin' ? 'user' : 'admin' }),
    onSuccess: invalidate,
  });
  const toggleActive = useMutation({
    mutationFn: () => updateUser(adminUser.id, { is_active: !adminUser.is_active }),
    onSuccess: invalidate,
  });

  const isAnyLoading =
    approve.isPending || reject.isPending || toggleRole.isPending || toggleActive.isPending;

  return { approve, reject, toggleRole, toggleActive, isAnyLoading };
}

/* ------------------------------------------------------------------ */
/*  User row                                                            */
/* ------------------------------------------------------------------ */

function UserRow({ adminUser, currentUserId }: { adminUser: AdminUser; currentUserId: number }) {
  const isSelf = adminUser.id === currentUserId;
  const { approve, reject, toggleRole, toggleActive, isAnyLoading } = useUserActions(adminUser);
  const isPending = adminUser.role === 'pending';

  return (
    <div className="flex flex-col gap-3 border-b border-[var(--color-border-muted)] p-4 last:border-b-0 sm:flex-row sm:items-center sm:justify-between">
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate text-[length:var(--font-size-sm)] font-medium text-[var(--color-text-base)]">
            {adminUser.name || adminUser.email}
          </span>
          <Badge variant={roleBadgeVariant[adminUser.role] ?? 'neutral'} size="xs">
            {roleLabel[adminUser.role] ?? adminUser.role}
          </Badge>
          {!adminUser.is_active && (
            <Badge variant="error" size="xs">
              Deaktiviert
            </Badge>
          )}
          {isSelf && (
            <Badge variant="neutral" size="xs">
              Du
            </Badge>
          )}
        </div>
        <div className="mt-0.5 flex flex-wrap gap-x-3 text-[length:var(--font-size-xs)] text-[var(--color-text-muted)]">
          <span>{adminUser.email}</span>
          {adminUser.has_apple && <span>Apple</span>}
          {adminUser.has_password && <span>Passwort</span>}
        </div>
      </div>

      {!isSelf && (
        <div className="flex shrink-0 flex-wrap gap-2">
          {isPending ? (
            <>
              <Button
                size="sm"
                variant="primary"
                onClick={() => approve.mutate()}
                disabled={isAnyLoading}
              >
                Freischalten
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => reject.mutate()}
                disabled={isAnyLoading}
              >
                Ablehnen
              </Button>
            </>
          ) : (
            <>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => toggleRole.mutate()}
                disabled={isAnyLoading}
              >
                {adminUser.role === 'admin' ? 'Zum Nutzer' : 'Zum Admin'}
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => toggleActive.mutate()}
                disabled={isAnyLoading}
              >
                {adminUser.is_active ? 'Deaktivieren' : 'Aktivieren'}
              </Button>
            </>
          )}
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Page                                                                */
/* ------------------------------------------------------------------ */

export function AdminUsersPage() {
  const { user } = useAuth();
  const {
    data: users,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['admin', 'users'],
    queryFn: getUsers,
  });

  const sortedUsers = users?.slice().sort((a, b) => {
    if (a.role === 'pending' && b.role !== 'pending') return -1;
    if (a.role !== 'pending' && b.role === 'pending') return 1;
    return (a.name ?? a.email).localeCompare(b.name ?? b.email);
  });

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-4 pt-6 md:p-6 md:pt-8">
      <div className="space-y-2 pb-2">
        <Breadcrumbs>
          <BreadcrumbItem>
            <Link to="/profile">Profil</Link>
          </BreadcrumbItem>
          <BreadcrumbItem isCurrent>Nutzerverwaltung</BreadcrumbItem>
        </Breadcrumbs>

        <h1 className="text-[length:var(--font-size-xl)] font-semibold text-[var(--color-text-primary)]">
          Nutzerverwaltung
        </h1>
      </div>

      {isLoading && (
        <div className="flex justify-center py-12">
          <Spinner size="lg" />
        </div>
      )}

      {error && (
        <div
          role="alert"
          className="rounded-[var(--radius-md)] bg-[var(--color-bg-error-subtle)] p-4 text-[length:var(--font-size-sm)] text-[var(--color-text-error)]"
        >
          Nutzer konnten nicht geladen werden.
        </div>
      )}

      {sortedUsers && sortedUsers.length > 0 && (
        <Card>
          {sortedUsers.map((u) => (
            <UserRow key={u.id} adminUser={u} currentUserId={user?.id ?? -1} />
          ))}
        </Card>
      )}

      {sortedUsers && sortedUsers.length === 0 && (
        <p className="py-8 text-center text-[length:var(--font-size-sm)] text-[var(--color-text-muted)]">
          Keine Nutzer vorhanden.
        </p>
      )}
    </div>
  );
}
