/**
 * Theme Store - Zustand Store with Persistence Middleware
 * 
 * Manages all customizable theme variables with localStorage persistence.
 * This store is the core of the Customization Engine, enabling real-time
 * visual customization without React re-renders.
 * 
 * Requirements: 2.1, 2.3, 11.1, 11.3
 * 
 * @module core/engine/useThemeStore
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { useShallow } from 'zustand/shallow';
import { useCallback, useMemo } from 'react';
import type { ThemeStore, ThemePreset, ThemeVariableDefinition } from './types';
import { 
  builtInPresets as presetsFromModule, 
  getDefaultVariables as getDefaultsFromModule 
} from './presets';

/**
 * Storage key for persisted theme state
 */
const STORAGE_KEY = 'refresh-ui-theme';

/**
 * Theme variable definitions with defaults, constraints, and metadata.
 * These define all customizable variables available in the Customization Engine.
 */
export const themeVariableDefinitions: ThemeVariableDefinition[] = [
  // Color Variables
  {
    key: 'colorPrimary',
    defaultValue: '#6b73ff',
    type: 'color',
    cssVar: '--primary',
    label: 'Primary Color',
    category: 'colors',
  },
  {
    key: 'colorPrimaryDark',
    defaultValue: '#5a63e0',
    type: 'color',
    cssVar: '--primary-dark',
    label: 'Primary Dark',
    category: 'colors',
  },
  {
    key: 'colorSuccess',
    defaultValue: '#2ed573',
    type: 'color',
    cssVar: '--success',
    label: 'Success Color',
    category: 'colors',
  },
  {
    key: 'colorWarning',
    defaultValue: '#ffa502',
    type: 'color',
    cssVar: '--warning',
    label: 'Warning Color',
    category: 'colors',
  },
  {
    key: 'colorError',
    defaultValue: '#ff4757',
    type: 'color',
    cssVar: '--error',
    label: 'Error Color',
    category: 'colors',
  },
  {
    key: 'colorInfo',
    defaultValue: '#3498db',
    type: 'color',
    cssVar: '--info',
    label: 'Info Color',
    category: 'colors',
  },
  
  // Effect Variables
  {
    key: 'glassOpacity',
    defaultValue: 0.7,
    type: 'number',
    cssVar: '--glass-opacity',
    min: 0,
    max: 1,
    step: 0.05,
    label: 'Glass Opacity',
    category: 'effects',
  },
  {
    key: 'glassBlur',
    defaultValue: 10,
    type: 'number',
    cssVar: '--glass-blur',
    min: 0,
    max: 30,
    step: 1,
    unit: 'px',
    label: 'Glass Blur',
    category: 'effects',
  },
  {
    key: 'glassBorderOpacity',
    defaultValue: 0.3,
    type: 'number',
    cssVar: '--glass-border-opacity',
    min: 0,
    max: 1,
    step: 0.05,
    label: 'Glass Border Opacity',
    category: 'effects',
  },
  {
    key: 'glowStrength',
    defaultValue: 50,
    type: 'number',
    cssVar: '--glow-strength',
    min: 0,
    max: 100,
    step: 5,
    label: 'Glow Strength',
    category: 'effects',
  },
  {
    key: 'grainOpacity',
    defaultValue: 0.05,
    type: 'number',
    cssVar: '--grain-opacity',
    min: 0,
    max: 0.3,
    step: 0.01,
    label: 'Grain Opacity',
    category: 'effects',
  },
  {
    key: 'parallaxDepth',
    defaultValue: 20,
    type: 'number',
    cssVar: '--parallax-depth',
    min: 0,
    max: 50,
    step: 5,
    label: 'Parallax Depth',
    category: 'effects',
  },
  {
    key: 'shadowStrength',
    defaultValue: 40,
    type: 'number',
    cssVar: '--shadow-strength',
    min: 0,
    max: 100,
    step: 5,
    label: 'Shadow Strength',
    category: 'effects',
  },
  
  // Animation Variables
  {
    key: 'animationSpeed',
    defaultValue: 1,
    type: 'number',
    cssVar: '--animation-speed',
    min: 0.25,
    max: 2,
    step: 0.25,
    label: 'Animation Speed',
    category: 'animation',
  },
  
  // Spacing Variables
  {
    key: 'borderRadius',
    defaultValue: 12,
    type: 'number',
    cssVar: '--border-radius',
    min: 0,
    max: 24,
    step: 2,
    unit: 'px',
    label: 'Border Radius',
    category: 'spacing',
  },
  
  // Typography Variables
  {
    key: 'fontFamily',
    defaultValue: 'default',
    type: 'color', // Using 'color' type for string values (font selection)
    cssVar: '--font-default',
    label: 'Font Family',
    category: 'typography',
  },
];

