/**
 * ApiDataService - REST API implementation of IDataService.
 * Communicates with the backend REST API for all data operations.
 * 
 * @module services/api/ApiDataService
 */

import type {
  Project,
  TaskList,
  Task,
} from '../../core/types';

import type {
  IDataService,
  CreateProjectDto,
  UpdateProjectDto,
  CreateTaskListDto,
  UpdateTaskListDto,
  CreateTaskDto,
  UpdateTaskDto,
  AddNoteDto,
  SearchQuery,
  PaginatedResponse,
  ProjectStats,
  TaskListStats,
  DataServiceConfig,
  ServiceErrorCode,
} from '../types';

import { ServiceError } from '../types';

import type {
  ApiProject,
  ApiTaskList,
  ApiTask,
  ApiProjectStats,
  ApiTaskListStats,
  ApiPaginatedResponse,
} from './types';

import {
  transformProject,
  transformTaskList,
  transformTask,
  transformProjectStats,
  transformTaskListStats,
  toApiCreateProject,
  toApiUpdateProject,
  toApiCreateTaskList,
  toApiUpdateTaskList,
  toApiCreateTask,
  toApiUpdateTask,
  toApiSearchRequest,
} from './transformers';

// ============================================================================
// Constants
// ============================================================================

/** Default API base URL */
const DEFAULT_API_BASE_URL = 'http://localhost:8000';


// ============================================================================
// ApiDataService Class
// ============================================================================

/**
 * ApiDataService implements IDataService using the REST API backend.
 * All operations communicate with the backend via HTTP requests.
 */
export class ApiDataService implements IDataService {
  private readonly baseUrl: string;

  constructor(config?: DataServiceConfig) {
    this.baseUrl = config?.apiBaseUrl ?? DEFAULT_API_BASE_URL;
  }

  // ==========================================================================
  // Private Helper Methods
  // ==========================================================================

  /**
   * Perform a fetch request with network error handling.
   * Wraps fetch to catch network errors and convert them to ServiceError.
   * 
   * @param url - The URL to fetch
   * @param options - Fetch options
   * @returns The Response object
   * @throws ServiceError with code 'NETWORK_ERROR' if network fails
   */
  private async fetchWithErrorHandling(
    url: string,
    options?: RequestInit
  ): Promise<Response> {
    try {
      return await fetch(url, options);
    } catch (error) {
      throw new ServiceError(
        'Network error: Unable to connect to the server',
        'NETWORK_ERROR',
        { originalError: error }
      );
    }
  }

  /**
   * Handle HTTP response and convert errors to ServiceError.
   * Maps HTTP status codes to appropriate ServiceErrorCode values.
   * 
   * @param response - The Response object from fetch
   * @returns The parsed JSON response
   * @throws ServiceError with appropriate code based on HTTP status
   */
  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      const errorInfo = errorBody.error || {};

      let code: ServiceErrorCode;
      switch (response.status) {
        case 404:
          code = 'NOT_FOUND';
          break;
        case 400:
        case 409:
          code = 'VALIDATION_ERROR';
          break;
        case 500:
        default:
          code = 'STORAGE_ERROR';
          break;
      }

