import { beforeEach, describe, expect, it, vi } from 'vitest';
import { taskService } from '../services/taskService';
import { Task } from '../types/task';

const mockTask: Task = {
  id: 1,
  title: 'Tarea de prueba API',
  description: 'Descripción API',
  status: 'Pending',
  created_at: '2026-11-18T10:00:00Z',
  updated_at: '2026-11-18T10:00:00Z',
};

describe('taskService', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('obtiene todas las tareas con getTasks()', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify([mockTask]), { status: 200 }),
    );

    const tasks = await taskService.getTasks();
    expect(tasks).toEqual([mockTask]);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/tasks'),
    );
  });

  it('obtiene una tarea por ID con getTaskById()', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(mockTask), { status: 200 }),
    );

    const task = await taskService.getTaskById(1);
    expect(task.id).toBe(1);
    expect(task.title).toBe('Tarea de prueba API');
  });

  it('crea, cambia estado y elimina una tarea', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch');

    fetchSpy.mockResolvedValueOnce(
      new Response(JSON.stringify(mockTask), { status: 201 }),
    );
    const created = await taskService.createTask({
      title: mockTask.title,
      description: mockTask.description,
    });
    expect(created.id).toBe(1);

    const completedMock: Task = { ...mockTask, status: 'Completed' };
    fetchSpy.mockResolvedValueOnce(
      new Response(JSON.stringify(completedMock), { status: 200 }),
    );
    const toggled = await taskService.updateTaskStatus(1, 'Completed');
    expect(toggled.status).toBe('Completed');

    fetchSpy.mockResolvedValueOnce(
      new Response(
        JSON.stringify({ message: 'Tarea eliminada correctamente.', id: 1 }),
        { status: 200 },
      ),
    );
    const deleted = await taskService.deleteTask(1);
    expect(deleted.id).toBe(1);
  });

  it('maneja errores HTTP con detalle string, lista de validación y cuerpo vacío', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch');

    fetchSpy.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: 'La tarea con ID 99 no existe.' }), {
        status: 404,
      }),
    );
    await expect(taskService.getTaskById(99)).rejects.toThrow(
      'La tarea con ID 99 no existe.',
    );

    fetchSpy.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          detail: [{ msg: 'El título de la tarea no puede estar vacío.' }],
        }),
        { status: 422 },
      ),
    );
    await expect(
      taskService.createTask({ title: '', description: '' }),
    ).rejects.toThrow('El título de la tarea no puede estar vacío.');

    fetchSpy.mockResolvedValueOnce(new Response('Internal Error', { status: 500 }));
    await expect(taskService.getTasks()).rejects.toThrow(
      'Error en la solicitud (HTTP 500)',
    );
  });
});
