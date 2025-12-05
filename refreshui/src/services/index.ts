/**
 * Services module - exports all service types and implementations.
 * 
 * @module services
 */

// Export all service types
export type {
  // DTOs
  CreateProjectDto,
  UpdateProjectDto,
  CreateTaskListDto,
  UpdateTaskListDto,
  CreateTaskDto,
  UpdateTaskDto,
  AddNoteDto,
  // Search types
  SearchQuery,
  PaginatedResponse,
  // Statistics types
  ProjectStats,
  TaskListStats,
  // Service interface
  IDataService,
  // Error types
  ServiceErrorCode,
  // Configuration
  DataServiceConfig,
} from './types';

// Export ServiceError class
export { ServiceError } from './types';

// Export mock data generator and LocalStorageService
export { MockDataGenerator, generateMockData, LocalStorageService } from './mock';
export type { MockData } from './mock';

// Export service factory
export {
  createDataService,
  getDataService,
  resetDataService,
  getServiceType,
  isMockDataEnabled,
  getConfiguredApiBaseUrl,
} from './factory';
export type { ServiceType, ServiceFactoryConfig } from './factory';
