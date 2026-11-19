import React, { useEffect, useState } from 'react';
import { Task, TaskCreateInput } from '../types/task';

interface TaskFormProps {
  editingTask: Task | null;
  isSubmitting: boolean;
  onSubmit: (data: TaskCreateInput) => Promise<boolean>;
  onCancelEdit: () => void;
}

export const TaskForm: React.FC<TaskFormProps> = ({
  editingTask,
  isSubmitting,
  onSubmit,
  onCancelEdit,
}) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);

  useEffect(() => {
    if (editingTask) {
      setTitle(editingTask.title);
      setDescription(editingTask.description);
      setValidationError(null);
    } else {
      setTitle('');
      setDescription('');
      setValidationError(null);
    }
  }, [editingTask]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const cleanedTitle = title.trim();
    const cleanedDescription = description.trim();

    if (!cleanedTitle) {
      setValidationError('El título de la tarea es obligatorio.');
      return;
    }

    if (cleanedTitle.length > 150) {
      setValidationError('El título no puede superar los 150 caracteres.');
      return;
    }

    setValidationError(null);
    const success = await onSubmit({
      title: cleanedTitle,
      description: cleanedDescription,
    });

    if (success && !editingTask) {
      setTitle('');
      setDescription('');
    }
  };

  return (
    <section className="form-card" aria-labelledby="task-form-heading">
      <h2 id="task-form-heading" className="section-title">
        {editingTask ? 'Editar Tarea' : 'Nueva Tarea'}
      </h2>
      <form onSubmit={handleSubmit} data-testid="task-form" noValidate>
        <div className="form-group">
          <label htmlFor="task-title" className="form-label">
            Título <span className="required-star">*</span>
          </label>
          <input
            id="task-title"
            type="text"
            className={`form-input ${validationError ? 'input-error' : ''}`}
            placeholder="Ej. Configurar pipeline de despliegue en AWS"
            value={title}
            maxLength={160}
            onChange={(e) => {
              setTitle(e.target.value);
              if (validationError) setValidationError(null);
            }}
            disabled={isSubmitting}
            data-testid="task-title-input"
          />
        </div>

        <div className="form-group">
          <label htmlFor="task-description" className="form-label">
            Descripción
          </label>
          <textarea
            id="task-description"
            className="form-textarea"
            rows={3}
            placeholder="Agrega detalles o notas relevantes sobre esta tarea..."
            value={description}
            maxLength={1000}
            onChange={(e) => setDescription(e.target.value)}
            disabled={isSubmitting}
            data-testid="task-description-input"
          />
        </div>

        {validationError && (
          <p
            className="form-error"
            role="alert"
            data-testid="form-error-message"
          >
            {validationError}
          </p>
        )}

        <div className="form-actions">
          {editingTask && (
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onCancelEdit}
              disabled={isSubmitting}
              data-testid="task-cancel-edit-button"
            >
              Cancelar
            </button>
          )}
          <button
            type="submit"
            className="btn btn-primary"
            disabled={isSubmitting}
            data-testid="task-submit-button"
          >
            {isSubmitting
              ? 'Guardando...'
              : editingTask
                ? 'Guardar Cambios'
                : 'Crear Tarea'}
          </button>
        </div>
      </form>
    </section>
  );
};
