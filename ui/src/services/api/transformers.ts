/**
 * Data transformers for converting between API (snake_case) and frontend (camelCase) formats.
 * 
 * @module services/api/transformers
 */

import type {
  Project,
  TaskList,
  Task,
  TaskDependency,
  ExitCriterion,
  Note,
  ActionPlanItem,
  TaskStatus,
  TaskPriority,
} from '../../core/types';

import type {
  ProjectStats,
  TaskListStats,
  CreateProjectDto,
  UpdateProjectDto,
  CreateTaskListDto,
  UpdateTaskListDto,
  CreateTaskDto,
  UpdateTaskDto,
  SearchQuery,
} from '../types';

import type {
  ApiProject,
  ApiTaskList,
  ApiTask,
  ApiDependency,
  ApiExitCriteria,
  ApiNote,
  ApiActionPlanItem,
  ApiProjectStats,
  ApiTaskListStats,
  ApiCreateProjectRequest,
  ApiUpdateProjectRequest,
  ApiCreateTaskListRequest,
  ApiUpdateTaskListRequest,
  ApiCreateTaskRequest,
  ApiUpdateTaskRequest,
  ApiSearchRequest,
} from './types';

// ============================================================================
// API Response to Frontend Transformers
// ============================================================================

/**
 * Transform an API project response to frontend Project type.
 * Converts snake_case fields to camelCase.
 */
export function transformProject(apiProject: ApiProject): Project {
  return {
    id: apiProject.id,
    name: apiProject.name,
    isDefault: apiProject.is_default,
    createdAt: apiProject.created_at,
    updatedAt: apiProject.updated_at,
  };
}

/**
 * Transform an API task list response to frontend TaskList type.
 * Converts snake_case fields to camelCase.
 */
export function transformTaskList(apiTaskList: ApiTaskList): TaskList {
  return {
    id: apiTaskList.id,
    name: apiTaskList.name,
    projectId: apiTaskList.project_id,
    createdAt: apiTaskList.created_at,
    updatedAt: apiTaskList.updated_at,
  };
}

/**
 * Transform an API dependency to frontend TaskDependency type.
 */
export function transformDependency(apiDep: ApiDependency): TaskDependency {
  return {
    taskId: apiDep.task_id,
    taskListId: apiDep.task_list_id,
  };
}

/**
 * Transform an API exit criteria to frontend ExitCriterion type.
 */
export function transformExitCriteria(apiCriteria: ApiExitCriteria): ExitCriterion {
  return {
    criteria: apiCriteria.criteria,
    status: apiCriteria.status as 'INCOMPLETE' | 'COMPLETE',
    comment: apiCriteria.comment ?? undefined,
  };
}

/**
 * Transform an API note to frontend Note type.
 */
export function transformNote(apiNote: ApiNote): Note {
  return {
    content: apiNote.content,
    timestamp: apiNote.timestamp ?? new Date().toISOString(),
  };
}

/**
 * Transform an API action plan item to frontend ActionPlanItem type.
 */
export function transformActionPlanItem(apiItem: ApiActionPlanItem): ActionPlanItem {
  return {
    sequence: apiItem.sequence,
    content: apiItem.content,
  };
}

/**
 * Transform an API task response to frontend Task type.
 * Converts snake_case fields to camelCase.
 */
export function transformTask(apiTask: ApiTask): Task {
  return {
    id: apiTask.id,
    taskListId: apiTask.task_list_id,
    title: apiTask.title,
    description: apiTask.description,
    status: apiTask.status as TaskStatus,
    priority: apiTask.priority as TaskPriority,
    dependencies: (apiTask.dependencies || []).map(transformDependency),
    exitCriteria: (apiTask.exit_criteria || []).map(transformExitCriteria),
    notes: (apiTask.notes || []).map(transformNote),
    researchNotes: (apiTask.research_notes || []).map(transformNote),
    executionNotes: (apiTask.execution_notes || []).map(transformNote),
    tags: apiTask.tags || [],
    actionPlan: apiTask.action_plan?.map(transformActionPlanItem),
    createdAt: apiTask.created_at,
    updatedAt: apiTask.updated_at,
  };
}

/**
 * Transform API project statistics to frontend ProjectStats type.
 */
