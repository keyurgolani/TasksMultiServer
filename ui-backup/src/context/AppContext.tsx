import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { Project, TaskList, Task } from '../types';
import { projectApi, taskListApi, taskApi } from '../api/services';
import { parseApiError, formatErrorMessage, ErrorDetails, ErrorType } from '../utils/errorHandler';

// Notification interface
export interface Notification {
  id: string;
  message: string;
  type: ErrorType | 'success' | 'info';
}

// Context state interface
interface AppState {
  projects: Project[];
  taskLists: TaskList[];
  tasks: Task[];
  selectedProjectId: string | null;
  selectedTaskListId: string | null;
  selectedTaskId: string | null;
  loading: boolean;
  error: string | null;
  notifications: Notification[];
  formError: ErrorDetails | null;
}

// Context actions interface
interface AppContextValue extends AppState {
  // Project actions
  loadProjects: () => Promise<void>;
  createProject: (project: Partial<Project>) => Promise<Project>;
  updateProject: (id: string, project: Partial<Project>) => Promise<Project>;
  deleteProject: (id: string) => Promise<void>;
  selectProject: (id: string | null) => void;

  // TaskList actions
  loadTaskLists: () => Promise<void>;
  createTaskList: (taskList: Partial<TaskList>) => Promise<TaskList>;
  updateTaskList: (id: string, taskList: Partial<TaskList>) => Promise<TaskList>;
  deleteTaskList: (id: string) => Promise<void>;
  resetTaskList: (id: string) => Promise<void>;
  selectTaskList: (id: string | null) => void;

  // Task actions
  loadTasks: () => Promise<void>;
  createTask: (task: Partial<Task>) => Promise<Task>;
  updateTask: (id: string, task: Partial<Task>) => Promise<Task>;
  deleteTask: (id: string) => Promise<void>;
  selectTask: (id: string | null) => void;

  // Utility actions
  setError: (error: string | null) => void;
  clearError: () => void;
  addNotification: (message: string, type: ErrorType | 'success' | 'info') => void;
  removeNotification: (id: string) => void;
  clearFormError: () => void;
}

// Create context with undefined default
const AppContext = createContext<AppContextValue | undefined>(undefined);

// Provider props
interface AppProviderProps {
  children: ReactNode;
}

