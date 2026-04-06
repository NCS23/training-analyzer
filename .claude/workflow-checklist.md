# Workflow Checklist — Auth & Multi-User (#556)

## Phase 0: Pre-Code
- [x] GitHub Issue gelesen (Akzeptanzkriterien + Taskbreakdown)
- [x] PROJEKT_REGELN.md gelesen
- [x] DESIGN_REVIEW.md gelesen (bei UI-Änderungen)
- [x] CLEAN_CODE.md gelesen

## Phase 1: Branch & Board
- [x] Feature-Branch erstellt (feature/auth-s01-user-model)
- [x] Issue auf "In Progress" im Project Board gesetzt

## Phase 2: Implementation
- [x] UserModel + RefreshTokenModel (users, refresh_tokens Tabellen)
- [x] user_id FK (nullable, CASCADE) in allen 17 bestehenden Tabellen
- [x] Alembic Migrationen c045 + c046
- [x] JWT Access Token + Refresh Token mit Rotation (security.py)
- [x] Apple Sign-In JWKS-Validierung (apple_auth_service.py)
- [x] Daten-Migration (data_migration_service.py)
- [x] get_current_user Dependency mit Fallback (dependencies.py)
- [x] auth_enabled Feature-Flag (config.py)
- [x] Auth-Endpoints: /auth/apple, /auth/status, /auth/refresh, /auth/logout, /auth/me
- [x] useAuth Zustand-Store (useAuth.ts)
- [x] AuthGuard (AuthGuard.tsx)
- [x] Login-Seite mit Apple Sign-In Platzhalter (Login.tsx)
- [x] Axios-Interceptor: Bearer-Token + 401-Refresh (client.ts)

## Phase 3: Quality Gates
- [x] ESLint 0 Warnings
- [x] Prettier Check bestanden
- [x] TSC --noEmit bestanden
- [x] Vitest 187 Tests bestanden
- [x] Ruff check bestanden
- [x] Ruff format bestanden
- [x] Mypy bestanden
- [x] Pytest 1193 Tests bestanden
- [x] Design Review PASS

## Phase 4: Abschluss (post-push, not validated by hook)
- [ ] Push auf Feature-Branch
- [ ] CI gruen
- [ ] GitHub Issue kommentiert
- [ ] GitHub Issue geschlossen
- [ ] Project Board Status auf Done
