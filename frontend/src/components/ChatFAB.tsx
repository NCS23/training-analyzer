import { useLocation, useNavigate } from 'react-router-dom';
import { MessageCircle } from 'lucide-react';

export function ChatFAB() {
  const location = useLocation();
  const navigate = useNavigate();

  // Auf der Chat-Seite ausblenden
  if (location.pathname.startsWith('/chat')) return null;

  return (
    <button
      onClick={() => navigate('/chat')}
      aria-label="KI-Chat öffnen"
      className="fixed right-4 bottom-[calc(62px+env(safe-area-inset-bottom)+var(--spacing-sm))] z-[201] flex h-12 w-12 items-center justify-center rounded-full bg-[var(--color-interactive-primary)] text-[var(--color-text-on-primary)] shadow-[var(--shadow-md)] transition-transform duration-150 active:scale-95 motion-reduce:transition-none lg:hidden"
    >
      <MessageCircle className="h-5 w-5" />
    </button>
  );
}