// Provider component
export const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  const [state, setState] = useState<AppState>({
    projects: [],
    taskLists: [],
    tasks: [],
    selectedProjectId: null,
    selectedTaskListId: null,
    selectedTaskId: null,
    loading: false,
    error: null,
    notifications: [],
    formError: null,
  });

  // Helper to update state
  const updateState = useCallback((updates: Partial<AppState>) => {
    setState((prev) => ({ ...prev, ...updates }));
  }, []);

  // Error handling wrapper
  const withErrorHandling = useCallback(
    async <T,>(operation: () => Promise<T>, showNotification = true): Promise<T> => {
      try {
        updateState({ loading: true, error: null, formError: null });
        const result = await operation();
        updateState({ loading: false });
        return result;
      } catch (error) {
        const errorDetails = parseApiError(error);
        const errorMessage = formatErrorMessage(errorDetails);
        
        // Set form error for validation errors
        if (errorDetails.type === ErrorType.VALIDATION) {
          updateState({ loading: false, formError: errorDetails });
        } else {
          updateState({ loading: false, formError: null });
        }
        
        // Show notification for all errors if enabled
        if (showNotification) {
          const notificationId = Date.now().toString();
          const notification: Notification = {
            id: notificationId,
            message: errorMessage,
            type: errorDetails.type,
          };
          updateState({ notifications: [...state.notifications, notification] });
        }
        
        // Also set global error for critical errors
        if (errorDetails.type === ErrorType.STORAGE || errorDetails.type === ErrorType.NETWORK) {
          updateState({ error: errorMessage });
        }
        
        throw error;
      }
    },
    [updateState, state.notifications]
  );

  // Project actions
  const loadProjects = useCallback(async () => {
    await withErrorHandling(async () => {
      const projects = await projectApi.list();
      updateState({ projects });
    });
  }, [withErrorHandling, updateState]);

  const createProject = useCallback(
    async (project: Partial<Project>) => {
      return withErrorHandling(async () => {
        const newProject = await projectApi.create(project);
        updateState({ projects: [...state.projects, newProject] });
        return newProject;
      });
    },
    [withErrorHandling, updateState, state.projects]
  );

  const updateProject = useCallback(
    async (id: string, project: Partial<Project>) => {
      return withErrorHandling(async () => {
        const updatedProject = await projectApi.update(id, project);
        updateState({
          projects: state.projects.map((p) => (p.id === id ? updatedProject : p)),
        });
        return updatedProject;
      });
    },
    [withErrorHandling, updateState, state.projects]
  );

  const deleteProject = useCallback(
    async (id: string) => {
      await withErrorHandling(async () => {
        await projectApi.delete(id);
        updateState({
          projects: state.projects.filter((p) => p.id !== id),
          selectedProjectId: state.selectedProjectId === id ? null : state.selectedProjectId,
        });
      });
    },
    [withErrorHandling, updateState, state.projects, state.selectedProjectId]
  );

  const selectProject = useCallback(
    (id: string | null) => {
      updateState({ selectedProjectId: id });
    },
    [updateState]
  );

  // TaskList actions
  const loadTaskLists = useCallback(async () => {
    await withErrorHandling(async () => {
      const taskLists = await taskListApi.list();
      updateState({ taskLists });
    });
  }, [withErrorHandling, updateState]);

  const createTaskList = useCallback(
    async (taskList: Partial<TaskList>) => {
      return withErrorHandling(async () => {
        const newTaskList = await taskListApi.create(taskList);
        updateState({ taskLists: [...state.taskLists, newTaskList] });
        return newTaskList;
      });
    },
    [withErrorHandling, updateState, state.taskLists]
  );

  const updateTaskList = useCallback(
    async (id: string, taskList: Partial<TaskList>) => {
      return withErrorHandling(async () => {
        const updatedTaskList = await taskListApi.update(id, taskList);
        updateState({
          taskLists: state.taskLists.map((tl) => (tl.id === id ? updatedTaskList : tl)),
        });
        return updatedTaskList;
      });
    },
    [withErrorHandling, updateState, state.taskLists]
  );

  const deleteTaskList = useCallback(
    async (id: string) => {
      await withErrorHandling(async () => {
        await taskListApi.delete(id);
        updateState({
          taskLists: state.taskLists.filter((tl) => tl.id !== id),
          selectedTaskListId: state.selectedTaskListId === id ? null : state.selectedTaskListId,
        });
      });
    },
    [withErrorHandling, updateState, state.taskLists, state.selectedTaskListId]
  );

  const resetTaskList = useCallback(
    async (id: string) => {
      await withErrorHandling(async () => {
        await taskListApi.reset(id);
        // Reload tasks after reset
        const tasks = await taskApi.list();
        updateState({ tasks });
      });
    },
    [withErrorHandling, updateState]
  );

  const selectTaskList = useCallback(
    (id: string | null) => {
      updateState({ selectedTaskListId: id });
    },
    [updateState]
  );

  // Task actions
  const loadTasks = useCallback(async () => {
    await withErrorHandling(async () => {
      const tasks = await taskApi.list();
      updateState({ tasks });
    });
  }, [withErrorHandling, updateState]);

  const createTask = useCallback(
    async (task: Partial<Task>) => {
      return withErrorHandling(async () => {
        const newTask = await taskApi.create(task);
        updateState({ tasks: [...state.tasks, newTask] });
        return newTask;
      });
    },
    [withErrorHandling, updateState, state.tasks]
  );

  const updateTask = useCallback(
    async (id: string, task: Partial<Task>) => {
      return withErrorHandling(async () => {
        const updatedTask = await taskApi.update(id, task);
        updateState({
          tasks: state.tasks.map((t) => (t.id === id ? updatedTask : t)),
        });
        return updatedTask;
      });
    },
    [withErrorHandling, updateState, state.tasks]
  );

  const deleteTask = useCallback(
    async (id: string) => {
      await withErrorHandling(async () => {
        await taskApi.delete(id);
        updateState({
          tasks: state.tasks.filter((t) => t.id !== id),
          selectedTaskId: state.selectedTaskId === id ? null : state.selectedTaskId,
        });
      });
    },
    [withErrorHandling, updateState, state.tasks, state.selectedTaskId]
  );

  const selectTask = useCallback(
    (id: string | null) => {
      updateState({ selectedTaskId: id });
    },
    [updateState]
  );

  // Utility actions
  const setError = useCallback(
    (error: string | null) => {
      updateState({ error });
    },
    [updateState]
  );

  const clearError = useCallback(() => {
    updateState({ error: null });
  }, [updateState]);

  const addNotification = useCallback(
    (message: string, type: ErrorType | 'success' | 'info') => {
      const notification: Notification = {
        id: Date.now().toString(),
        message,
        type,
      };
      updateState({ notifications: [...state.notifications, notification] });
    },
    [updateState, state.notifications]
  );

  const removeNotification = useCallback(
    (id: string) => {
      updateState({ notifications: state.notifications.filter((n) => n.id !== id) });
    },
    [updateState, state.notifications]
  );

  const clearFormError = useCallback(() => {
    updateState({ formError: null });
  }, [updateState]);

  const value: AppContextValue = {
    ...state,
    loadProjects,
    createProject,
    updateProject,
    deleteProject,
    selectProject,
    loadTaskLists,
    createTaskList,
    updateTaskList,
    deleteTaskList,
    resetTaskList,
    selectTaskList,
    loadTasks,
    createTask,
    updateTask,
    deleteTask,
    selectTask,
    setError,
    clearError,
    addNotification,
    removeNotification,
    clearFormError,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

// Custom hook to use the context
export const useApp = (): AppContextValue => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