/**
 * Generate default variable values from definitions.
 * This function creates defaults from the variable definitions array,
 * which is useful for ensuring all defined variables have values.
 */
export const getDefaultVariables = (): Record<string, string | number> => {
  // Start with the preset defaults
  const defaults = getDefaultsFromModule();
  
  // Merge with any additional variables from definitions
  themeVariableDefinitions.forEach((def) => {
    if (!(def.key in defaults)) {
      defaults[def.key] = def.defaultValue;
    }
  });
  
  return defaults;
};

/**
 * Built-in theme presets
 * Requirement 2.4: Default theme presets (Default, Cyberpunk, Minimal, High Contrast)
 * 
 * Each preset defines a complete set of theme variables that can be applied
 * as a batch update. Presets are designed to provide distinct visual experiences:
 * 
 * - Default: Clean, balanced design suitable for everyday use
 * - Cyberpunk: Neon-infused futuristic aesthetic with strong glow effects
 * - Minimal: Clean and simple with reduced visual effects for focus
 * - High Contrast: Maximum visibility for accessibility compliance
 * 
 * @see ./presets.ts for detailed preset definitions
 */
export const builtInPresets: ThemePreset[] = presetsFromModule;


/**
 * Create the theme store with Zustand and persistence middleware.
 * 
 * The store manages:
 * - All theme variable values
 * - Available presets (built-in + custom)
 * - Active preset tracking
 * - Persistence to localStorage
 * 
 * Requirements:
 * - 2.1: Zustand store managing all customizable variables with default values
 * - 2.3: Restore previously saved customization settings from localStorage
 * - 11.1: Zustand store with persistence middleware for localStorage sync
 */
