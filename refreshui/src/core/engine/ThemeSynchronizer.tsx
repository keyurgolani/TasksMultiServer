/**
 * ThemeSynchronizer Component
 * 
 * Listens to the Zustand theme store and updates CSS variables on document.documentElement.
 * This enables real-time visual customization without triggering React re-renders.
 * 
 * Requirements: 1.2, 2.2, 11.4
 * - 1.2: Update CSS variables on document.documentElement without triggering React re-renders
 * - 2.2: Update CSS variables immediately via ThemeSynchronizer without component re-renders
 * - 11.4: Update CSS variables via ThemeSynchronizer without triggering component re-renders
 * 
 * @module core/engine/ThemeSynchronizer
 */

/* eslint-disable react-refresh/only-export-components */
import { useEffect, useRef } from 'react';
import { useThemeStore, themeVariableDefinitions } from './useThemeStore';
import type { ThemeSynchronizerProps } from './types';

/**
 * Formats a value with its unit for CSS variable assignment.
 * 
 * @param value - The raw value from the theme store
 * @param unit - Optional unit suffix (e.g., 'px', '%', 'ms')
 * @returns Formatted string value for CSS
 */
const formatCssValue = (value: string | number, unit?: string): string => {
  if (typeof value === 'string') {
    return value;
  }
  return unit ? `${value}${unit}` : String(value);
};

/**
 * Updates a single CSS variable on the document root.
 * 
 * @param cssVar - The CSS variable name (e.g., '--glass-opacity')
 * @param value - The value to set
 */
const setCssVariable = (cssVar: string, value: string): void => {
  document.documentElement.style.setProperty(cssVar, value);
};

/**
 * ThemeSynchronizer Component
 * 
 * This component subscribes to the Zustand theme store and synchronizes
 * all theme variable changes to CSS variables on the document root.
 * 
 * Key features:
 * - Uses shallow comparison to minimize updates
 * - Updates CSS variables directly without React re-renders
 * - Supports all variable types (color, number, boolean)
 * - Handles unit suffixes for numeric values
 * 
 * Usage:
 * ```tsx
 * <ThemeSynchronizer>
 *   <App />
 * </ThemeSynchronizer>
 * ```
 */
export const ThemeSynchronizer: React.FC<ThemeSynchronizerProps> = ({ children }) => {
  // Track previous values to enable shallow comparison
  const previousVariablesRef = useRef<Record<string, string | number>>({});
  
  // Subscribe to the theme store variables
  const variables = useThemeStore((state) => state.variables);

  useEffect(() => {
    // Build a map of variable keys to their definitions for quick lookup
    const definitionMap = new Map(
      themeVariableDefinitions.map((def) => [def.key, def])
    );

    // Iterate through all variables and update CSS variables
    Object.entries(variables).forEach(([key, value]) => {
      const previousValue = previousVariablesRef.current[key];
      
      // Only update if the value has changed (shallow comparison)
      if (previousValue !== value) {
        const definition = definitionMap.get(key);
        
        if (definition) {
          const formattedValue = formatCssValue(value, definition.unit);
          setCssVariable(definition.cssVar, formattedValue);
        }
      }
    });

    // Update the previous values reference
    previousVariablesRef.current = { ...variables };
  }, [variables]);

  // Initial sync on mount - ensure all CSS variables are set
  useEffect(() => {
    const definitionMap = new Map(
      themeVariableDefinitions.map((def) => [def.key, def])
    );

    // Set all CSS variables on initial mount
    Object.entries(variables).forEach(([key, value]) => {
      const definition = definitionMap.get(key);
      
      if (definition) {
        const formattedValue = formatCssValue(value, definition.unit);
        setCssVariable(definition.cssVar, formattedValue);
      }
    });

    // Initialize the previous values reference
    previousVariablesRef.current = { ...variables };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run on mount

  // Render children without any wrapper element to avoid affecting layout
  return <>{children}</>;
};

/**
 * Hook to manually sync a specific variable to CSS.
 * Useful for components that need to update CSS variables outside the normal flow.
 * 
 * @returns A function to sync a variable to CSS
 */
export const useSyncCssVariable = () => {
  return (key: string, value: string | number) => {
    const definition = themeVariableDefinitions.find((def) => def.key === key);
    
    if (definition) {
      const formattedValue = formatCssValue(value, definition.unit);
      setCssVariable(definition.cssVar, formattedValue);
    }
  };
};

export default ThemeSynchronizer;
