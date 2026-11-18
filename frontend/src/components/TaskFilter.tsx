import React from 'react';
import { TaskFilterValue } from '../types/task';

interface TaskFilterProps {
  currentFilter: TaskFilterValue;
  counts: {
    all: number;
    pending: number;
    completed: number;
  };
  onFilterChange: (filter: TaskFilterValue) => void;
}

export const TaskFilter: React.FC<TaskFilterProps> = ({
  currentFilter,
  counts,
  onFilterChange,
}) => {
  return (
    <div
      className="filter-bar"
      role="tablist"
      aria-label="Filtrar tareas por estado"
    >
      <button
        type="button"
        role="tab"
        aria-selected={currentFilter === 'All'}
        className={`filter-tab ${currentFilter === 'All' ? 'active' : ''}`}
        onClick={() => onFilterChange('All')}
        data-testid="filter-all"
      >
        Todas <span className="filter-count">{counts.all}</span>
      </button>

      <button
        type="button"
        role="tab"
        aria-selected={currentFilter === 'Pending'}
        className={`filter-tab ${currentFilter === 'Pending' ? 'active' : ''}`}
        onClick={() => onFilterChange('Pending')}
        data-testid="filter-Pending"
      >
        Pendientes <span className="filter-count">{counts.pending}</span>
      </button>

      <button
        type="button"
        role="tab"
        aria-selected={currentFilter === 'Completed'}
        className={`filter-tab ${currentFilter === 'Completed' ? 'active' : ''}`}
        onClick={() => onFilterChange('Completed')}
        data-testid="filter-Completed"
      >
        Completadas <span className="filter-count">{counts.completed}</span>
      </button>
    </div>
  );
};
