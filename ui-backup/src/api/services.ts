import apiClient from './client';
import { Project, TaskList, Task } from '../types';

// Project API
export const projectApi = {
  list: async (): Promise<Project[]> => {
    const response = await apiClient.get('/projects');
    return response.data.projects;
  },

  get: async (id: string): Promise<Project> => {
    const response = await apiClient.get(`/projects/${id}`);
    return response.data;
  },

  create: async (project: Partial<Project>): Promise<Project> => {
    const response = await apiClient.post('/projects', project);
    return response.data;
  },

  update: async (id: string, project: Partial<Project>): Promise<Project> => {
    const response = await apiClient.put(`/projects/${id}`, project);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/projects/${id}`);
  },
};

// TaskList API
export const taskListApi = {
  list: async (): Promise<TaskList[]> => {
    const response = await apiClient.get('/task-lists');
    return response.data.task_lists;
  },

  get: async (id: string): Promise<TaskList> => {
    const response = await apiClient.get(`/task-lists/${id}`);
    return response.data;
  },

  create: async (taskList: Partial<TaskList>): Promise<TaskList> => {
    const response = await apiClient.post('/task-lists', taskList);
    return response.data;
  },

  update: async (id: string, taskList: Partial<TaskList>): Promise<TaskList> => {
    const response = await apiClient.put(`/task-lists/${id}`, taskList);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/task-lists/${id}`);
  },

  reset: async (id: string): Promise<void> => {
    await apiClient.post(`/task-lists/${id}/reset`);
  },
};

// Task API
export const taskApi = {
  list: async (): Promise<Task[]> => {
    const response = await apiClient.get('/tasks');
    return response.data.tasks;
  },

  get: async (id: string): Promise<Task> => {
    const response = await apiClient.get(`/tasks/${id}`);
    return response.data;
  },

  create: async (task: Partial<Task>): Promise<Task> => {
    const response = await apiClient.post('/tasks', task);
    return response.data;
  },

  update: async (id: string, task: Partial<Task>): Promise<Task> => {
    const response = await apiClient.put(`/tasks/${id}`, task);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/tasks/${id}`);
  },

  getReady: async (scopeType: 'project' | 'task_list', scopeId: string): Promise<Task[]> => {
    const response = await apiClient.get('/ready-tasks', {
      params: { scope_type: scopeType, scope_id: scopeId },
    });
    return response.data.ready_tasks || [];
  },

  search: async (criteria: any): Promise<any> => {
    const response = await apiClient.post('/search/tasks', criteria);
    return response.data;
  },
};
