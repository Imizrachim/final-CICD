import React from 'react';

interface TaskStatsProps {
  total: number;
  pending: number;
  completed: number;
}

export const TaskStats: React.FC<TaskStatsProps> = ({
  total,
  pending,
  completed,
}) => {
  const completionRate = total > 0 ? Math.round((completed / total) * 100) : 0;

  return (
    <section className="stats-section" aria-label="Resumen de tareas">
      <div className="stats-grid">
        <div className="stat-card stat-card-total">
          <span className="stat-label">Tareas Totales</span>
          <strong className="stat-value" data-testid="stat-total">
            {total}
          </strong>
          <span className="stat-helper">{completionRate}% completado</span>
        </div>

        <div className="stat-card stat-card-pending">
          <span className="stat-label">Pendientes</span>
          <strong className="stat-value" data-testid="stat-pending">
            {pending}
          </strong>
          <span className="stat-helper">En progreso o por iniciar</span>
        </div>

        <div className="stat-card stat-card-completed">
          <span className="stat-label">Completadas</span>
          <strong className="stat-value" data-testid="stat-completed">
            {completed}
          </strong>
          <span className="stat-helper">Finalizadas con éxito</span>
        </div>
      </div>

      <div className="progress-bar-container" aria-hidden="true">
        <div
          className="progress-bar-fill"
          style={{ width: `${completionRate}%` }}
        />
      </div>
    </section>
  );
};
