import { Navigate } from 'react-router-dom';

/** Redirect to the unified upload page with strength pre-selected. */
export function StrengthSessionPage() {
  return <Navigate to="/sessions/new" state={{ preselect: 'strength' }} replace />;
}
