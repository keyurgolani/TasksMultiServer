/**
 * API service module - exports API types, transformers, and ApiDataService.
 * 
 * @module services/api
 */

// Export ApiDataService
export { ApiDataService } from './ApiDataService';

// Export API types
export type {
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
  ApiNoteRequest,
  ApiSearchRequest,
  ApiPaginatedResponse,
} from './types';

// Export transformers
export {
  // API to Frontend transformers
  transformProject,
  transformTaskList,
  transformTask,
  transformDependency,
  transformExitCriteria,
  transformNote,
  transformActionPlanItem,
  transformProjectStats,
  transformTaskListStats,
  // Frontend to API transformers
  toApiCreateProject,
  toApiUpdateProject,
  toApiCreateTaskList,
  toApiUpdateTaskList,
  toApiCreateTask,
  toApiUpdateTask,
  toApiDependency,
  toApiExitCriteria,
  toApiNote,
  toApiActionPlanItem,
  toApiSearchRequest,
  // Reverse transformers for round-trip testing
  toApiProject,
  toApiTaskList,
  toApiTask,
  toApiProjectStats,
  toApiTaskListStats,
} from './transformers';
