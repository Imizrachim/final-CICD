import React from 'react';
import { Task } from '../types/task';

interface TaskCardProps {
  task: Task;
  isBusy: boolean;
  onToggleStatus: (task: Task) => void;
  onEdit: (task: Task) => void;
  onRequestDelete: (task: Task) => void;
}

function formatDate(isoString: string): string {
  const parsed = new Date(isoString);
  if (Number.isNaN(parsed.getTime())) {
    return isoString;
  }
  return parsed.toLocaleDateString('es-CO', {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
  });
}

export const TaskCard: React.FC<TaskCardProps> = ({
  task,
  isBusy,
  onToggleStatus,
  onEdit,
  onRequestDelete,
}) => {
  const isCompleted = task.status === 'Completed';

  return (
    <article
      className={`task-card ${isCompleted ? 'task-card-completed' : 'task-card-pending'}`}
      data-testid="task-card"
      data-task-id={task.id}
    >
      <div className="task-card-header">
        <span
          className={`status-badge ${isCompleted ? 'badge-completed' : 'badge-pending'}`}
          data-testid="task-status-badge"
          data-status={task.status}
        >
          <span className="status-dot" aria-hidden="true" />
          {isCompleted ? 'Completada' : 'Pendiente'}
        </span>

        <span className="task-date" title={`Actualizada: ${task.updated_at}`}>
          Creada: {formatDate(task.created_at)}
        </span>
      </div>

      <h3
        className={`task-title ${isCompleted ? 'title-completed' : ''}`}
        data-testid="task-title"
      >
        {task.title}
      </h3>

      {task.description ? (
        <p className="task-description" data-testid="task-description">
          {task.description}
        </p>
      ) : (
        <p className="task-description task-description-empty" data-testid="task-description">
          Sin descripción adicional.
        </p>
      )}

      <div className="task-card-actions">
        <button
          type="button"
          className={`btn btn-sm ${isCompleted ? 'btn-outline' : 'btn-success'}`}
          onClick={() => onToggleStatus(task)}
          disabled={isBusy}
          data-testid="task-toggle-status-btn"
        >
          {isCompleted ? 'Marcar Pendiente' : 'Completar'}
        </button>

        <div className="task-secondary-actions">
          <button
            type="button"
            className="btn btn-sm btn-secondary"
            onClick={() => onEdit(task)}
            disabled={isBusy}
            data-testid="task-edit-btn"
          >
            Editar
          </button>
          <button
            type="button"
            className="btn btn-sm btn-danger-outline"
            onClick={() => onRequestDelete(task)}
            disabled={isBusy}
            data-testid="task-delete-btn"
          >
            Eliminar
          </button>
        </div>
      </div>
    </article>
  );
};
