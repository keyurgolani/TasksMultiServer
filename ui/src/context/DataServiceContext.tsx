/**
 * DataServiceContext - React context for dependency injection of data services.
 * 
 * This context provides the IDataService instance to all components in the tree,
 * enabling easy switching between mock and API implementations without changing
 * component code.
 * 
 * @module context/DataServiceContext
 */

/* eslint-disable react-refresh/only-export-components */
import React, { createContext, useContext, useMemo } from 'react';
import type { IDataService } from '../services/types';
import { createDataService, type ServiceFactoryConfig } from '../services/factory';

// ============================================================================
// Context Types
// ============================================================================

/**
 * Context value type containing the data service instance.
 */
interface DataServiceContextValue {
  /** The data service instance for performing CRUD operations */
  dataService: IDataService;
}

/**
 * Props for the DataServiceProvider component.
 */
export interface DataServiceProviderProps {
  /** Child components that will have access to the data service */
  children: React.ReactNode;
  /** Optional pre-configured service instance (useful for testing) */
  service?: IDataService;
  /** Optional factory configuration (used when service is not provided) */
  config?: ServiceFactoryConfig;
}

// ============================================================================
// Context Creation
// ============================================================================

/**
 * React context for the data service.
 * Initialized as undefined to detect usage outside of provider.
 */
const DataServiceContext = createContext<DataServiceContextValue | undefined>(undefined);

// Set display name for React DevTools
DataServiceContext.displayName = 'DataServiceContext';

// ============================================================================
// Provider Component
// ============================================================================

/**
 * DataServiceProvider - Provides data service instance to the component tree.
 * 
 * This provider can be configured in two ways:
 * 1. Pass a pre-configured service instance via the `service` prop (useful for testing)
 * 2. Let the provider create a service using the factory with optional config
 * 
 * @example
 * ```tsx
 * // Basic usage - uses environment-based service selection
 * <DataServiceProvider>
 *   <App />
 * </DataServiceProvider>
 * 
 * // With custom configuration
 * <DataServiceProvider config={{ forceType: 'mock' }}>
 *   <App />
 * </DataServiceProvider>
 * 
 * // With pre-configured service (for testing)
 * <DataServiceProvider service={mockService}>
 *   <App />
 * </DataServiceProvider>
 * ```
 */
export const DataServiceProvider: React.FC<DataServiceProviderProps> = ({
  children,
  service,
  config,
}) => {
  // Create or use the provided service instance
  // useMemo ensures we don't recreate the service on every render
  const dataService = useMemo(() => {
    if (service) {
      return service;
    }
    return createDataService(config);
  }, [service, config]);

  // Memoize the context value to prevent unnecessary re-renders
  const contextValue = useMemo<DataServiceContextValue>(
    () => ({ dataService }),
    [dataService]
  );

  return (
    <DataServiceContext.Provider value={contextValue}>
      {children}
    </DataServiceContext.Provider>
  );
};

// ============================================================================
// Hook
// ============================================================================

/**
 * useDataService - Hook to access the data service from context.
 * 
 * This hook provides access to the IDataService instance for performing
 * CRUD operations on projects, task lists, and tasks.
 * 
 * @returns The data service instance
 * @throws Error if used outside of DataServiceProvider
 * 
 * @example
 * ```tsx
 * function ProjectList() {
 *   const { dataService } = useDataService();
 *   const [projects, setProjects] = useState<Project[]>([]);
 * 
 *   useEffect(() => {
 *     dataService.getProjects().then(setProjects);
 *   }, [dataService]);
 * 
 *   return (
 *     <ul>
 *       {projects.map(p => <li key={p.id}>{p.name}</li>)}
 *     </ul>
 *   );
 * }
 * ```
 */
export function useDataService(): DataServiceContextValue {
  const context = useContext(DataServiceContext);
  
  if (context === undefined) {
    throw new Error(
      'useDataService must be used within a DataServiceProvider. ' +
      'Wrap your component tree with <DataServiceProvider> to fix this error.'
    );
  }
  
  return context;
}

// ============================================================================
// Utility Exports
// ============================================================================

/**
 * Export the raw context for advanced use cases (e.g., class components).
 * Prefer using the useDataService hook when possible.
 */
export { DataServiceContext };