export function transformProjectStats(apiStats: ApiProjectStats): ProjectStats {
  return {
    taskListCount: apiStats.task_list_count,
    totalTasks: apiStats.total_tasks,
    readyTasks: apiStats.ready_tasks,
    completedTasks: apiStats.completed_tasks,
    inProgressTasks: apiStats.in_progress_tasks,
    blockedTasks: apiStats.blocked_tasks,
  };
}

/**
 * Transform API task list statistics to frontend TaskListStats type.
 */
export function transformTaskListStats(apiStats: ApiTaskListStats): TaskListStats {
  return {
    taskCount: apiStats.task_count,
    readyTasks: apiStats.ready_tasks,
    completedTasks: apiStats.completed_tasks,
    inProgressTasks: apiStats.in_progress_tasks,
    blockedTasks: apiStats.blocked_tasks,
    completionPercentage: apiStats.completion_percentage,
  };
}

// ============================================================================
// Frontend to API Request Transformers (Reverse Transformers)
// ============================================================================

/**
 * Transform frontend CreateProjectDto to API request format.
 */
export function toApiCreateProject(dto: CreateProjectDto): ApiCreateProjectRequest {
  return {
    name: dto.name,
  };
}

/**
 * Transform frontend UpdateProjectDto to API request format.
 */
export function toApiUpdateProject(dto: UpdateProjectDto): ApiUpdateProjectRequest {
  return {
    name: dto.name,
  };
}

/**
 * Transform frontend CreateTaskListDto to API request format.
 */
export function toApiCreateTaskList(dto: CreateTaskListDto): ApiCreateTaskListRequest {
  return {
    name: dto.name,
    project_id: dto.projectId,
  };
}

/**
 * Transform frontend UpdateTaskListDto to API request format.
 */
export function toApiUpdateTaskList(dto: UpdateTaskListDto): ApiUpdateTaskListRequest {
  const request: ApiUpdateTaskListRequest = {};
  if (dto.name !== undefined) {
    request.name = dto.name;
  }
  if (dto.projectId !== undefined) {
    request.project_id = dto.projectId;
  }
  return request;
}

/**
 * Transform frontend TaskDependency to API dependency format.
 */
export function toApiDependency(dep: TaskDependency): ApiDependency {
  return {
    task_id: dep.taskId,
    task_list_id: dep.taskListId,
  };
}

/**
 * Transform frontend ExitCriterion to API exit criteria format.
 */
export function toApiExitCriteria(criterion: ExitCriterion): ApiExitCriteria {
  return {
    criteria: criterion.criteria,
    status: criterion.status,
    comment: criterion.comment ?? null,
  };
}

/**
 * Transform frontend Note to API note format.
 */
export function toApiNote(note: Note): ApiNote {
  return {
    content: note.content,
    timestamp: note.timestamp,
  };
}

/**
 * Transform frontend ActionPlanItem to API action plan item format.
 */
export function toApiActionPlanItem(item: ActionPlanItem): ApiActionPlanItem {
  return {
    sequence: item.sequence,
    content: item.content,
  };
}

/**
 * Transform frontend CreateTaskDto to API request format.
 */
export function toApiCreateTask(dto: CreateTaskDto): ApiCreateTaskRequest {
  return {
    task_list_id: dto.taskListId,
    title: dto.title,
    description: dto.description ?? '',
    status: dto.status ?? 'NOT_STARTED',
    priority: dto.priority ?? 'MEDIUM',
    dependencies: dto.dependencies?.map(toApiDependency) ?? [],
    exit_criteria: dto.exitCriteria?.map(toApiExitCriteria) ?? [
      { criteria: 'Task completed', status: 'INCOMPLETE' },
    ],
    notes: dto.notes?.map(toApiNote) ?? [],
    research_notes: dto.researchNotes?.map(toApiNote) ?? null,
    action_plan: dto.actionPlan?.map(toApiActionPlanItem) ?? null,
    execution_notes: dto.executionNotes?.map(toApiNote) ?? null,
    tags: dto.tags ?? [],
  };
}

/**
 * Transform frontend UpdateTaskDto to API request format.
 */
