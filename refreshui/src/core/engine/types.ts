/**
 * Theme Engine Types
 * 
 * Core type definitions for the Customization Engine that manages
 * design tokens, presets, and real-time CSS variable injection.
 * 
 * @module core/engine/types
 */

/**
 * The type of value a theme variable can hold.
 */
export type ThemeVariableType = 'color' | 'number' | 'boolean';

/**
 * Represents a single customizable theme variable.
 * Theme variables are the atomic units of customization that map
 * directly to CSS variables on the document root.
 */
export interface ThemeVariable {
  /** Unique identifier for the variable */
  key: string;
  /** Current value of the variable */
  value: string | number;
  /** Type of the variable for UI rendering and validation */
  type: ThemeVariableType;
  /** The CSS variable name (e.g., '--color-primary') */
  cssVar: string;
  /** Minimum value for number types */
  min?: number;
  /** Maximum value for number types */
  max?: number;
  /** Step increment for number types */
  step?: number;
  /** Unit suffix for number types (e.g., 'px', '%', 'ms') */
  unit?: string;
  /** Human-readable label for the variable */
  label?: string;
  /** Category for grouping in UI (e.g., 'colors', 'effects', 'spacing') */
  category?: string;
}

/**
 * Represents a theme preset - a predefined collection of variable values.
 * Presets allow users to quickly switch between different visual configurations.
 */
export interface ThemePreset {
  /** Unique identifier for the preset */
  id: string;
  /** Display name of the preset */
  name: string;
  /** Optional description of the preset */
  description?: string;
  /** Map of variable keys to their preset values */
  variables: Record<string, string | number>;
  /** Whether this is a built-in preset (cannot be deleted) */
  isBuiltIn?: boolean;
  /** Category for grouping presets (e.g., 'dark', 'light', 'colorful') */
  category?: string;
}

/**
 * The state and actions for the theme store.
 * This interface defines the shape of the Zustand store that manages
 * all theme-related state and operations.
 */
export interface ThemeStore {
  /** Map of all theme variable values by key */
  variables: Record<string, string | number>;
  /** Available theme presets */
  presets: ThemePreset[];
  /** ID of the currently active preset, or null if custom */
  activePresetId: string | null;
  
  /**
   * Set a single variable value.
   * This triggers CSS variable update via ThemeSynchronizer.
   * @param key - The variable key
   * @param value - The new value
   */
  setVariable: (key: string, value: string | number) => void;
  
  /**
   * Set multiple variables at once.
   * Useful for batch updates to minimize re-renders.
   * @param variables - Map of variable keys to values
   */
  setVariables: (variables: Record<string, string | number>) => void;
  
  /**
   * Apply a preset by ID.
   * This sets all variables defined in the preset.
   * @param presetId - The preset ID to apply
   */
  applyPreset: (presetId: string) => void;
  
  /**
   * Reset all variables to their default values.
   */
  resetToDefaults: () => void;
  
  /**
   * Add a custom preset based on current variable values.
   * @param name - Name for the new preset
   * @param description - Optional description
   * @returns The created preset
   */
  saveAsPreset: (name: string, description?: string) => ThemePreset;
  
  /**
   * Delete a custom preset.
   * Built-in presets cannot be deleted.
   * @param presetId - The preset ID to delete
   */
  deletePreset: (presetId: string) => void;
}

/**
 * Configuration for theme variable definitions.
 * Used to define the available variables and their constraints.
 */
export interface ThemeVariableDefinition {
  /** Unique identifier for the variable */
  key: string;
  /** Default value */
  defaultValue: string | number;
  /** Type of the variable */
  type: ThemeVariableType;
  /** The CSS variable name */
  cssVar: string;
  /** Minimum value for number types */
  min?: number;
  /** Maximum value for number types */
  max?: number;
  /** Step increment for number types */
  step?: number;
  /** Unit suffix for number types */
  unit?: string;
  /** Human-readable label */
  label: string;
  /** Category for grouping */
  category: string;
}

/**
 * Theme state that gets persisted to localStorage.
 * This is a subset of ThemeStore that needs to survive page reloads.
 */
export interface PersistedThemeState {
  /** Map of all theme variable values */
  variables: Record<string, string | number>;
  /** ID of the active preset */
  activePresetId: string | null;
  /** Custom presets created by the user */
  customPresets: ThemePreset[];
}

/**
 * Props for the ThemeSynchronizer component.
 */
export interface ThemeSynchronizerProps {
  /** Optional children to render */
  children?: React.ReactNode;
}

/**
 * Category definitions for organizing theme variables in the UI.
 */
export type ThemeVariableCategory = 
  | 'colors'
  | 'effects'
  | 'spacing'
  | 'typography'
  | 'animation';

/**
 * Default theme variable categories with display information.
 */
export interface ThemeCategoryInfo {
  /** Category identifier */
  id: ThemeVariableCategory;
  /** Display label */
  label: string;
  /** Description of the category */
  description: string;
  /** Icon name (for Lucide icons) */
  icon?: string;
}
