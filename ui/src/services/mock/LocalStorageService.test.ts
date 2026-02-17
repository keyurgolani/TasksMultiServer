/**
 * Tests for LocalStorageService.
 * Verifies CRUD operations, simulated network delay, and data persistence.
 *
 * @module services/mock/LocalStorageService.test
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { LocalStorageService } from './LocalStorageService';
import { ServiceError } from '../types';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] ?? null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      store = {};
    }),
    get length() {
      return Object.keys(store).length;
    },
    key: vi.fn((index: number) => Object.keys(store)[index] ?? null),
  };
})();

Object.defineProperty(globalThis, 'localStorage', {
  value: localStorageMock,
});

describe('LocalStorageService', () => {
  let service: LocalStorageService;

  beforeEach(() => {
    localStorageMock.clear();
    vi.clearAllMocks();
    // Use minimal delay for faster tests
    service = new LocalStorageService({
      mockDelayRange: { min: 1, max: 5 },
      storageKeyPrefix: 'test_db_',
    });
  });

  afterEach(() => {
    service.clearAllData();
  });

  describe('initialization', () => {
    it('should initialize with seed data when localStorage is empty', () => {
      expect(localStorageMock.setItem).toHaveBeenCalled();
      expect(localStorageMock.getItem('test_db_initialized')).toBe('true');
    });

    it('should not reinitialize when data already exists', () => {
      localStorageMock.clear();
      vi.clearAllMocks();
      
      // Set initialized flag
      localStorageMock.setItem('test_db_initialized', 'true');
      
      // Create new service
      new LocalStorageService({
        mockDelayRange: { min: 1, max: 5 },
        storageKeyPrefix: 'test_db_',
      });
      
      // Should not have written projects (only checked initialized flag)
      const projectsCalls = localStorageMock.setItem.mock.calls.filter(
        (call) => call[0] === 'test_db_projects'
      );
      expect(projectsCalls.length).toBe(0);
    });
  });

  describe('delay configuration', () => {
    it('should return configured delay range', () => {
      const range = service.getDelayRange();
      expect(range.min).toBe(1);
      expect(range.max).toBe(5);
    });

    it('should use default delay range when not configured', () => {
      localStorageMock.clear();
      const defaultService = new LocalStorageService({
        storageKeyPrefix: 'default_test_',
      });
      const range = defaultService.getDelayRange();
      expect(range.min).toBe(300);
      expect(range.max).toBe(500);
      defaultService.clearAllData();
    });
  });

  describe('Projects CRUD', () => {
    it('should get all projects', async () => {
      const projects = await service.getProjects();
      expect(Array.isArray(projects)).toBe(true);
      expect(projects.length).toBeGreaterThan(0);
    });

    it('should get a single project by ID', async () => {
      const projects = await service.getProjects();
      const project = await service.getProject(projects[0].id);
      expect(project.id).toBe(projects[0].id);
      expect(project.name).toBe(projects[0].name);
    });

    it('should throw NOT_FOUND for non-existent project', async () => {
      await expect(service.getProject('non-existent-id')).rejects.toThrow(ServiceError);
      try {
        await service.getProject('non-existent-id');
      } catch (error) {
        expect((error as ServiceError).code).toBe('NOT_FOUND');
      }
    });

    it('should create a new project', async () => {
      const newProject = await service.createProject({
        name: 'Test Project',
        description: 'A test project',
      });
      
      expect(newProject.id).toBeDefined();
      expect(newProject.name).toBe('Test Project');
      expect(newProject.description).toBe('A test project');
      expect(newProject.createdAt).toBeDefined();
      expect(newProject.updatedAt).toBeDefined();
      
      // Verify it was persisted
      const retrieved = await service.getProject(newProject.id);
      expect(retrieved.name).toBe('Test Project');
    });

    it('should update an existing project', async () => {
      const projects = await service.getProjects();
      const originalProject = projects[0];
      
      const updated = await service.updateProject(originalProject.id, {
        name: 'Updated Name',
      });
      
      expect(updated.id).toBe(originalProject.id);
      expect(updated.name).toBe('Updated Name');
      expect(new Date(updated.updatedAt).getTime()).toBeGreaterThanOrEqual(
        new Date(originalProject.updatedAt).getTime()
      );
    });

    it('should delete a project and its task lists and tasks', async () => {
      const projects = await service.getProjects();
      const projectId = projects[0].id;
      
      // Get task lists before deletion
      const taskListsBefore = await service.getTaskLists(projectId);
      expect(taskListsBefore.length).toBeGreaterThan(0);
      
      await service.deleteProject(projectId);
      
      // Verify project is deleted
      await expect(service.getProject(projectId)).rejects.toThrow(ServiceError);
      
      // Verify task lists are deleted
      const taskListsAfter = await service.getTaskLists(projectId);
      expect(taskListsAfter.length).toBe(0);
    });

    it('should get project stats', async () => {
      const projects = await service.getProjects();
      const stats = await service.getProjectStats(projects[0].id);
      
      expect(stats.taskListCount).toBeGreaterThanOrEqual(0);
      expect(stats.totalTasks).toBeGreaterThanOrEqual(0);
      expect(stats.readyTasks).toBeGreaterThanOrEqual(0);
      expect(stats.completedTasks).toBeGreaterThanOrEqual(0);
      expect(stats.inProgressTasks).toBeGreaterThanOrEqual(0);
      expect(stats.blockedTasks).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Task Lists CRUD', () => {
    it('should get all task lists', async () => {
      const taskLists = await service.getTaskLists();
      expect(Array.isArray(taskLists)).toBe(true);
      expect(taskLists.length).toBeGreaterThan(0);
    });

    it('should filter task lists by project ID', async () => {
      const projects = await service.getProjects();
      const projectId = projects[0].id;
      
      const taskLists = await service.getTaskLists(projectId);
      expect(taskLists.every((tl) => tl.projectId === projectId)).toBe(true);
    });

    it('should create a new task list', async () => {
      const projects = await service.getProjects();
      
      const newTaskList = await service.createTaskList({
        projectId: projects[0].id,
        name: 'Test Task List',
        description: 'A test task list',
      });
      
      expect(newTaskList.id).toBeDefined();
      expect(newTaskList.name).toBe('Test Task List');
      expect(newTaskList.projectId).toBe(projects[0].id);
    });

    it('should throw NOT_FOUND when creating task list for non-existent project', async () => {
      await expect(
        service.createTaskList({
          projectId: 'non-existent-id',
          name: 'Test',
        })
      ).rejects.toThrow(ServiceError);
    });

    it('should get task list stats', async () => {
      const taskLists = await service.getTaskLists();
      const stats = await service.getTaskListStats(taskLists[0].id);
      
      expect(stats.taskCount).toBeGreaterThanOrEqual(0);
      expect(stats.completionPercentage).toBeGreaterThanOrEqual(0);
      expect(stats.completionPercentage).toBeLessThanOrEqual(100);
    });
  });

  describe('Tasks CRUD', () => {
    it('should get all tasks', async () => {
      const tasks = await service.getTasks();
      expect(Array.isArray(tasks)).toBe(true);
      expect(tasks.length).toBeGreaterThan(0);
    });

    it('should filter tasks by task list ID', async () => {
      const taskLists = await service.getTaskLists();
      const taskListId = taskLists[0].id;
      
      const tasks = await service.getTasks(taskListId);
      expect(tasks.every((t) => t.taskListId === taskListId)).toBe(true);
    });

    it('should create a new task', async () => {
      const taskLists = await service.getTaskLists();
      
      const newTask = await service.createTask({
        taskListId: taskLists[0].id,
        title: 'Test Task',
        description: 'A test task',
        priority: 'HIGH',
      });
      
      expect(newTask.id).toBeDefined();
      expect(newTask.title).toBe('Test Task');
      expect(newTask.status).toBe('NOT_STARTED');
      expect(newTask.priority).toBe('HIGH');
    });

    it('should update a task', async () => {
      const tasks = await service.getTasks();
      const originalTask = tasks[0];
      
      const updated = await service.updateTask(originalTask.id, {
        status: 'IN_PROGRESS',
        title: 'Updated Title',
      });
      
      expect(updated.status).toBe('IN_PROGRESS');
      expect(updated.title).toBe('Updated Title');
    });

    it('should delete a task', async () => {
      const tasks = await service.getTasks();
      const taskId = tasks[0].id;
      
      await service.deleteTask(taskId);
      
      await expect(service.getTask(taskId)).rejects.toThrow(ServiceError);
    });
  });

  describe('Task Notes', () => {
    it('should add a general note to a task', async () => {
      const tasks = await service.getTasks();
      const taskId = tasks[0].id;
      const originalNotesCount = tasks[0].notes.length;
      
      const updated = await service.addNote(taskId, {
        content: 'Test note content',
      });
      
      expect(updated.notes.length).toBe(originalNotesCount + 1);
      expect(updated.notes[updated.notes.length - 1].content).toBe('Test note content');
    });

    it('should add a research note to a task', async () => {
      const tasks = await service.getTasks();
      const taskId = tasks[0].id;
      const originalNotesCount = tasks[0].researchNotes.length;
      
      const updated = await service.addResearchNote(taskId, {
        content: 'Research note content',
      });
      
      expect(updated.researchNotes.length).toBe(originalNotesCount + 1);
    });

    it('should add an execution note to a task', async () => {
      const tasks = await service.getTasks();
      const taskId = tasks[0].id;
      const originalNotesCount = tasks[0].executionNotes.length;
      
      const updated = await service.addExecutionNote(taskId, {
        content: 'Execution note content',
      });
      
      expect(updated.executionNotes.length).toBe(originalNotesCount + 1);
    });
  });

  describe('Search', () => {
    it('should search tasks by text', async () => {
      const tasks = await service.getTasks();
      const searchText = tasks[0].title.substring(0, 5);
      
      const results = await service.searchTasks({ text: searchText });
      
      expect(results.items.length).toBeGreaterThan(0);
      expect(
        results.items.some(
          (t) =>
            t.title.toLowerCase().includes(searchText.toLowerCase()) ||
            t.description?.toLowerCase().includes(searchText.toLowerCase())
        )
      ).toBe(true);
    });

    it('should filter tasks by status', async () => {
      const results = await service.searchTasks({
        status: ['COMPLETED'],
      });
      
      expect(results.items.every((t) => t.status === 'COMPLETED')).toBe(true);
    });

    it('should filter tasks by priority', async () => {
      const results = await service.searchTasks({
        priority: ['HIGH', 'CRITICAL'],
      });
      
      expect(
        results.items.every((t) => t.priority === 'HIGH' || t.priority === 'CRITICAL')
      ).toBe(true);
    });

    it('should paginate results', async () => {
      const allResults = await service.searchTasks({ limit: 100 });
      const firstPage = await service.searchTasks({ limit: 5, offset: 0 });
      const secondPage = await service.searchTasks({ limit: 5, offset: 5 });
      
      expect(firstPage.items.length).toBeLessThanOrEqual(5);
      expect(firstPage.total).toBe(allResults.total);
      expect(firstPage.offset).toBe(0);
      
      if (allResults.total > 5) {
        expect(secondPage.offset).toBe(5);
        expect(firstPage.items[0].id).not.toBe(secondPage.items[0]?.id);
      }
    });

    it('should sort results', async () => {
      const ascResults = await service.searchTasks({
        sortBy: 'title',
        sortOrder: 'asc',
      });
      
      const descResults = await service.searchTasks({
        sortBy: 'title',
        sortOrder: 'desc',
      });
      
      if (ascResults.items.length > 1) {
        expect(ascResults.items[0].title.localeCompare(ascResults.items[1].title)).toBeLessThanOrEqual(0);
      }
      
      if (descResults.items.length > 1) {
        expect(descResults.items[0].title.localeCompare(descResults.items[1].title)).toBeGreaterThanOrEqual(0);
      }
    });
  });

  describe('Ready Tasks', () => {
    it('should get ready tasks for a project', async () => {
      const projects = await service.getProjects();
      const readyTasks = await service.getReadyTasks({
        type: 'project',
        id: projects[0].id,
      });
      
      expect(Array.isArray(readyTasks)).toBe(true);
      // Ready tasks should not be COMPLETED or BLOCKED
      expect(
        readyTasks.every((t) => t.status !== 'COMPLETED' && t.status !== 'BLOCKED')
      ).toBe(true);
    });

    it('should get ready tasks for a task list', async () => {
      const taskLists = await service.getTaskLists();
      const readyTasks = await service.getReadyTasks({
        type: 'taskList',
        id: taskLists[0].id,
      });
      
      expect(Array.isArray(readyTasks)).toBe(true);
    });
  });

  describe('Data Persistence', () => {
    it('should persist data to localStorage with correct prefix', async () => {
      await service.createProject({ name: 'Persistence Test' });
      
      const storedData = localStorageMock.getItem('test_db_projects');
      expect(storedData).toBeDefined();
      expect(storedData).toContain('Persistence Test');
    });

    it('should serialize and deserialize data correctly', async () => {
      const created = await service.createProject({
        name: 'Serialization Test',
        description: 'Testing JSON serialization',
      });
      
      // Clear service cache by creating new instance
      const newService = new LocalStorageService({
        mockDelayRange: { min: 1, max: 5 },
        storageKeyPrefix: 'test_db_',
      });
      
      const retrieved = await newService.getProject(created.id);
      expect(retrieved.name).toBe(created.name);
      expect(retrieved.description).toBe(created.description);
      expect(retrieved.createdAt).toBe(created.createdAt);
    });
  });

  describe('Utility Methods', () => {
    it('should clear all data', async () => {
      const projectsBefore = await service.getProjects();
      expect(projectsBefore.length).toBeGreaterThan(0);
      
      service.clearAllData();
      
      // After clearing, localStorage should be empty for our keys
      expect(localStorageMock.getItem('test_db_projects')).toBeNull();
      expect(localStorageMock.getItem('test_db_initialized')).toBeNull();
    });

    it('should reset to seed data', async () => {
      // Create a custom project
      await service.createProject({ name: 'Custom Project' });
      
      // Reset
      service.resetToSeedData();
      
      // Should have seed data again
      const projects = await service.getProjects();
      expect(projects.some((p) => p.name === 'Custom Project')).toBe(false);
      expect(projects.length).toBe(15); // Default seed count
    });
  });
});
