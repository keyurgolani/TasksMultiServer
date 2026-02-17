/**
 * API response types matching the REST API snake_case format.
 * These types represent the raw JSON responses from the backend API.
 * 
 * @module services/api/types
 */

// ============================================================================
// API Response Types (snake_case format from REST API)
// ============================================================================

/**
 * API response for a project.
 * Matches the ProjectResponse model from the REST API.
 */
export interface ApiProject {
  id: string;
  name: string;
  is_default: boolean;
  agent_instructions_template: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * API response for a task list.
 * Matches the TaskListResponse model from the REST API.
 */
export interface ApiTaskList {
  id: string;
  name: string;
  project_id: string;
  agent_instructions_template: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * API model for a task dependency.
 * Matches the DependencyModel from the REST API.
 */
export interface ApiDependency {
  task_id: string;
  task_list_id: string;
}

/**
 * API model for an exit criterion.
 * Matches the ExitCriteriaModel from the REST API.
 */
export interface ApiExitCriteria {
  criteria: string;
  status: string;
  comment?: string | null;
}

/**
 * API model for a note.
 * Matches the NoteModel from the REST API.
 */
export interface ApiNote {
  content: string;
  timestamp: string | null;
}

/**
 * API model for an action plan item.
 * Matches the ActionPlanItemModel from the REST API.
 */
export interface ApiActionPlanItem {
  sequence: number;
  content: string;
}

/**
 * API response for a task.
 * Matches the TaskResponse model from the REST API.
 */
export interface ApiTask {
  id: string;
  task_list_id: string;
  title: string;
  description: string;
  status: string;
  priority: string;
  dependencies: ApiDependency[];
  exit_criteria: ApiExitCriteria[];
  notes: ApiNote[];
  research_notes: ApiNote[] | null;
  action_plan: ApiActionPlanItem[] | null;
  execution_notes: ApiNote[] | null;
  agent_instructions_template: string | null;
  tags: string[];
  created_at: string;
  updated_at: string;
}

/**
 * API response for project statistics.
 * Matches the response from GET /projects/{id}/stats.
 */
export interface ApiProjectStats {
  task_list_count: number;
  total_tasks: number;
  ready_tasks: number;
  completed_tasks: number;
  in_progress_tasks: number;
  blocked_tasks: number;
}

/**
 * API response for task list statistics.
 * Matches the response from GET /task-lists/{id}/stats.
 */
export interface ApiTaskListStats {
  task_count: number;
  ready_tasks: number;
  completed_tasks: number;
  in_progress_tasks: number;
  blocked_tasks: number;
  completion_percentage: number;
}

// ============================================================================
// API Request Types (snake_case format for REST API)
// ============================================================================

/**
 * API request for creating a project.
 * Matches the ProjectCreateRequest model from the REST API.
 */
export interface ApiCreateProjectRequest {
  name: string;
  agent_instructions_template?: string | null;
}

/**
 * API request for updating a project.
 * Matches the ProjectUpdateRequest model from the REST API.
 */
export interface ApiUpdateProjectRequest {
  name?: string;
  agent_instructions_template?: string | null;
}

/**
 * API request for creating a task list.
 * Matches the TaskListCreateRequest model from the REST API.
 */
export interface ApiCreateTaskListRequest {
  name: string;
  project_id: string;
  agent_instructions_template?: string | null;
}

/**
 * API request for updating a task list.
 * Matches the TaskListUpdateRequest model from the REST API.
 */
export interface ApiUpdateTaskListRequest {
  name?: string;
  agent_instructions_template?: string | null;
  project_id?: string;
}

/**
 * API request for creating a task.
 * Matches the TaskCreateRequest model from the REST API.
 */
export interface ApiCreateTaskRequest {
  task_list_id: string;
  title: string;
  description: string;
  status: string;
  priority: string;
  dependencies?: ApiDependency[];
  exit_criteria: ApiExitCriteria[];
  notes?: ApiNote[];
  research_notes?: ApiNote[] | null;
  action_plan?: ApiActionPlanItem[] | null;
  execution_notes?: ApiNote[] | null;
  agent_instructions_template?: string | null;
  tags?: string[];
}

/**
 * API request for updating a task.
 * Matches the TaskUpdateRequest model from the REST API.
 */
export interface ApiUpdateTaskRequest {
  title?: string;
  description?: string;
  status?: string;
  priority?: string;
  agent_instructions_template?: string | null;
}

/**
 * API request for adding a note.
 * Matches the NoteRequest model from the REST API.
 */
export interface ApiNoteRequest {
  content: string;
}

/**
 * API request for searching tasks.
 * Matches the SearchCriteriaRequest model from the REST API.
 */
export interface ApiSearchRequest {
  query?: string;
  status?: string[];
  priority?: string[];
  tags?: string[];
  project_id?: string;
  limit?: number;
  offset?: number;
  sort_by?: string;
}

/**
 * API response for paginated search results.
 */
export interface ApiPaginatedResponse<T> {
  items: T[];
  total: number;
  count: number;
  offset: number;
}
