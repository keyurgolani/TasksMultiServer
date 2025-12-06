/**
 * Core entity types for the Refresh UI task management system.
 * These types represent the domain model and are used throughout the application.
 * 
 * @module core/types/entities
 */

/**
 * Represents a project in the task management system.
 * Projects are the top-level organizational unit containing task lists.
 */
export interface Project {
  /** Unique identifier for the project */
  id: string;
  /** Display name of the project */
  name: string;
  /** Optional description of the project */
  description?: string;
  /** ISO 8601 timestamp when the project was created */
  createdAt: string;
  /** ISO 8601 timestamp when the project was last updated */
  updatedAt: string;
}

/**
 * Represents a task list within a project.
 * Task lists group related tasks together.
 */
export interface TaskList {
  /** Unique identifier for the task list */
  id: string;
  /** ID of the parent project */
  projectId: string;
  /** Display name of the task list */
  name: string;
  /** Optional description of the task list */
  description?: string;
  /** ISO 8601 timestamp when the task list was created */
  createdAt: string;
  /** ISO 8601 timestamp when the task list was last updated */
  updatedAt: string;
}

/**
 * Represents a dependency between tasks.
 * A task can depend on other tasks, forming a DAG (Directed Acyclic Graph).
 */
export interface TaskDependency {
  /** ID of the task that this task depends on */
  taskId: string;
  /** ID of the task list containing the dependent task */
  taskListId: string;
}

/**
 * Represents an exit criterion for a task.
 * Exit criteria define the conditions that must be met for a task to be considered complete.
 */
export interface ExitCriterion {
  /** Description of the criterion */
  criteria: string;
  /** Current status of the criterion */
  status: 'INCOMPLETE' | 'COMPLETE';
  /** Optional comment providing additional context */
  comment?: string;
}

/**
 * Represents a note attached to a task.
 * Notes can be general notes, research notes, or execution notes.
 */
export interface Note {
  /** Content of the note */
  content: string;
  /** ISO 8601 timestamp when the note was created */
  timestamp: string;
}

/**
 * Represents an action plan item for a task.
 * Action plan items define the steps to complete a task.
 */
export interface ActionPlanItem {
  /** Sequence number for ordering */
  sequence: number;
  /** Content/description of the action item */
  content: string;
}

/**
 * Task status values.
 */
export type TaskStatus = 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED' | 'BLOCKED';

/**
 * Task priority values.
 */
export type TaskPriority = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'TRIVIAL';

/**
 * Represents a task in the task management system.
 * Tasks are the fundamental work items that users track and complete.
 */
export interface Task {
  /** Unique identifier for the task */
  id: string;
  /** ID of the task list containing this task */
  taskListId: string;
  /** Title/name of the task */
  title: string;
  /** Optional detailed description of the task */
  description?: string;
  /** Current status of the task */
  status: TaskStatus;
  /** Priority level of the task */
  priority: TaskPriority;
  /** List of task dependencies */
  dependencies: TaskDependency[];
  /** List of exit criteria that must be met */
  exitCriteria: ExitCriterion[];
  /** General notes about the task */
  notes: Note[];
  /** Research notes gathered during task investigation */
  researchNotes: Note[];
  /** Notes recorded during task execution */
  executionNotes: Note[];
  /** Tags for categorization and filtering */
  tags: string[];
  /** Action plan items for completing the task */
  actionPlan?: ActionPlanItem[];
  /** ISO 8601 timestamp when the task was created */
  createdAt: string;
  /** ISO 8601 timestamp when the task was last updated */
  updatedAt: string;
}
