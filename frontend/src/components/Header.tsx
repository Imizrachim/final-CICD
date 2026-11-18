import React from 'react';

interface HeaderProps {
  onRefresh: () => void;
  isLoading: boolean;
}

export const Header: React.FC<HeaderProps> = ({ onRefresh, isLoading }) => {
  return (
    <header className="app-header" data-testid="app-header">
      <div className="header-brand">
        <div className="brand-icon" aria-hidden="true">
          ✓
        </div>
        <div>
          <h1 className="header-title">Task Manager</h1>
          <p className="header-subtitle">
            Organiza, prioriza y da seguimiento a tus actividades diarias
          </p>
        </div>
      </div>
      <button
        type="button"
        className="btn btn-secondary"
        onClick={onRefresh}
        disabled={isLoading}
        data-testid="refresh-tasks-btn"
      >
        {isLoading ? 'Actualizando...' : 'Actualizar'}
      </button>
    </header>
  );
};
