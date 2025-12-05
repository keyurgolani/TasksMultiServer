/**
 * Mock Data Generator for the Refresh UI.
 * Generates seed data following the specified distribution:
 * - 15 projects
 * - 35 task lists (distributed across projects)
 * - Varied task states (NOT_STARTED, IN_PROGRESS, COMPLETED, BLOCKED)
 *
 * @module services/mock/MockDataGenerator
 */

import type {
  Project,
  TaskList,
  Task,
  TaskStatus,
  TaskPriority,
  ExitCriterion,
  Note,
} from '../../core/types';

// ============================================================================
// Configuration Constants
// ============================================================================

/** Number of projects to generate */
const PROJECT_COUNT = 15;

/** Number of task lists to generate */
const TASK_LIST_COUNT = 35;

/** Minimum tasks per task list */
const MIN_TASKS_PER_LIST = 2;

/** Maximum tasks per task list */
const MAX_TASKS_PER_LIST = 8;

// ============================================================================
// Sample Data for Generation
// ============================================================================

const PROJECT_NAMES = [
  'Website Redesign',
  'Mobile App Development',
  'API Integration',
  'Database Migration',
  'Security Audit',
  'Performance Optimization',
  'User Research',
  'Documentation Update',
  'Testing Framework',
  'CI/CD Pipeline',
  'Analytics Dashboard',
  'Customer Portal',
  'Internal Tools',
  'Cloud Migration',
  'Accessibility Improvements',
];

const PROJECT_DESCRIPTIONS = [
  'Modernize the user interface with new design system',
  'Build native mobile applications for iOS and Android',
  'Integrate third-party services and APIs',
  'Migrate legacy database to new schema',
  'Comprehensive security review and improvements',
  'Optimize application performance and load times',
  'Conduct user interviews and usability testing',
  'Update technical documentation and guides',
  'Implement automated testing infrastructure',
  'Set up continuous integration and deployment',
  'Build real-time analytics and reporting',
  'Create self-service customer portal',
  'Develop internal productivity tools',
  'Move infrastructure to cloud platform',
  'Ensure WCAG compliance across all pages',
];

const TASK_LIST_NAMES = [
  'Sprint 1',
  'Sprint 2',
  'Sprint 3',
  'Backlog',
  'Planning',
  'Design Phase',
  'Development',
  'Testing',
  'Deployment',
  'Review',
  'Research',
  'Documentation',
  'Bug Fixes',
  'Enhancements',
  'Infrastructure',
  'Security',
  'Performance',
  'Accessibility',
  'Integration',
  'Migration',
  'Setup',
  'Configuration',
  'Monitoring',
  'Maintenance',
  'Cleanup',
  'Phase 1',
  'Phase 2',
  'Phase 3',
  'MVP',
  'Beta',
  'Release',
  'Hotfixes',
  'Technical Debt',
  'Refactoring',
  'Optimization',
];

const TASK_TITLES = [
  'Set up development environment',
  'Create project structure',
  'Design database schema',
  'Implement authentication',
  'Build user registration',
  'Create login page',
  'Implement password reset',
  'Design API endpoints',
  'Build REST API',
  'Write unit tests',
  'Configure CI pipeline',
  'Set up monitoring',
  'Create documentation',
  'Review code changes',
  'Fix reported bugs',
  'Optimize queries',
  'Add caching layer',
  'Implement search',
  'Build dashboard',
  'Create reports',
  'Design UI components',
  'Implement responsive layout',
  'Add accessibility features',
  'Conduct security review',
  'Performance testing',
  'Load testing',
  'User acceptance testing',
  'Deploy to staging',
  'Deploy to production',
  'Configure backups',
  'Set up alerts',
  'Create runbooks',
  'Train team members',
  'Update dependencies',
  'Refactor legacy code',
  'Migrate data',
  'Integrate third-party service',
  'Build notification system',
  'Implement file upload',
  'Create admin panel',
];

const TASK_DESCRIPTIONS = [
  'Complete the initial setup and configuration',
  'Implement the core functionality as specified',
  'Review and test all edge cases',
  'Document the implementation details',
  'Ensure proper error handling',
  'Add logging and monitoring',
  'Optimize for performance',
  'Follow security best practices',
  'Write comprehensive tests',
  'Update related documentation',
];

const TAGS = [
  'frontend',
  'backend',
  'database',
  'api',
  'security',
  'performance',
  'testing',
  'documentation',
  'infrastructure',
  'design',
  'ux',
  'accessibility',
  'mobile',
  'web',
  'devops',
  'urgent',
  'blocked',
  'review',
  'research',
  'spike',
];

const EXIT_CRITERIA_TEMPLATES = [
  'Code review completed',
  'Unit tests passing',
  'Integration tests passing',
  'Documentation updated',
  'Deployed to staging',
  'QA sign-off received',
  'Performance benchmarks met',
  'Security review passed',
  'Accessibility audit passed',
  'User acceptance testing completed',
];

