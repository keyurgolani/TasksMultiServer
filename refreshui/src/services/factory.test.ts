/**
 * Tests for the service factory module.
 * 
 * @module services/factory.test
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
  createDataService,
  getDataService,
  resetDataService,
  getServiceType,
  isMockDataEnabled,
  getConfiguredApiBaseUrl,
} from './factory';
import { LocalStorageService } from './mock';

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

    it('should fall back to mock service when API is selected but not implemented', () => {
      vi.stubEnv('VITE_USE_MOCK_DATA', 'false');
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      
      const service = createDataService();
      
      // Should still return a working service (LocalStorageService as fallback)
      expect(service).toBeInstanceOf(LocalStorageService);
      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('API service not yet implemented')
      );
      
      consoleSpy.mockRestore();
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
});
