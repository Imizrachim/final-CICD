import React, { useCallback, useEffect, useMemo, useState } from 'react';
import './App.css';
import { AlertBanner, AlertState } from './components/AlertBanner';
import { ConfirmModal } from './components/ConfirmModal';
import { Header } from './components/Header';
import { TaskFilter } from './components/TaskFilter';
import { TaskForm } from './components/TaskForm';
import { TaskList } from './components/TaskList';
import { TaskStats } from './components/TaskStats';
import { taskService } from './services/taskService';
import {
  Task,
  TaskCreateInput,
  TaskFilterValue,
  TaskStatus,
} from './types/task';

export const App: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [filter, setFilter] = useState<TaskFilterValue>('All');
  const [taskToDelete, setTaskToDelete] = useState<Task | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [alert, setAlert] = useState<AlertState | null>(null);

  const loadTasks = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await taskService.getTasks();
      setTasks(data);
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : 'No fue posible cargar las tareas.';
      setAlert({ type: 'error', message });
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadTasks();
  }, [loadTasks]);

  const counts = useMemo(() => {
    const pending = tasks.filter((t) => t.status === 'Pending').length;
    const completed = tasks.filter((t) => t.status === 'Completed').length;
    return {
      all: tasks.length,
      pending,
      completed,
    };
  }, [tasks]);

  const filteredTasks = useMemo(() => {
    if (filter === 'All') {
      return tasks;
    }
    return tasks.filter((t) => t.status === filter);
  }, [tasks, filter]);

  const handleCreateTask = async (
    payload: TaskCreateInput,
  ): Promise<boolean> => {
    setIsSubmitting(true);
    try {
      const created = await taskService.createTask(payload);
      setTasks((prev) => [created, ...prev]);
      setAlert({
        type: 'success',
        message: 'Tarea creada exitosamente.',
      });
      return true;
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : 'Error al guardar los datos de la tarea.';
      setAlert({ type: 'error', message });
      return false;
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleToggleStatus = async (task: Task) => {
    const nextStatus: TaskStatus =
      task.status === 'Pending' ? 'Completed' : 'Pending';
    setIsSubmitting(true);
    try {
      const updated = await taskService.updateTaskStatus(task.id, nextStatus);
      setTasks((prev) =>
        prev.map((item) => (item.id === updated.id ? updated : item)),
      );
      setAlert({
        type: 'success',
        message:
          nextStatus === 'Completed'
            ? 'Tarea marcada como completada.'
            : 'Tarea marcada como pendiente.',
      });
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : 'No se pudo cambiar el estado de la tarea.';
      setAlert({ type: 'error', message });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleConfirmDelete = async () => {
    if (!taskToDelete) {
      return;
    }
    setIsSubmitting(true);
    try {
      await taskService.deleteTask(taskToDelete.id);
      setTasks((prev) => prev.filter((item) => item.id !== taskToDelete.id));
      setTaskToDelete(null);
      setAlert({
        type: 'success',
        message: 'Tarea eliminada correctamente.',
      });
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : 'No fue posible eliminar la tarea.';
      setAlert({ type: 'error', message });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="app-shell">
      <div className="app-container">
        <Header onRefresh={loadTasks} isLoading={isLoading} />

        <AlertBanner alert={alert} onDismiss={() => setAlert(null)} />

        <TaskStats
          total={counts.all}
          pending={counts.pending}
          completed={counts.completed}
        />

        <main className="dashboard-grid">
          <aside className="dashboard-sidebar">
            <TaskForm
              isSubmitting={isSubmitting}
              onSubmit={handleCreateTask}
            />
          </aside>

          <section className="dashboard-content" aria-label="Listado de tareas">
            <div className="content-header">
              <h2 className="section-title">Mis Tareas</h2>
              <TaskFilter
                currentFilter={filter}
                counts={counts}
                onFilterChange={setFilter}
              />
            </div>

            <TaskList
              tasks={filteredTasks}
              currentFilter={filter}
              isLoading={isLoading}
              isBusy={isSubmitting}
              onToggleStatus={handleToggleStatus}
              onRequestDelete={(task) => setTaskToDelete(task)}
            />
          </section>
        </main>
      </div>

      <ConfirmModal
        taskToDelete={taskToDelete}
        isSubmitting={isSubmitting}
        onConfirm={handleConfirmDelete}
        onCancel={() => setTaskToDelete(null)}
      />
    </div>
  );
};

export default App;