export function toApiUpdateTask(dto: UpdateTaskDto): ApiUpdateTaskRequest {
  const request: ApiUpdateTaskRequest = {};
  if (dto.title !== undefined) {
    request.title = dto.title;
  }
  if (dto.description !== undefined) {
    request.description = dto.description;
  }
  if (dto.status !== undefined) {
    request.status = dto.status;
  }
  if (dto.priority !== undefined) {
    request.priority = dto.priority;
  }
  return request;
}

/**
 * Transform frontend SearchQuery to API search request format.
 */
export function toApiSearchRequest(query: SearchQuery): ApiSearchRequest {
  const request: ApiSearchRequest = {};
  if (query.text !== undefined) {
    request.query = query.text;
  }
  if (query.status !== undefined) {
    request.status = query.status;
  }
  if (query.priority !== undefined) {
    request.priority = query.priority;
  }
  if (query.tags !== undefined) {
    request.tags = query.tags;
  }
  if (query.projectId !== undefined) {
    request.project_id = query.projectId;
  }
  if (query.limit !== undefined) {
    request.limit = query.limit;
  }
  if (query.offset !== undefined) {
    request.offset = query.offset;
  }
  if (query.sortBy !== undefined) {
    // Map frontend sortBy to API sort_by
    const sortByMap: Record<string, string> = {
      createdAt: 'created_at',
      updatedAt: 'updated_at',
      priority: 'priority',
      title: 'relevance', // API doesn't support title sort, use relevance
    };
    request.sort_by = sortByMap[query.sortBy] ?? 'relevance';
  }
  return request;
}

// ============================================================================
// Reverse Transformers (Frontend to API format for round-trip testing)
// ============================================================================

/**
 * Transform frontend Project back to API format.
 * Used for round-trip testing.
 */
export function toApiProject(project: Project): ApiProject {
  return {
    id: project.id,
    name: project.name,
    is_default: project.isDefault,
    agent_instructions_template: null, // Frontend doesn't track this
    created_at: project.createdAt,
    updated_at: project.updatedAt,
  };
}

/**
 * Transform frontend TaskList back to API format.
 * Used for round-trip testing.
 */
export function toApiTaskList(taskList: TaskList): ApiTaskList {
  return {
    id: taskList.id,
    name: taskList.name,
    project_id: taskList.projectId,
    agent_instructions_template: null, // Frontend doesn't track this
    created_at: taskList.createdAt,
    updated_at: taskList.updatedAt,
  };
}

/**
 * Transform frontend Task back to API format.
 * Used for round-trip testing.
 */
export function toApiTask(task: Task): ApiTask {
  return {
    id: task.id,
    task_list_id: task.taskListId,
    title: task.title,
    description: task.description ?? '',
    status: task.status,
    priority: task.priority,
    dependencies: task.dependencies.map(toApiDependency),
    exit_criteria: task.exitCriteria.map(toApiExitCriteria),
    notes: task.notes.map(toApiNote),
    research_notes: task.researchNotes.length > 0 ? task.researchNotes.map(toApiNote) : null,
    action_plan: task.actionPlan?.map(toApiActionPlanItem) ?? null,
    execution_notes: task.executionNotes.length > 0 ? task.executionNotes.map(toApiNote) : null,
    agent_instructions_template: null, // Frontend doesn't track this
    tags: task.tags,
    created_at: task.createdAt,
    updated_at: task.updatedAt,
  };
}

/**
 * Transform frontend ProjectStats back to API format.
 * Used for round-trip testing.
 */
export function toApiProjectStats(stats: ProjectStats): ApiProjectStats {
  return {
    task_list_count: stats.taskListCount,
    total_tasks: stats.totalTasks,
    ready_tasks: stats.readyTasks,
    completed_tasks: stats.completedTasks,
    in_progress_tasks: stats.inProgressTasks,
    blocked_tasks: stats.blockedTasks,
  };
}

/**
 * Transform frontend TaskListStats back to API format.
 * Used for round-trip testing.
 */
export function toApiTaskListStats(stats: TaskListStats): ApiTaskListStats {
  return {
    task_count: stats.taskCount,
    ready_tasks: stats.readyTasks,
    completed_tasks: stats.completedTasks,
    in_progress_tasks: stats.inProgressTasks,
    blocked_tasks: stats.blockedTasks,
    completion_percentage: stats.completionPercentage,
  };
}
