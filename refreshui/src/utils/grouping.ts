/**
 * Grouping utility functions for task lists and tasks.
 * Groups task lists by project and tasks by task list.
 *
 * @module utils/grouping
 */

import type { Project, TaskList, Task } from '../core/types/entities';

/**
 * Represents a group of items with a parent entity.
 */
export interface GroupedItems<T> {
  /** Unique identifier of the group (parent entity ID) */
  groupId: string;
  /** Display name of the group (parent entity name) */
  groupName: string;
  /** Items belonging to this group */
  items: T[];
}

/**
 * Groups task lists by their parent project.
 * Each group contains all task lists belonging to a single project.
 *
 * @param taskLists - Array of task lists to group
 * @param projects - Array of projects for group names
 * @returns Array of grouped task lists, one group per project
 */
export function groupTaskListsByProject(
  taskLists: TaskList[],
  projects: Project[]
): GroupedItems<TaskList>[] {
  // Create a map of project IDs to project names for quick lookup
  const projectMap = new Map<string, string>();
  for (const project of projects) {
    projectMap.set(project.id, project.name);
  }

  // Group task lists by project ID
  const groupMap = new Map<string, TaskList[]>();
  for (const taskList of taskLists) {
    const existing = groupMap.get(taskList.projectId);
    if (existing) {
      existing.push(taskList);
    } else {
      groupMap.set(taskList.projectId, [taskList]);
    }
  }

  // Convert map to array of GroupedItems
  const result: GroupedItems<TaskList>[] = [];
  for (const [projectId, items] of groupMap) {
    result.push({
      groupId: projectId,
      groupName: projectMap.get(projectId) ?? 'Unknown Project',
      items,
    });
  }

  return result;
}

/**
 * Groups tasks by their parent task list.
 * Each group contains all tasks belonging to a single task list.
 *
 * @param tasks - Array of tasks to group
 * @param taskLists - Array of task lists for group names
 * @returns Array of grouped tasks, one group per task list
 */
export function groupTasksByTaskList(
  tasks: Task[],
  taskLists: TaskList[]
): GroupedItems<Task>[] {
  // Create a map of task list IDs to task list names for quick lookup
  const taskListMap = new Map<string, string>();
  for (const taskList of taskLists) {
    taskListMap.set(taskList.id, taskList.name);
  }

  // Group tasks by task list ID
  const groupMap = new Map<string, Task[]>();
  for (const task of tasks) {
    const existing = groupMap.get(task.taskListId);
    if (existing) {
      existing.push(task);
    } else {
      groupMap.set(task.taskListId, [task]);
    }
  }

  // Convert map to array of GroupedItems
  const result: GroupedItems<Task>[] = [];
  for (const [taskListId, items] of groupMap) {
    result.push({
      groupId: taskListId,
      groupName: taskListMap.get(taskListId) ?? 'Unknown Task List',
      items,
    });
  }

  return result;
}

/**
 * Generic grouping function that can group any array of items by a parent field.
 *
 * @param items - Array of items to group
 * @param getParentId - Function to extract the parent ID from an item
 * @param parentNameMap - Map of parent IDs to parent names
 * @returns Array of grouped items
 */
export function groupByParent<T>(
  items: T[],
  getParentId: (item: T) => string,
  parentNameMap: Map<string, string>
): GroupedItems<T>[] {
  // Group items by parent ID
  const groupMap = new Map<string, T[]>();
  for (const item of items) {
    const parentId = getParentId(item);
    const existing = groupMap.get(parentId);
    if (existing) {
      existing.push(item);
    } else {
      groupMap.set(parentId, [item]);
    }
  }

  // Convert map to array of GroupedItems
  const result: GroupedItems<T>[] = [];
  for (const [parentId, groupItems] of groupMap) {
    result.push({
      groupId: parentId,
      groupName: parentNameMap.get(parentId) ?? 'Unknown',
      items: groupItems,
    });
  }

  return result;
}
