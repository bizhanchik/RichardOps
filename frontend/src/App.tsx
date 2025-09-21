import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LandingPage from './components/LandingPage';
import Solution from './components/Solution';
import { ToastProvider } from './contexts/ToastContext';

// Main App component for Team Richards landing page
function App() {
  return (
    <ToastProvider>
      <Router>
        <div className="min-h-screen bg-white">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/solution" element={
              <div className="min-h-screen bg-gray-50">
                <Solution />
              </div>
            } />
          </Routes>
        </div>
      </Router>
    </ToastProvider>
  );
}

export default App;