      throw new ServiceError(
        errorInfo.message || `HTTP ${response.status}`,
        code,
        errorInfo.details
      );
    }

    return response.json();
  }

  /**
   * Build the full URL for an API endpoint.
   * 
   * @param path - The API path (e.g., '/projects')
   * @returns The full URL
   */
  private buildUrl(path: string): string {
    return `${this.baseUrl}${path}`;
  }

  /**
   * Get default headers for JSON requests.
   */
  private getJsonHeaders(): HeadersInit {
    return {
      'Content-Type': 'application/json',
    };
  }

  // ==========================================================================
  // Projects
  // ==========================================================================

  async getProjects(): Promise<Project[]> {
    const response = await this.fetchWithErrorHandling(
      this.buildUrl('/projects')
    );
    const data = await this.handleResponse<{ projects: ApiProject[] }>(response);
    return data.projects.map(transformProject);
  }

  async getProject(id: string): Promise<Project> {
    const response = await this.fetchWithErrorHandling(
      this.buildUrl(`/projects/${id}`)
    );
    const data = await this.handleResponse<{ project: ApiProject }>(response);
    return transformProject(data.project);
  }

  async createProject(data: CreateProjectDto): Promise<Project> {
    const response = await this.fetchWithErrorHandling(
      this.buildUrl('/projects'),
      {
        method: 'POST',
        headers: this.getJsonHeaders(),
        body: JSON.stringify(toApiCreateProject(data)),
      }
    );
    const apiProject = await this.handleResponse<ApiProject>(response);
    return transformProject(apiProject);
  }

  async updateProject(id: string, data: UpdateProjectDto): Promise<Project> {
    const response = await this.fetchWithErrorHandling(
      this.buildUrl(`/projects/${id}`),
      {
        method: 'PUT',
        headers: this.getJsonHeaders(),
        body: JSON.stringify(toApiUpdateProject(data)),
      }
    );
    const apiProject = await this.handleResponse<ApiProject>(response);
    return transformProject(apiProject);
  }

  async deleteProject(id: string): Promise<void> {
    const response = await this.fetchWithErrorHandling(
      this.buildUrl(`/projects/${id}`),
      {
        method: 'DELETE',
      }
    );
    if (!response.ok) {
      await this.handleResponse(response);
    }
  }

  async getProjectStats(id: string): Promise<ProjectStats> {
    // Compute stats client-side since the API doesn't have a stats endpoint
    const taskLists = await this.getTaskLists(id);
    
    // Get all tasks for this project's task lists
    const taskListIds = new Set(taskLists.map(tl => tl.id));
    const allTasks = await this.getTasks();
    const projectTasks = allTasks.filter(t => taskListIds.has(t.taskListId));
    
    return {
      taskListCount: taskLists.length,
      totalTasks: projectTasks.length,
      readyTasks: projectTasks.filter(t => t.status === 'NOT_STARTED').length,
      completedTasks: projectTasks.filter(t => t.status === 'COMPLETED').length,
      inProgressTasks: projectTasks.filter(t => t.status === 'IN_PROGRESS').length,
      blockedTasks: projectTasks.filter(t => t.status === 'BLOCKED').length,
    };
  }

  // ==========================================================================
  // Task Lists
  // ==========================================================================

  async getTaskLists(projectId?: string): Promise<TaskList[]> {
    const url = projectId
      ? this.buildUrl(`/task-lists?project_id=${projectId}`)
      : this.buildUrl('/task-lists');
    const response = await this.fetchWithErrorHandling(url);
    const data = await this.handleResponse<{ task_lists: ApiTaskList[] }>(response);
    return data.task_lists.map(transformTaskList);
  }

  async getTaskList(id: string): Promise<TaskList> {
    const response = await this.fetchWithErrorHandling(
      this.buildUrl(`/task-lists/${id}`)
    );
    const data = await this.handleResponse<{ task_list: ApiTaskList }>(response);
    return transformTaskList(data.task_list);
  }

  async createTaskList(data: CreateTaskListDto): Promise<TaskList> {
    const response = await this.fetchWithErrorHandling(
      this.buildUrl('/task-lists'),
      {
        method: 'POST',
        headers: this.getJsonHeaders(),
        body: JSON.stringify(toApiCreateTaskList(data)),
      }
    );
    const apiTaskList = await this.handleResponse<ApiTaskList>(response);
    return transformTaskList(apiTaskList);
  }

  async updateTaskList(id: string, data: UpdateTaskListDto): Promise<TaskList> {
    const response = await this.fetchWithErrorHandling(
      this.buildUrl(`/task-lists/${id}`),
      {
        method: 'PUT',
        headers: this.getJsonHeaders(),
        body: JSON.stringify(toApiUpdateTaskList(data)),
      }
    );
    const apiTaskList = await this.handleResponse<ApiTaskList>(response);
    return transformTaskList(apiTaskList);
  }

  async deleteTaskList(id: string): Promise<void> {
    const response = await this.fetchWithErrorHandling(
      this.buildUrl(`/task-lists/${id}`),
      {
        method: 'DELETE',
      }
    );
    if (!response.ok) {
      await this.handleResponse(response);
    }
  }

  async getTaskListStats(id: string): Promise<TaskListStats> {
    // Compute stats client-side since the API doesn't have a stats endpoint
    const tasks = await this.getTasks(id);
    const totalTasks = tasks.length;
    const completedTasks = tasks.filter(t => t.status === 'COMPLETED').length;
    
    return {
      taskCount: totalTasks,
      readyTasks: tasks.filter(t => t.status === 'NOT_STARTED').length,
      completedTasks,
      inProgressTasks: tasks.filter(t => t.status === 'IN_PROGRESS').length,
      blockedTasks: tasks.filter(t => t.status === 'BLOCKED').length,
      completionPercentage: totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0,
    };
  }

  // ==========================================================================
  // Tasks
  // ==========================================================================

  async getTasks(taskListId?: string): Promise<Task[]> {
    const url = taskListId
      ? this.buildUrl(`/tasks?task_list_id=${taskListId}`)
      : this.buildUrl('/tasks');
    const response = await this.fetchWithErrorHandling(url);
    const data = await this.handleResponse<{ tasks: ApiTask[] }>(response);
    return data.tasks.map(transformTask);
  }

  async getTask(id: string): Promise<Task> {
    const response = await this.fetchWithErrorHandling(
      this.buildUrl(`/tasks/${id}`)
    );
    const data = await this.handleResponse<{ task: ApiTask }>(response);
    return transformTask(data.task);
  }

  async createTask(data: CreateTaskDto): Promise<Task> {
    const response = await this.fetchWithErrorHandling(
      this.buildUrl('/tasks'),
      {
        method: 'POST',
        headers: this.getJsonHeaders(),
        body: JSON.stringify(toApiCreateTask(data)),
      }
    );
    const apiTask = await this.handleResponse<ApiTask>(response);
    return transformTask(apiTask);
  }

  async updateTask(id: string, data: UpdateTaskDto): Promise<Task> {
    const response = await this.fetchWithErrorHandling(
      this.buildUrl(`/tasks/${id}`),
      {
        method: 'PUT',
        headers: this.getJsonHeaders(),
        body: JSON.stringify(toApiUpdateTask(data)),
      }
    );
    const apiTask = await this.handleResponse<ApiTask>(response);
    return transformTask(apiTask);
  }

  async deleteTask(id: string): Promise<void> {
    const response = await this.fetchWithErrorHandling(
      this.buildUrl(`/tasks/${id}`),
      {
        method: 'DELETE',
      }
    );
    if (!response.ok) {
      await this.handleResponse(response);
    }
  }

  // ==========================================================================
  // Task Notes
  // ==========================================================================

  async addNote(taskId: string, data: AddNoteDto): Promise<Task> {
    const response = await this.fetchWithErrorHandling(
      this.buildUrl(`/tasks/${taskId}/notes`),
      {
        method: 'POST',
        headers: this.getJsonHeaders(),
        body: JSON.stringify({ content: data.content }),
      }
    );
    const apiTask = await this.handleResponse<ApiTask>(response);
    return transformTask(apiTask);
  }

  async addResearchNote(taskId: string, data: AddNoteDto): Promise<Task> {
    const response = await this.fetchWithErrorHandling(
      this.buildUrl(`/tasks/${taskId}/research-notes`),
      {
        method: 'POST',
        headers: this.getJsonHeaders(),
        body: JSON.stringify({ content: data.content }),
      }
    );
    const apiTask = await this.handleResponse<ApiTask>(response);
    return transformTask(apiTask);
  }

  async addExecutionNote(taskId: string, data: AddNoteDto): Promise<Task> {
    const response = await this.fetchWithErrorHandling(
      this.buildUrl(`/tasks/${taskId}/execution-notes`),
      {
        method: 'POST',
        headers: this.getJsonHeaders(),
        body: JSON.stringify({ content: data.content }),
      }
    );
    const apiTask = await this.handleResponse<ApiTask>(response);
    return transformTask(apiTask);
  }

  // ==========================================================================
  // Search
  // ==========================================================================

  async searchTasks(query: SearchQuery): Promise<PaginatedResponse<Task>> {
    const response = await this.fetchWithErrorHandling(
      this.buildUrl('/tasks/search'),
      {
        method: 'POST',
        headers: this.getJsonHeaders(),
        body: JSON.stringify(toApiSearchRequest(query)),
      }
    );
    const apiResponse = await this.handleResponse<ApiPaginatedResponse<ApiTask>>(response);
    return {
      items: apiResponse.items.map(transformTask),
      total: apiResponse.total,
      count: apiResponse.count,
      offset: apiResponse.offset,
    };
  }

  async getReadyTasks(scope: { type: 'project' | 'taskList'; id: string }): Promise<Task[]> {
    const scopeType = scope.type === 'project' ? 'project' : 'task_list';
    const response = await this.fetchWithErrorHandling(
      this.buildUrl(`/tasks/ready?scope_type=${scopeType}&scope_id=${scope.id}`)
    );
    const apiTasks = await this.handleResponse<ApiTask[]>(response);
    return apiTasks.map(transformTask);
  }

  // ==========================================================================
  // Utility Methods (for testing)
  // ==========================================================================

  /**
   * Get the configured base URL.
   * Useful for testing.
   */
  getBaseUrl(): string {
    return this.baseUrl;
  }
}
