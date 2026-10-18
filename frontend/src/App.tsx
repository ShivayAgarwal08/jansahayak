import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { LanguageProvider } from './context/LanguageContext';
import { Navbar } from './components/layout/Navbar';
import { Footer } from './components/layout/Footer';

// Pages
import { HomePage } from './pages/HomePage';
import { SchemesPage } from './pages/SchemesPage';
import { SchemeDetailPage } from './pages/SchemeDetailPage';
import { EligibilityPage } from './pages/EligibilityPage';
import { ComparePage } from './pages/ComparePage';
import { AssistantPage } from './pages/AssistantPage';
import { ApplicationPrepPage } from './pages/ApplicationPrepPage';
import { RtiAssistantPage } from './pages/RtiAssistantPage';
import { GrievanceAssistantPage } from './pages/GrievanceAssistantPage';
import { DashboardPage } from './pages/DashboardPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { AdminPage } from './pages/AdminPage';
import { PrivacyPage } from './pages/PrivacyPage';

export const App: React.FC = () => {
  return (
    <Router>
      <LanguageProvider>
        <AuthProvider>
          <div className="min-h-screen flex flex-col bg-ivory-50 text-navy-900">
            <Navbar />
            <main className="flex-1">
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/schemes" element={<SchemesPage />} />
                <Route path="/schemes/:slug" element={<SchemeDetailPage />} />
                <Route path="/eligibility" element={<EligibilityPage />} />
                <Route path="/compare" element={<ComparePage />} />
                <Route path="/assistant" element={<AssistantPage />} />
                <Route path="/applications" element={<ApplicationPrepPage />} />
                <Route path="/rti" element={<RtiAssistantPage />} />
                <Route path="/grievances" element={<GrievanceAssistantPage />} />
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />
                <Route path="/admin" element={<AdminPage />} />
                <Route path="/privacy" element={<PrivacyPage />} />
                {/* Fallback to home */}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </main>
            <Footer />
          </div>
        </AuthProvider>
      </LanguageProvider>
    </Router>
  );
};

export default App;
