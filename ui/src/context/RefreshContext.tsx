/**
 * RefreshContext - React context for triggering data refreshes across components.
 * 
 * This context provides a mechanism for components to subscribe to refresh events
 * and trigger refreshes when data changes (e.g., after creating a new project).
 * 
 * @module context/RefreshContext
 */

/* eslint-disable react-refresh/only-export-components */
import React, { createContext, useContext, useState, useCallback, useMemo } from 'react';

// ============================================================================
// Context Types
// ============================================================================

/**
 * Refresh keys for different entity types
 */
export type RefreshKey = 'projects' | 'taskLists' | 'tasks' | 'all';

/**
 * Context value type containing refresh state and trigger function.
 */
interface RefreshContextValue {
  /** Counter that increments on each refresh trigger - components can use this as a dependency */
  refreshCounter: Record<RefreshKey, number>;
  /** Trigger a refresh for a specific entity type or all */
  triggerRefresh: (key: RefreshKey) => void;
}

/**
 * Props for the RefreshProvider component.
 */
export interface RefreshProviderProps {
  /** Child components that will have access to the refresh context */
  children: React.ReactNode;
}

// ============================================================================
// Context Creation
// ============================================================================

/**
 * React context for refresh triggers.
 * Initialized as undefined to detect usage outside of provider.
 */
const RefreshContext = createContext<RefreshContextValue | undefined>(undefined);

// Set display name for React DevTools
RefreshContext.displayName = 'RefreshContext';

// ============================================================================
// Provider Component
// ============================================================================

/**
 * RefreshProvider - Provides refresh trigger mechanism to the component tree.
 * 
 * Components can subscribe to refresh events by using the refreshCounter value
 * as a dependency in their useEffect hooks.
 * 
 * @example
 * ```tsx
 * // In a component that needs to refresh on project changes
 * function ProjectList() {
 *   const { refreshCounter } = useRefresh();
 *   const [projects, setProjects] = useState([]);
 * 
 *   useEffect(() => {
 *     loadProjects().then(setProjects);
 *   }, [refreshCounter.projects]); // Re-runs when projects refresh is triggered
 * 
 *   return <ul>{projects.map(p => <li key={p.id}>{p.name}</li>)}</ul>;
 * }
 * 
 * // In a component that creates a project
 * function CreateProjectButton() {
 *   const { triggerRefresh } = useRefresh();
 * 
 *   const handleCreate = async () => {
 *     await createProject({ name: 'New Project' });
 *     triggerRefresh('projects'); // Triggers refresh in ProjectList
 *   };
 * 
 *   return <button onClick={handleCreate}>Create</button>;
 * }
 * ```
 */
export const RefreshProvider: React.FC<RefreshProviderProps> = ({ children }) => {
  const [refreshCounter, setRefreshCounter] = useState<Record<RefreshKey, number>>({
    projects: 0,
    taskLists: 0,
    tasks: 0,
    all: 0,
  });

  const triggerRefresh = useCallback((key: RefreshKey) => {
    setRefreshCounter((prev) => {
      if (key === 'all') {
        return {
          projects: prev.projects + 1,
          taskLists: prev.taskLists + 1,
          tasks: prev.tasks + 1,
          all: prev.all + 1,
        };
      }
      return {
        ...prev,
        [key]: prev[key] + 1,
      };
    });
  }, []);

  // Memoize the context value to prevent unnecessary re-renders
  const contextValue = useMemo<RefreshContextValue>(
    () => ({ refreshCounter, triggerRefresh }),
    [refreshCounter, triggerRefresh]
  );

  return (
    <RefreshContext.Provider value={contextValue}>
      {children}
    </RefreshContext.Provider>
  );
};

// ============================================================================
// Hook
// ============================================================================

/**
 * useRefresh - Hook to access the refresh context.
 * 
 * This hook provides access to the refresh counter and trigger function
 * for coordinating data refreshes across components.
 * 
 * @returns The refresh context value
 * @throws Error if used outside of RefreshProvider
 */
export function useRefresh(): RefreshContextValue {
  const context = useContext(RefreshContext);
  
  if (context === undefined) {
    throw new Error(
      'useRefresh must be used within a RefreshProvider. ' +
      'Wrap your component tree with <RefreshProvider> to fix this error.'
    );
  }
  
  return context;
}

// ============================================================================
// Utility Exports
// ============================================================================

/**
 * Export the raw context for advanced use cases.
 * Prefer using the useRefresh hook when possible.
 */
export { RefreshContext };
