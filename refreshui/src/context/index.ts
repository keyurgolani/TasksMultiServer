/**
 * Context module - exports all React context providers and hooks.
 * 
 * @module context
 */

// Theme context
export { ThemeProvider, useTheme } from './ThemeContext';

// Toast context
export { ToastProvider, useToast } from './ToastContext';

// Data service context
export {
  DataServiceProvider,
  useDataService,
  DataServiceContext,
} from './DataServiceContext';
export type { DataServiceProviderProps } from './DataServiceContext';
