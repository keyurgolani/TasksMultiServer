/**
 * LocalStorageService - Mock data service implementation using localStorage.
 * Implements IDataService interface with simulated network delay (300-500ms).
 * 
 * Data is stored in localStorage with keys prefixed by "db_" and serialized as JSON.
 * 
 * @module services/mock/LocalStorageService
 */

import type {
  Project,
  TaskList,
  Task,
  Note,
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
} from '../types';

import { ServiceError } from '../types';
import { generateMockData } from './MockDataGenerator';

// ============================================================================
// Constants
// ============================================================================

/** Default localStorage key prefix */
const DEFAULT_STORAGE_PREFIX = 'db_';

/** Default minimum delay in milliseconds */
const DEFAULT_MIN_DELAY = 300;

/** Default maximum delay in milliseconds */
const DEFAULT_MAX_DELAY = 500;

/** Storage keys */
const STORAGE_KEYS = {
  PROJECTS: 'projects',
  TASK_LISTS: 'taskLists',
  TASKS: 'tasks',
  INITIALIZED: 'initialized',
} as const;

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Generate a UUID v4.
 */
function generateId(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

/**
 * Get current ISO timestamp.
 */
function getCurrentTimestamp(): string {
  return new Date().toISOString();
}

/**
 * Generate a random delay between min and max milliseconds.
 */
function getRandomDelay(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

// ============================================================================
// LocalStorageService Class
// ============================================================================

/**
 * LocalStorageService implements IDataService using browser localStorage.
 * All operations include simulated network delay to mimic real API behavior.
 */
export class LocalStorageService implements IDataService {
  private readonly storagePrefix: string;
  private readonly minDelay: number;
  private readonly maxDelay: number;

  constructor(config?: DataServiceConfig) {
    this.storagePrefix = config?.storageKeyPrefix ?? DEFAULT_STORAGE_PREFIX;
    this.minDelay = config?.mockDelayRange?.min ?? DEFAULT_MIN_DELAY;
    this.maxDelay = config?.mockDelayRange?.max ?? DEFAULT_MAX_DELAY;
    
    // Initialize with seed data if not already initialized
    this.initializeIfNeeded();
  }

  // ==========================================================================
  // Private Helper Methods
  // ==========================================================================

  /**
   * Get the full storage key with prefix.
   */
  private getStorageKey(key: string): string {
    return `${this.storagePrefix}${key}`;
  }

  /**
   * Simulate network delay.
   */
  private async simulateDelay(): Promise<void> {
    const delay = getRandomDelay(this.minDelay, this.maxDelay);
    await new Promise((resolve) => setTimeout(resolve, delay));
  }

  /**
   * Read data from localStorage.
   */
  private readFromStorage<T>(key: string): T[] {
    const storageKey = this.getStorageKey(key);
    const data = localStorage.getItem(storageKey);
    if (!data) {
      return [];
    }
    try {
      return JSON.parse(data) as T[];
    } catch {
      console.error(`Failed to parse localStorage data for key: ${storageKey}`);
      return [];
    }
  }

  /**
   * Write data to localStorage.
   */
  private writeToStorage<T>(key: string, data: T[]): void {
    const storageKey = this.getStorageKey(key);
    try {
      localStorage.setItem(storageKey, JSON.stringify(data));
    } catch (error) {
      throw new ServiceError(
        'Failed to write to localStorage. Storage quota may be exceeded.',
        'STORAGE_ERROR',
        { originalError: error }
      );
    }
  }

  /**
   * Initialize localStorage with seed data if not already initialized.
   */
  private initializeIfNeeded(): void {
    const initializedKey = this.getStorageKey(STORAGE_KEYS.INITIALIZED);
    const isInitialized = localStorage.getItem(initializedKey);
    
    if (!isInitialized) {
      const mockData = generateMockData();
      this.writeToStorage(STORAGE_KEYS.PROJECTS, mockData.projects);
      this.writeToStorage(STORAGE_KEYS.TASK_LISTS, mockData.taskLists);
      this.writeToStorage(STORAGE_KEYS.TASKS, mockData.tasks);
      localStorage.setItem(initializedKey, 'true');
    }
  }

  // ==========================================================================
  // Projects
  // ==========================================================================

  async getProjects(): Promise<Project[]> {
    await this.simulateDelay();
    return this.readFromStorage<Project>(STORAGE_KEYS.PROJECTS);
  }

  async getProject(id: string): Promise<Project> {
    await this.simulateDelay();
    const projects = this.readFromStorage<Project>(STORAGE_KEYS.PROJECTS);
    const project = projects.find((p) => p.id === id);
    if (!project) {
      throw new ServiceError(`Project not found: ${id}`, 'NOT_FOUND', { id });
    }
    return project;
  }

  async createProject(data: CreateProjectDto): Promise<Project> {
    await this.simulateDelay();
    const projects = this.readFromStorage<Project>(STORAGE_KEYS.PROJECTS);
    const now = getCurrentTimestamp();
    const project: Project = {
      id: generateId(),
      name: data.name,
      description: data.description,
      createdAt: now,
      updatedAt: now,
    };
    projects.push(project);
    this.writeToStorage(STORAGE_KEYS.PROJECTS, projects);
    return project;
  }

  async updateProject(id: string, data: UpdateProjectDto): Promise<Project> {
    await this.simulateDelay();
    const projects = this.readFromStorage<Project>(STORAGE_KEYS.PROJECTS);
    const index = projects.findIndex((p) => p.id === id);
    if (index === -1) {
      throw new ServiceError(`Project not found: ${id}`, 'NOT_FOUND', { id });
    }
    const updated: Project = {
      ...projects[index],
      ...data,
      updatedAt: getCurrentTimestamp(),
    };
    projects[index] = updated;
    this.writeToStorage(STORAGE_KEYS.PROJECTS, projects);
    return updated;
  }

  async deleteProject(id: string): Promise<void> {
    await this.simulateDelay();
    const projects = this.readFromStorage<Project>(STORAGE_KEYS.PROJECTS);
    const index = projects.findIndex((p) => p.id === id);
    if (index === -1) {
      throw new ServiceError(`Project not found: ${id}`, 'NOT_FOUND', { id });
    }
    
    // Delete all task lists and tasks in this project
    const taskLists = this.readFromStorage<TaskList>(STORAGE_KEYS.TASK_LISTS);
    const taskListIds = taskLists.filter((tl) => tl.projectId === id).map((tl) => tl.id);
    
    const tasks = this.readFromStorage<Task>(STORAGE_KEYS.TASKS);
    const remainingTasks = tasks.filter((t) => !taskListIds.includes(t.taskListId));
    const remainingTaskLists = taskLists.filter((tl) => tl.projectId !== id);
    
    projects.splice(index, 1);
    this.writeToStorage(STORAGE_KEYS.PROJECTS, projects);
    this.writeToStorage(STORAGE_KEYS.TASK_LISTS, remainingTaskLists);
    this.writeToStorage(STORAGE_KEYS.TASKS, remainingTasks);
  }

  async getProjectStats(id: string): Promise<ProjectStats> {
    await this.simulateDelay();
    
    // Verify project exists
    const projects = this.readFromStorage<Project>(STORAGE_KEYS.PROJECTS);
    if (!projects.find((p) => p.id === id)) {
      throw new ServiceError(`Project not found: ${id}`, 'NOT_FOUND', { id });
    }
    
    const taskLists = this.readFromStorage<TaskList>(STORAGE_KEYS.TASK_LISTS);
    const projectTaskLists = taskLists.filter((tl) => tl.projectId === id);
    const taskListIds = projectTaskLists.map((tl) => tl.id);
    
    const tasks = this.readFromStorage<Task>(STORAGE_KEYS.TASKS);
    const projectTasks = tasks.filter((t) => taskListIds.includes(t.taskListId));
    
    // Calculate ready tasks (no pending dependencies)
    const completedTaskIds = new Set(
      projectTasks.filter((t) => t.status === 'COMPLETED').map((t) => t.id)
    );
    const readyTasks = projectTasks.filter((t) => {
      if (t.status === 'COMPLETED' || t.status === 'BLOCKED') return false;
      return t.dependencies.every((dep) => completedTaskIds.has(dep.taskId));
    });
    
    return {
      taskListCount: projectTaskLists.length,
      totalTasks: projectTasks.length,
      readyTasks: readyTasks.length,
      completedTasks: projectTasks.filter((t) => t.status === 'COMPLETED').length,
      inProgressTasks: projectTasks.filter((t) => t.status === 'IN_PROGRESS').length,
      blockedTasks: projectTasks.filter((t) => t.status === 'BLOCKED').length,
    };
  }

  // ==========================================================================
  // Task Lists
  // ==========================================================================

  async getTaskLists(projectId?: string): Promise<TaskList[]> {
    await this.simulateDelay();
    const taskLists = this.readFromStorage<TaskList>(STORAGE_KEYS.TASK_LISTS);
    if (projectId) {
      return taskLists.filter((tl) => tl.projectId === projectId);
    }
    return taskLists;
  }

  async getTaskList(id: string): Promise<TaskList> {
    await this.simulateDelay();
    const taskLists = this.readFromStorage<TaskList>(STORAGE_KEYS.TASK_LISTS);
    const taskList = taskLists.find((tl) => tl.id === id);
    if (!taskList) {
      throw new ServiceError(`Task list not found: ${id}`, 'NOT_FOUND', { id });
    }
    return taskList;
  }

  async createTaskList(data: CreateTaskListDto): Promise<TaskList> {
    await this.simulateDelay();
    
    // Verify project exists
    const projects = this.readFromStorage<Project>(STORAGE_KEYS.PROJECTS);
    if (!projects.find((p) => p.id === data.projectId)) {
      throw new ServiceError(`Project not found: ${data.projectId}`, 'NOT_FOUND', { id: data.projectId });
    }
    
    const taskLists = this.readFromStorage<TaskList>(STORAGE_KEYS.TASK_LISTS);
    const now = getCurrentTimestamp();
    const taskList: TaskList = {
      id: generateId(),
      projectId: data.projectId,
      name: data.name,
      description: data.description,
      createdAt: now,
      updatedAt: now,
    };
    taskLists.push(taskList);
    this.writeToStorage(STORAGE_KEYS.TASK_LISTS, taskLists);
    return taskList;
  }

  async updateTaskList(id: string, data: UpdateTaskListDto): Promise<TaskList> {
    await this.simulateDelay();
    const taskLists = this.readFromStorage<TaskList>(STORAGE_KEYS.TASK_LISTS);
    const index = taskLists.findIndex((tl) => tl.id === id);
    if (index === -1) {
      throw new ServiceError(`Task list not found: ${id}`, 'NOT_FOUND', { id });
    }
    const updated: TaskList = {
      ...taskLists[index],
      ...data,
      updatedAt: getCurrentTimestamp(),
    };
    taskLists[index] = updated;
    this.writeToStorage(STORAGE_KEYS.TASK_LISTS, taskLists);
    return updated;
  }

  async deleteTaskList(id: string): Promise<void> {
    await this.simulateDelay();
    const taskLists = this.readFromStorage<TaskList>(STORAGE_KEYS.TASK_LISTS);
    const index = taskLists.findIndex((tl) => tl.id === id);
    if (index === -1) {
      throw new ServiceError(`Task list not found: ${id}`, 'NOT_FOUND', { id });
    }
    
    // Delete all tasks in this task list
    const tasks = this.readFromStorage<Task>(STORAGE_KEYS.TASKS);
    const remainingTasks = tasks.filter((t) => t.taskListId !== id);
    
    taskLists.splice(index, 1);
    this.writeToStorage(STORAGE_KEYS.TASK_LISTS, taskLists);
    this.writeToStorage(STORAGE_KEYS.TASKS, remainingTasks);
  }

  async getTaskListStats(id: string): Promise<TaskListStats> {
    await this.simulateDelay();
    
    // Verify task list exists
    const taskLists = this.readFromStorage<TaskList>(STORAGE_KEYS.TASK_LISTS);
    if (!taskLists.find((tl) => tl.id === id)) {
      throw new ServiceError(`Task list not found: ${id}`, 'NOT_FOUND', { id });
    }
    
    const tasks = this.readFromStorage<Task>(STORAGE_KEYS.TASKS);
    const listTasks = tasks.filter((t) => t.taskListId === id);
    
    const completedCount = listTasks.filter((t) => t.status === 'COMPLETED').length;
    const inProgressCount = listTasks.filter((t) => t.status === 'IN_PROGRESS').length;
    const blockedCount = listTasks.filter((t) => t.status === 'BLOCKED').length;
    
    // Calculate ready tasks
    const completedTaskIds = new Set(
      listTasks.filter((t) => t.status === 'COMPLETED').map((t) => t.id)
    );
    const readyTasks = listTasks.filter((t) => {
      if (t.status === 'COMPLETED' || t.status === 'BLOCKED') return false;
      return t.dependencies.every((dep) => completedTaskIds.has(dep.taskId));
    });
    
    return {
      taskCount: listTasks.length,
      readyTasks: readyTasks.length,
      completedTasks: completedCount,
      inProgressTasks: inProgressCount,
      blockedTasks: blockedCount,
      completionPercentage: listTasks.length > 0 
        ? Math.round((completedCount / listTasks.length) * 100) 
        : 0,
    };
  }

  // ==========================================================================
  // Tasks
  // ==========================================================================

  async getTasks(taskListId?: string): Promise<Task[]> {
    await this.simulateDelay();
    const tasks = this.readFromStorage<Task>(STORAGE_KEYS.TASKS);
    if (taskListId) {
      return tasks.filter((t) => t.taskListId === taskListId);
    }
    return tasks;
  }

  async getTask(id: string): Promise<Task> {
    await this.simulateDelay();
    const tasks = this.readFromStorage<Task>(STORAGE_KEYS.TASKS);
    const task = tasks.find((t) => t.id === id);
    if (!task) {
      throw new ServiceError(`Task not found: ${id}`, 'NOT_FOUND', { id });
    }
    return task;
  }

  async createTask(data: CreateTaskDto): Promise<Task> {
    await this.simulateDelay();
    
    // Verify task list exists
    const taskLists = this.readFromStorage<TaskList>(STORAGE_KEYS.TASK_LISTS);
    if (!taskLists.find((tl) => tl.id === data.taskListId)) {
      throw new ServiceError(`Task list not found: ${data.taskListId}`, 'NOT_FOUND', { id: data.taskListId });
    }
    
    const tasks = this.readFromStorage<Task>(STORAGE_KEYS.TASKS);
    const now = getCurrentTimestamp();
    const task: Task = {
      id: generateId(),
      taskListId: data.taskListId,
      title: data.title,
      description: data.description,
      status: data.status ?? 'NOT_STARTED',
      priority: data.priority ?? 'MEDIUM',
      dependencies: data.dependencies ?? [],
      exitCriteria: data.exitCriteria ?? [],
      notes: data.notes ?? [],
      researchNotes: data.researchNotes ?? [],
      executionNotes: [],
      tags: data.tags ?? [],
      createdAt: now,
      updatedAt: now,
    };
    tasks.push(task);
    this.writeToStorage(STORAGE_KEYS.TASKS, tasks);
    return task;
  }

  async updateTask(id: string, data: UpdateTaskDto): Promise<Task> {
    await this.simulateDelay();
    const tasks = this.readFromStorage<Task>(STORAGE_KEYS.TASKS);
    const index = tasks.findIndex((t) => t.id === id);
    if (index === -1) {
      throw new ServiceError(`Task not found: ${id}`, 'NOT_FOUND', { id });
    }
    const updated: Task = {
      ...tasks[index],
      ...data,
      updatedAt: getCurrentTimestamp(),
    };
    tasks[index] = updated;
    this.writeToStorage(STORAGE_KEYS.TASKS, tasks);
    return updated;
  }

  async deleteTask(id: string): Promise<void> {
    await this.simulateDelay();
    const tasks = this.readFromStorage<Task>(STORAGE_KEYS.TASKS);
    const index = tasks.findIndex((t) => t.id === id);
    if (index === -1) {
      throw new ServiceError(`Task not found: ${id}`, 'NOT_FOUND', { id });
    }
    tasks.splice(index, 1);
    this.writeToStorage(STORAGE_KEYS.TASKS, tasks);
  }

  // ==========================================================================
  // Task Notes
  // ==========================================================================

  async addNote(taskId: string, data: AddNoteDto): Promise<Task> {
    await this.simulateDelay();
    const tasks = this.readFromStorage<Task>(STORAGE_KEYS.TASKS);
    const index = tasks.findIndex((t) => t.id === taskId);
    if (index === -1) {
      throw new ServiceError(`Task not found: ${taskId}`, 'NOT_FOUND', { id: taskId });
    }
    
    const note: Note = {
      content: data.content,
      timestamp: getCurrentTimestamp(),
    };
    
    const updated: Task = {
      ...tasks[index],
      notes: [...tasks[index].notes, note],
      updatedAt: getCurrentTimestamp(),
    };
    tasks[index] = updated;
    this.writeToStorage(STORAGE_KEYS.TASKS, tasks);
    return updated;
  }

  async addResearchNote(taskId: string, data: AddNoteDto): Promise<Task> {
    await this.simulateDelay();
    const tasks = this.readFromStorage<Task>(STORAGE_KEYS.TASKS);
    const index = tasks.findIndex((t) => t.id === taskId);
    if (index === -1) {
      throw new ServiceError(`Task not found: ${taskId}`, 'NOT_FOUND', { id: taskId });
    }
    
    const note: Note = {
      content: data.content,
      timestamp: getCurrentTimestamp(),
    };
    
    const updated: Task = {
      ...tasks[index],
      researchNotes: [...tasks[index].researchNotes, note],
      updatedAt: getCurrentTimestamp(),
    };
    tasks[index] = updated;
    this.writeToStorage(STORAGE_KEYS.TASKS, tasks);
    return updated;
  }

  async addExecutionNote(taskId: string, data: AddNoteDto): Promise<Task> {
    await this.simulateDelay();
    const tasks = this.readFromStorage<Task>(STORAGE_KEYS.TASKS);
    const index = tasks.findIndex((t) => t.id === taskId);
    if (index === -1) {
      throw new ServiceError(`Task not found: ${taskId}`, 'NOT_FOUND', { id: taskId });
    }
    
    const note: Note = {
      content: data.content,
      timestamp: getCurrentTimestamp(),
    };
    
    const updated: Task = {
      ...tasks[index],
      executionNotes: [...tasks[index].executionNotes, note],
      updatedAt: getCurrentTimestamp(),
    };
    tasks[index] = updated;
    this.writeToStorage(STORAGE_KEYS.TASKS, tasks);
    return updated;
  }

  // ==========================================================================
  // Search
  // ==========================================================================

  async searchTasks(query: SearchQuery): Promise<PaginatedResponse<Task>> {
    await this.simulateDelay();
    
    let tasks = this.readFromStorage<Task>(STORAGE_KEYS.TASKS);
    
    // Filter by project (get all task lists in project first)
    if (query.projectId) {
      const taskLists = this.readFromStorage<TaskList>(STORAGE_KEYS.TASK_LISTS);
      const projectTaskListIds = taskLists
        .filter((tl) => tl.projectId === query.projectId)
        .map((tl) => tl.id);
      tasks = tasks.filter((t) => projectTaskListIds.includes(t.taskListId));
    }
    
    // Filter by task list
    if (query.taskListId) {
      tasks = tasks.filter((t) => t.taskListId === query.taskListId);
    }
    
    // Filter by text (search in title and description)
    if (query.text) {
      const searchText = query.text.toLowerCase();
      tasks = tasks.filter(
        (t) =>
          t.title.toLowerCase().includes(searchText) ||
          (t.description?.toLowerCase().includes(searchText) ?? false)
      );
    }
    
    // Filter by status
    if (query.status && query.status.length > 0) {
      tasks = tasks.filter((t) => query.status!.includes(t.status));
    }
    
    // Filter by priority
    if (query.priority && query.priority.length > 0) {
      tasks = tasks.filter((t) => query.priority!.includes(t.priority));
    }
    
    // Filter by tags
    if (query.tags && query.tags.length > 0) {
      tasks = tasks.filter((t) => t.tags.some((tag) => query.tags!.includes(tag)));
    }
    
    // Sort
    const sortBy = query.sortBy ?? 'createdAt';
    const sortOrder = query.sortOrder ?? 'desc';
    
    tasks.sort((a, b) => {
      let comparison = 0;
      
      switch (sortBy) {
        case 'title':
          comparison = a.title.localeCompare(b.title);
          break;
        case 'priority': {
          const priorityOrder: Record<string, number> = {
            CRITICAL: 0,
            HIGH: 1,
            MEDIUM: 2,
            LOW: 3,
            TRIVIAL: 4,
          };
          comparison = priorityOrder[a.priority] - priorityOrder[b.priority];
          break;
        }
        case 'updatedAt':
          comparison = new Date(a.updatedAt).getTime() - new Date(b.updatedAt).getTime();
          break;
        case 'createdAt':
        default:
          comparison = new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();
          break;
      }
      
      return sortOrder === 'asc' ? comparison : -comparison;
    });
    
    // Pagination
    const total = tasks.length;
    const offset = query.offset ?? 0;
    const limit = query.limit ?? 50;
    const paginatedTasks = tasks.slice(offset, offset + limit);
    
    return {
      items: paginatedTasks,
      total,
      count: paginatedTasks.length,
      offset,
    };
  }

  async getReadyTasks(scope: { type: 'project' | 'taskList'; id: string }): Promise<Task[]> {
    await this.simulateDelay();
    
    let tasks = this.readFromStorage<Task>(STORAGE_KEYS.TASKS);
    
    if (scope.type === 'project') {
      const taskLists = this.readFromStorage<TaskList>(STORAGE_KEYS.TASK_LISTS);
      const projectTaskListIds = taskLists
        .filter((tl) => tl.projectId === scope.id)
        .map((tl) => tl.id);
      tasks = tasks.filter((t) => projectTaskListIds.includes(t.taskListId));
    } else {
      tasks = tasks.filter((t) => t.taskListId === scope.id);
    }
    
    // Get completed task IDs for dependency checking
    const completedTaskIds = new Set(
      tasks.filter((t) => t.status === 'COMPLETED').map((t) => t.id)
    );
    
    // Ready tasks are those that:
    // 1. Are not COMPLETED or BLOCKED
    // 2. Have all dependencies completed
    return tasks.filter((t) => {
      if (t.status === 'COMPLETED' || t.status === 'BLOCKED') return false;
      return t.dependencies.every((dep) => completedTaskIds.has(dep.taskId));
    });
  }

  // ==========================================================================
  // Utility Methods (for testing)
  // ==========================================================================

  /**
   * Clear all data from localStorage.
   * Useful for testing.
   */
  clearAllData(): void {
    localStorage.removeItem(this.getStorageKey(STORAGE_KEYS.PROJECTS));
    localStorage.removeItem(this.getStorageKey(STORAGE_KEYS.TASK_LISTS));
    localStorage.removeItem(this.getStorageKey(STORAGE_KEYS.TASKS));
    localStorage.removeItem(this.getStorageKey(STORAGE_KEYS.INITIALIZED));
  }

  /**
   * Reset to initial seed data.
   * Useful for testing.
   */
  resetToSeedData(): void {
    this.clearAllData();
    this.initializeIfNeeded();
  }

  /**
   * Get the configured delay range.
   * Useful for testing.
   */
  getDelayRange(): { min: number; max: number } {
    return { min: this.minDelay, max: this.maxDelay };
  }
}
