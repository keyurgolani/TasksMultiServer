/**
 * Filtering utility functions for projects, task lists, and tasks.
 * Implements case-insensitive text matching on name/title fields.
 *
 * @module utils/filtering
 */

import type { Project, TaskList, Task } from '../core/types/entities';

/**
 * Filters projects by search query.
 * Performs case-insensitive matching on the project name.
 *
 * @param projects - Array of projects to filter
 * @param query - Search query string
 * @returns Filtered array of projects matching the query
 */
export function filterProjects(projects: Project[], query: string): Project[] {
  if (!query || query.trim() === '') {
    return projects;
  }

  const normalizedQuery = query.toLowerCase().trim();

  return projects.filter((project) =>
    project.name.toLowerCase().includes(normalizedQuery)
  );
}

/**
 * Filters task lists by search query.
 * Performs case-insensitive matching on the task list name.
 *
 * @param taskLists - Array of task lists to filter
 * @param query - Search query string
 * @returns Filtered array of task lists matching the query
 */
export function filterTaskLists(taskLists: TaskList[], query: string): TaskList[] {
  if (!query || query.trim() === '') {
    return taskLists;
  }

  const normalizedQuery = query.toLowerCase().trim();

  return taskLists.filter((taskList) =>
    taskList.name.toLowerCase().includes(normalizedQuery)
  );
}

/**
 * Filters tasks by search query.
 * Performs case-insensitive matching on the task title.
 *
 * @param tasks - Array of tasks to filter
 * @param query - Search query string
 * @returns Filtered array of tasks matching the query
 */
export function filterTasks(tasks: Task[], query: string): Task[] {
  if (!query || query.trim() === '') {
    return tasks;
  }

  const normalizedQuery = query.toLowerCase().trim();

  return tasks.filter((task) =>
    task.title.toLowerCase().includes(normalizedQuery)
  );
}

/**
 * Generic filter function that can filter any array of items with a name or title field.
 * Performs case-insensitive matching.
 *
 * @param items - Array of items to filter
 * @param query - Search query string
 * @param getSearchField - Function to extract the searchable field from an item
 * @returns Filtered array of items matching the query
 */
export function filterBySearchQuery<T>(
  items: T[],
  query: string,
  getSearchField: (item: T) => string
): T[] {
  if (!query || query.trim() === '') {
    return items;
  }

  const normalizedQuery = query.toLowerCase().trim();

  return items.filter((item) =>
    getSearchField(item).toLowerCase().includes(normalizedQuery)
  );
}
