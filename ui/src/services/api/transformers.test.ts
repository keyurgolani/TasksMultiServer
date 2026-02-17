/**
 * Property-based tests for data transformers.
 * Tests round-trip consistency between API and frontend formats.
 * 
 * **Feature: refreshui-api-integration, Property 4: Data Transformation Round-Trip Consistency**
 * **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**
 */

import { describe, it, expect } from 'vitest';
import fc from 'fast-check';

import {
  transformProject,
  transformTaskList,
  transformTask,
  transformProjectStats,
  transformTaskListStats,
  toApiProject,
  toApiTaskList,
  toApiTask,
  toApiProjectStats,
  toApiTaskListStats,
} from './transformers';

import type {
  ApiProject,
  ApiTaskList,
  ApiTask,
  ApiProjectStats,
  ApiTaskListStats,
} from './types';

// ============================================================================
// Arbitraries (Generators) for API types
// ============================================================================

// Use a simpler approach for ISO date strings to avoid invalid date issues
const isoDateArb = fc.tuple(
  fc.integer({ min: 2020, max: 2030 }),
  fc.integer({ min: 1, max: 12 }),
  fc.integer({ min: 1, max: 28 }), // Use 28 to avoid month-day issues
  fc.integer({ min: 0, max: 23 }),
  fc.integer({ min: 0, max: 59 }),
  fc.integer({ min: 0, max: 59 })
).map(([year, month, day, hour, min, sec]) => {
  const d = new Date(Date.UTC(year, month - 1, day, hour, min, sec));
  return d.toISOString();
});

const uuidArb = fc.uuid();

const apiProjectArb: fc.Arbitrary<ApiProject> = fc.record({
  id: uuidArb,
  name: fc.string({ minLength: 1, maxLength: 100 }),
  is_default: fc.boolean(),
  agent_instructions_template: fc.option(fc.string(), { nil: null }),
  created_at: isoDateArb,
  updated_at: isoDateArb,
});

const apiTaskListArb: fc.Arbitrary<ApiTaskList> = fc.record({
  id: uuidArb,
  name: fc.string({ minLength: 1, maxLength: 100 }),
  project_id: uuidArb,
  agent_instructions_template: fc.option(fc.string(), { nil: null }),
  created_at: isoDateArb,
  updated_at: isoDateArb,
});

const apiDependencyArb = fc.record({
  task_id: uuidArb,
  task_list_id: uuidArb,
});

const apiExitCriteriaArb = fc.record({
  criteria: fc.string({ minLength: 1, maxLength: 200 }),
  status: fc.constantFrom('INCOMPLETE', 'COMPLETE'),
  comment: fc.option(fc.string(), { nil: null }),
});

const apiNoteArb = fc.record({
  content: fc.string({ minLength: 1, maxLength: 500 }),
  timestamp: isoDateArb,
});

const apiActionPlanItemArb = fc.record({
  sequence: fc.nat({ max: 100 }),
  content: fc.string({ minLength: 1, maxLength: 200 }),
});

