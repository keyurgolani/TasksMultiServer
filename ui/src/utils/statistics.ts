/**
 * Statistics utility functions for calculating completion stats.
 * Calculates completed, in-progress, blocked counts and percentages.
 *
 * @module utils/statistics
 */

import type { Task, TaskStatus } from '../core/types/entities';

/**
 * Statistics for a collection of tasks.
 */
export interface TaskStatistics {
  /** Total number of tasks */
  totalTasks: number;
  /** Number of completed tasks */
  completedTasks: number;
  /** Number of in-progress tasks */
  inProgressTasks: number;
  /** Number of blocked tasks */
  blockedTasks: number;
  /** Number of not started tasks */
  notStartedTasks: number;
  /** Completion percentage (0-100) */
  completionPercentage: number;
}

/**
 * Calculates statistics for a collection of tasks.
 * Counts tasks by status and calculates completion percentage.
 *
 * @param tasks - Array of tasks to calculate statistics for
 * @returns TaskStatistics object with counts and percentage
 */
export function calculateTaskStatistics(tasks: Task[]): TaskStatistics {
  const totalTasks = tasks.length;

  if (totalTasks === 0) {
    return {
      totalTasks: 0,
      completedTasks: 0,
      inProgressTasks: 0,
      blockedTasks: 0,
      notStartedTasks: 0,
      completionPercentage: 0,
    };
  }

  let completedTasks = 0;
  let inProgressTasks = 0;
  let blockedTasks = 0;
  let notStartedTasks = 0;

  for (const task of tasks) {
    switch (task.status) {
      case 'COMPLETED':
        completedTasks++;
        break;
      case 'IN_PROGRESS':
        inProgressTasks++;
        break;
      case 'BLOCKED':
        blockedTasks++;
        break;
      case 'NOT_STARTED':
        notStartedTasks++;
        break;
    }
  }

  const completionPercentage = (completedTasks / totalTasks) * 100;

  return {
    totalTasks,
    completedTasks,
    inProgressTasks,
    blockedTasks,
    notStartedTasks,
    completionPercentage,
  };
}

/**
 * Counts tasks with a specific status.
 *
 * @param tasks - Array of tasks to count
 * @param status - Status to count
 * @returns Number of tasks with the specified status
 */
export function countTasksByStatus(tasks: Task[], status: TaskStatus): number {
  return tasks.filter((task) => task.status === status).length;
}

/**
 * Calculates the completion percentage for a collection of tasks.
 * Returns 0 if there are no tasks.
 *
 * @param tasks - Array of tasks
 * @returns Completion percentage (0-100)
 */
export function calculateCompletionPercentage(tasks: Task[]): number {
  if (tasks.length === 0) {
    return 0;
  }

  const completedCount = tasks.filter((task) => task.status === 'COMPLETED').length;
  return (completedCount / tasks.length) * 100;
}

/**
 * Gets a breakdown of task counts by status.
 *
 * @param tasks - Array of tasks
 * @returns Object with counts for each status
 */
export function getStatusBreakdown(tasks: Task[]): Record<TaskStatus, number> {
  const breakdown: Record<TaskStatus, number> = {
    NOT_STARTED: 0,
    IN_PROGRESS: 0,
    BLOCKED: 0,
    COMPLETED: 0,
  };

  for (const task of tasks) {
    breakdown[task.status]++;
  }

  return breakdown;
}
