export type TaskStatus = 'Pending' | 'Completed';

export type TaskFilterValue = 'All' | TaskStatus;

export interface Task {
  id: number;
  title: string;
  description: string;
  status: TaskStatus;
  created_at: string;
  updated_at: string;
}

export interface TaskCreateInput {
  title: string;
  description: string;
}

export interface DeleteTaskResult {
  message: string;
  id: number;
}
