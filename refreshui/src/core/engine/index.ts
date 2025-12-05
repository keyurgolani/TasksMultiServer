/**
 * Theme Engine Module
 * 
 * Exports all theme engine types and utilities for the Customization Engine.
 * 
 * @module core/engine
 */

export type {
  ThemeVariableType,
  ThemeVariable,
  ThemePreset,
  ThemeStore,
  ThemeVariableDefinition,
  PersistedThemeState,
  ThemeSynchronizerProps,
  ThemeVariableCategory,
  ThemeCategoryInfo,
} from './types';

export {
  useThemeStore,
  useThemeVariable,
  useThemeVariablesByKeys,
  useThemeVariables,
  useThemePresets,
  useActivePresetId,
  useActivePreset,
  useThemeActions,
  useThemeAction,
  useThemeVariablesByCategory,
  useThemeSelector,
  useThemeVariableEffect,
  getVariableDefinition,
  getVariablesByCategory,
  themeVariableDefinitions,
  getDefaultVariables,
  builtInPresets,
  STORAGE_KEY,
} from './useThemeStore';

export {
  ThemeSynchronizer,
  useSyncCssVariable,
} from './ThemeSynchronizer';

// Re-export preset utilities for convenience
export {
  defaultPreset,
  cyberpunkPreset,
  minimalPreset,
  highContrastPreset,
  getPresetById,
  getPresetsByCategory,
  isBuiltInPreset,
  defaultThemeVariables,
} from './presets';
