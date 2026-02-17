/**
 * Sorting utility functions for projects, task lists, and tasks.
 * Supports sorting by name, date, priority, and status fields.
 *
 * @module utils/sorting
 */

import type { Project, TaskList, Task, TaskStatus, TaskPriority } from '../core/types/entities';

/**
 * Sort direction type.
 */
export type SortDirection = 'asc' | 'desc';

/**
 * Sort field options for projects.
 */
export type ProjectSortField = 'name' | 'createdAt' | 'updatedAt';

/**
 * Sort field options for task lists.
 */
export type TaskListSortField = 'name' | 'createdAt' | 'updatedAt';

/**
 * Sort field options for tasks.
 */
export type TaskSortField = 'title' | 'createdAt' | 'updatedAt' | 'priority' | 'status';

/**
 * Priority order mapping for sorting (higher priority = lower number).
 */
const PRIORITY_ORDER: Record<TaskPriority, number> = {
  CRITICAL: 0,
  HIGH: 1,
  MEDIUM: 2,
  LOW: 3,
  TRIVIAL: 4,
};

/**
 * Status order mapping for sorting.
 */
const STATUS_ORDER: Record<TaskStatus, number> = {
  IN_PROGRESS: 0,
  NOT_STARTED: 1,
  BLOCKED: 2,
  COMPLETED: 3,
};

/**
 * Compares two string values for sorting.
 *
 * @param a - First string value
 * @param b - Second string value
 * @param direction - Sort direction
 * @returns Comparison result (-1, 0, or 1)
 */
function compareStrings(a: string, b: string, direction: SortDirection): number {
  const comparison = a.localeCompare(b, undefined, { sensitivity: 'base' });
  return direction === 'asc' ? comparison : -comparison;
}

/**
 * Compares two date strings for sorting.
 *
 * @param a - First date string (ISO 8601)
 * @param b - Second date string (ISO 8601)
 * @param direction - Sort direction
 * @returns Comparison result (-1, 0, or 1)
 */
function compareDates(a: string, b: string, direction: SortDirection): number {
  const dateA = new Date(a).getTime();
  const dateB = new Date(b).getTime();
  const comparison = dateA - dateB;
  return direction === 'asc' ? comparison : -comparison;
}

/**
 * Compares two numeric values for sorting.
 *
 * @param a - First numeric value
 * @param b - Second numeric value
 * @param direction - Sort direction
 * @returns Comparison result
 */
function compareNumbers(a: number, b: number, direction: SortDirection): number {
  const comparison = a - b;
  return direction === 'asc' ? comparison : -comparison;
}

/**
 * Sorts projects by the specified field and direction.
 *
 * @param projects - Array of projects to sort
 * @param field - Field to sort by
 * @param direction - Sort direction (asc or desc)
 * @returns New sorted array of projects
 */
export function sortProjects(
  projects: Project[],
  field: ProjectSortField,
  direction: SortDirection
): Project[] {
  return [...projects].sort((a, b) => {
    switch (field) {
      case 'name':
        return compareStrings(a.name, b.name, direction);
      case 'createdAt':
        return compareDates(a.createdAt, b.createdAt, direction);
      case 'updatedAt':
        return compareDates(a.updatedAt, b.updatedAt, direction);
      default:
        return 0;
    }
  });
}

/**
 * Sorts task lists by the specified field and direction.
 *
 * @param taskLists - Array of task lists to sort
 * @param field - Field to sort by
 * @param direction - Sort direction (asc or desc)
 * @returns New sorted array of task lists
 */
export function sortTaskLists(
  taskLists: TaskList[],
  field: TaskListSortField,
  direction: SortDirection
): TaskList[] {
  return [...taskLists].sort((a, b) => {
    switch (field) {
      case 'name':
        return compareStrings(a.name, b.name, direction);
      case 'createdAt':
        return compareDates(a.createdAt, b.createdAt, direction);
      case 'updatedAt':
        return compareDates(a.updatedAt, b.updatedAt, direction);
      default:
        return 0;
    }
  });
}

/**
 * Sorts tasks by the specified field and direction.
 *
 * @param tasks - Array of tasks to sort
 * @param field - Field to sort by
 * @param direction - Sort direction (asc or desc)
 * @returns New sorted array of tasks
 */
export function sortTasks(
  tasks: Task[],
  field: TaskSortField,
  direction: SortDirection
): Task[] {
  return [...tasks].sort((a, b) => {
    switch (field) {
      case 'title':
        return compareStrings(a.title, b.title, direction);
      case 'createdAt':
        return compareDates(a.createdAt, b.createdAt, direction);
      case 'updatedAt':
        return compareDates(a.updatedAt, b.updatedAt, direction);
      case 'priority':
        return compareNumbers(
          PRIORITY_ORDER[a.priority],
          PRIORITY_ORDER[b.priority],
          direction
        );
      case 'status':
        return compareNumbers(
          STATUS_ORDER[a.status],
          STATUS_ORDER[b.status],
          direction
        );
      default:
        return 0;
    }
  });
}

/**
 * Generic sort function that can sort any array of items.
 *
 * @param items - Array of items to sort
 * @param getField - Function to extract the sortable value from an item
 * @param direction - Sort direction (asc or desc)
 * @param compareType - Type of comparison to use
 * @returns New sorted array of items
 */
export function sortByField<T>(
  items: T[],
  getField: (item: T) => string | number | Date,
  direction: SortDirection,
  compareType: 'string' | 'number' | 'date' = 'string'
): T[] {
  return [...items].sort((a, b) => {
    const valueA = getField(a);
    const valueB = getField(b);

    switch (compareType) {
      case 'string':
        return compareStrings(String(valueA), String(valueB), direction);
      case 'number':
        return compareNumbers(Number(valueA), Number(valueB), direction);
      case 'date':
        return compareDates(String(valueA), String(valueB), direction);
      default:
        return 0;
    }
  });
}

/**
 * Gets the priority order value for a given priority.
 * Useful for custom sorting logic.
 *
 * @param priority - Task priority
 * @returns Numeric order value (lower = higher priority)
 */
export function getPriorityOrder(priority: TaskPriority): number {
  return PRIORITY_ORDER[priority];
}

/**
 * Gets the status order value for a given status.
 * Useful for custom sorting logic.
 *
 * @param status - Task status
 * @returns Numeric order value
 */
export function getStatusOrder(status: TaskStatus): number {
  return STATUS_ORDER[status];
}

/**
 * Sorts tasks by priority in descending order (CRITICAL first, then HIGH, MEDIUM, LOW, TRIVIAL).
 * This is a convenience function for sorting ready tasks in the dashboard sidebar.
 *
 * Requirements: 1.14 - Sort ready tasks by priority in descending order
 *
 * @param tasks - Array of tasks to sort
 * @returns New sorted array of tasks with highest priority first
 */
export function sortTasksByPriorityDescending(tasks: Task[]): Task[] {
  return [...tasks].sort((a, b) => {
    return PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority];
  });
}
