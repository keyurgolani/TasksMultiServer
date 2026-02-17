import { describe, it, expect } from 'vitest';
import { MockDataGenerator, generateMockData } from './MockDataGenerator';

describe('MockDataGenerator', () => {
  describe('generate()', () => {
    it('should generate 15 projects', () => {
      const generator = new MockDataGenerator();
      const data = generator.generate();

      expect(data.projects).toHaveLength(15);
    });

    it('should generate 35 task lists', () => {
      const generator = new MockDataGenerator();
      const data = generator.generate();

      expect(data.taskLists).toHaveLength(35);
    });

    it('should distribute task lists across all projects', () => {
      const generator = new MockDataGenerator();
      const data = generator.generate();

      // Each project should have at least 1 task list
      const projectIds = new Set(data.projects.map((p) => p.id));
      const taskListProjectIds = new Set(data.taskLists.map((tl) => tl.projectId));

      // All task lists should belong to valid projects
      for (const projectId of taskListProjectIds) {
        expect(projectIds.has(projectId)).toBe(true);
      }

      // Each project should have at least one task list
      for (const projectId of projectIds) {
        const taskListsForProject = data.taskLists.filter(
          (tl) => tl.projectId === projectId
        );
        expect(taskListsForProject.length).toBeGreaterThanOrEqual(1);
      }
    });

    it('should generate tasks for each task list', () => {
      const generator = new MockDataGenerator();
      const data = generator.generate();

      // Each task list should have between 2-8 tasks
      const taskListIds = new Set(data.taskLists.map((tl) => tl.id));

      for (const taskListId of taskListIds) {
        const tasksForList = data.tasks.filter((t) => t.taskListId === taskListId);
        expect(tasksForList.length).toBeGreaterThanOrEqual(2);
        expect(tasksForList.length).toBeLessThanOrEqual(8);
      }
    });

    it('should generate tasks with varied statuses', () => {
      const generator = new MockDataGenerator();
      const data = generator.generate();

      const statuses = new Set(data.tasks.map((t) => t.status));

      // Should have multiple different statuses
      expect(statuses.size).toBeGreaterThan(1);

      // Should include the main statuses
      const allStatuses = ['NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'BLOCKED'];
      const hasVariedStatuses = allStatuses.some((s) => statuses.has(s as typeof data.tasks[0]['status']));
      expect(hasVariedStatuses).toBe(true);
    });

    it('should generate tasks with varied priorities', () => {
      const generator = new MockDataGenerator();
      const data = generator.generate();

      const priorities = new Set(data.tasks.map((t) => t.priority));

      // Should have multiple different priorities
      expect(priorities.size).toBeGreaterThan(1);
    });

    it('should generate valid project entities', () => {
      const generator = new MockDataGenerator();
      const data = generator.generate();

      for (const project of data.projects) {
        expect(project.id).toBeDefined();
        expect(project.name).toBeDefined();
        expect(project.createdAt).toBeDefined();
        expect(project.updatedAt).toBeDefined();
        expect(new Date(project.createdAt).getTime()).toBeLessThanOrEqual(
          new Date(project.updatedAt).getTime()
        );
      }
    });

    it('should generate valid task list entities', () => {
      const generator = new MockDataGenerator();
      const data = generator.generate();

      for (const taskList of data.taskLists) {
        expect(taskList.id).toBeDefined();
        expect(taskList.projectId).toBeDefined();
        expect(taskList.name).toBeDefined();
        expect(taskList.createdAt).toBeDefined();
        expect(taskList.updatedAt).toBeDefined();
      }
    });

    it('should generate valid task entities', () => {
      const generator = new MockDataGenerator();
      const data = generator.generate();

      for (const task of data.tasks) {
        expect(task.id).toBeDefined();
        expect(task.taskListId).toBeDefined();
        expect(task.title).toBeDefined();
        expect(task.status).toBeDefined();
        expect(task.priority).toBeDefined();
        expect(task.dependencies).toBeDefined();
        expect(task.exitCriteria).toBeDefined();
        expect(task.notes).toBeDefined();
        expect(task.tags).toBeDefined();
        expect(task.createdAt).toBeDefined();
        expect(task.updatedAt).toBeDefined();
      }
    });

    it('should generate tasks with exit criteria', () => {
      const generator = new MockDataGenerator();
      const data = generator.generate();

      // At least some tasks should have exit criteria
      const tasksWithCriteria = data.tasks.filter(
        (t) => t.exitCriteria.length > 0
      );
      expect(tasksWithCriteria.length).toBeGreaterThan(0);
    });

    it('should generate tasks with tags', () => {
      const generator = new MockDataGenerator();
      const data = generator.generate();

      // All tasks should have at least one tag
      for (const task of data.tasks) {
        expect(task.tags.length).toBeGreaterThanOrEqual(1);
      }
    });
  });

  describe('generateMockData()', () => {
    it('should be a convenience function that returns mock data', () => {
      const data = generateMockData();

      expect(data.projects).toHaveLength(15);
      expect(data.taskLists).toHaveLength(35);
      expect(data.tasks.length).toBeGreaterThan(0);
    });
  });
});
