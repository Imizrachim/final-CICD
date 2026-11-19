import {
  DeleteTaskResult,
  Task,
  TaskCreateInput,
  TaskStatus,
  TaskUpdateInput,
} from '../types/task';

const rawBaseUrl = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
export const API_BASE_URL = String(rawBaseUrl).replace(/\/+$/, '');

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = `Error en la solicitud (HTTP ${response.status})`;
    try {
      const errorData = await response.json();
      if (typeof errorData?.detail === 'string') {
        errorMessage = errorData.detail;
      } else if (Array.isArray(errorData?.detail) && errorData.detail.length > 0) {
        errorMessage = errorData.detail
          .map((item: { msg?: string }) => item.msg ?? 'Dato inválido')
          .join(', ');
      }
    } catch {
      // Mantiene el mensaje de error HTTP predeterminado si el cuerpo no es JSON
    }
    throw new Error(errorMessage);
  }
  return response.json() as Promise<T>;
}

export const taskService = {
  async getTasks(): Promise<Task[]> {
    const response = await fetch(`${API_BASE_URL}/api/tasks`);
    return parseResponse<Task[]>(response);
  },

  async getTaskById(id: number): Promise<Task> {
    const response = await fetch(`${API_BASE_URL}/api/tasks/${id}`);
    return parseResponse<Task>(response);
  },

  async createTask(payload: TaskCreateInput): Promise<Task> {
    const response = await fetch(`${API_BASE_URL}/api/tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return parseResponse<Task>(response);
  },

  async updateTask(id: number, payload: TaskUpdateInput): Promise<Task> {
    const response = await fetch(`${API_BASE_URL}/api/tasks/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return parseResponse<Task>(response);
  },

  async updateTaskStatus(id: number, status: TaskStatus): Promise<Task> {
    const response = await fetch(`${API_BASE_URL}/api/tasks/${id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    });
    return parseResponse<Task>(response);
  },

  async deleteTask(id: number): Promise<DeleteTaskResult> {
    const response = await fetch(`${API_BASE_URL}/api/tasks/${id}`, {
      method: 'DELETE',
    });
    return parseResponse<DeleteTaskResult>(response);
  },
};
