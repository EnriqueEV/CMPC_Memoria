import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import Tooltip from '../components/Tooltip';

const HomePage = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [sortField, setSortField] = useState(null);
  const [sortDirection, setSortDirection] = useState('asc');
  const itemsPerPage = 4;

  const analysisData = [
    {
      id: 1,
      name: 'Resumen_07-2026',
      createdBy: 'rocio@cmpc.cl',
      sucursal: '504',
      creationDate: '01-08-2026',
      status: 'En proceso'
    },
    {
      id: 2,
      name: 'Resumen_06-2026',
      createdBy: 'javier.acuna@cmpc.cl',
      sucursal: '514',
      creationDate: '01-07-2026',
      status: 'Guardado'
    },
    {
      id: 3,
      name: 'Resumen_05-2025',
      createdBy: 'enrique.escalona@cmpc.cl',
      sucursal: '504',
      creationDate: '01-06-2026',
      status: 'Guardado'
    },
    {
      id: 4,
      name: 'Resumen_04-2026',
      createdBy: 'rocio@cmpc.cl',
      sucursal: '514',
      creationDate: '01-05-2026',
      status: 'Guardado'
    },
    {
      id: 5,
      name: 'Resumen_05-2026',
      createdBy: 'javier.acuna@cmpc.cl',
      sucursal: '514',
      creationDate: '01-04-2026',
      status: 'Guardado'
    },
    {
      id: 6,
      name: 'Resumen_06-2026',
      createdBy: 'enrique.escalona@cmpc.cl',
      sucursal: '504',
      creationDate: '01-03-2026',
      status: 'Guardado'
    }
  ];

  const filteredAndSortedData = useMemo(() => {
    let filtered = analysisData.filter(analysis =>
      analysis.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      analysis.createdBy.toLowerCase().includes(searchTerm.toLowerCase()) ||
      analysis.sucursal.includes(searchTerm)
    );

    if (sortField) {
      filtered = [...filtered].sort((a, b) => {
        const aVal = a[sortField];
        const bVal = b[sortField];
        const modifier = sortDirection === 'asc' ? 1 : -1;
        return aVal > bVal ? modifier : -modifier;
      });
    }

    return filtered;
  }, [searchTerm, sortField, sortDirection]);

  const totalPages = Math.ceil(filteredAndSortedData.length / itemsPerPage);
  const paginatedData = filteredAndSortedData.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const handleRowClick = (id) => {
    navigate(`/analisis/${id}`);
  };

  const handlePageChange = (newPage) => {
    setCurrentPage(newPage);
  };

  return (
    <div className="home-page">
      <h1 className="home-page__title">Sus análisis</h1>
      
      <div className="home-page__search">
        <input
          type="text"
          placeholder="Buscar por nombre, creador o sucursal..."
          value={searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            setCurrentPage(1);
          }}
          className="home-page__search-input"
        />
      </div>

      <div className="home-page__table-container">
        <table className="home-page__table">
          <thead>
            <tr>
              <Tooltip text="Click para ordenar">
                <th onClick={() => handleSort('name')}>
                  Análisis {sortField === 'name' && (sortDirection === 'asc' ? '↑' : '↓')}
                </th>
              </Tooltip>
              <Tooltip text="Click para ordenar">
                <th onClick={() => handleSort('createdBy')}>
                  Creado por {sortField === 'createdBy' && (sortDirection === 'asc' ? '↑' : '↓')}
                </th>
              </Tooltip>
              <Tooltip text="Click para ordenar">
                <th onClick={() => handleSort('sucursal')}>
                  Sucursal {sortField === 'sucursal' && (sortDirection === 'asc' ? '↑' : '↓')}
                </th>
              </Tooltip>
              <Tooltip text="Click para ordenar">
                <th onClick={() => handleSort('creationDate')}>
                  Fecha creación {sortField === 'creationDate' && (sortDirection === 'asc' ? '↑' : '↓')}
                </th>
              </Tooltip>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {paginatedData.map((analysis) => (
              <tr
                key={analysis.id}
                onClick={() => handleRowClick(analysis.id)}
                className="home-page__table-row"
              >
                <td>{analysis.name}</td>
                <td>{analysis.createdBy}</td>
                <td>{analysis.sucursal}</td>
                <td>{analysis.creationDate}</td>
                <td>
                  <span className={`home-page__status home-page__status--${analysis.status === 'En proceso' ? 'progress' : 'completed'}`}>
                    {analysis.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="home-page__pagination">
          <div className="home-page__pagination-info">
            Mostrando {((currentPage - 1) * itemsPerPage) + 1}-{Math.min(currentPage * itemsPerPage, filteredAndSortedData.length)} de {filteredAndSortedData.length}
          </div>
          <div className="home-page__pagination-controls">
            <button
              className="home-page__pagination-btn"
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
            >
              Anterior
            </button>
            <span className="home-page__pagination-current">
              Página {currentPage} de {totalPages}
            </span>
            <button
              className="home-page__pagination-btn"
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
            >
              Siguiente
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default HomePage;
