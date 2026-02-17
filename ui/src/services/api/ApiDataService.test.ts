/**
 * Property-based tests for ApiDataService error handling.
 * Tests error code mapping consistency between HTTP status codes and ServiceErrorCode.
 * 
 * **Feature: refreshui-api-integration, Property 5: Error Code Mapping Consistency**
 * **Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5**
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import fc from 'fast-check';

import { ApiDataService } from './ApiDataService';
import { ServiceError } from '../types';

// ============================================================================
// Test Setup
// ============================================================================

// Mock fetch globally
const mockFetch = vi.fn();

beforeEach(() => {
  vi.stubGlobal('fetch', mockFetch);
  mockFetch.mockReset();
});

afterEach(() => {
  vi.unstubAllGlobals();
  mockFetch.mockReset();
});

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Create a mock Response object with the given status and body.
 */
function createMockResponse(status: number, body: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body),
    headers: new Headers(),
    redirected: false,
    statusText: '',
    type: 'basic',
    url: '',
    clone: () => createMockResponse(status, body),
    body: null,
    bodyUsed: false,
    arrayBuffer: () => Promise.resolve(new ArrayBuffer(0)),
    blob: () => Promise.resolve(new Blob()),
    formData: () => Promise.resolve(new FormData()),
    text: () => Promise.resolve(JSON.stringify(body)),
  } as Response;
}


// ============================================================================
// Property Tests
// ============================================================================

