import React from 'react';

const SuccessModal = ({ onClose, onGoHome }) => {
  return (
    <div className="success-modal">
      <div className="success-modal__overlay" onClick={onClose}></div>
      <div className="success-modal__content">
        <h2 className="success-modal__title">
          ¡Feedback guardado exitosamente!
        </h2>
        <div className="success-modal__buttons">
          <button
            className="success-modal__btn success-modal__btn--secondary"
            onClick={onClose}
          >
            Deshacer
          </button>
          <button
            className="success-modal__btn success-modal__btn--primary"
            onClick={onGoHome}
          >
            Ir a inicio
          </button>
        </div>
      </div>
    </div>
  );
};

export default SuccessModal;
