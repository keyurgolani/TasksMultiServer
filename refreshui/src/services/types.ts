/**
 * Service layer type definitions.
 * Defines the IDataService interface and DTOs for data operations.
 * 
 * @module services/types
 */

import type {
  Project,
  TaskList,
  Task,
  TaskStatus,
  TaskPriority,
  ExitCriterion,
  TaskDependency,
  Note,
} from '../core/types';

// Re-export entity types for convenience
export type {
  Project,
  TaskList,
  Task,
  TaskStatus,
  TaskPriority,
  ExitCriterion,
  TaskDependency,
  Note,
};

// ============================================================================
// DTOs (Data Transfer Objects)
// ============================================================================

/**
 * DTO for creating a new project.
 */
export interface CreateProjectDto {
  /** Display name of the project */
  name: string;
  /** Optional description of the project */
  description?: string;
}

/**
 * DTO for updating an existing project.
 */
export interface UpdateProjectDto {
  /** Updated display name */
  name?: string;
  /** Updated description */
  description?: string;
}

/**
 * DTO for creating a new task list.
 */
export interface CreateTaskListDto {
  /** ID of the parent project */
  projectId: string;
  /** Display name of the task list */
  name: string;
  /** Optional description of the task list */
  description?: string;
}

/**
 * DTO for updating an existing task list.
 */
export interface UpdateTaskListDto {
  /** Updated display name */
  name?: string;
  /** Updated description */
  description?: string;
  /** Updated project ID - allows changing project assignment (Requirements: 21.3) */
  projectId?: string;
}

/**
 * DTO for creating a new task.
 */
export interface CreateTaskDto {
  /** ID of the task list to contain this task */
  taskListId: string;
  /** Title/name of the task */
  title: string;
  /** Optional detailed description */
  description?: string;
  /** Initial status (defaults to NOT_STARTED) */
  status?: TaskStatus;
  /** Priority level (defaults to MEDIUM) */
  priority?: TaskPriority;
  /** Initial dependencies */
  dependencies?: TaskDependency[];
  /** Initial exit criteria */
  exitCriteria?: ExitCriterion[];
  /** Initial tags */
  tags?: string[];
  /** Initial general notes */
  notes?: Note[];
  /** Initial research notes */
  researchNotes?: Note[];
}

/**
 * DTO for updating an existing task.
 */
export interface UpdateTaskDto {
  /** Updated title */
  title?: string;
  /** Updated description */
  description?: string;
  /** Updated status */
  status?: TaskStatus;
  /** Updated priority */
  priority?: TaskPriority;
  /** Updated dependencies */
  dependencies?: TaskDependency[];
  /** Updated exit criteria */
  exitCriteria?: ExitCriterion[];
  /** Updated tags */
  tags?: string[];
}

/**
 * DTO for adding a note to a task.
 */
export interface AddNoteDto {
  /** Content of the note */
  content: string;
}

// ============================================================================
// Search and Filter Types
// ============================================================================

/**
 * Query parameters for searching tasks.
 */
export interface SearchQuery {
  /** Text to search in title and description */
  text?: string;
  /** Filter by status values */
  status?: TaskStatus[];
  /** Filter by priority values */
  priority?: TaskPriority[];
  /** Filter by tags (tasks must have at least one matching tag) */
  tags?: string[];
  /** Filter by task list ID */
  taskListId?: string;
  /** Filter by project ID (searches all task lists in project) */
  projectId?: string;
  /** Maximum number of results to return */
  limit?: number;
  /** Number of results to skip (for pagination) */
  offset?: number;
  /** Sort field */
  sortBy?: 'createdAt' | 'updatedAt' | 'priority' | 'title';
  /** Sort direction */
  sortOrder?: 'asc' | 'desc';
}

/**
 * Paginated response wrapper.
 */
export interface PaginatedResponse<T> {
  /** Array of items */
  items: T[];
  /** Total count of items matching the query */
  total: number;
  /** Number of items returned */
  count: number;
  /** Offset used in the query */
  offset: number;
}

// ============================================================================
// Statistics Types
// ============================================================================

/**
 * Statistics for a project.
 */
export interface ProjectStats {
  /** Number of task lists in the project */
  taskListCount: number;
  /** Total number of tasks across all task lists */
  totalTasks: number;
  /** Number of tasks ready for execution */
  readyTasks: number;
  /** Number of completed tasks */
  completedTasks: number;
  /** Number of in-progress tasks */
  inProgressTasks: number;
  /** Number of blocked tasks */
  blockedTasks: number;
}

/**
 * Statistics for a task list.
 */
export interface TaskListStats {
  /** Total number of tasks */
  taskCount: number;
  /** Number of tasks ready for execution */
  readyTasks: number;
  /** Number of completed tasks */
  completedTasks: number;
  /** Number of in-progress tasks */
  inProgressTasks: number;
  /** Number of blocked tasks */
  blockedTasks: number;
  /** Completion percentage (0-100) */
  completionPercentage: number;
}

// ============================================================================
// Service Interface
// ============================================================================

/**
 * Abstract data service interface.
 * Implementations can be mock (localStorage) or real API.
 * All methods return Promises to support async operations.
 */
export interface IDataService {
  // -------------------------------------------------------------------------
  // Projects
  // -------------------------------------------------------------------------
  
  /**
   * Get all projects.
   * @returns Promise resolving to array of projects
   */
  getProjects(): Promise<Project[]>;
  
  /**
   * Get a single project by ID.
   * @param id - Project ID
   * @returns Promise resolving to the project
   * @throws Error if project not found
   */
  getProject(id: string): Promise<Project>;
  
