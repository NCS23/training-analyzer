import { BrowserRouter, Routes, Route, useNavigate } from 'react-router-dom';
import { Button } from '@nordlig/components';
import UploadPage from './pages/Upload';

function HomePage() {
  const navigate = useNavigate();
  return (
    <div className="min-h-screen bg-[var(--color-bg-base)]">
      <div className="max-w-7xl mx-auto py-12 px-4">
        <h1 className="text-4xl font-bold text-[var(--color-text-base)] mb-4">Training Analyzer</h1>
        <p className="text-[var(--color-text-muted)] mb-8">
          AI-powered half-marathon training platform
        </p>
        <Button variant="primary" onClick={() => navigate('/upload')}>
          Training hochladen
        </Button>
      </div>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/upload" element={<UploadPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
