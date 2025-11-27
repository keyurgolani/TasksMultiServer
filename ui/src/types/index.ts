// Enums
export enum Status {
  NOT_STARTED = 'NOT_STARTED',
  IN_PROGRESS = 'IN_PROGRESS',
  BLOCKED = 'BLOCKED',
  COMPLETED = 'COMPLETED',
}

export enum Priority {
  CRITICAL = 'CRITICAL',
  HIGH = 'HIGH',
  MEDIUM = 'MEDIUM',
  LOW = 'LOW',
  TRIVIAL = 'TRIVIAL',
}

export enum ExitCriteriaStatus {
  INCOMPLETE = 'INCOMPLETE',
  COMPLETE = 'COMPLETE',
}

export enum NoteType {
  GENERAL = 'GENERAL',
  RESEARCH = 'RESEARCH',
  EXECUTION = 'EXECUTION',
}

// Core entities
export interface Project {
  id: string;
  name: string;
  is_default: boolean;
  agent_instructions_template?: string;
  created_at: string;
  updated_at: string;
}

export interface TaskList {
  id: string;
  name: string;
  project_id: string;
  agent_instructions_template?: string;
  created_at: string;
  updated_at: string;
}

export interface Dependency {
  task_id: string;
  task_list_id: string;
}

export interface ExitCriteria {
  criteria: string;
  status: ExitCriteriaStatus;
  comment?: string;
}

export interface Note {
  content: string;
  timestamp: string;
}

export interface ActionPlanItem {
  sequence: number;
  content: string;
}

export interface Task {
  id: string;
  task_list_id: string;
  title: string;
  description: string;
  status: Status;
  priority: Priority;
  dependencies: Dependency[];
  exit_criteria: ExitCriteria[];
  notes: Note[];
  research_notes?: Note[];
  action_plan?: ActionPlanItem[];
  execution_notes?: Note[];
  agent_instructions_template?: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

// API Error response
export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}
