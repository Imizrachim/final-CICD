import React from 'react';
import { Task } from '../types/task';

interface ConfirmModalProps {
  taskToDelete: Task | null;
  isSubmitting: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export const ConfirmModal: React.FC<ConfirmModalProps> = ({
  taskToDelete,
  isSubmitting,
  onConfirm,
  onCancel,
}) => {
  if (!taskToDelete) {
    return null;
  }

  return (
    <div
      className="modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-modal-title"
      data-testid="confirm-modal"
    >
      <div className="modal-card">
        <h2 id="confirm-modal-title" className="modal-title">
          Confirmar eliminación
        </h2>
        <p className="modal-description">
          ¿Estás seguro de que deseas eliminar la tarea{' '}
          <strong>&ldquo;{taskToDelete.title}&rdquo;</strong>? Esta acción no se
          puede deshacer.
        </p>
        <div className="modal-actions">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onCancel}
            disabled={isSubmitting}
            data-testid="cancel-delete-btn"
          >
            Cancelar
          </button>
          <button
            type="button"
            className="btn btn-danger"
            onClick={onConfirm}
            disabled={isSubmitting}
            data-testid="confirm-delete-btn"
          >
            {isSubmitting ? 'Eliminando...' : 'Sí, eliminar'}
          </button>
        </div>
      </div>
    </div>
  );
};