const apiTaskArb: fc.Arbitrary<ApiTask> = fc.record({
  id: uuidArb,
  task_list_id: uuidArb,
  title: fc.string({ minLength: 1, maxLength: 100 }),
  description: fc.string({ maxLength: 500 }),
  status: fc.constantFrom('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'BLOCKED'),
  priority: fc.constantFrom('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'TRIVIAL'),
  dependencies: fc.array(apiDependencyArb, { maxLength: 5 }),
  exit_criteria: fc.array(apiExitCriteriaArb, { minLength: 1, maxLength: 5 }),
  notes: fc.array(apiNoteArb, { maxLength: 5 }),
  research_notes: fc.option(fc.array(apiNoteArb, { maxLength: 3 }), { nil: null }),
  action_plan: fc.option(fc.array(apiActionPlanItemArb, { maxLength: 5 }), { nil: null }),
  execution_notes: fc.option(fc.array(apiNoteArb, { maxLength: 3 }), { nil: null }),
  agent_instructions_template: fc.option(fc.string(), { nil: null }),
  tags: fc.array(fc.string({ minLength: 1, maxLength: 30 }), { maxLength: 5 }),
  created_at: isoDateArb,
  updated_at: isoDateArb,
});

const apiProjectStatsArb: fc.Arbitrary<ApiProjectStats> = fc.record({
  task_list_count: fc.nat({ max: 100 }),
  total_tasks: fc.nat({ max: 1000 }),
  ready_tasks: fc.nat({ max: 500 }),
  completed_tasks: fc.nat({ max: 500 }),
  in_progress_tasks: fc.nat({ max: 500 }),
  blocked_tasks: fc.nat({ max: 500 }),
});

const apiTaskListStatsArb: fc.Arbitrary<ApiTaskListStats> = fc.record({
  task_count: fc.nat({ max: 100 }),
  ready_tasks: fc.nat({ max: 50 }),
  completed_tasks: fc.nat({ max: 50 }),
  in_progress_tasks: fc.nat({ max: 50 }),
  blocked_tasks: fc.nat({ max: 50 }),
  completion_percentage: fc.integer({ min: 0, max: 100 }),
});

// ============================================================================
// Property Tests
// ============================================================================

describe('Data Transformation Round-Trip', () => {
  /**
   * **Feature: refreshui-api-integration, Property 4: Data Transformation Round-Trip Consistency**
   * **Validates: Requirements 9.1**
   * 
   * For any valid API project response, transforming it to frontend format
   * and then back to API format should produce an equivalent object
   * (accounting for fields not tracked by frontend).
   */
  describe('Project transformation', () => {
    it('should preserve core fields through round-trip', () => {
      fc.assert(
        fc.property(apiProjectArb, (apiProject) => {
          const frontend = transformProject(apiProject);
          const backToApi = toApiProject(frontend);

          // Core fields should be preserved
          expect(backToApi.id).toBe(apiProject.id);
          expect(backToApi.name).toBe(apiProject.name);
          expect(backToApi.created_at).toBe(apiProject.created_at);
          expect(backToApi.updated_at).toBe(apiProject.updated_at);
        }),
        { numRuns: 100 }
      );
    });

    it('should correctly transform snake_case to camelCase', () => {
      fc.assert(
        fc.property(apiProjectArb, (apiProject) => {
          const frontend = transformProject(apiProject);

          expect(frontend.createdAt).toBe(apiProject.created_at);
          expect(frontend.updatedAt).toBe(apiProject.updated_at);
        }),
        { numRuns: 100 }
      );
    });
  });

  /**
   * **Feature: refreshui-api-integration, Property 4: Data Transformation Round-Trip Consistency**
   * **Validates: Requirements 9.2**
   */
  describe('TaskList transformation', () => {
    it('should preserve core fields through round-trip', () => {
      fc.assert(
        fc.property(apiTaskListArb, (apiTaskList) => {
          const frontend = transformTaskList(apiTaskList);
          const backToApi = toApiTaskList(frontend);

          expect(backToApi.id).toBe(apiTaskList.id);
          expect(backToApi.name).toBe(apiTaskList.name);
          expect(backToApi.project_id).toBe(apiTaskList.project_id);
          expect(backToApi.created_at).toBe(apiTaskList.created_at);
          expect(backToApi.updated_at).toBe(apiTaskList.updated_at);
        }),
        { numRuns: 100 }
      );
    });

    it('should correctly transform project_id to projectId', () => {
      fc.assert(
        fc.property(apiTaskListArb, (apiTaskList) => {
          const frontend = transformTaskList(apiTaskList);

          expect(frontend.projectId).toBe(apiTaskList.project_id);
        }),
        { numRuns: 100 }
      );
    });
  });

  /**
   * **Feature: refreshui-api-integration, Property 4: Data Transformation Round-Trip Consistency**
   * **Validates: Requirements 9.3, 9.4**
   */
  describe('Task transformation', () => {
    it('should preserve core fields through round-trip', () => {
      fc.assert(
        fc.property(apiTaskArb, (apiTask) => {
          const frontend = transformTask(apiTask);
          const backToApi = toApiTask(frontend);

          expect(backToApi.id).toBe(apiTask.id);
          expect(backToApi.task_list_id).toBe(apiTask.task_list_id);
          expect(backToApi.title).toBe(apiTask.title);
          expect(backToApi.description).toBe(apiTask.description);
          expect(backToApi.status).toBe(apiTask.status);
          expect(backToApi.priority).toBe(apiTask.priority);
          expect(backToApi.tags).toEqual(apiTask.tags);
          expect(backToApi.created_at).toBe(apiTask.created_at);
          expect(backToApi.updated_at).toBe(apiTask.updated_at);
        }),
        { numRuns: 100 }
      );
    });

    it('should correctly transform task_list_id to taskListId', () => {
      fc.assert(
        fc.property(apiTaskArb, (apiTask) => {
          const frontend = transformTask(apiTask);

          expect(frontend.taskListId).toBe(apiTask.task_list_id);
        }),
        { numRuns: 100 }
      );
    });

    it('should correctly transform dependencies', () => {
      fc.assert(
        fc.property(apiTaskArb, (apiTask) => {
          const frontend = transformTask(apiTask);

          expect(frontend.dependencies.length).toBe(apiTask.dependencies.length);
          for (let i = 0; i < apiTask.dependencies.length; i++) {
            expect(frontend.dependencies[i].taskId).toBe(apiTask.dependencies[i].task_id);
            expect(frontend.dependencies[i].taskListId).toBe(apiTask.dependencies[i].task_list_id);
          }
        }),
        { numRuns: 100 }
      );
    });

    it('should correctly transform exit_criteria to exitCriteria', () => {
      fc.assert(
        fc.property(apiTaskArb, (apiTask) => {
          const frontend = transformTask(apiTask);

          expect(frontend.exitCriteria.length).toBe(apiTask.exit_criteria.length);
          for (let i = 0; i < apiTask.exit_criteria.length; i++) {
            expect(frontend.exitCriteria[i].criteria).toBe(apiTask.exit_criteria[i].criteria);
            expect(frontend.exitCriteria[i].status).toBe(apiTask.exit_criteria[i].status);
          }
        }),
        { numRuns: 100 }
      );
    });

    it('should correctly transform notes arrays', () => {
      fc.assert(
        fc.property(apiTaskArb, (apiTask) => {
          const frontend = transformTask(apiTask);

          // Regular notes
          expect(frontend.notes.length).toBe(apiTask.notes.length);
          
          // Research notes (null becomes empty array)
          const expectedResearchLength = apiTask.research_notes?.length ?? 0;
          expect(frontend.researchNotes.length).toBe(expectedResearchLength);
          
          // Execution notes (null becomes empty array)
          const expectedExecutionLength = apiTask.execution_notes?.length ?? 0;
          expect(frontend.executionNotes.length).toBe(expectedExecutionLength);
        }),
        { numRuns: 100 }
      );
    });

    it('should correctly transform action_plan to actionPlan', () => {
      fc.assert(
        fc.property(apiTaskArb, (apiTask) => {
          const frontend = transformTask(apiTask);

          if (apiTask.action_plan === null) {
            expect(frontend.actionPlan).toBeUndefined();
          } else {
            expect(frontend.actionPlan?.length).toBe(apiTask.action_plan.length);
            for (let i = 0; i < apiTask.action_plan.length; i++) {
              expect(frontend.actionPlan![i].sequence).toBe(apiTask.action_plan[i].sequence);
              expect(frontend.actionPlan![i].content).toBe(apiTask.action_plan[i].content);
            }
          }
        }),
        { numRuns: 100 }
      );
    });
  });

  /**
   * **Feature: refreshui-api-integration, Property 4: Data Transformation Round-Trip Consistency**
   * **Validates: Requirements 9.5**
   */
  describe('Statistics transformation', () => {
    it('should preserve ProjectStats through round-trip', () => {
      fc.assert(
        fc.property(apiProjectStatsArb, (apiStats) => {
          const frontend = transformProjectStats(apiStats);
          const backToApi = toApiProjectStats(frontend);

          expect(backToApi.task_list_count).toBe(apiStats.task_list_count);
          expect(backToApi.total_tasks).toBe(apiStats.total_tasks);
          expect(backToApi.ready_tasks).toBe(apiStats.ready_tasks);
          expect(backToApi.completed_tasks).toBe(apiStats.completed_tasks);
          expect(backToApi.in_progress_tasks).toBe(apiStats.in_progress_tasks);
          expect(backToApi.blocked_tasks).toBe(apiStats.blocked_tasks);
        }),
        { numRuns: 100 }
      );
    });

    it('should correctly transform snake_case stats to camelCase', () => {
      fc.assert(
        fc.property(apiProjectStatsArb, (apiStats) => {
          const frontend = transformProjectStats(apiStats);

          expect(frontend.taskListCount).toBe(apiStats.task_list_count);
          expect(frontend.totalTasks).toBe(apiStats.total_tasks);
          expect(frontend.readyTasks).toBe(apiStats.ready_tasks);
          expect(frontend.completedTasks).toBe(apiStats.completed_tasks);
          expect(frontend.inProgressTasks).toBe(apiStats.in_progress_tasks);
          expect(frontend.blockedTasks).toBe(apiStats.blocked_tasks);
        }),
        { numRuns: 100 }
      );
    });

    it('should preserve TaskListStats through round-trip', () => {
      fc.assert(
        fc.property(apiTaskListStatsArb, (apiStats) => {
          const frontend = transformTaskListStats(apiStats);
          const backToApi = toApiTaskListStats(frontend);

          expect(backToApi.task_count).toBe(apiStats.task_count);
          expect(backToApi.ready_tasks).toBe(apiStats.ready_tasks);
          expect(backToApi.completed_tasks).toBe(apiStats.completed_tasks);
          expect(backToApi.in_progress_tasks).toBe(apiStats.in_progress_tasks);
          expect(backToApi.blocked_tasks).toBe(apiStats.blocked_tasks);
          expect(backToApi.completion_percentage).toBe(apiStats.completion_percentage);
        }),
        { numRuns: 100 }
      );
    });

    it('should correctly transform snake_case task list stats to camelCase', () => {
      fc.assert(
        fc.property(apiTaskListStatsArb, (apiStats) => {
          const frontend = transformTaskListStats(apiStats);

          expect(frontend.taskCount).toBe(apiStats.task_count);
          expect(frontend.readyTasks).toBe(apiStats.ready_tasks);
          expect(frontend.completedTasks).toBe(apiStats.completed_tasks);
          expect(frontend.inProgressTasks).toBe(apiStats.in_progress_tasks);
          expect(frontend.blockedTasks).toBe(apiStats.blocked_tasks);
          expect(frontend.completionPercentage).toBe(apiStats.completion_percentage);
        }),
        { numRuns: 100 }
      );
    });
  });
});