describe('ApiDataService Error Handling', () => {
  /**
   * **Feature: refreshui-api-integration, Property 5: Error Code Mapping Consistency**
   * **Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5**
   * 
   * For any HTTP error response from the REST API, the ApiDataService SHALL throw
   * a ServiceError with the appropriate error code based on HTTP status.
   */
  describe('Error Code Mapping', () => {
    it('should map 404 status to NOT_FOUND error code', async () => {
      /**
       * **Feature: refreshui-api-integration, Property 5: Error Code Mapping Consistency**
       * **Validates: Requirements 12.1**
       */
      await fc.assert(
        fc.asyncProperty(
          fc.string({ minLength: 1, maxLength: 100 }),
          async (errorMessage) => {
            mockFetch.mockReset();
            const service = new ApiDataService({ apiBaseUrl: 'http://test-api' });
            
            mockFetch.mockResolvedValue(
              createMockResponse(404, {
                error: { message: errorMessage, code: 'NOT_FOUND' },
              })
            );

            try {
              await service.getProject('non-existent-id');
              expect.fail('Should have thrown ServiceError');
            } catch (error) {
              expect(error).toBeInstanceOf(ServiceError);
              const serviceError = error as ServiceError;
              expect(serviceError.code).toBe('NOT_FOUND');
              expect(serviceError.message).toBe(errorMessage);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should map 400 status to VALIDATION_ERROR error code', async () => {
      /**
       * **Feature: refreshui-api-integration, Property 5: Error Code Mapping Consistency**
       * **Validates: Requirements 12.2**
       */
      await fc.assert(
        fc.asyncProperty(
          fc.string({ minLength: 1, maxLength: 100 }),
          async (errorMessage) => {
            mockFetch.mockReset();
            const service = new ApiDataService({ apiBaseUrl: 'http://test-api' });
            
            mockFetch.mockResolvedValue(
              createMockResponse(400, {
                error: { message: errorMessage, code: 'VALIDATION_ERROR' },
              })
            );

            try {
              await service.createProject({ name: '' });
              expect.fail('Should have thrown ServiceError');
            } catch (error) {
              expect(error).toBeInstanceOf(ServiceError);
              const serviceError = error as ServiceError;
              expect(serviceError.code).toBe('VALIDATION_ERROR');
              expect(serviceError.message).toBe(errorMessage);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should map 409 status to VALIDATION_ERROR error code', async () => {
      /**
       * **Feature: refreshui-api-integration, Property 5: Error Code Mapping Consistency**
       * **Validates: Requirements 12.3**
       */
      await fc.assert(
        fc.asyncProperty(
          fc.string({ minLength: 1, maxLength: 100 }),
          async (errorMessage) => {
            mockFetch.mockReset();
            const service = new ApiDataService({ apiBaseUrl: 'http://test-api' });
            
            mockFetch.mockResolvedValue(
              createMockResponse(409, {
                error: { message: errorMessage, code: 'CONFLICT' },
              })
            );

            try {
              await service.createProject({ name: 'duplicate' });
              expect.fail('Should have thrown ServiceError');
            } catch (error) {
              expect(error).toBeInstanceOf(ServiceError);
              const serviceError = error as ServiceError;
              expect(serviceError.code).toBe('VALIDATION_ERROR');
              expect(serviceError.message).toBe(errorMessage);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should map 500 status to STORAGE_ERROR error code', async () => {
      /**
       * **Feature: refreshui-api-integration, Property 5: Error Code Mapping Consistency**
       * **Validates: Requirements 12.4**
       */
      await fc.assert(
        fc.asyncProperty(
          fc.string({ minLength: 1, maxLength: 100 }),
          async (errorMessage) => {
            mockFetch.mockReset();
            const service = new ApiDataService({ apiBaseUrl: 'http://test-api' });
            
            mockFetch.mockResolvedValue(
              createMockResponse(500, {
                error: { message: errorMessage, code: 'INTERNAL_ERROR' },
              })
            );

            try {
              await service.getProjects();
              expect.fail('Should have thrown ServiceError');
            } catch (error) {
              expect(error).toBeInstanceOf(ServiceError);
              const serviceError = error as ServiceError;
              expect(serviceError.code).toBe('STORAGE_ERROR');
              expect(serviceError.message).toBe(errorMessage);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should throw NETWORK_ERROR when fetch fails', async () => {
      /**
       * **Feature: refreshui-api-integration, Property 5: Error Code Mapping Consistency**
       * **Validates: Requirements 12.5**
       */
      await fc.assert(
        fc.asyncProperty(
          fc.string({ minLength: 1, maxLength: 100 }),
          async (networkErrorMessage) => {
            mockFetch.mockReset();
            const service = new ApiDataService({ apiBaseUrl: 'http://test-api' });
            
            mockFetch.mockRejectedValue(new Error(networkErrorMessage));

            try {
              await service.getProjects();
              expect.fail('Should have thrown ServiceError');
            } catch (error) {
              expect(error).toBeInstanceOf(ServiceError);
              const serviceError = error as ServiceError;
              expect(serviceError.code).toBe('NETWORK_ERROR');
              expect(serviceError.message).toBe('Network error: Unable to connect to the server');
            }
          }
        ),
        { numRuns: 100 }
      );
    });


    it('should map any other 4xx/5xx status to STORAGE_ERROR', async () => {
      /**
       * **Feature: refreshui-api-integration, Property 5: Error Code Mapping Consistency**
       * **Validates: Requirements 12.4**
       */
      const otherErrorCodes = [401, 403, 405, 408, 422, 429, 501, 502, 503, 504];
      
      await fc.assert(
        fc.asyncProperty(
          fc.constantFrom(...otherErrorCodes),
          fc.string({ minLength: 1, maxLength: 100 }),
          async (statusCode, errorMessage) => {
            mockFetch.mockReset();
            const service = new ApiDataService({ apiBaseUrl: 'http://test-api' });
            
            mockFetch.mockResolvedValue(
              createMockResponse(statusCode, {
                error: { message: errorMessage },
              })
            );

            try {
              await service.getProjects();
              expect.fail('Should have thrown ServiceError');
            } catch (error) {
              expect(error).toBeInstanceOf(ServiceError);
              const serviceError = error as ServiceError;
              expect(serviceError.code).toBe('STORAGE_ERROR');
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should handle missing error message in response', async () => {
      const statusCodes = [400, 404, 409, 500];
      
      for (const statusCode of statusCodes) {
        mockFetch.mockReset();
        const service = new ApiDataService({ apiBaseUrl: 'http://test-api' });
        
        mockFetch.mockResolvedValue(createMockResponse(statusCode, {}));

        try {
          await service.getProjects();
          expect.fail('Should have thrown ServiceError');
        } catch (error) {
          expect(error).toBeInstanceOf(ServiceError);
          const serviceError = error as ServiceError;
          expect(serviceError.message).toBe(`HTTP ${statusCode}`);
        }
      }
    });

    it('should handle malformed JSON in error response', async () => {
      mockFetch.mockReset();
      const service = new ApiDataService({ apiBaseUrl: 'http://test-api' });
      
      const badResponse = {
        ok: false,
        status: 500,
        json: () => Promise.reject(new Error('Invalid JSON')),
        headers: new Headers(),
        redirected: false,
        statusText: '',
        type: 'basic',
        url: '',
        clone: function() { return this; },
        body: null,
        bodyUsed: false,
        arrayBuffer: () => Promise.resolve(new ArrayBuffer(0)),
        blob: () => Promise.resolve(new Blob()),
        formData: () => Promise.resolve(new FormData()),
        text: () => Promise.resolve('not json'),
      } as Response;
      
      mockFetch.mockResolvedValue(badResponse);

      try {
        await service.getProjects();
        expect.fail('Should have thrown ServiceError');
      } catch (error) {
        expect(error).toBeInstanceOf(ServiceError);
        const serviceError = error as ServiceError;
        expect(serviceError.code).toBe('STORAGE_ERROR');
        expect(serviceError.message).toBe('HTTP 500');
      }
    });
  });

  describe('Constructor Configuration', () => {
    it('should use default base URL when not configured', () => {
      const service = new ApiDataService();
      expect(service.getBaseUrl()).toBe('http://localhost:8000');
    });

    it('should use configured base URL', () => {
      fc.assert(
        fc.property(
          fc.webUrl(),
          (url) => {
            const service = new ApiDataService({ apiBaseUrl: url });
            expect(service.getBaseUrl()).toBe(url);
          }
        ),
        { numRuns: 100 }
      );
    });
  });
});
