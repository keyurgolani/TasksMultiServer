/**
 * Tests for DataServiceContext - React context for dependency injection.
 * 
 * @module context/DataServiceContext.test
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, renderHook } from '@testing-library/react';
import { DataServiceProvider, useDataService } from './DataServiceContext';
import type { IDataService } from '../services/types';

// ============================================================================
// Mock Service
// ============================================================================

/**
 * Create a mock data service for testing.
 */
function createMockService(): IDataService {
  return {
    getProjects: vi.fn().mockResolvedValue([]),
    getProject: vi.fn().mockResolvedValue({ id: '1', name: 'Test' }),
    createProject: vi.fn().mockResolvedValue({ id: '1', name: 'Test' }),
    updateProject: vi.fn().mockResolvedValue({ id: '1', name: 'Updated' }),
    deleteProject: vi.fn().mockResolvedValue(undefined),
    getProjectStats: vi.fn().mockResolvedValue({ taskListCount: 0, totalTasks: 0 }),
    getTaskLists: vi.fn().mockResolvedValue([]),
    getTaskList: vi.fn().mockResolvedValue({ id: '1', name: 'Test List' }),
    createTaskList: vi.fn().mockResolvedValue({ id: '1', name: 'Test List' }),
    updateTaskList: vi.fn().mockResolvedValue({ id: '1', name: 'Updated List' }),
    deleteTaskList: vi.fn().mockResolvedValue(undefined),
    getTaskListStats: vi.fn().mockResolvedValue({ taskCount: 0, completionPercentage: 0 }),
    getTasks: vi.fn().mockResolvedValue([]),
    getTask: vi.fn().mockResolvedValue({ id: '1', title: 'Test Task' }),
    createTask: vi.fn().mockResolvedValue({ id: '1', title: 'Test Task' }),
    updateTask: vi.fn().mockResolvedValue({ id: '1', title: 'Updated Task' }),
    deleteTask: vi.fn().mockResolvedValue(undefined),
    addNote: vi.fn().mockResolvedValue({ id: '1', title: 'Test Task' }),
    addResearchNote: vi.fn().mockResolvedValue({ id: '1', title: 'Test Task' }),
    addExecutionNote: vi.fn().mockResolvedValue({ id: '1', title: 'Test Task' }),
    searchTasks: vi.fn().mockResolvedValue({ items: [], total: 0, count: 0, offset: 0 }),
    getReadyTasks: vi.fn().mockResolvedValue([]),
  };
}

// ============================================================================
// Tests
// ============================================================================

describe('DataServiceContext', () => {
  describe('DataServiceProvider', () => {
    it('should render children', () => {
      render(
        <DataServiceProvider>
          <div data-testid="child">Child Content</div>
        </DataServiceProvider>
      );

      expect(screen.getByTestId('child')).toBeInTheDocument();
      expect(screen.getByText('Child Content')).toBeInTheDocument();
    });

    it('should provide a data service instance', () => {
      const TestComponent = () => {
        const { dataService } = useDataService();
        return <div data-testid="has-service">{dataService ? 'yes' : 'no'}</div>;
      };

      render(
        <DataServiceProvider>
          <TestComponent />
        </DataServiceProvider>
      );

      expect(screen.getByTestId('has-service')).toHaveTextContent('yes');
    });

    it('should use provided service instance', () => {
      const mockService = createMockService();
      
      const TestComponent = () => {
        const { dataService } = useDataService();
        // Call a method to verify it's the mock
        dataService.getProjects();
        return <div data-testid="test">Test</div>;
      };

      render(
        <DataServiceProvider service={mockService}>
          <TestComponent />
        </DataServiceProvider>
      );

      expect(mockService.getProjects).toHaveBeenCalled();
    });

    it('should create service with config when no service provided', () => {
      const TestComponent = () => {
        const { dataService } = useDataService();
        return <div data-testid="has-service">{dataService ? 'yes' : 'no'}</div>;
      };

      render(
        <DataServiceProvider config={{ forceType: 'mock' }}>
          <TestComponent />
        </DataServiceProvider>
      );

      expect(screen.getByTestId('has-service')).toHaveTextContent('yes');
    });
  });

  describe('useDataService', () => {
    it('should throw error when used outside provider', () => {
      // Suppress console.error for this test
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const TestComponent = () => {
        useDataService();
        return <div>Test</div>;
      };

      expect(() => render(<TestComponent />)).toThrow(
        'useDataService must be used within a DataServiceProvider'
      );

      consoleSpy.mockRestore();
    });

    it('should return the same service instance on re-renders', () => {
      const mockService = createMockService();
      const serviceInstances: IDataService[] = [];

      const TestComponent = () => {
        const { dataService } = useDataService();
        serviceInstances.push(dataService);
        return <div data-testid="test">Test</div>;
      };

      const { rerender } = render(
        <DataServiceProvider service={mockService}>
          <TestComponent />
        </DataServiceProvider>
      );

      // Re-render to trigger another call
      rerender(
        <DataServiceProvider service={mockService}>
          <TestComponent />
        </DataServiceProvider>
      );

      expect(serviceInstances).toHaveLength(2);
      expect(serviceInstances[0]).toBe(serviceInstances[1]);
    });
  });

  describe('renderHook usage', () => {
    it('should work with renderHook', () => {
      const mockService = createMockService();

      const { result } = renderHook(() => useDataService(), {
        wrapper: ({ children }) => (
          <DataServiceProvider service={mockService}>
            {children}
          </DataServiceProvider>
        ),
      });

      expect(result.current.dataService).toBe(mockService);
    });
  });
});
