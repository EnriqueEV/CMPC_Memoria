import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Tooltip from '../components/Tooltip';

const NewAnalysisPage = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [fileName, setFileName] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [fileError, setFileError] = useState('');
  const [sucursal, setSucursal] = useState('0504');
  const [funcion, setFuncion] = useState('ML81N');
  const [departamento, setDepartamento] = useState('CORP_FINANCE');
  const [filterUsers, setFilterUsers] = useState([{ id: 'AABATTI' }, { id: '' }]);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      const fileExtension = selectedFile.name.split('.').pop().toLowerCase();
      if (fileExtension === 'csv' || fileExtension === 'xlsx') {
        setFile(selectedFile);
        setFileName(selectedFile.name);
        setFileError('');
        simulateUpload();
      } else {
        setFileError('Error: Solo se permiten archivos .csv o .xlsx');
        setFile(null);
        setFileName('');
        e.target.value = null;
      }
    }
  };

  const simulateUpload = () => {
    setIsUploading(true);
    setUploadProgress(0);
    
    const interval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsUploading(false);
          return 100;
        }
        return prev + 10;
      });
    }, 200);
  };

  const handleAddUser = () => {
    setFilterUsers([...filterUsers, { id: '' }]);
  };

  const handleUserChange = (index, value) => {
    const newUsers = [...filterUsers];
    newUsers[index].id = value;
    setFilterUsers(newUsers);
  };

  const handleStartAnalysis = () => {
    if (!file) {
      setFileError('Debe seleccionar un archivo antes de comenzar');
      return;
    }
    if (uploadProgress < 100) {
      setFileError('Por favor espere a que se complete la carga del archivo');
      return;
    }
    navigate('/analisis/1');
  };

  return (
    <div className="new-analysis-page">
      <h1 className="new-analysis-page__title">Nuevo análisis</h1>

      <div className="new-analysis-page__section">
        <div className="new-analysis-page__section-header">
          <h3 className="new-analysis-page__section-title">
            Cargar archivo de datos <span className="new-analysis-page__required">*</span>
          </h3>
          <Tooltip text="Seleccione un archivo CSV o XLSX con los datos de usuarios SAP">
            <span className="new-analysis-page__help-icon">ℹ️</span>
          </Tooltip>
        </div>

        <div className="new-analysis-page__upload-section">
          <div className="new-analysis-page__upload-container">
            <label htmlFor="file-upload" className="new-analysis-page__upload-label">
              {fileName || 'Ingresar xlsx/csv'}
            </label>
            <input
              id="file-upload"
              type="file"
              accept=".csv,.xlsx"
              onChange={handleFileChange}
              className="new-analysis-page__file-input"
            />
            <Tooltip text="Seleccionar archivo">
              <span className="new-analysis-page__upload-icon">📁</span>
            </Tooltip>
          </div>

          {isUploading && (
            <div className="new-analysis-page__progress">
              <div className="new-analysis-page__progress-text">Estado de carga</div>
              <div className="new-analysis-page__progress-circle">
                <svg width="80" height="80" viewBox="0 0 80 80">
                  <circle
                    cx="40"
                    cy="40"
                    r="35"
                    fill="none"
                    stroke="#e0e0e0"
                    strokeWidth="8"
                  />
                  <circle
                    cx="40"
                    cy="40"
                    r="35"
                    fill="none"
                    stroke="#4caf50"
                    strokeWidth="8"
                    strokeDasharray={`${uploadProgress * 2.2} 220`}
                    strokeLinecap="round"
                    transform="rotate(-90 40 40)"
                  />
                  <text
                    x="40"
                    y="45"
                    textAnchor="middle"
                    fontSize="16"
                    fontWeight="600"
                    fill="#000"
                  >
                    {uploadProgress}%
                  </text>
                </svg>
              </div>
            </div>
          )}

          {file && uploadProgress === 100 && (
            <div className="new-analysis-page__success-message">
              ✓ Archivo cargado exitosamente
            </div>
          )}
        </div>

        {fileError && (
          <div className="new-analysis-page__error-message">
            {fileError}
          </div>
        )}
      </div>

      <div className="new-analysis-page__section">
        <h3 className="new-analysis-page__section-title">Información del análisis</h3>
        <table className="new-analysis-page__info-table">
          <thead>
            <tr>
              <th>Sucursal</th>
              <th>Función</th>
              <th>Departamento</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>{sucursal}</td>
              <td>{funcion}</td>
              <td>{departamento}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="new-analysis-page__section">
        <div className="new-analysis-page__section-header">
          <h3 className="new-analysis-page__section-title">
            Filtro por usuario <span className="new-analysis-page__optional">(Opcional)</span>
          </h3>
          <Tooltip text="Puede especificar IDs de usuarios específicos para analizar">
            <span className="new-analysis-page__help-icon">ℹ️</span>
          </Tooltip>
        </div>
        <div className="new-analysis-page__filter-container">
          {filterUsers.map((user, index) => (
            <div key={index} className="new-analysis-page__filter-row">
              <span className="new-analysis-page__filter-label">ID</span>
              <input
                type="text"
                value={user.id}
                onChange={(e) => handleUserChange(index, e.target.value)}
                className="new-analysis-page__filter-input"
                placeholder="Ingrese ID de usuario"
              />
            </div>
          ))}
        </div>
      </div>

      <div className="new-analysis-page__actions">
        <p className="new-analysis-page__required-note">
          * Campos obligatorios
        </p>
        <Tooltip text="Iniciar el procesamiento del análisis de usuarios">
          <button
            className="new-analysis-page__start-btn"
            onClick={handleStartAnalysis}
            disabled={!file || uploadProgress < 100}
          >
            Comenzar análisis
          </button>
        </Tooltip>
      </div>
    </div>
  );
};

export default NewAnalysisPage;
