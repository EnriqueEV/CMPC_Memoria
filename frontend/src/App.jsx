import React, { useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import HomePage from './pages/HomePage';
import NewAnalysisPage from './pages/NewAnalysisPage';
import AnalysisDetailPage from './pages/AnalysisDetailPage';

const App = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const handleLogin = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
  };

  if (!isAuthenticated) {
    return <LoginPage onLogin={handleLogin} />;
  }

  return (
    <Layout onLogout={handleLogout}>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/nuevo-analisis" element={<NewAnalysisPage />} />
        <Route path="/analisis/:id" element={<AnalysisDetailPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
};

export default App;
