export interface Project {
  id: string;
  name: string;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface TaskList {
  id: string;
  name: string;
  project_id: string;
  created_at: string;
  updated_at: string;
}

export interface ActionPlanItem {
  sequence: number;
  content: string;
}

export interface ExitCriterion {
  sequence: number;
  criteria: string;
  status: 'INCOMPLETE' | 'COMPLETE';
  comment?: string;
}

export interface Note {
  sequence: number;
  content: string;
}

export interface Task {
  id: string;
  task_list_id: string;
  title: string;
  description: string;
  status: 'NOT_STARTED' | 'IN_PROGRESS' | 'BLOCKED' | 'COMPLETED';
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'TRIVIAL';
  tags: string[];
  action_plan?: ActionPlanItem[];
  exit_criteria?: ExitCriterion[];
  notes?: Note[];
  research_notes?: Note[];
  execution_notes?: Note[];
  dependencies?: string[];
  created_at: string;
  updated_at: string;
}

export interface ProjectStats {
  task_list_count: number;
  total_tasks: number;
  ready_tasks: number;
  completed_tasks: number;
}

export interface TaskListStats {
  task_count: number;
  ready_tasks: number;
  completed_tasks: number;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const api = {
  getProjects: async (): Promise<Project[]> => {
    const response = await fetch(`${API_BASE_URL}/projects`);
    if (!response.ok) throw new Error('Failed to fetch projects');
    const data = await response.json();
    return data.projects;
  },

  createProject: async (name: string): Promise<Project> => {
    const response = await fetch(`${API_BASE_URL}/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    });
    if (!response.ok) throw new Error('Failed to create project');
    const data = await response.json();
    return data.project;
  },

  getTaskLists: async (projectId?: string): Promise<TaskList[]> => {
    const url = projectId 
      ? `${API_BASE_URL}/task-lists?project_id=${projectId}`
      : `${API_BASE_URL}/task-lists`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to fetch task lists');
    const data = await response.json();
    return data.task_lists;
  },

  getTasks: async (taskListId?: string): Promise<Task[]> => {
    const url = taskListId
      ? `${API_BASE_URL}/tasks?task_list_id=${taskListId}`
      : `${API_BASE_URL}/tasks`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to fetch tasks');
    const data = await response.json();
    return data.tasks;
  },
  
  createTask: async (task: Partial<Task>): Promise<Task> => {
      const response = await fetch(`${API_BASE_URL}/tasks`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(task)
      });
      if (!response.ok) throw new Error('Failed to create task');
      const data = await response.json();
      return data.task;
  },

  updateTask: async (taskId: string, updates: Partial<Task>): Promise<Task> => {
    const response = await fetch(`${API_BASE_URL}/tasks/${taskId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates)
    });
    if (!response.ok) throw new Error('Failed to update task');
    const data = await response.json();
    return data.task;
  },

  getProjectStats: async (projectId: string): Promise<ProjectStats> => {
    const [taskLists, allTasks] = await Promise.all([
      api.getTaskLists(projectId),
      fetch(`${API_BASE_URL}/tasks`).then(r => r.json()).then(d => d.tasks as Task[])
    ]);
    
    const projectTaskLists = taskLists.filter(tl => tl.project_id === projectId);
    const projectTasks = allTasks.filter(t => 
      projectTaskLists.some(tl => tl.id === t.task_list_id)
    );
    
    return {
      task_list_count: projectTaskLists.length,
      total_tasks: projectTasks.length,
      ready_tasks: projectTasks.filter(t => t.status === 'NOT_STARTED').length,
      completed_tasks: projectTasks.filter(t => t.status === 'COMPLETED').length
    };
  },

  getTaskListStats: async (taskListId: string): Promise<TaskListStats> => {
    const tasks = await api.getTasks(taskListId);
    return {
      task_count: tasks.length,
      ready_tasks: tasks.filter(t => t.status === 'NOT_STARTED').length,
      completed_tasks: tasks.filter(t => t.status === 'COMPLETED').length
    };
  }
};
