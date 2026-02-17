/**
 * Tests for the service factory module.
 * 
 * @module services/factory.test
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fc from 'fast-check';
import {
  createDataService,
  getDataService,
  resetDataService,
  getServiceType,
  isMockDataEnabled,
  getConfiguredApiBaseUrl,
} from './factory';
import { LocalStorageService } from './mock';
import { ApiDataService } from './api';

describe('Service Factory', () => {
  beforeEach(() => {
    // Reset singleton before each test
    resetDataService();
    // Clear localStorage
    localStorage.clear();
  });

  afterEach(() => {
    // Clean up
    resetDataService();
    vi.unstubAllEnvs();
  });

  describe('getServiceType', () => {
    it('should return "mock" when VITE_USE_MOCK_DATA is not set', () => {
      vi.stubEnv('VITE_USE_MOCK_DATA', '');
      expect(getServiceType()).toBe('mock');
    });

    it('should return "mock" when VITE_USE_MOCK_DATA is "true"', () => {
      vi.stubEnv('VITE_USE_MOCK_DATA', 'true');
      expect(getServiceType()).toBe('mock');
    });

    it('should return "api" when VITE_USE_MOCK_DATA is "false"', () => {
      vi.stubEnv('VITE_USE_MOCK_DATA', 'false');
      expect(getServiceType()).toBe('api');
    });
  });

  describe('isMockDataEnabled', () => {
    it('should return true when VITE_USE_MOCK_DATA is not set', () => {
      vi.stubEnv('VITE_USE_MOCK_DATA', '');
      expect(isMockDataEnabled()).toBe(true);
    });

    it('should return true when VITE_USE_MOCK_DATA is "true"', () => {
      vi.stubEnv('VITE_USE_MOCK_DATA', 'true');
      expect(isMockDataEnabled()).toBe(true);
    });

    it('should return false when VITE_USE_MOCK_DATA is "false"', () => {
      vi.stubEnv('VITE_USE_MOCK_DATA', 'false');
      expect(isMockDataEnabled()).toBe(false);
    });
  });

  describe('getConfiguredApiBaseUrl', () => {
    it('should return default URL when VITE_API_BASE_URL is not set', () => {
      vi.stubEnv('VITE_API_BASE_URL', '');
      expect(getConfiguredApiBaseUrl()).toBe('http://localhost:8000');
    });

    it('should return configured URL when VITE_API_BASE_URL is set', () => {
      vi.stubEnv('VITE_API_BASE_URL', 'https://api.example.com');
      expect(getConfiguredApiBaseUrl()).toBe('https://api.example.com');
    });
  });

  describe('createDataService', () => {
    it('should create a LocalStorageService when mock is enabled', () => {
      vi.stubEnv('VITE_USE_MOCK_DATA', 'true');
      const service = createDataService();
      expect(service).toBeInstanceOf(LocalStorageService);
    });

    it('should create a service with forceType override', () => {
      vi.stubEnv('VITE_USE_MOCK_DATA', 'false');
      const service = createDataService({ forceType: 'mock' });
      expect(service).toBeInstanceOf(LocalStorageService);
    });

    it('should create a service with custom mock config', () => {
      const service = createDataService({
        forceType: 'mock',
        mockConfig: {
          mockDelayRange: { min: 10, max: 20 },
          storageKeyPrefix: 'test_',
        },
      });
      expect(service).toBeInstanceOf(LocalStorageService);
      // Verify the config was applied
      const delayRange = (service as LocalStorageService).getDelayRange();
      expect(delayRange.min).toBe(10);
      expect(delayRange.max).toBe(20);
    });

    it('should create an ApiDataService when API is selected', () => {
      vi.stubEnv('VITE_USE_MOCK_DATA', 'false');
      
      const service = createDataService();
      
      expect(service).toBeInstanceOf(ApiDataService);
    });

    it('should create ApiDataService with custom base URL', () => {
      vi.stubEnv('VITE_USE_MOCK_DATA', 'false');
      
      const service = createDataService({
        forceType: 'api',
        apiConfig: { apiBaseUrl: 'https://api.example.com' },
      });
      
      expect(service).toBeInstanceOf(ApiDataService);
      expect((service as ApiDataService).getBaseUrl()).toBe('https://api.example.com');
    });

    it('should use VITE_API_BASE_URL when creating ApiDataService', () => {
      vi.stubEnv('VITE_USE_MOCK_DATA', 'false');
      vi.stubEnv('VITE_API_BASE_URL', 'https://custom-api.example.com');
      
      const service = createDataService();
      
      expect(service).toBeInstanceOf(ApiDataService);
      expect((service as ApiDataService).getBaseUrl()).toBe('https://custom-api.example.com');
    });
  });

  describe('getDataService (singleton)', () => {
    it('should return the same instance on multiple calls', () => {
      const service1 = getDataService();
      const service2 = getDataService();
      expect(service1).toBe(service2);
    });

    it('should create a new instance after reset', () => {
      const service1 = getDataService();
      resetDataService();
      const service2 = getDataService();
      expect(service1).not.toBe(service2);
    });

    it('should use config only on first call', () => {
      const service1 = getDataService({
        forceType: 'mock',
        mockConfig: { mockDelayRange: { min: 50, max: 100 } },
      });
      
      // Second call with different config should return same instance
      const service2 = getDataService({
        forceType: 'mock',
        mockConfig: { mockDelayRange: { min: 200, max: 300 } },
      });
      
      expect(service1).toBe(service2);
      // Verify original config was used
      const delayRange = (service1 as LocalStorageService).getDelayRange();
      expect(delayRange.min).toBe(50);
      expect(delayRange.max).toBe(100);
    });
  });

  describe('resetDataService', () => {
    it('should clear the singleton instance', () => {
      const service1 = getDataService();
      resetDataService();
      const service2 = getDataService();
      expect(service1).not.toBe(service2);
    });
  });

  describe('Service functionality', () => {
    it('should return a fully functional IDataService', async () => {
      const service = createDataService({ forceType: 'mock' });
      
      // Test that the service implements IDataService correctly
      const projects = await service.getProjects();
      expect(Array.isArray(projects)).toBe(true);
      expect(projects.length).toBeGreaterThan(0);
      
      // Test creating a project
      const newProject = await service.createProject({
        name: 'Test Project',
        description: 'A test project',
      });
      expect(newProject.id).toBeDefined();
      expect(newProject.name).toBe('Test Project');
    });
  });

  /**
   * **Feature: refreshui-api-integration, Property 6: Service Factory Type Selection**
   * **Validates: Requirements 10.1, 10.2**
   * 
   * For any environment configuration, the service factory SHALL return:
   * - ApiDataService when VITE_USE_MOCK_DATA is "false"
   * - LocalStorageService when VITE_USE_MOCK_DATA is "true" or undefined
   */
  describe('Property: Service Factory Type Selection', () => {
    /**
     * Property: For any forceType='mock' configuration, the factory returns LocalStorageService
     */
    it('should always return LocalStorageService when forceType is mock', () => {
      fc.assert(
        fc.property(
          // Generate random API base URLs
          fc.option(fc.webUrl(), { nil: undefined }),
          (apiBaseUrl) => {
            resetDataService();
            
            const service = createDataService({
              forceType: 'mock',
              apiConfig: apiBaseUrl ? { apiBaseUrl } : undefined,
            });
            
            expect(service).toBeInstanceOf(LocalStorageService);
          }
        ),
        { numRuns: 100 }
      );
    });

    /**
     * Property: For any forceType='api' configuration, the factory returns ApiDataService
     */
    it('should always return ApiDataService when forceType is api', () => {
      fc.assert(
        fc.property(
          // Generate random API base URLs
          fc.option(fc.webUrl(), { nil: undefined }),
          (apiBaseUrl) => {
            resetDataService();
            
            const service = createDataService({
              forceType: 'api',
              apiConfig: apiBaseUrl ? { apiBaseUrl } : undefined,
            });
            
            expect(service).toBeInstanceOf(ApiDataService);
          }
        ),
        { numRuns: 100 }
      );
    });

    /**
     * Property: ApiDataService should use the provided base URL
     */
    it('should configure ApiDataService with provided base URL', () => {
      fc.assert(
        fc.property(
          fc.webUrl(),
          (apiBaseUrl) => {
            resetDataService();
            
            const service = createDataService({
              forceType: 'api',
              apiConfig: { apiBaseUrl },
            });
            
            expect(service).toBeInstanceOf(ApiDataService);
            expect((service as ApiDataService).getBaseUrl()).toBe(apiBaseUrl);
          }
        ),
        { numRuns: 100 }
      );
    });

    /**
     * Property: Service type selection is deterministic based on forceType
     */
    it('should be deterministic - same config always produces same service type', () => {
      fc.assert(
        fc.property(
          fc.constantFrom('mock', 'api') as fc.Arbitrary<'mock' | 'api'>,
          fc.option(fc.webUrl(), { nil: undefined }),
          (forceType, apiBaseUrl) => {
            resetDataService();
            const service1 = createDataService({
              forceType,
              apiConfig: apiBaseUrl ? { apiBaseUrl } : undefined,
            });
            
            resetDataService();
            const service2 = createDataService({
              forceType,
              apiConfig: apiBaseUrl ? { apiBaseUrl } : undefined,
            });
            
            // Both should be the same type
            if (forceType === 'mock') {
              expect(service1).toBeInstanceOf(LocalStorageService);
              expect(service2).toBeInstanceOf(LocalStorageService);
            } else {
              expect(service1).toBeInstanceOf(ApiDataService);
              expect(service2).toBeInstanceOf(ApiDataService);
            }
          }
        ),
        { numRuns: 100 }
      );
    });
  });
});
