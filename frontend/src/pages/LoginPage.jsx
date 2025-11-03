import React, { useState } from 'react';

const LoginPage = ({ onLogin }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    // Simple validation - in production, this would authenticate against a backend
    if (username && password) {
      onLogin();
    }
  };

  return (
    <div className="login-page">
      <div className="login-page__container">
        <div className="login-page__left">
          <div className="login-page__logo">
            <div className="login-page__logo-icon">🌿</div>
            <div className="login-page__logo-text">cmpc</div>
          </div>
          <h1 className="login-page__title">
            ¡Bienvenidos al<br />
            Gestor de Accesos<br />
            SAP!
          </h1>
        </div>

        <div className="login-page__right">
          <form className="login-page__form" onSubmit={handleSubmit}>
            <h2 className="login-page__form-title">Login</h2>
            
            <div className="login-page__form-group">
              <label className="login-page__label">Usuario:</label>
              <input
                type="text"
                className="login-page__input"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="********************"
              />
            </div>

            <div className="login-page__form-group">
              <label className="login-page__label">Contraseña:</label>
              <input
                type="password"
                className="login-page__input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="********************"
              />
            </div>

            <button
              type="submit"
              className="login-page__submit-btn"
            >
              Ingresar
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
