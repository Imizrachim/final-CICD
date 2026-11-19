import React from 'react';
import { Task, TaskFilterValue } from '../types/task';
import { TaskCard } from './TaskCard';

interface TaskListProps {
  tasks: Task[];
  currentFilter: TaskFilterValue;
  isLoading: boolean;
  isBusy: boolean;
  onToggleStatus: (task: Task) => void;
  onEdit: (task: Task) => void;
  onRequestDelete: (task: Task) => void;
}

export const TaskList: React.FC<TaskListProps> = ({
  tasks,
  currentFilter,
  isLoading,
  isBusy,
  onToggleStatus,
  onEdit,
  onRequestDelete,
}) => {
  if (isLoading) {
    return (
      <div className="loading-state" data-testid="loading-state">
        <div className="spinner" aria-hidden="true" />
        <p>Cargando tareas...</p>
      </div>
    );
  }

  if (tasks.length === 0) {
    const emptyMessages: Record<TaskFilterValue, string> = {
      All: 'No hay tareas registradas todavía. ¡Crea tu primera tarea en el formulario!',
      Pending: 'No tienes tareas pendientes en este momento.',
      Completed: 'Aún no hay tareas completadas.',
    };

    return (
      <div className="empty-state" data-testid="empty-state">
        <p className="empty-title">Sin tareas para mostrar</p>
        <p className="empty-subtitle">{emptyMessages[currentFilter]}</p>
      </div>
    );
  }

  return (
    <div className="task-list" data-testid="task-list">
      {tasks.map((task) => (
        <TaskCard
          key={task.id}
          task={task}
          isBusy={isBusy}
          onToggleStatus={onToggleStatus}
          onEdit={onEdit}
          onRequestDelete={onRequestDelete}
        />
      ))}
    </div>
  );
};