export const useThemeStore = create<ThemeStore>()(
  persist(
    (set, get) => ({
      // Initial state
      variables: getDefaultVariables(),
      presets: [...builtInPresets],
      activePresetId: 'default',

      /**
       * Set a single variable value.
       * Clears activePresetId since we're now in a custom state.
       */
      setVariable: (key: string, value: string | number) => {
        set((state) => ({
          variables: {
            ...state.variables,
            [key]: value,
          },
          // Clear active preset when manually changing a variable
          activePresetId: null,
        }));
      },

      /**
       * Set multiple variables at once.
       * Useful for batch updates to minimize re-renders.
       */
      setVariables: (variables: Record<string, string | number>) => {
        set((state) => ({
          variables: {
            ...state.variables,
            ...variables,
          },
          // Clear active preset when manually changing variables
          activePresetId: null,
        }));
      },

      /**
       * Apply a preset by ID.
       * Sets all variables defined in the preset and marks it as active.
       */
      applyPreset: (presetId: string) => {
        const state = get();
        const preset = state.presets.find((p) => p.id === presetId);
        
        if (!preset) {
          console.warn(`Preset "${presetId}" not found`);
          return;
        }

        set({
          variables: {
            ...getDefaultVariables(), // Start with defaults
            ...preset.variables, // Apply preset overrides
          },
          activePresetId: presetId,
        });
      },

      /**
       * Reset all variables to their default values.
       */
      resetToDefaults: () => {
        set({
          variables: getDefaultVariables(),
          activePresetId: 'default',
        });
      },

      /**
       * Save current variable values as a new custom preset.
       */
      saveAsPreset: (name: string, description?: string): ThemePreset => {
        const state = get();
        const newPreset: ThemePreset = {
          id: `custom-${Date.now()}`,
          name,
          description,
          isBuiltIn: false,
          category: 'custom',
          variables: { ...state.variables },
        };

        set((state) => ({
          presets: [...state.presets, newPreset],
          activePresetId: newPreset.id,
        }));

        return newPreset;
      },

      /**
       * Delete a custom preset.
       * Built-in presets cannot be deleted.
       */
      deletePreset: (presetId: string) => {
        const state = get();
        const preset = state.presets.find((p) => p.id === presetId);

        if (!preset) {
          console.warn(`Preset "${presetId}" not found`);
          return;
        }

        if (preset.isBuiltIn) {
          console.warn(`Cannot delete built-in preset "${preset.name}"`);
          return;
        }

        set((state) => ({
          presets: state.presets.filter((p) => p.id !== presetId),
          // If we deleted the active preset, clear the active preset ID
          activePresetId: state.activePresetId === presetId ? null : state.activePresetId,
        }));
      },
    }),
    {
      name: STORAGE_KEY,
      storage: createJSONStorage(() => localStorage),
      // Only persist specific parts of the state
      partialize: (state) => ({
        variables: state.variables,
        activePresetId: state.activePresetId,
        // Only persist custom presets (filter out built-in ones)
        presets: state.presets.filter((p) => !p.isBuiltIn),
      }),
      // Merge persisted state with initial state
      merge: (persistedState, currentState) => {
        const persisted = persistedState as Partial<ThemeStore> | undefined;
        
        return {
          ...currentState,
          variables: {
            ...currentState.variables,
            ...(persisted?.variables || {}),
          },
          activePresetId: persisted?.activePresetId ?? currentState.activePresetId,
          // Combine built-in presets with persisted custom presets
          presets: [
            ...builtInPresets,
            ...(persisted?.presets || []),
          ],
        };
      },
    }
  )
);

/**
 * Selector hooks for optimized re-renders.
 * Use these instead of accessing the full store to minimize component updates.
 * 
 * Requirement 11.3: Only re-render components that depend on the selected slice
 * 
 * These hooks implement Zustand selector isolation patterns:
 * - Primitive selectors (string, number, null) use direct selection
 * - Object selectors use useShallow for shallow comparison
 * - Action selectors are stable references that don't cause re-renders
 */

/**
 * Get a single variable value.
 * Only re-renders when the specific variable changes.
 * 
 * @param key - The variable key to select
 * @returns The variable value
 */
export const useThemeVariable = <T extends string | number>(key: string): T => {
  return useThemeStore((state) => state.variables[key] as T);
};

/**
 * Get multiple specific variable values.
 * Only re-renders when any of the selected variables change.
 * Uses shallow comparison to prevent unnecessary re-renders.
 * 
 * @param keys - Array of variable keys to select
 * @returns Object with selected variable values
 */
export const useThemeVariablesByKeys = (keys: string[]): Record<string, string | number> => {
  return useThemeStore(
    useShallow((state) => {
      const result: Record<string, string | number> = {};
      for (const key of keys) {
        if (key in state.variables) {
          result[key] = state.variables[key];
        }
      }
      return result;
    })
  );
};

/**
 * Get all variables.
 * Uses shallow comparison to prevent re-renders when variables object reference changes
 * but values remain the same.
 * 
 * @returns All theme variables
 */
export const useThemeVariables = () => {
  return useThemeStore(useShallow((state) => state.variables));
};

