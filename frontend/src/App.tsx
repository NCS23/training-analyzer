import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import UploadPage from './pages/Upload';

function HomePage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-12 px-4">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          🏃‍♂️ Training Analyzer
        </h1>
        <p className="text-gray-600 mb-8">
          AI-powered half-marathon training platform
        </p>
        <Link 
          to="/upload"
          className="inline-block bg-blue-600 text-white px-6 py-3 rounded-md font-medium hover:bg-blue-700"
        >
          Training hochladen →
        </Link>
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