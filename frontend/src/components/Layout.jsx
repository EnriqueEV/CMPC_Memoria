import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';

const Layout = ({ children, onLogout }) => {
  const navigate = useNavigate();

  const navLinkClass = ({ isActive }) => {
    const classes = ['layout__sidebar-link'];
    if (isActive) classes.push('layout__sidebar-link--active');
    return classes.join(' ');
  };

  const handleNewAnalysis = () => {
    navigate('/nuevo-analisis');
  };

  const previousAnalyses = [
    { id: 1, name: 'Resumen_07-2026' },
    { id: 2, name: 'Resumen_06-2026' },
    { id: 3, name: 'Resumen_05-2025' },
    { id: 4, name: 'Resumen_04-2026' },
    { id: 5, name: 'Resumen_03-2026' },
    { id: 6, name: 'Resumen_02-2026' }
  ];

  return (
    <div className="layout">
      <div className="layout__sidebar">
        <div className="layout__logo">
          <div className="layout__logo-icon">🌿</div>
          <div className="layout__logo-text">cmpc</div>
        </div>

        <button
          className="layout__new-analysis-btn"
          onClick={handleNewAnalysis}
        >
          Nuevo análisis
        </button>

        <div className="layout__sidebar-section">
          <h3 className="layout__sidebar-title">Análisis previos</h3>
          <nav className="layout__sidebar-nav">
            {previousAnalyses.map((analysis) => (
              <NavLink
                key={analysis.id}
                className={navLinkClass}
                to={`/analisis/${analysis.id}`}
              >
                {analysis.name}
              </NavLink>
            ))}
          </nav>
        </div>
      </div>

      <div className="layout__main">
        <div className="layout__content">
          {children}
        </div>
      </div>
    </div>
  );
};

export default Layout;