  /**
   * Create a new project.
   * @param data - Project creation data
   * @returns Promise resolving to the created project
   */
  createProject(data: CreateProjectDto): Promise<Project>;
  
  /**
   * Update an existing project.
   * @param id - Project ID
   * @param data - Project update data
   * @returns Promise resolving to the updated project
   * @throws Error if project not found
   */
  updateProject(id: string, data: UpdateProjectDto): Promise<Project>;
  
  /**
   * Delete a project and all its task lists and tasks.
   * @param id - Project ID
   * @throws Error if project not found
   */
  deleteProject(id: string): Promise<void>;
  
  /**
   * Get statistics for a project.
   * @param id - Project ID
   * @returns Promise resolving to project statistics
   */
  getProjectStats(id: string): Promise<ProjectStats>;

  // -------------------------------------------------------------------------
  // Task Lists
  // -------------------------------------------------------------------------
  
  /**
   * Get task lists, optionally filtered by project.
   * @param projectId - Optional project ID to filter by
   * @returns Promise resolving to array of task lists
   */
  getTaskLists(projectId?: string): Promise<TaskList[]>;
  
  /**
   * Get a single task list by ID.
   * @param id - Task list ID
   * @returns Promise resolving to the task list
   * @throws Error if task list not found
   */
  getTaskList(id: string): Promise<TaskList>;
  
  /**
   * Create a new task list.
   * @param data - Task list creation data
   * @returns Promise resolving to the created task list
   */
  createTaskList(data: CreateTaskListDto): Promise<TaskList>;
  
  /**
   * Update an existing task list.
   * @param id - Task list ID
   * @param data - Task list update data
   * @returns Promise resolving to the updated task list
   * @throws Error if task list not found
   */
  updateTaskList(id: string, data: UpdateTaskListDto): Promise<TaskList>;
  
  /**
   * Delete a task list and all its tasks.
   * @param id - Task list ID
   * @throws Error if task list not found
   */
  deleteTaskList(id: string): Promise<void>;
  
  /**
   * Get statistics for a task list.
   * @param id - Task list ID
   * @returns Promise resolving to task list statistics
   */
  getTaskListStats(id: string): Promise<TaskListStats>;

  // -------------------------------------------------------------------------
  // Tasks
  // -------------------------------------------------------------------------
  
  /**
   * Get tasks, optionally filtered by task list.
   * @param taskListId - Optional task list ID to filter by
   * @returns Promise resolving to array of tasks
   */
  getTasks(taskListId?: string): Promise<Task[]>;
  
  /**
   * Get a single task by ID.
   * @param id - Task ID
   * @returns Promise resolving to the task
   * @throws Error if task not found
   */
  getTask(id: string): Promise<Task>;
  
  /**
   * Create a new task.
   * @param data - Task creation data
   * @returns Promise resolving to the created task
   */
  createTask(data: CreateTaskDto): Promise<Task>;
  
  /**
   * Update an existing task.
   * @param id - Task ID
   * @param data - Task update data
   * @returns Promise resolving to the updated task
   * @throws Error if task not found
   */
  updateTask(id: string, data: UpdateTaskDto): Promise<Task>;
  
  /**
   * Delete a task.
   * @param id - Task ID
   * @throws Error if task not found
   */
  deleteTask(id: string): Promise<void>;

  // -------------------------------------------------------------------------
  // Task Notes
  // -------------------------------------------------------------------------
  
  /**
   * Add a general note to a task.
   * @param taskId - Task ID
   * @param data - Note data
   * @returns Promise resolving to the updated task
   */
  addNote(taskId: string, data: AddNoteDto): Promise<Task>;
  
  /**
   * Add a research note to a task.
   * @param taskId - Task ID
   * @param data - Note data
   * @returns Promise resolving to the updated task
   */
  addResearchNote(taskId: string, data: AddNoteDto): Promise<Task>;
  
  /**
   * Add an execution note to a task.
   * @param taskId - Task ID
   * @param data - Note data
   * @returns Promise resolving to the updated task
   */
  addExecutionNote(taskId: string, data: AddNoteDto): Promise<Task>;

  // -------------------------------------------------------------------------
  // Search
  // -------------------------------------------------------------------------
  
  /**
   * Search tasks with filtering, sorting, and pagination.
   * @param query - Search query parameters
   * @returns Promise resolving to paginated task results
   */
  searchTasks(query: SearchQuery): Promise<PaginatedResponse<Task>>;
  
  /**
   * Get tasks that are ready for execution (no pending dependencies).
   * @param scope - Scope to search within
   * @returns Promise resolving to array of ready tasks
   */
  getReadyTasks(scope: { type: 'project' | 'taskList'; id: string }): Promise<Task[]>;
}

// ============================================================================
// Service Error Types
// ============================================================================

/**
 * Error codes for service operations.
 */
export type ServiceErrorCode =
  | 'NOT_FOUND'
  | 'VALIDATION_ERROR'
  | 'NETWORK_ERROR'
  | 'STORAGE_ERROR'
  | 'UNKNOWN_ERROR';

/**
 * Custom error class for service operations.
 */
export class ServiceError extends Error {
  readonly code: ServiceErrorCode;
  readonly details?: Record<string, unknown>;

  constructor(
    message: string,
    code: ServiceErrorCode,
    details?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'ServiceError';
    this.code = code;
    this.details = details;
  }
}

// ============================================================================
// Service Configuration
// ============================================================================

/**
 * Configuration options for data services.
 */
export interface DataServiceConfig {
  /** Base URL for API service */
  apiBaseUrl?: string;
  /** Simulated network delay range for mock service (ms) */
  mockDelayRange?: { min: number; max: number };
  /** localStorage key prefix for mock service */
  storageKeyPrefix?: string;
}