const NOTE_TEMPLATES = [
  'Started working on this task',
  'Made good progress today',
  'Encountered some issues, investigating',
  'Found a solution, implementing now',
  'Waiting for feedback from team',
  'Blocked by dependency',
  'Ready for review',
  'Addressed review comments',
  'Testing in progress',
  'Completed successfully',
];

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Generate a UUID v4.
 */
function generateId(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

/**
 * Get a random item from an array.
 */
function randomItem<T>(array: T[]): T {
  return array[Math.floor(Math.random() * array.length)];
}

/**
 * Get multiple random items from an array (without duplicates).
 */
function randomItems<T>(array: T[], count: number): T[] {
  const shuffled = [...array].sort(() => Math.random() - 0.5);
  return shuffled.slice(0, Math.min(count, array.length));
}

/**
 * Get a random integer between min and max (inclusive).
 */
function randomInt(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

/**
 * Generate a random ISO timestamp within the last N days.
 */
function randomTimestamp(daysAgo: number = 30): string {
  const now = Date.now();
  const past = now - daysAgo * 24 * 60 * 60 * 1000;
  const timestamp = past + Math.random() * (now - past);
  return new Date(timestamp).toISOString();
}

/**
 * Generate a timestamp that is after the given timestamp.
 */
function timestampAfter(baseTimestamp: string): string {
  const base = new Date(baseTimestamp).getTime();
  const now = Date.now();
  const timestamp = base + Math.random() * (now - base);
  return new Date(timestamp).toISOString();
}

// ============================================================================
// Generator Functions
// ============================================================================

/**
 * Generate exit criteria for a task.
 */
function generateExitCriteria(taskStatus: TaskStatus): ExitCriterion[] {
  const count = randomInt(1, 4);
  const criteria = randomItems(EXIT_CRITERIA_TEMPLATES, count);

  return criteria.map((c, index) => {
    // Determine status based on task status
    let status: 'INCOMPLETE' | 'COMPLETE' = 'INCOMPLETE';
    if (taskStatus === 'COMPLETED') {
      status = 'COMPLETE';
    } else if (taskStatus === 'IN_PROGRESS') {
      // Some criteria complete for in-progress tasks
      status = index < count / 2 ? 'COMPLETE' : 'INCOMPLETE';
    }

    return {
      criteria: c,
      status,
      comment: status === 'COMPLETE' ? 'Verified and approved' : undefined,
    };
  });
}

/**
 * Generate notes for a task.
 */
function generateNotes(count: number, baseTimestamp: string): Note[] {
  const notes: Note[] = [];
  let lastTimestamp = baseTimestamp;

  for (let i = 0; i < count; i++) {
    lastTimestamp = timestampAfter(lastTimestamp);
    notes.push({
      content: randomItem(NOTE_TEMPLATES),
      timestamp: lastTimestamp,
    });
  }

  return notes;
}

// ============================================================================
// Main Generator Class
// ============================================================================

/**
 * Generated mock data structure.
 */
export interface MockData {
  projects: Project[];
  taskLists: TaskList[];
  tasks: Task[];
}

/**
 * MockDataGenerator class.
 * Generates seed data with specified distribution.
 */
export class MockDataGenerator {
  private projects: Project[] = [];
  private taskLists: TaskList[] = [];
  private tasks: Task[] = [];

  /**
   * Generate all mock data.
   * @returns Generated mock data
   */
  generate(): MockData {
    this.generateProjects();
    this.generateTaskLists();
    this.generateTasks();

    return {
      projects: this.projects,
      taskLists: this.taskLists,
      tasks: this.tasks,
    };
  }

  /**
   * Generate projects.
   */
  private generateProjects(): void {
    for (let i = 0; i < PROJECT_COUNT; i++) {
      const createdAt = randomTimestamp(60);
      const project: Project = {
        id: generateId(),
        name: PROJECT_NAMES[i],
        description: PROJECT_DESCRIPTIONS[i],
        createdAt,
        updatedAt: timestampAfter(createdAt),
      };
      this.projects.push(project);
    }
  }

  /**
   * Generate task lists distributed across projects.
   */
  private generateTaskLists(): void {
    // Distribute task lists across projects
    // Ensure each project has at least 1 task list
    const projectTaskListCounts: number[] = new Array(PROJECT_COUNT).fill(1);
    let remaining = TASK_LIST_COUNT - PROJECT_COUNT;

    // Distribute remaining task lists randomly
    while (remaining > 0) {
      const projectIndex = randomInt(0, PROJECT_COUNT - 1);
      projectTaskListCounts[projectIndex]++;
      remaining--;
    }

    let taskListNameIndex = 0;
    for (let i = 0; i < PROJECT_COUNT; i++) {
      const project = this.projects[i];
      const count = projectTaskListCounts[i];

      for (let j = 0; j < count; j++) {
        const createdAt = timestampAfter(project.createdAt);
        const taskList: TaskList = {
          id: generateId(),
          projectId: project.id,
          name: TASK_LIST_NAMES[taskListNameIndex % TASK_LIST_NAMES.length],
          description: `Task list for ${project.name}`,
          createdAt,
          updatedAt: timestampAfter(createdAt),
        };
        this.taskLists.push(taskList);
        taskListNameIndex++;
      }
    }
  }

  /**
   * Generate tasks for each task list.
   */
  private generateTasks(): void {
    // Status distribution weights
    const statusWeights: { status: TaskStatus; weight: number }[] = [
      { status: 'NOT_STARTED', weight: 30 },
      { status: 'IN_PROGRESS', weight: 25 },
      { status: 'COMPLETED', weight: 35 },
      { status: 'BLOCKED', weight: 10 },
    ];

    // Priority distribution weights
    const priorityWeights: { priority: TaskPriority; weight: number }[] = [
      { priority: 'CRITICAL', weight: 5 },
      { priority: 'HIGH', weight: 20 },
      { priority: 'MEDIUM', weight: 40 },
      { priority: 'LOW', weight: 25 },
      { priority: 'TRIVIAL', weight: 10 },
    ];

    const selectWeighted = <T>(
      items: { weight: number }[],
      getValue: (item: { weight: number }) => T
    ): T => {
      const totalWeight = items.reduce((sum, item) => sum + item.weight, 0);
      let random = Math.random() * totalWeight;
      for (const item of items) {
        random -= item.weight;
        if (random <= 0) {
          return getValue(item);
        }
      }
      return getValue(items[items.length - 1]);
    };

    let taskTitleIndex = 0;
    const tasksByTaskList: Map<string, Task[]> = new Map();

    for (const taskList of this.taskLists) {
      const taskCount = randomInt(MIN_TASKS_PER_LIST, MAX_TASKS_PER_LIST);
      const tasksInList: Task[] = [];

      for (let i = 0; i < taskCount; i++) {
        const status = selectWeighted(
          statusWeights,
          (item) => (item as { status: TaskStatus; weight: number }).status
        );
        const priority = selectWeighted(
          priorityWeights,
          (item) => (item as { priority: TaskPriority; weight: number }).priority
        );

        const createdAt = timestampAfter(taskList.createdAt);
        const task: Task = {
          id: generateId(),
          taskListId: taskList.id,
          title: TASK_TITLES[taskTitleIndex % TASK_TITLES.length],
          description: randomItem(TASK_DESCRIPTIONS),
          status,
          priority,
          dependencies: [], // Will be populated after all tasks are created
          exitCriteria: generateExitCriteria(status),
          notes: generateNotes(randomInt(0, 3), createdAt),
          researchNotes: status !== 'NOT_STARTED' ? generateNotes(randomInt(0, 2), createdAt) : [],
          executionNotes:
            status === 'IN_PROGRESS' || status === 'COMPLETED'
              ? generateNotes(randomInt(1, 3), createdAt)
              : [],
          tags: randomItems(TAGS, randomInt(1, 4)),
          createdAt,
          updatedAt: timestampAfter(createdAt),
        };

        tasksInList.push(task);
        this.tasks.push(task);
        taskTitleIndex++;
      }

      tasksByTaskList.set(taskList.id, tasksInList);
    }

    // Add some dependencies (only within the same task list to avoid circular deps)
    this.addDependencies(tasksByTaskList);
  }

  /**
   * Add dependencies between tasks within the same task list.
   */
  private addDependencies(tasksByTaskList: Map<string, Task[]>): void {
    for (const [taskListId, tasks] of tasksByTaskList) {
      // Only add dependencies if there are multiple tasks
      if (tasks.length < 2) continue;

      // Add dependencies for some tasks (not all)
      const tasksWithDeps = tasks.filter(() => Math.random() < 0.3);

      for (const task of tasksWithDeps) {
        // Find potential dependencies (tasks created before this one)
        const potentialDeps = tasks.filter(
          (t) =>
            t.id !== task.id &&
            new Date(t.createdAt).getTime() < new Date(task.createdAt).getTime()
        );

        if (potentialDeps.length > 0) {
          // Add 1-2 dependencies
          const depCount = randomInt(1, Math.min(2, potentialDeps.length));
          const deps = randomItems(potentialDeps, depCount);

          task.dependencies = deps.map((dep) => ({
            taskId: dep.id,
            taskListId,
          }));
        }
      }
    }
  }
}

/**
 * Generate mock data with the specified distribution.
 * Convenience function that creates a generator and returns the data.
 */
export function generateMockData(): MockData {
  const generator = new MockDataGenerator();
  return generator.generate();
}
