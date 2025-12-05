/**
 * Core types module - exports all type definitions.
 * 
 * @module core/types
 */

export type {
  Project,
  TaskList,
  Task,
  TaskDependency,
  ExitCriterion,
  Note,
  TaskStatus,
  TaskPriority,
} from './entities';

// Re-export theme engine types for convenience
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
} from '../engine';
