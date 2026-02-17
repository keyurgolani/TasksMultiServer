/**
 * Service Factory - Creates data service instances based on environment configuration.
 * 
 * The factory reads the VITE_USE_MOCK_DATA environment variable to determine
 * which service implementation to use:
 * - "true" or undefined: Use MockDataService (LocalStorageService)
 * - "false": Use ApiDataService (REST API)
 * 
 * @module services/factory
 */

import type { IDataService, DataServiceConfig } from './types';
import { LocalStorageService } from './mock';
import { ApiDataService } from './api';

// ============================================================================
// Environment Configuration
// ============================================================================

/**
 * Check if mock data should be used based on environment configuration.
 * Defaults to true if VITE_USE_MOCK_DATA is not set.
 */
function shouldUseMockData(): boolean {
  const envValue = import.meta.env.VITE_USE_MOCK_DATA;
  
  // If not set, default to mock data
  if (envValue === undefined || envValue === null || envValue === '') {
    return true;
  }
  
  // Parse string value
  return envValue === 'true' || envValue === true;
}

/**
 * Get the API base URL from environment configuration.
 */
function getApiBaseUrl(): string {
  return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
}

// ============================================================================
// Service Type
// ============================================================================

/**
 * Available service types.
 */
export type ServiceType = 'mock' | 'api';

/**
 * Get the current service type based on environment configuration.
 */
export function getServiceType(): ServiceType {
  return shouldUseMockData() ? 'mock' : 'api';
}

// ============================================================================
// Service Factory
// ============================================================================

/** Singleton instance of the data service */
let serviceInstance: IDataService | null = null;

/**
 * Factory configuration options.
 */
export interface ServiceFactoryConfig {
  /** Force a specific service type (overrides environment) */
  forceType?: ServiceType;
  /** Configuration for the mock service */
  mockConfig?: DataServiceConfig;
  /** Configuration for the API service */
  apiConfig?: DataServiceConfig;
}

/**
 * Create a data service instance based on environment configuration.
 * 
 * This factory function determines which service implementation to use
 * based on the VITE_USE_MOCK_DATA environment variable.
 * 
 * @param config - Optional configuration to override defaults
 * @returns An IDataService implementation
 * 
 * @example
 * ```typescript
 * // Use environment-based selection
 * const service = createDataService();
 * 
 * // Force mock service
 * const mockService = createDataService({ forceType: 'mock' });
 * 
 * // Force API service with custom base URL
 * const apiService = createDataService({ 
 *   forceType: 'api',
 *   apiConfig: { apiBaseUrl: 'https://api.example.com' }
 * });
 * ```
 */
export function createDataService(config?: ServiceFactoryConfig): IDataService {
  const serviceType = config?.forceType ?? getServiceType();
  
  if (serviceType === 'mock') {
    return new LocalStorageService(config?.mockConfig);
  }
  
  // Create ApiDataService with configured base URL
  const apiBaseUrl = config?.apiConfig?.apiBaseUrl ?? getApiBaseUrl();
  return new ApiDataService({ apiBaseUrl });
}

/**
 * Get the singleton data service instance.
 * 
 * This function returns a cached instance of the data service,
 * creating it on first call. Use this for application-wide service access.
 * 
 * @param config - Optional configuration (only used on first call)
 * @returns The singleton IDataService instance
 * 
 * @example
 * ```typescript
 * // Get the singleton service
 * const service = getDataService();
 * 
 * // Use the service
 * const projects = await service.getProjects();
 * ```
 */
export function getDataService(config?: ServiceFactoryConfig): IDataService {
  if (!serviceInstance) {
    serviceInstance = createDataService(config);
  }
  return serviceInstance;
}

/**
 * Reset the singleton service instance.
 * 
 * This is primarily useful for testing to ensure a fresh service instance.
 * In production, this should rarely be needed.
 */
export function resetDataService(): void {
  serviceInstance = null;
}

/**
 * Check if the current environment is configured to use mock data.
 * 
 * @returns true if mock data is being used, false if API is being used
 */
export function isMockDataEnabled(): boolean {
  return shouldUseMockData();
}

/**
 * Get the current API base URL configuration.
 * 
 * @returns The configured API base URL
 */
export function getConfiguredApiBaseUrl(): string {
  return getApiBaseUrl();
}
