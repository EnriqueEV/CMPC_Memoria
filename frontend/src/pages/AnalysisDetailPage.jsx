import React, { useState, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import SuccessModal from '../components/SuccessModal';
import Tooltip from '../components/Tooltip';

const AnalysisDetailPage = () => {
  const { id } = useParams();
  const [showModal, setShowModal] = useState(false);
  const [selectedUsers, setSelectedUsers] = useState({});
  const [feedback, setFeedback] = useState({});
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [rolesPage, setRolesPage] = useState(1);
  const usersPerPage = 5;
  const rolesPerPage = 3;

  const usersData = [
    {
      usuario: 'KPPIRES',
      sucursal: '0504',
      funcion: 'ANALISTA FINANCEIRO',
      departamento: 'CORP_FINANCE',
      asignado: 'OK'
    },
    {
      usuario: 'ZVALASKI',
      sucursal: '0504',
      funcion: 'DIRETOR GERAL',
      departamento: 'DIRETORIA GERAL',
      asignado: 'OK'
    },
    {
      usuario: 'MKSOUZA',
      sucursal: '0504',
      funcion: 'PORTEIRO',
      departamento: 'CN_PORTARIA',
      asignado: 'Pendiente'
    },
    {
      usuario: 'ASILVA',
      sucursal: '0514',
      funcion: 'CONTADOR',
      departamento: 'CONTABILIDAD',
      asignado: 'OK'
    },
    {
      usuario: 'JPEREZ',
      sucursal: '0514',
      funcion: 'ANALISTA',
      departamento: 'RECURSOS HUMANOS',
      asignado: 'Pendiente'
    },
    {
      usuario: 'MRODRIGUEZ',
      sucursal: '0504',
      funcion: 'GERENTE',
      departamento: 'VENTAS',
      asignado: 'OK'
    }
  ];

  const rolesData = [
    {
      usuario: 'KPPIRES',
      rol: 'ZDX_DMPSST0-008-01-001:0514',
      numSimilares: 7,
      feedbackNo: false,
      feedbackSi: true,
      guardarNo: false,
      guardarSi: true
    },
    {
      usuario: 'KPPIRES',
      rol: 'ZD_ALCOPCO-001-01-001:0514',
      numSimilares: 5,
      feedbackNo: true,
      feedbackSi: false,
      guardarNo: false,
      guardarSi: true
    },
    {
      usuario: 'KPPIRES',
      rol: 'ZD_ALFIFI0-001-01-001:0107',
      numSimilares: 3,
      feedbackNo: true,
      feedbackSi: false,
      guardarNo: false,
      guardarSi: true
    },
    {
      usuario: 'ZVALASKI',
      rol: 'ZD_DIRECTOR-001-01-001:0504',
      numSimilares: 8,
      feedbackNo: false,
      feedbackSi: true,
      guardarNo: false,
      guardarSi: true
    },
    {
      usuario: 'MKSOUZA',
      rol: 'ZD_PORTARIA-001-01-001:0504',
      numSimilares: 4,
      feedbackNo: true,
      feedbackSi: false,
      guardarNo: false,
      guardarSi: true
    }
  ];

  const filteredUsers = useMemo(() => {
    return usersData.filter(user =>
      user.usuario.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.funcion.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.departamento.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [searchTerm]);

  const totalUsersPages = Math.ceil(filteredUsers.length / usersPerPage);
  const paginatedUsers = filteredUsers.slice(
    (currentPage - 1) * usersPerPage,
    currentPage * usersPerPage
  );

  const totalRolesPages = Math.ceil(rolesData.length / rolesPerPage);
  const paginatedRoles = rolesData.slice(
    (rolesPage - 1) * rolesPerPage,
    rolesPage * rolesPerPage
  );

  const handleUserSelection = (usuario) => {
    setSelectedUsers((prev) => ({
      ...prev,
      [usuario]: !prev[usuario]
    }));
  };

  const handleFeedback = (usuario, rol, type, value) => {
    const key = `${usuario}-${rol}`;
    setFeedback((prev) => ({
      ...prev,
      [key]: { ...prev[key], [type]: value }
    }));
  };

  const handleSaveFeedback = () => {
    setShowModal(true);
  };

  const handleDownload = () => {
    const blob = new Blob(['Recomendaciones de roles...'], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'recomendaciones_roles.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="analysis-detail-page">
      <h1 className="analysis-detail-page__title">
        Revisión de análisis: Resumen_07_2026
      </h1>

      <div className="analysis-detail-page__section">
        <h2 className="analysis-detail-page__section-title">Usuarios analizados</h2>
        
        <div className="analysis-detail-page__search">
          <input
            type="text"
            placeholder="Buscar por usuario, función o departamento..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentPage(1);
            }}
            className="analysis-detail-page__search-input"
          />
        </div>

        <div className="analysis-detail-page__table-container">
          <table className="analysis-detail-page__table">
            <thead>
              <tr>
                <Tooltip text="Seleccione usuarios para filtrar roles">
                  <th>Selección</th>
                </Tooltip>
                <th>Usuario</th>
                <th>Sucursal</th>
                <th>Función</th>
                <th>Departamento</th>
                <th>Asignado</th>
              </tr>
            </thead>
            <tbody>
              {paginatedUsers.map((user, index) => (
                <tr key={index}>
                  <td>
                    <input
                      type="checkbox"
                      checked={selectedUsers[user.usuario] || false}
                      onChange={() => handleUserSelection(user.usuario)}
                      className="analysis-detail-page__checkbox"
                    />
                  </td>
                  <td>{user.usuario}</td>
                  <td>{user.sucursal}</td>
                  <td>{user.funcion}</td>
                  <td>{user.departamento}</td>
                  <td>
                    <span className={`analysis-detail-page__status analysis-detail-page__status--${user.asignado === 'OK' ? 'ok' : 'pending'}`}>
                      {user.asignado}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {totalUsersPages > 1 && (
          <div className="analysis-detail-page__pagination-controls">
            <div className="analysis-detail-page__pagination-info">
              Mostrando {((currentPage - 1) * usersPerPage) + 1}-{Math.min(currentPage * usersPerPage, filteredUsers.length)} de {filteredUsers.length}
            </div>
            <div className="analysis-detail-page__pagination-buttons">
              <button
                className="analysis-detail-page__pagination-btn"
                onClick={() => setCurrentPage(currentPage - 1)}
                disabled={currentPage === 1}
              >
                Anterior
              </button>
              <span className="analysis-detail-page__pagination-current">
                Página {currentPage} de {totalUsersPages}
              </span>
              <button
                className="analysis-detail-page__pagination-btn"
                onClick={() => setCurrentPage(currentPage + 1)}
                disabled={currentPage === totalUsersPages}
              >
                Siguiente
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="analysis-detail-page__section">
        <h2 className="analysis-detail-page__section-title">
          Recomendaciones de roles
        </h2>

        <div className="analysis-detail-page__roles-header">
          <div className="analysis-detail-page__roles-header-left">
            <span className="analysis-detail-page__roles-label">Usuario</span>
            <span className="analysis-detail-page__roles-label">Rol</span>
            <span className="analysis-detail-page__roles-label">N. de usuarios similares</span>
          </div>
          <div className="analysis-detail-page__roles-header-right">
            <div className="analysis-detail-page__feedback-group">
              <Tooltip text="Indique si esta recomendación es correcta">
                <span className="analysis-detail-page__feedback-title">Feed back</span>
              </Tooltip>
              <div className="analysis-detail-page__feedback-options">
                <span>No</span>
                <span>Sí</span>
              </div>
            </div>
            <div className="analysis-detail-page__feedback-group">
              <Tooltip text="Guarde las recomendaciones que desea aplicar">
                <span className="analysis-detail-page__feedback-title">Guardar</span>
              </Tooltip>
              <div className="analysis-detail-page__feedback-options">
                <span>No</span>
                <span>Sí</span>
              </div>
            </div>
          </div>
        </div>

        <div className="analysis-detail-page__roles-container">
          {paginatedRoles.map((role, index) => (
            <div key={index} className="analysis-detail-page__role-row">
              <div className="analysis-detail-page__role-info">
                <span className="analysis-detail-page__role-user">{role.usuario}</span>
                <span className="analysis-detail-page__role-name">{role.rol}</span>
                <span className="analysis-detail-page__role-similar">{role.numSimilares}</span>
              </div>
              <div className="analysis-detail-page__role-actions">
                <div className="analysis-detail-page__radio-group">
                  <input
                    type="radio"
                    name={`feedback-${index}`}
                    checked={role.feedbackNo}
                    onChange={() => handleFeedback(role.usuario, role.rol, 'feedback', 'no')}
                  />
                  <input
                    type="radio"
                    name={`feedback-${index}`}
                    checked={role.feedbackSi}
                    onChange={() => handleFeedback(role.usuario, role.rol, 'feedback', 'si')}
                  />
                </div>
                <div className="analysis-detail-page__radio-group">
                  <input
                    type="radio"
                    name={`save-${index}`}
                    checked={role.guardarNo}
                    onChange={() => handleFeedback(role.usuario, role.rol, 'save', 'no')}
                  />
                  <input
                    type="radio"
                    name={`save-${index}`}
                    checked={role.guardarSi}
                    onChange={() => handleFeedback(role.usuario, role.rol, 'save', 'si')}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>

        {totalRolesPages > 1 && (
          <div className="analysis-detail-page__pagination">
            {Array.from({ length: totalRolesPages }, (_, i) => (
              <span
                key={i}
                className={`analysis-detail-page__page-dot ${rolesPage === i + 1 ? 'analysis-detail-page__page-dot--active' : ''}`}
                onClick={() => setRolesPage(i + 1)}
              ></span>
            ))}
          </div>
        )}
      </div>

      <div className="analysis-detail-page__actions">
        <Tooltip text="Descargar las recomendaciones en formato de texto">
          <button
            className="analysis-detail-page__download-btn"
            onClick={handleDownload}
          >
            Descargar recomendación
          </button>
        </Tooltip>
        <Tooltip text="Guardar el feedback proporcionado">
          <button
            className="analysis-detail-page__save-btn"
            onClick={handleSaveFeedback}
          >
            Guardar feedback
          </button>
        </Tooltip>
      </div>

      {showModal && (
        <SuccessModal
          onClose={() => setShowModal(false)}
          onGoHome={() => window.location.href = '/'}
        />
      )}
    </div>
  );
};

export default AnalysisDetailPage;