/**
 * Get all presets.
 * Uses shallow comparison for the presets array.
 * 
 * @returns All theme presets
 */
export const useThemePresets = () => {
  return useThemeStore(useShallow((state) => state.presets));
};

/**
 * Get active preset ID.
 * Primitive selector - only re-renders when the ID changes.
 * 
 * @returns The active preset ID or null
 */
export const useActivePresetId = () => {
  return useThemeStore((state) => state.activePresetId);
};

/**
 * Get the active preset object.
 * Only re-renders when the active preset changes.
 * 
 * @returns The active preset or undefined if no preset is active
 */
export const useActivePreset = (): ThemePreset | undefined => {
  return useThemeStore((state) => {
    if (!state.activePresetId) return undefined;
    return state.presets.find((p) => p.id === state.activePresetId);
  });
};

/**
 * Get theme actions (setVariable, applyPreset, etc.)
 * 
 * Actions are stable references from the store and don't cause re-renders.
 * Uses useShallow to ensure the returned object reference is stable when
 * the action references haven't changed.
 * 
 * @returns Object containing all theme actions
 */
export const useThemeActions = () => {
  return useThemeStore(
    useShallow((state) => ({
      setVariable: state.setVariable,
      setVariables: state.setVariables,
      applyPreset: state.applyPreset,
      resetToDefaults: state.resetToDefaults,
      saveAsPreset: state.saveAsPreset,
      deletePreset: state.deletePreset,
    }))
  );
};

/**
 * Get a single theme action.
 * More granular than useThemeActions - only subscribes to the specific action.
 * 
 * @param actionName - The name of the action to select
 * @returns The action function
 */
export function useThemeAction<K extends keyof ThemeStore>(
  actionName: K
): ThemeStore[K] {
  return useThemeStore((state) => state[actionName]);
}

/**
 * Get variables for a specific category.
 * Only re-renders when variables in the specified category change.
 * 
 * @param category - The category to filter by
 * @returns Object with variable values for the category
 */
export const useThemeVariablesByCategory = (
  category: string
): Record<string, string | number> => {
  // Get the keys for this category from definitions
  const categoryKeys = useMemo(
    () => themeVariableDefinitions
      .filter((def) => def.category === category)
      .map((def) => def.key),
    [category]
  );
  
  return useThemeStore(
    useShallow((state) => {
      const result: Record<string, string | number> = {};
      for (const key of categoryKeys) {
        if (key in state.variables) {
          result[key] = state.variables[key];
        }
      }
      return result;
    })
  );
};

/**
 * Create a custom selector with shallow comparison.
 * Useful for creating component-specific selectors.
 * 
 * @param selector - The selector function
 * @returns The selected value with shallow comparison
 */
export function useThemeSelector<T>(
  selector: (state: ThemeStore) => T
): T {
  return useThemeStore(useShallow(selector));
}

/**
 * Hook to check if a specific variable has changed.
 * Useful for triggering effects only when specific variables change.
 * 
 * @param key - The variable key to watch
 * @param callback - Callback to execute when the variable changes
 */
export const useThemeVariableEffect = (
  key: string,
  callback: (value: string | number) => void
): void => {
  const value = useThemeVariable(key);
  const callbackRef = useCallback((v: string | number) => callback(v), [callback]);
  
  // The effect will only run when the specific variable changes
  useMemo(() => {
    callbackRef(value);
  }, [value, callbackRef]);
};

/**
 * Get variable definition by key
 */
export const getVariableDefinition = (key: string): ThemeVariableDefinition | undefined => {
  return themeVariableDefinitions.find((def) => def.key === key);
};

/**
 * Get all variable definitions for a category
 */
export const getVariablesByCategory = (category: string): ThemeVariableDefinition[] => {
  return themeVariableDefinitions.filter((def) => def.category === category);
};

/**
 * Export the storage key for testing purposes
 */
export { STORAGE_KEY };
