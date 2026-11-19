import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../App';
import { taskService } from '../services/taskService';
import { Task } from '../types/task';

const sampleTasks: Task[] = [
  {
    id: 1,
    title: 'Configurar Docker Compose',
    description: 'Levantar servicios de frontend, backend y postgres',
    status: 'Pending',
    created_at: '2026-11-18T10:00:00Z',
    updated_at: '2026-11-18T10:00:00Z',
  },
  {
    id: 2,
    title: 'Implementar pruebas unitarias',
    description: 'Superar el 80% de cobertura con Pytest-Cov',
    status: 'Completed',
    created_at: '2026-11-18T11:00:00Z',
    updated_at: '2026-11-18T11:30:00Z',
  },
];

describe('App - Task Manager UI & Integration', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('muestra estado de carga y renderiza dashboard, contadores y listado de tareas', async () => {
    vi.spyOn(taskService, 'getTasks').mockResolvedValueOnce(sampleTasks);

    render(<App />);
    expect(screen.getByTestId('loading-state')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByTestId('task-list')).toBeInTheDocument();
    });

    expect(screen.getByTestId('app-header')).toHaveTextContent('Task Manager');
    expect(screen.getByTestId('stat-total')).toHaveTextContent('2');
    expect(screen.getByTestId('stat-pending')).toHaveTextContent('1');
    expect(screen.getByTestId('stat-completed')).toHaveTextContent('1');

    const cards = screen.getAllByTestId('task-card');
    expect(cards).toHaveLength(2);
    expect(screen.getByText('Configurar Docker Compose')).toBeInTheDocument();
    expect(
      screen.getByText('Implementar pruebas unitarias'),
    ).toBeInTheDocument();
  });

  it('valida el formulario evitando títulos vacíos y crea una nueva tarea correctamente', async () => {
    const user = userEvent.setup();
    vi.spyOn(taskService, 'getTasks').mockResolvedValueOnce([]);
    const createSpy = vi
      .spyOn(taskService, 'createTask')
      .mockResolvedValueOnce({
        id: 10,
        title: 'Preparar SonarCloud',
        description: 'Configurar sonar-project.properties',
        status: 'Pending',
        created_at: '2026-11-18T12:00:00Z',
        updated_at: '2026-11-18T12:00:00Z',
      });

    render(<App />);
    await waitFor(() => {
      expect(screen.getByTestId('empty-state')).toBeInTheDocument();
    });

    await user.click(screen.getByTestId('task-submit-button'));
    expect(screen.getByTestId('form-error-message')).toHaveTextContent(
      'El título de la tarea es obligatorio.',
    );
    expect(createSpy).not.toHaveBeenCalled();

    await user.type(
      screen.getByTestId('task-title-input'),
      '  Preparar SonarCloud  ',
    );
    await user.type(
      screen.getByTestId('task-description-input'),
      'Configurar sonar-project.properties',
    );
    await user.click(screen.getByTestId('task-submit-button'));

    await waitFor(() => {
      expect(createSpy).toHaveBeenCalledWith({
        title: 'Preparar SonarCloud',
        description: 'Configurar sonar-project.properties',
      });
    });

    expect(screen.getByText('Preparar SonarCloud')).toBeInTheDocument();
    expect(screen.getByTestId('stat-total')).toHaveTextContent('1');
    expect(screen.getByTestId('alert-banner')).toHaveTextContent(
      'Tarea creada exitosamente.',
    );
  });

  it('permite editar una tarea existente o cancelar la edición', async () => {
    const user = userEvent.setup();
    vi.spyOn(taskService, 'getTasks').mockResolvedValueOnce([sampleTasks[0]]);
    const updateSpy = vi
      .spyOn(taskService, 'updateTask')
      .mockResolvedValueOnce({
        ...sampleTasks[0],
        title: 'Docker Compose Actualizado',
        description: 'Con healthcheck en PostgreSQL',
      });

    render(<App />);
    await waitFor(() => {
      expect(screen.getByText('Configurar Docker Compose')).toBeInTheDocument();
    });

    await user.click(screen.getByTestId('task-edit-btn'));
    expect(screen.getByTestId('task-title-input')).toHaveValue(
      'Configurar Docker Compose',
    );
    await user.click(screen.getByTestId('task-cancel-edit-button'));
    expect(screen.getByTestId('task-title-input')).toHaveValue('');

    await user.click(screen.getByTestId('task-edit-btn'));
    const titleInput = screen.getByTestId('task-title-input');
    const descInput = screen.getByTestId('task-description-input');

    await user.clear(titleInput);
    await user.type(titleInput, 'Docker Compose Actualizado');
    await user.clear(descInput);
    await user.type(descInput, 'Con healthcheck en PostgreSQL');
    await user.click(screen.getByTestId('task-submit-button'));

    await waitFor(() => {
      expect(updateSpy).toHaveBeenCalledWith(1, {
        title: 'Docker Compose Actualizado',
        description: 'Con healthcheck en PostgreSQL',
        status: 'Pending',
      });
    });

    expect(screen.getByText('Docker Compose Actualizado')).toBeInTheDocument();
    expect(screen.getByTestId('alert-banner')).toHaveTextContent(
      'Tarea actualizada correctamente.',
    );
  });

  it('cambia el estado de una tarea entre Pending y Completed', async () => {
    const user = userEvent.setup();
    vi.spyOn(taskService, 'getTasks').mockResolvedValueOnce([sampleTasks[0]]);
    const statusSpy = vi
      .spyOn(taskService, 'updateTaskStatus')
      .mockResolvedValueOnce({
        ...sampleTasks[0],
        status: 'Completed',
      });

    render(<App />);
    await waitFor(() => {
      expect(screen.getByTestId('task-card')).toBeInTheDocument();
    });

    expect(screen.getByTestId('task-status-badge')).toHaveAttribute(
      'data-status',
      'Pending',
    );

    await user.click(screen.getByTestId('task-toggle-status-btn'));

    await waitFor(() => {
      expect(statusSpy).toHaveBeenCalledWith(1, 'Completed');
    });

    expect(screen.getByTestId('task-status-badge')).toHaveAttribute(
      'data-status',
      'Completed',
    );
    expect(screen.getByTestId('stat-completed')).toHaveTextContent('1');
    expect(screen.getByTestId('stat-pending')).toHaveTextContent('0');
  });

  it('filtra las tareas por Todas, Pendientes y Completadas', async () => {
    const user = userEvent.setup();
    vi.spyOn(taskService, 'getTasks').mockResolvedValueOnce(sampleTasks);

    render(<App />);
    await waitFor(() => {
      expect(screen.getAllByTestId('task-card')).toHaveLength(2);
    });

    await user.click(screen.getByTestId('filter-Pending'));
    expect(screen.getAllByTestId('task-card')).toHaveLength(1);
    expect(screen.getByText('Configurar Docker Compose')).toBeInTheDocument();

    await user.click(screen.getByTestId('filter-Completed'));
    expect(screen.getAllByTestId('task-card')).toHaveLength(1);
    expect(
      screen.getByText('Implementar pruebas unitarias'),
    ).toBeInTheDocument();

    await user.click(screen.getByTestId('filter-all'));
    expect(screen.getAllByTestId('task-card')).toHaveLength(2);
  });

  it('solicita confirmación antes de eliminar una tarea y permite cancelar o confirmar', async () => {
    const user = userEvent.setup();
    vi.spyOn(taskService, 'getTasks').mockResolvedValueOnce([sampleTasks[0]]);
    const deleteSpy = vi
      .spyOn(taskService, 'deleteTask')
      .mockResolvedValueOnce({
        message: 'Tarea eliminada correctamente.',
        id: 1,
      });

    render(<App />);
    await waitFor(() => {
      expect(screen.getByTestId('task-card')).toBeInTheDocument();
    });

    await user.click(screen.getByTestId('task-delete-btn'));
    const modal = screen.getByTestId('confirm-modal');
    expect(modal).toBeInTheDocument();
    await user.click(within(modal).getByTestId('cancel-delete-btn'));
    expect(screen.queryByTestId('confirm-modal')).not.toBeInTheDocument();
    expect(deleteSpy).not.toHaveBeenCalled();

    await user.click(screen.getByTestId('task-delete-btn'));
    await user.click(screen.getByTestId('confirm-delete-btn'));

    await waitFor(() => {
      expect(deleteSpy).toHaveBeenCalledWith(1);
    });

    expect(screen.queryByTestId('task-card')).not.toBeInTheDocument();
    expect(screen.getByTestId('empty-state')).toBeInTheDocument();
    expect(screen.getByTestId('stat-total')).toHaveTextContent('0');
  });

  it('muestra y permite cerrar mensajes de error cuando falla la API', async () => {
    const user = userEvent.setup();
    vi.spyOn(taskService, 'getTasks').mockRejectedValueOnce(
      new Error('Error de conexión con el servidor backend'),
    );

    render(<App />);

    const alert = await screen.findByTestId('alert-banner');
    expect(alert).toHaveAttribute('data-alert-type', 'error');
    expect(alert).toHaveTextContent(
      'Error de conexión con el servidor backend',
    );

    await user.click(screen.getByTestId('alert-close-btn'));
    expect(screen.queryByTestId('alert-banner')).not.toBeInTheDocument();
  });
});
