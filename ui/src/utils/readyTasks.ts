/**
 * Ready tasks utility functions for identifying tasks with no pending dependencies.
 * A task is considered "ready" when it is not completed and all its dependencies are completed.
 *
 * @module utils/readyTasks
 */

import type { Task } from '../core/types/entities';

/**
 * Determines if a task is ready for execution.
 * A task is ready when:
 * - Its status is NOT_STARTED or IN_PROGRESS (not COMPLETED or BLOCKED)
 * - All tasks it depends on have status "COMPLETED"
 *
 * Note: BLOCKED tasks are excluded because they have dependencies that are not yet complete.
 * If all dependencies are complete, the task should be NOT_STARTED or IN_PROGRESS, not BLOCKED.
 *
 * @param task - The task to check
 * @param allTasks - All tasks in the system (used to look up dependency statuses)
 * @returns true if the task is ready for execution, false otherwise
 */
export function isTaskReady(task: Task, allTasks: Task[]): boolean {
  // Only NOT_STARTED and IN_PROGRESS tasks can be ready
  // COMPLETED tasks are done, BLOCKED tasks have incomplete dependencies
  if (task.status === 'COMPLETED' || task.status === 'BLOCKED') {
    return false;
  }

  // If no dependencies, the task is ready
  if (task.dependencies.length === 0) {
    return true;
  }

  // Create a map for efficient task lookup by ID
  const taskMap = new Map<string, Task>();
  for (const t of allTasks) {
    taskMap.set(t.id, t);
  }

  // Check if all dependencies are completed
  for (const dependency of task.dependencies) {
    const dependentTask = taskMap.get(dependency.taskId);
    
    // If the dependent task doesn't exist or is not completed, this task is not ready
    if (!dependentTask || dependentTask.status !== 'COMPLETED') {
      return false;
    }
  }

  return true;
}

/**
 * Filters tasks to return only those that are ready for execution.
 * A task is ready when it is not completed and all its dependencies are completed.
 *
 * @param tasks - Array of tasks to filter
 * @param allTasks - All tasks in the system (used to look up dependency statuses).
 *                   If not provided, uses the tasks array itself.
 * @returns Array of tasks that are ready for execution
 */
export function getReadyTasks(tasks: Task[], allTasks?: Task[]): Task[] {
  const tasksForLookup = allTasks ?? tasks;
  return tasks.filter((task) => isTaskReady(task, tasksForLookup));
}

/**
 * Counts the number of ready tasks in a collection.
 *
 * @param tasks - Array of tasks to check
 * @param allTasks - All tasks in the system (used to look up dependency statuses).
 *                   If not provided, uses the tasks array itself.
 * @returns Number of tasks that are ready for execution
 */
export function countReadyTasks(tasks: Task[], allTasks?: Task[]): number {
  return getReadyTasks(tasks, allTasks).length;
}
