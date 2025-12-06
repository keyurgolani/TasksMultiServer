import React, { useState, useEffect, useCallback, useMemo } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useDataService } from "../../context/DataServiceContext";
import { DeleteConfirmationDialog } from "../../components/organisms/DeleteConfirmationDialog";
import { TaskCard } from "../../components/organisms/TaskCard";
import { Typography } from "../../components/atoms/Typography";
import { Button } from "../../components/atoms/Button";
import { Badge, type BadgeVariant } from "../../components/atoms/Badge";
import { Icon } from "../../components/atoms/Icon";
import { Input } from "../../components/atoms/Input";
import { Skeleton } from "../../components/atoms/Skeleton";
import { StatusIndicator, type StatusType } from "../../components/molecules/StatusIndicator";
import { cn } from "../../lib/utils";
import type {
  Task,
  TaskStatus,
  TaskPriority,
  ExitCriterion,
  Note,
  TaskDependency,
  ActionPlanItem,
} from "../../core/types/entities";
import type { UpdateTaskDto } from "../../services/types";

/**
 * SingleTaskView Component
 *
 * A view component for displaying and editing a single task's details.
 * Provides back navigation, view/edit mode display, and edit/delete buttons.
 *
 * Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6
 * - 8.1: Display a back navigation button to return to the previous screen
 * - 8.2: Display the task information in view mode by default
 * - 8.3: Switch to edit mode allowing field modifications when edit button is clicked
 * - 8.4: Persist the changes and return to view mode when save is clicked
 * - 8.5: Discard changes and return to view mode when cancel is clicked
 * - 8.6: Display edit and delete buttons for the task
 */

export interface SingleTaskViewProps {
  /** Task ID from route params (optional, can also use useParams) */
  taskId?: string;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Editable task fields for edit mode
 */
interface EditableTaskFields {
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  tags: string[];
  exitCriteria: ExitCriterion[];
  dependencies: TaskDependency[];
  actionPlan: ActionPlanItem[];
}

/**
 * Available task status options
 */
const TASK_STATUS_OPTIONS: { value: TaskStatus; label: string }[] = [
  { value: "NOT_STARTED", label: "Not Started" },
  { value: "IN_PROGRESS", label: "In Progress" },
  { value: "COMPLETED", label: "Completed" },
  { value: "BLOCKED", label: "Blocked" },
];

/**
 * Available task priority options
 */
const TASK_PRIORITY_OPTIONS: { value: TaskPriority; label: string }[] = [
  { value: "CRITICAL", label: "Critical" },
  { value: "HIGH", label: "High" },
  { value: "MEDIUM", label: "Medium" },
  { value: "LOW", label: "Low" },
  { value: "TRIVIAL", label: "Trivial" },
];

/**
 * Maps TaskStatus to StatusIndicator status type
 */
const mapTaskStatusToIndicator = (status: TaskStatus): StatusType => {
  const statusMap: Record<TaskStatus, StatusType> = {
    NOT_STARTED: "not_started",
    IN_PROGRESS: "in_progress",
    COMPLETED: "completed",
    BLOCKED: "blocked",
  };
  return statusMap[status];
};

/**
 * Maps TaskPriority to Badge variant
 */
const mapPriorityToVariant = (priority: TaskPriority): BadgeVariant => {
  const priorityMap: Record<TaskPriority, BadgeVariant> = {
    CRITICAL: "error",
    HIGH: "warning",
    MEDIUM: "info",
    LOW: "neutral",
    TRIVIAL: "neutral",
  };
  return priorityMap[priority];
};

/**
 * Formats priority text for display
 */
const formatPriority = (priority: TaskPriority): string => {
  return priority.charAt(0) + priority.slice(1).toLowerCase();
};

/**
 * Formats status text for display
 */
const formatStatus = (status: TaskStatus): string => {
  return status.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
};

/**
 * Formats a date string for display
 */
const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
};

/**
 * Note type for combined notes display
 */
type NoteWithType = Note & { type: "general" | "research" | "execution" };

/**
 * SingleTaskView component
 */
export const SingleTaskView: React.FC<SingleTaskViewProps> = ({
  taskId: propTaskId,
  className,
}) => {
  const navigate = useNavigate();
  const params = useParams<{ taskId: string }>();
  const { dataService } = useDataService();

  // Get task ID from props or route params
  const taskId = propTaskId || params.taskId;

  // State
  const [task, setTask] = useState<Task | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Edit mode state - Requirements: 8.3, 8.4, 8.5
  const [isEditMode, setIsEditMode] = useState(false);
  const [editedFields, setEditedFields] = useState<EditableTaskFields | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [tagInput, setTagInput] = useState("");

  // Dependencies state - Requirements: 8.9, 20.1, 20.2, 20.3, 20.4, 20.5
  const [availableTasks, setAvailableTasks] = useState<Task[]>([]);
  const [taskLists, setTaskLists] = useState<{ id: string; name: string }[]>([]);
  const [loadingTasks, setLoadingTasks] = useState(false);
  const [dependencySearchQuery, setDependencySearchQuery] = useState<string>("");

  // Notes state - Requirements: 8.10, 8.11, 8.12
  const [newExecutionNote, setNewExecutionNote] = useState("");
  const [newGeneralNote, setNewGeneralNote] = useState("");
  const [newResearchNote, setNewResearchNote] = useState("");
  const [isAddingNote, setIsAddingNote] = useState(false);

  // Action plan state - Requirements: 8.13
  const [newActionPlanItem, setNewActionPlanItem] = useState("");

  // Modal state
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  /**
   * Load task data
   */
  const loadTaskData = useCallback(async () => {
    if (!taskId) {
      setError("Task ID is required");
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const loadedTask = await dataService.getTask(taskId);
      setTask(loadedTask);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load task");
    } finally {
      setIsLoading(false);
    }
  }, [dataService, taskId]);

  // Load task data on mount
  useEffect(() => {
    loadTaskData();
  }, [loadTaskData]);

  /**
   * Load available tasks and task lists for dependency selection
   * Requirements: 8.9, 20.5 - Allow adding and managing task dependencies with task list names
   */
  const loadAvailableTasks = useCallback(async () => {
    setLoadingTasks(true);
    try {
      const [tasks, lists] = await Promise.all([
        dataService.getTasks(),
        dataService.getTaskLists(),
      ]);
      setAvailableTasks(tasks);
      setTaskLists(lists.map(tl => ({ id: tl.id, name: tl.name })));
    } catch (err) {
      console.error("Failed to load available tasks:", err);
    } finally {
      setLoadingTasks(false);
    }
  }, [dataService]);

  // Load available tasks when entering edit mode or when task has dependencies
  // This ensures dependency TaskCards can be rendered in view mode
  useEffect(() => {
    if (isEditMode || (task && task.dependencies && task.dependencies.length > 0)) {
      loadAvailableTasks();
    }
  }, [isEditMode, task, loadAvailableTasks]);

  /**
   * Handle back navigation
   * Requirements: 8.1 - Display a back navigation button to return to the previous screen
   */
  const handleBackClick = useCallback(() => {
    navigate(-1);
  }, [navigate]);

  /**
   * Handle edit button click
   * Requirements: 8.3 - Switch to edit mode allowing field modifications
   */
  const handleEditClick = useCallback(() => {
    if (!task) return;
    
    // Initialize editable fields with current task values
    setEditedFields({
      title: task.title,
      description: task.description || "",
      status: task.status,
      priority: task.priority,
      tags: [...task.tags],
      exitCriteria: task.exitCriteria.map(ec => ({ ...ec })),
      dependencies: task.dependencies.map(dep => ({ ...dep })),
      actionPlan: (task.actionPlan || []).map(item => ({ ...item })),
    });
    setSaveError(null);
    setDependencySearchQuery("");
    setNewActionPlanItem("");
    setIsEditMode(true);
  }, [task]);

  /**
   * Handle cancel button click in edit mode
   * Requirements: 8.5 - Discard changes and return to view mode
   */
  const handleCancelEdit = useCallback(() => {
    setEditedFields(null);
    setSaveError(null);
    setTagInput("");
    setDependencySearchQuery("");
    setNewExecutionNote("");
    setNewGeneralNote("");
    setNewResearchNote("");
    setNewActionPlanItem("");
    setIsEditMode(false);
  }, []);

  /**
   * Handle save button click in edit mode
   * Requirements: 8.4 - Persist the changes and return to view mode
   */
  const handleSaveEdit = useCallback(async () => {
    if (!taskId || !editedFields) return;

    // Validate required fields
    if (!editedFields.title.trim()) {
      setSaveError("Title is required");
      return;
    }

    setIsSaving(true);
    setSaveError(null);

    try {
      const updateData: UpdateTaskDto = {
        title: editedFields.title.trim(),
        description: editedFields.description.trim() || undefined,
        status: editedFields.status,
        priority: editedFields.priority,
        tags: editedFields.tags,
        exitCriteria: editedFields.exitCriteria,
        dependencies: editedFields.dependencies,
        actionPlan: editedFields.actionPlan,
      };

      const updatedTask = await dataService.updateTask(taskId, updateData);
      setTask(updatedTask);
      setEditedFields(null);
      setTagInput("");
      setIsEditMode(false);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Failed to save changes");
    } finally {
      setIsSaving(false);
    }
  }, [taskId, editedFields, dataService]);

  /**
   * Handle field change in edit mode
   */
  const handleFieldChange = useCallback(<K extends keyof EditableTaskFields>(
    field: K,
    value: EditableTaskFields[K]
  ) => {
    setEditedFields(prev => prev ? { ...prev, [field]: value } : null);
    setSaveError(null);
  }, []);

  /**
   * Handle adding a tag
   */
  const handleAddTag = useCallback(() => {
    const trimmedTag = tagInput.trim();
    if (!trimmedTag || !editedFields) return;
    
    if (!editedFields.tags.includes(trimmedTag)) {
      handleFieldChange("tags", [...editedFields.tags, trimmedTag]);
    }
    setTagInput("");
  }, [tagInput, editedFields, handleFieldChange]);

  /**
   * Handle removing a tag
   */
  const handleRemoveTag = useCallback((tagToRemove: string) => {
    if (!editedFields) return;
    handleFieldChange("tags", editedFields.tags.filter(tag => tag !== tagToRemove));
  }, [editedFields, handleFieldChange]);

  /**
   * Handle tag input key press
   */
  const handleTagKeyPress = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAddTag();
    }
  }, [handleAddTag]);

  /**
   * Handle exit criterion status toggle in edit mode
   */
  const handleExitCriterionToggle = useCallback((index: number) => {
    if (!editedFields) return;
    
    const newCriteria = [...editedFields.exitCriteria];
    newCriteria[index] = {
      ...newCriteria[index],
      status: newCriteria[index].status === "COMPLETE" ? "INCOMPLETE" : "COMPLETE",
    };
    handleFieldChange("exitCriteria", newCriteria);
  }, [editedFields, handleFieldChange]);

  /**
   * Check if a task is selected as a dependency
   * Requirements: 20.3 - Add checkbox or click-to-select for adding dependencies
   */
  const isDependencySelected = useCallback((taskToCheck: Task): boolean => {
    if (!editedFields) return false;
    return editedFields.dependencies.some(dep => dep.taskId === taskToCheck.id);
  }, [editedFields]);

  /**
   * Toggle a dependency selection
   * Requirements: 8.9, 20.3 - Allow adding and managing task dependencies
   */
  const toggleDependency = useCallback((taskToToggle: Task) => {
    if (!editedFields) return;
    
    if (isDependencySelected(taskToToggle)) {
      // Remove dependency
      handleFieldChange(
        "dependencies",
        editedFields.dependencies.filter(dep => dep.taskId !== taskToToggle.id)
      );
    } else {
      // Add dependency
      const newDependency: TaskDependency = {
        taskId: taskToToggle.id,
        taskListId: taskToToggle.taskListId,
      };
      handleFieldChange("dependencies", [...editedFields.dependencies, newDependency]);
    }
  }, [editedFields, isDependencySelected, handleFieldChange]);

  /**
   * Handle removing a dependency
   * Requirements: 8.9 - Allow adding and managing task dependencies
   */
  const handleRemoveDependency = useCallback((taskIdToRemove: string) => {
    if (!editedFields) return;
    handleFieldChange(
      "dependencies",
      editedFields.dependencies.filter(dep => dep.taskId !== taskIdToRemove)
    );
  }, [editedFields, handleFieldChange]);

  /**
   * Handle adding an execution note
   * Requirements: 8.10 - Allow adding and managing execution notes
   */
  const handleAddExecutionNote = useCallback(async () => {
    if (!taskId || !newExecutionNote.trim()) return;
    
    setIsAddingNote(true);
    try {
      const updatedTask = await dataService.addExecutionNote(taskId, { content: newExecutionNote.trim() });
      setTask(updatedTask);
      setNewExecutionNote("");
    } catch (err) {
      console.error("Failed to add execution note:", err);
    } finally {
      setIsAddingNote(false);
    }
  }, [taskId, newExecutionNote, dataService]);

  /**
   * Handle adding a general note
   * Requirements: 8.11 - Allow adding and managing general notes
   */
  const handleAddGeneralNote = useCallback(async () => {
    if (!taskId || !newGeneralNote.trim()) return;
    
    setIsAddingNote(true);
    try {
      const updatedTask = await dataService.addNote(taskId, { content: newGeneralNote.trim() });
      setTask(updatedTask);
      setNewGeneralNote("");
    } catch (err) {
      console.error("Failed to add general note:", err);
    } finally {
      setIsAddingNote(false);
    }
  }, [taskId, newGeneralNote, dataService]);

  /**
   * Handle adding a research note
   * Requirements: 8.12 - Allow adding and managing research notes
   */
  const handleAddResearchNote = useCallback(async () => {
    if (!taskId || !newResearchNote.trim()) return;
    
    setIsAddingNote(true);
    try {
      const updatedTask = await dataService.addResearchNote(taskId, { content: newResearchNote.trim() });
      setTask(updatedTask);
      setNewResearchNote("");
    } catch (err) {
      console.error("Failed to add research note:", err);
    } finally {
      setIsAddingNote(false);
    }
  }, [taskId, newResearchNote, dataService]);

  /**
   * Handle adding an action plan item
   * Requirements: 8.13 - Allow adding and managing action plan items
   */
  const handleAddActionPlanItem = useCallback(() => {
    if (!editedFields || !newActionPlanItem.trim()) return;
    
    const maxSequence = editedFields.actionPlan.length > 0
      ? Math.max(...editedFields.actionPlan.map(item => item.sequence))
      : 0;
    
    const newItem: ActionPlanItem = {
      sequence: maxSequence + 1,
      content: newActionPlanItem.trim(),
    };
    
    handleFieldChange("actionPlan", [...editedFields.actionPlan, newItem]);
    setNewActionPlanItem("");
  }, [editedFields, newActionPlanItem, handleFieldChange]);

  /**
   * Handle removing an action plan item
   * Requirements: 8.13 - Allow adding and managing action plan items
   */
  const handleRemoveActionPlanItem = useCallback((sequence: number) => {
    if (!editedFields) return;
    
    const updatedPlan = editedFields.actionPlan
      .filter(item => item.sequence !== sequence)
      .map((item, idx) => ({ ...item, sequence: idx + 1 })); // Re-sequence
    
    handleFieldChange("actionPlan", updatedPlan);
  }, [editedFields, handleFieldChange]);

  /**
   * Handle moving an action plan item up
   * Requirements: 8.13 - Allow reordering action plan items
   */
  const handleMoveActionPlanItemUp = useCallback((index: number) => {
    if (!editedFields || index === 0) return;
    
    const items = [...editedFields.actionPlan];
    [items[index - 1], items[index]] = [items[index], items[index - 1]];
    
    // Re-sequence
    const resequenced = items.map((item, idx) => ({ ...item, sequence: idx + 1 }));
    handleFieldChange("actionPlan", resequenced);
  }, [editedFields, handleFieldChange]);

  /**
   * Handle moving an action plan item down
   * Requirements: 8.13 - Allow reordering action plan items
   */
  const handleMoveActionPlanItemDown = useCallback((index: number) => {
    if (!editedFields || index >= editedFields.actionPlan.length - 1) return;
    
    const items = [...editedFields.actionPlan];
    [items[index], items[index + 1]] = [items[index + 1], items[index]];
    
    // Re-sequence
    const resequenced = items.map((item, idx) => ({ ...item, sequence: idx + 1 }));
    handleFieldChange("actionPlan", resequenced);
  }, [editedFields, handleFieldChange]);

  /**
   * Handle delete button click
   * Requirements: 8.6 - Display delete button for the task
   */
  const handleDeleteClick = useCallback(() => {
    setIsDeleteDialogOpen(true);
  }, []);

  /**
   * Handle delete dialog close
   */
  const handleDeleteDialogClose = useCallback(() => {
    setIsDeleteDialogOpen(false);
  }, []);

  /**
   * Handle delete confirmation
   * Note: Full delete functionality will be implemented in task 12.4
   */
  const handleDeleteConfirm = useCallback(async () => {
    if (!taskId) return;

    setIsDeleting(true);
    try {
      await dataService.deleteTask(taskId);
      setIsDeleteDialogOpen(false);
      navigate(-1);
    } catch (err) {
      console.error("Failed to delete task:", err);
    } finally {
      setIsDeleting(false);
    }
  }, [taskId, dataService, navigate]);

  /**
   * Calculate exit criteria progress
   */
  const exitCriteriaProgress = useMemo(() => {
    if (!task || !task.exitCriteria || task.exitCriteria.length === 0) {
      return { completed: 0, total: 0, percentage: 0 };
    }
    const completed = task.exitCriteria.filter((c) => c.status === "COMPLETE").length;
    const total = task.exitCriteria.length;
    return {
      completed,
      total,
      percentage: Math.round((completed / total) * 100),
    };
  }, [task]);

  /**
   * Combine all notes with type information
   */
  const allNotes: NoteWithType[] = useMemo(() => {
    if (!task) return [];
    return [
      ...task.researchNotes.map((n) => ({ ...n, type: "research" as const })),
      ...task.executionNotes.map((n) => ({ ...n, type: "execution" as const })),
      ...task.notes.map((n) => ({ ...n, type: "general" as const })),
    ].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  }, [task]);

  /**
   * Render loading skeleton
   */
  const renderLoadingSkeleton = () => (
    <div
      className="flex flex-col gap-6"
      data-testid="single-task-view-loading"
      aria-busy="true"
      aria-label="Loading task"
    >
      <div className="flex items-center gap-3">
        <Skeleton width={80} height={32} />
        <Skeleton width={200} height={32} />
      </div>
      <div className="flex gap-2">
        <Skeleton width={100} height={24} />
        <Skeleton width={80} height={24} />
      </div>
      <Skeleton width="100%" height={100} />
      <div className="grid grid-cols-2 gap-6">
        <Skeleton width="100%" height={200} />
        <Skeleton width="100%" height={200} />
      </div>
    </div>
  );

  /**
   * Render error state
   */
  const renderErrorState = () => (
    <div
      className="flex flex-col items-center justify-center py-16 text-center"
      data-testid="single-task-view-error"
    >
      <svg
        className="w-16 h-16 text-[var(--error)] mb-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
        />
      </svg>
      <Typography variant="h5" color="secondary" className="mb-2">
        Failed to load task
      </Typography>
      <Typography variant="body-sm" color="muted" className="mb-4">
        {error}
      </Typography>
      <Button variant="primary" onClick={loadTaskData}>
        Try Again
      </Button>
    </div>
  );

  /**
   * Render exit criterion item
   */
  const renderExitCriterion = (criterion: ExitCriterion, index: number) => {
    const isComplete = isEditMode && editedFields 
      ? editedFields.exitCriteria[index]?.status === "COMPLETE"
      : criterion.status === "COMPLETE";
    
    return (
      <div
        key={index}
        className={cn(
          "flex items-start gap-3 p-3 rounded-lg",
          "bg-[var(--bg-surface)] border border-[var(--border)]",
          isComplete && "opacity-70"
        )}
      >
        <button
          type="button"
          onClick={() => isEditMode && handleExitCriterionToggle(index)}
          disabled={!isEditMode}
          className={cn(
            "flex-shrink-0 w-5 h-5 rounded border-2 transition-all",
            "flex items-center justify-center",
            isComplete
              ? "bg-[var(--success)] border-[var(--success)] text-white"
              : "border-[var(--border)]",
            isEditMode && "cursor-pointer hover:border-[var(--primary)]"
          )}
          aria-label={isComplete ? "Mark as incomplete" : "Mark as complete"}
          data-testid={`exit-criterion-toggle-${index}`}
        >
          {isComplete && (
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
            </svg>
          )}
        </button>
        <div className="flex-1 min-w-0">
          <Typography
            variant="body-sm"
            color={isComplete ? "muted" : "primary"}
            className={isComplete ? "line-through" : ""}
          >
            {criterion.criteria}
          </Typography>
          {criterion.comment && (
            <Typography variant="caption" color="muted" className="mt-1 block">
              {criterion.comment}
            </Typography>
          )}
        </div>
      </div>
    );
  };

  /**
   * Render note item
   */
  const renderNoteItem = (note: NoteWithType, index: number) => {
    const typeColors: Record<string, string> = {
      general: "bg-[var(--info)]/10 text-[var(--info)]",
      research: "bg-[var(--warning)]/10 text-[var(--warning)]",
      execution: "bg-[var(--success)]/10 text-[var(--success)]",
    };

    return (
      <div
        key={index}
        className="p-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--border)]"
      >
        <div className="flex items-center gap-2 mb-2">
          <span className={cn("px-2 py-0.5 rounded text-xs font-medium", typeColors[note.type])}>
            {note.type.charAt(0).toUpperCase() + note.type.slice(1)}
          </span>
          <Typography variant="caption" color="muted">
            {formatDate(note.timestamp)}
          </Typography>
        </div>
        <Typography variant="body-sm" color="secondary" className="whitespace-pre-wrap">
          {note.content}
        </Typography>
      </div>
    );
  };

  /**
   * Get task list name by ID for display
   * Requirements: 20.5 - Display task title and parent task list name
   */
  const getTaskListName = useCallback((taskListId: string): string => {
    const foundList = taskLists.find(tl => tl.id === taskListId);
    return foundList?.name || "Unknown List";
  }, [taskLists]);

  /**
   * Get available tasks for dependency selection (exclude current task, apply search filter)
   * Requirements: 20.1, 20.5 - Create scrollable list with search input
   */
  const filteredAvailableTasks = useMemo(() => {
    if (!task) return availableTasks;
    
    // Exclude current task
    let filtered = availableTasks.filter(t => t.id !== task.id);
    
    // Apply search filter
    const query = dependencySearchQuery.toLowerCase().trim();
    if (query) {
      filtered = filtered.filter(t => 
        t.title.toLowerCase().includes(query) ||
        (t.description && t.description.toLowerCase().includes(query))
      );
    }
    
    return filtered;
  }, [availableTasks, task, dependencySearchQuery]);

  /**
   * Get full task object by ID for dependency display
   */
  const getDependencyTask = useCallback((taskId: string): Task | null => {
    return availableTasks.find(t => t.id === taskId) || null;
  }, [availableTasks]);

  /**
   * Render dependency item using TaskCard with dependency variant
   */
  const renderDependencyItem = (dependency: TaskDependency, index: number, isEditing: boolean) => {
    const depTask = getDependencyTask(dependency.taskId);
    
    // If we have the full task object, render as TaskCard
    if (depTask) {
      return (
        <div
          key={index}
          className="flex items-center gap-2"
        >
          <div className="flex-1">
            <TaskCard
              task={depTask}
              variant="dependency"
              onClick={() => navigate(`/tasks/${depTask.id}`)}
            />
          </div>
          {isEditing && (
            <button
              type="button"
              onClick={() => handleRemoveDependency(dependency.taskId)}
              className="p-2 rounded hover:bg-[var(--error)]/10 text-[var(--text-muted)] hover:text-[var(--error)] transition-colors flex-shrink-0"
              aria-label={`Remove dependency ${depTask.title}`}
              data-testid={`remove-dependency-${index}`}
            >
              <Icon name="X" size={16} />
            </button>
          )}
        </div>
      );
    }
    
    // Fallback to simple display if task not loaded yet
    return (
      <div
        key={index}
        className="flex items-center gap-2 p-2 rounded-lg bg-[var(--bg-surface)] border border-[var(--border)]"
      >
        <Icon name="Link2" size="sm" className="text-[var(--text-muted)] flex-shrink-0" />
        <Typography variant="body-sm" color="secondary" className="flex-1 truncate">
          Loading...
        </Typography>
        {isEditing && (
          <button
            type="button"
            onClick={() => handleRemoveDependency(dependency.taskId)}
            className="p-1 rounded hover:bg-[var(--error)]/10 text-[var(--text-muted)] hover:text-[var(--error)] transition-colors"
            aria-label={`Remove dependency`}
            data-testid={`remove-dependency-${index}`}
          >
            <Icon name="X" size={14} />
          </button>
        )}
      </div>
    );
  };

  // Show error state
  if (error && !isLoading) {
    return (
      <div className={cn("flex flex-col gap-6", className)} data-testid="single-task-view">
        {renderErrorState()}
      </div>
    );
  }

  return (
    <div
      className={cn("flex flex-col gap-6", className)}
      data-testid="single-task-view"
    >
      {/* Loading state */}
      {isLoading && renderLoadingSkeleton()}

      {/* Task content - Requirements: 8.2 */}
      {!isLoading && task && (
        <>
          {/* Header - Requirements: 8.1, 8.3, 8.4, 8.5, 8.6, 14.1, 14.2, 14.3 */}
          <div className="flex flex-col gap-4">
            {/* Top row with back button and action buttons - 40px height, 12px gap */}
            <div className="flex items-center justify-between gap-3">
              {/* Back button and title - Requirements: 8.1, 14.1, 14.3 */}
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <button
                  onClick={handleBackClick}
                  aria-label="Go back"
                  data-testid="back-button"
                  disabled={isEditMode}
                  className="flex-shrink-0 w-10 h-10 flex items-center justify-center rounded-lg bg-[var(--bg-surface)] border border-[var(--border)] text-[var(--text-primary)] hover:bg-[var(--bg-surface-hover)] hover:border-[var(--primary)] hover:text-[var(--primary)] transition-all duration-200 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Icon name="ChevronLeft" size={20} />
                </button>
                {isEditMode && editedFields ? (
                  <Input
                    type="text"
                    value={editedFields.title}
                    onChange={(e) => handleFieldChange("title", e.target.value)}
                    placeholder="Task title"
                    className="text-lg font-semibold max-w-md flex-1"
                    state={saveError && !editedFields.title.trim() ? "error" : "default"}
                    data-testid="edit-title-input"
                  />
                ) : (
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <Typography variant="h3" color="muted" className="text-lg md:text-xl font-medium flex-shrink-0">
                      Task:
                    </Typography>
                    <Typography variant="h3" color="primary" className="text-lg md:text-xl font-semibold truncate">
                      {task.title}
                    </Typography>
                  </div>
                )}
              </div>

              {/* Action buttons - Requirements: 8.3, 8.4, 8.5, 8.6, 14.2, 14.3 */}
              <div className="flex items-center gap-3 flex-shrink-0">
                {isEditMode ? (
                  <>
                    <Button
                      variant="ghost"
                      size="md"
                      onClick={handleCancelEdit}
                      leftIcon={<Icon name="X" size="sm" />}
                      data-testid="cancel-edit-button"
                      disabled={isSaving}
                    >
                      Cancel
                    </Button>
                    <Button
                      variant="primary"
                      size="md"
                      onClick={handleSaveEdit}
                      leftIcon={<Icon name="Check" size="sm" />}
                      data-testid="save-edit-button"
                      disabled={isSaving}
                    >
                      {isSaving ? "Saving..." : "Save"}
                    </Button>
                  </>
                ) : (
                  <>
                    <Button
                      variant="secondary"
                      size="md"
                      onClick={handleEditClick}
                      leftIcon={<Icon name="Pencil" size="sm" />}
                      data-testid="edit-task-button"
                    >
                      Edit
                    </Button>
                    <Button
                      variant="destructive"
                      size="md"
                      onClick={handleDeleteClick}
                      leftIcon={<Icon name="Trash2" size="sm" />}
                      data-testid="delete-task-button"
                    >
                      Delete
                    </Button>
                  </>
                )}
              </div>
            </div>

            {/* Save error message */}
            {saveError && (
              <div className="p-3 rounded-lg bg-[var(--error)]/10 border border-[var(--error)]/20">
                <Typography variant="body-sm" className="text-[var(--error)]">
                  {saveError}
                </Typography>
              </div>
            )}

            {/* Status and priority badges/selects */}
            <div className="flex items-center gap-2 flex-wrap">
              {isEditMode && editedFields ? (
                <>
                  {/* Status select in edit mode */}
                  <div className="flex items-center gap-2">
                    <Typography variant="caption" color="muted" className="uppercase tracking-wider">
                      Status:
                    </Typography>
                    <select
                      value={editedFields.status}
                      onChange={(e) => handleFieldChange("status", e.target.value as TaskStatus)}
                      className={cn(
                        "px-3 py-1.5 text-sm rounded-lg border",
                        "bg-[var(--bg-surface)] text-[var(--text-primary)]",
                        "border-[var(--border)] focus:border-[var(--primary)]",
                        "focus:ring-2 focus:ring-[rgba(var(--primary-rgb),0.2)]",
                        "outline-none cursor-pointer"
                      )}
                      data-testid="edit-status-select"
                    >
                      {TASK_STATUS_OPTIONS.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  {/* Priority select in edit mode */}
                  <div className="flex items-center gap-2">
                    <Typography variant="caption" color="muted" className="uppercase tracking-wider">
                      Priority:
                    </Typography>
                    <select
                      value={editedFields.priority}
                      onChange={(e) => handleFieldChange("priority", e.target.value as TaskPriority)}
                      className={cn(
                        "px-3 py-1.5 text-sm rounded-lg border",
                        "bg-[var(--bg-surface)] text-[var(--text-primary)]",
                        "border-[var(--border)] focus:border-[var(--primary)]",
                        "focus:ring-2 focus:ring-[rgba(var(--primary-rgb),0.2)]",
                        "outline-none cursor-pointer"
                      )}
                      data-testid="edit-priority-select"
                    >
                      {TASK_PRIORITY_OPTIONS.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </>
              ) : (
                <>
                  <div className="flex items-center gap-2">
                    <StatusIndicator
                      status={mapTaskStatusToIndicator(task.status)}
                      pulse={task.status === "IN_PROGRESS" || task.status === "BLOCKED"}
                      size="md"
                    />
                    <Typography variant="caption" color="muted" className="uppercase tracking-wider">
                      {formatStatus(task.status)}
                    </Typography>
                  </div>
                  <Badge variant={mapPriorityToVariant(task.priority)} size="sm">
                    {formatPriority(task.priority)}
                  </Badge>
                </>
              )}
              <div className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-[var(--bg-surface-hover)]">
                <Icon name="Calendar" size={12} className="text-[var(--text-muted)]" />
                <Typography variant="caption" color="muted">
                  {formatDate(task.createdAt)}
                </Typography>
              </div>
              {task.updatedAt !== task.createdAt && (
                <div className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-[var(--bg-surface-hover)]">
                  <Icon name="Clock" size={12} className="text-[var(--text-muted)]" />
                  <Typography variant="caption" color="muted">
                    Updated {formatDate(task.updatedAt)}
                  </Typography>
                </div>
              )}
            </div>

            {/* Description */}
            {(isEditMode || task.description) && (
              <div className="p-4 rounded-lg bg-[var(--bg-surface)] border border-[var(--border)]">
                <div className="flex items-center gap-2 mb-2">
                  <Icon name="FileText" size="sm" className="text-[var(--text-muted)]" />
                  <Typography variant="caption" color="muted" className="uppercase tracking-wider">
                    Description
                  </Typography>
                </div>
                {isEditMode && editedFields ? (
                  <textarea
                    value={editedFields.description}
                    onChange={(e) => handleFieldChange("description", e.target.value)}
                    placeholder="Add a description..."
                    rows={4}
                    className={cn(
                      "w-full px-3 py-2 text-sm rounded-lg border resize-y",
                      "bg-[var(--bg-surface)] text-[var(--text-primary)]",
                      "border-[var(--border)] focus:border-[var(--primary)]",
                      "focus:ring-2 focus:ring-[rgba(var(--primary-rgb),0.2)]",
                      "outline-none placeholder:text-[var(--text-tertiary)]"
                    )}
                    data-testid="edit-description-textarea"
                  />
                ) : (
                  <Typography variant="body" color="secondary">
                    {task.description}
                  </Typography>
                )}
              </div>
            )}

            {/* Tags */}
            {isEditMode && editedFields ? (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Icon name="Tag" size="sm" className="text-[var(--text-muted)]" />
                  <Typography variant="caption" color="muted" className="uppercase tracking-wider">
                    Tags
                  </Typography>
                </div>
                <div className="flex flex-wrap gap-2">
                  {editedFields.tags.map((tag, idx) => (
                    <span
                      key={`${tag}-${idx}`}
                      className={cn(
                        "inline-flex items-center gap-1 px-2 py-1 rounded-full",
                        "bg-[var(--primary)]/10 text-[var(--primary)] text-xs font-medium"
                      )}
                    >
                      <Icon name="Tag" size={10} />
                      {tag}
                      <button
                        type="button"
                        onClick={() => handleRemoveTag(tag)}
                        className="ml-1 hover:text-[var(--error)] transition-colors"
                        aria-label={`Remove tag ${tag}`}
                        data-testid={`remove-tag-${tag}`}
                      >
                        <Icon name="X" size={10} />
                      </button>
                    </span>
                  ))}
                  <div className="flex items-center gap-1">
                    <Input
                      type="text"
                      value={tagInput}
                      onChange={(e) => setTagInput(e.target.value)}
                      onKeyPress={handleTagKeyPress}
                      placeholder="Add tag..."
                      className="w-24 text-xs py-1"
                      data-testid="add-tag-input"
                    />
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleAddTag}
                      disabled={!tagInput.trim()}
                      data-testid="add-tag-button"
                    >
                      <Icon name="Plus" size={12} />
                    </Button>
                  </div>
                </div>
              </div>
            ) : (
              task.tags && task.tags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {task.tags.map((tag, idx) => (
                    <span
                      key={`${tag}-${idx}`}
                      className={cn(
                        "inline-flex items-center gap-1 px-2 py-1 rounded-full",
                        "bg-[var(--primary)]/10 text-[var(--primary)] text-xs font-medium"
                      )}
                    >
                      <Icon name="Tag" size={10} />
                      {tag}
                    </span>
                  ))}
                </div>
              )
            )}
          </div>

          {/* Content grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Left column - Exit Criteria */}
            <div className="space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-[var(--border)]">
                <div className="flex items-center gap-2">
                  <Icon name="Target" size="sm" className="text-[var(--primary)]" />
                  <Typography variant="h6" color="primary">
                    Exit Criteria
                  </Typography>
                </div>
                {exitCriteriaProgress.total > 0 && (
                  <Typography variant="caption" color="muted">
                    {exitCriteriaProgress.completed} of {exitCriteriaProgress.total} complete
                  </Typography>
                )}
              </div>

              {/* Progress bar */}
              {exitCriteriaProgress.total > 0 && (
                <div className="h-2 bg-[var(--bg-surface-hover)] rounded-full overflow-hidden">
                  <div
                    className="h-full bg-[var(--success)] rounded-full transition-all duration-300"
                    style={{ width: `${exitCriteriaProgress.percentage}%` }}
                  />
                </div>
              )}

              {/* Criteria list */}
              <div className="space-y-2">
                {task.exitCriteria && task.exitCriteria.length > 0 ? (
                  task.exitCriteria.map((criterion, idx) => renderExitCriterion(criterion, idx))
                ) : (
                  <div className="p-4 text-center rounded-lg border border-dashed border-[var(--border)]">
                    <Typography variant="body-sm" color="muted">
                      No exit criteria defined
                    </Typography>
                  </div>
                )}
              </div>

              {/* Dependencies - Requirements: 8.9, 20.1, 20.2, 20.3, 20.4, 20.5 */}
              <div className="pt-4">
                <div className="flex items-center gap-2 pb-3 border-b border-[var(--border)]">
                  <Icon name="Link2" size="sm" className="text-[var(--primary)]" />
                  <Typography variant="h6" color="primary">
                    Dependencies ({isEditMode && editedFields ? editedFields.dependencies.length : (task.dependencies?.length || 0)})
                  </Typography>
                </div>
                
                {/* Edit mode: List-based dependency selection - Requirements: 20.1, 20.2, 20.3, 20.4, 20.5 */}
                {isEditMode && editedFields && (
                  <div className="mt-4 space-y-3">
                    {/* Selected dependencies section - Requirements: 20.4 */}
                    {editedFields.dependencies.length > 0 && (
                      <div className="space-y-2">
                        <Typography variant="caption" color="muted" className="uppercase tracking-wider">
                          Selected Dependencies
                        </Typography>
                        <div className="flex flex-wrap gap-2">
                          {editedFields.dependencies.map((dep) => {
                            const depTask = getDependencyTask(dep.taskId);
                            return (
                              <div
                                key={dep.taskId}
                                className={cn(
                                  "flex items-center gap-2 px-3 py-1.5 rounded-lg",
                                  "bg-[var(--primary)]/10 border border-[var(--primary)]/30"
                                )}
                              >
                                <Icon name="Link2" size={12} className="text-[var(--primary)]" />
                                <span className="text-sm text-[var(--text-primary)] max-w-[150px] truncate">
                                  {depTask?.title || "Loading..."}
                                </span>
                                <button
                                  type="button"
                                  onClick={() => handleRemoveDependency(dep.taskId)}
                                  className="p-0.5 rounded hover:bg-[var(--error)]/20 text-[var(--text-muted)] hover:text-[var(--error)] transition-colors"
                                  aria-label={`Remove dependency ${depTask?.title || dep.taskId}`}
                                  data-testid={`remove-dependency-chip-${dep.taskId}`}
                                >
                                  <Icon name="X" size={14} />
                                </button>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                    
                    {/* Available tasks section - Requirements: 20.1, 20.5 */}
                    <div className="space-y-2">
                      <Typography variant="caption" color="muted" className="uppercase tracking-wider">
                        Available Tasks
                      </Typography>
                      
                      {/* Search input - Requirements: 20.1 */}
                      <input
                        type="text"
                        value={dependencySearchQuery}
                        onChange={(e) => setDependencySearchQuery(e.target.value)}
                        placeholder="Search tasks..."
                        className={cn(
                          "w-full px-3 py-2 text-sm rounded-lg border",
                          "bg-[var(--bg-surface)] text-[var(--text-primary)]",
                          "border-[var(--border)] focus:border-[var(--primary)]",
                          "focus:ring-2 focus:ring-[rgba(var(--primary-rgb),0.2)]",
                          "outline-none placeholder:text-[var(--text-tertiary)]"
                        )}
                        data-testid="dependency-search-input"
                      />
                      
                      {/* Scrollable task list - Requirements: 20.1, 20.3, 20.5 */}
                      <div
                        className={cn(
                          "max-h-[200px] overflow-y-auto rounded-lg border border-[var(--border)]",
                          "bg-[var(--bg-app)]"
                        )}
                        data-testid="dependency-list-container"
                      >
                        {loadingTasks ? (
                          <div className="p-4 text-center text-[var(--text-tertiary)] text-sm italic">
                            Loading tasks...
                          </div>
                        ) : filteredAvailableTasks.length > 0 ? (
                          filteredAvailableTasks.map((availableTask) => {
                            const isSelected = isDependencySelected(availableTask);
                            return (
                              <div
                                key={availableTask.id}
                                className={cn(
                                  "flex items-center gap-3 px-3 py-2 cursor-pointer",
                                  "border-b border-[var(--border)] last:border-b-0",
                                  "transition-colors hover:bg-[var(--bg-surface)]",
                                  isSelected && "bg-[rgba(var(--primary-rgb),0.1)]"
                                )}
                                onClick={() => toggleDependency(availableTask)}
                                role="checkbox"
                                aria-checked={isSelected}
                                tabIndex={0}
                                onKeyDown={(e) => {
                                  if (e.key === "Enter" || e.key === " ") {
                                    e.preventDefault();
                                    toggleDependency(availableTask);
                                  }
                                }}
                                data-testid={`dependency-item-${availableTask.id}`}
                              >
                                {/* Checkbox - Requirements: 20.3 */}
                                <div
                                  className={cn(
                                    "flex items-center justify-center w-4 h-4 rounded border-2 flex-shrink-0",
                                    isSelected
                                      ? "bg-[var(--primary)] border-[var(--primary)] text-white"
                                      : "border-[var(--border)] bg-[var(--bg-surface)]"
                                  )}
                                >
                                  {isSelected && (
                                    <svg className="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                                    </svg>
                                  )}
                                </div>
                                
                                {/* Task info - Requirements: 20.5 */}
                                <div className="flex flex-col min-w-0 flex-1">
                                  <span className="text-sm font-medium text-[var(--text-primary)] truncate">
                                    {availableTask.title}
                                  </span>
                                  <span className="text-xs text-[var(--text-tertiary)]">
                                    {getTaskListName(availableTask.taskListId)}
                                  </span>
                                </div>
                              </div>
                            );
                          })
                        ) : (
                          <div className="p-4 text-center text-[var(--text-tertiary)] text-sm italic">
                            {dependencySearchQuery ? "No tasks match your search" : "No tasks available"}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
                
                {/* View mode: Display dependencies */}
                {!isEditMode && (
                  <div className="space-y-2 mt-4">
                    {task.dependencies && task.dependencies.length > 0 ? (
                      task.dependencies.map((dep, idx) => renderDependencyItem(dep, idx, false))
                    ) : (
                      <div className="p-4 text-center rounded-lg border border-dashed border-[var(--border)]">
                        <Typography variant="body-sm" color="muted">
                          No dependencies
                        </Typography>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Right column - Notes - Requirements: 8.10, 8.11, 8.12 */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 pb-3 border-b border-[var(--border)]">
                <Icon name="FileText" size="sm" className="text-[var(--primary)]" />
                <Typography variant="h6" color="primary">
                  Notes ({allNotes.length})
                </Typography>
              </div>

              {/* Add notes UI in edit mode */}
              {isEditMode && (
                <div className="space-y-4 p-4 rounded-lg bg-[var(--bg-surface-hover)] border border-[var(--border)]">
                  <Typography variant="body-sm" color="primary" className="font-medium">
                    Add New Note
                  </Typography>
                  
                  {/* Execution Note - Requirements: 8.10 */}
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded text-xs font-medium bg-[var(--success)]/10 text-[var(--success)]">
                        Execution
                      </span>
                    </div>
                    <div className="flex gap-2">
                      <textarea
                        value={newExecutionNote}
                        onChange={(e) => setNewExecutionNote(e.target.value)}
                        placeholder="Add execution note..."
                        rows={2}
                        className={cn(
                          "flex-1 px-3 py-2 text-sm rounded-lg border resize-none",
                          "bg-[var(--bg-surface)] text-[var(--text-primary)]",
                          "border-[var(--border)] focus:border-[var(--primary)]",
                          "focus:ring-2 focus:ring-[rgba(var(--primary-rgb),0.2)]",
                          "outline-none placeholder:text-[var(--text-tertiary)]"
                        )}
                        data-testid="execution-note-input"
                      />
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={handleAddExecutionNote}
                        disabled={!newExecutionNote.trim() || isAddingNote}
                        data-testid="add-execution-note-button"
                      >
                        <Icon name="Plus" size={14} />
                      </Button>
                    </div>
                  </div>
                  
                  {/* General Note - Requirements: 8.11 */}
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded text-xs font-medium bg-[var(--info)]/10 text-[var(--info)]">
                        General
                      </span>
                    </div>
                    <div className="flex gap-2">
                      <textarea
                        value={newGeneralNote}
                        onChange={(e) => setNewGeneralNote(e.target.value)}
                        placeholder="Add general note..."
                        rows={2}
                        className={cn(
                          "flex-1 px-3 py-2 text-sm rounded-lg border resize-none",
                          "bg-[var(--bg-surface)] text-[var(--text-primary)]",
                          "border-[var(--border)] focus:border-[var(--primary)]",
                          "focus:ring-2 focus:ring-[rgba(var(--primary-rgb),0.2)]",
                          "outline-none placeholder:text-[var(--text-tertiary)]"
                        )}
                        data-testid="general-note-input"
                      />
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={handleAddGeneralNote}
                        disabled={!newGeneralNote.trim() || isAddingNote}
                        data-testid="add-general-note-button"
                      >
                        <Icon name="Plus" size={14} />
                      </Button>
                    </div>
                  </div>
                  
                  {/* Research Note - Requirements: 8.12 */}
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded text-xs font-medium bg-[var(--warning)]/10 text-[var(--warning)]">
                        Research
                      </span>
                    </div>
                    <div className="flex gap-2">
                      <textarea
                        value={newResearchNote}
                        onChange={(e) => setNewResearchNote(e.target.value)}
                        placeholder="Add research note..."
                        rows={2}
                        className={cn(
                          "flex-1 px-3 py-2 text-sm rounded-lg border resize-none",
                          "bg-[var(--bg-surface)] text-[var(--text-primary)]",
                          "border-[var(--border)] focus:border-[var(--primary)]",
                          "focus:ring-2 focus:ring-[rgba(var(--primary-rgb),0.2)]",
                          "outline-none placeholder:text-[var(--text-tertiary)]"
                        )}
                        data-testid="research-note-input"
                      />
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={handleAddResearchNote}
                        disabled={!newResearchNote.trim() || isAddingNote}
                        data-testid="add-research-note-button"
                      >
                        <Icon name="Plus" size={14} />
                      </Button>
                    </div>
                  </div>
                </div>
              )}

              <div className="space-y-2">
                {allNotes.length > 0 ? (
                  allNotes.map((note, idx) => renderNoteItem(note, idx))
                ) : (
                  <div className="p-4 text-center rounded-lg border border-dashed border-[var(--border)]">
                    <Typography variant="body-sm" color="muted">
                      No notes yet
                    </Typography>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Action Plan Section - Requirements: 8.13 */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 pb-3 border-b border-[var(--border)]">
              <Icon name="ListChecks" size="sm" className="text-[var(--primary)]" />
              <Typography variant="h6" color="primary">
                Action Plan ({isEditMode && editedFields ? editedFields.actionPlan.length : (task.actionPlan?.length || 0)})
              </Typography>
            </div>

            {/* Add action plan item UI in edit mode */}
            {isEditMode && editedFields && (
              <div className="flex gap-2">
                <Input
                  type="text"
                  value={newActionPlanItem}
                  onChange={(e) => setNewActionPlanItem(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      handleAddActionPlanItem();
                    }
                  }}
                  placeholder="Add action plan item..."
                  className="flex-1"
                  data-testid="action-plan-input"
                />
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleAddActionPlanItem}
                  disabled={!newActionPlanItem.trim()}
                  leftIcon={<Icon name="Plus" size="sm" />}
                  data-testid="add-action-plan-button"
                >
                  Add
                </Button>
              </div>
            )}

            {/* Action plan items list */}
            <div className="space-y-2">
              {isEditMode && editedFields ? (
                editedFields.actionPlan.length > 0 ? (
                  editedFields.actionPlan
                    .sort((a, b) => a.sequence - b.sequence)
                    .map((item, idx) => (
                      <div
                        key={item.sequence}
                        className="flex items-center gap-2 p-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--border)]"
                      >
                        <span className="flex-shrink-0 w-6 h-6 rounded-full bg-[var(--primary)]/10 text-[var(--primary)] text-xs font-medium flex items-center justify-center">
                          {item.sequence}
                        </span>
                        <Typography variant="body-sm" color="secondary" className="flex-1">
                          {item.content}
                        </Typography>
                        <div className="flex items-center gap-1">
                          <button
                            type="button"
                            onClick={() => handleMoveActionPlanItemUp(idx)}
                            disabled={idx === 0}
                            className={cn(
                              "p-1 rounded transition-colors",
                              idx === 0
                                ? "text-[var(--text-tertiary)] cursor-not-allowed"
                                : "text-[var(--text-muted)] hover:text-[var(--primary)] hover:bg-[var(--primary)]/10"
                            )}
                            aria-label="Move up"
                            data-testid={`move-up-${idx}`}
                          >
                            <Icon name="ChevronUp" size={14} />
                          </button>
                          <button
                            type="button"
                            onClick={() => handleMoveActionPlanItemDown(idx)}
                            disabled={idx >= editedFields.actionPlan.length - 1}
                            className={cn(
                              "p-1 rounded transition-colors",
                              idx >= editedFields.actionPlan.length - 1
                                ? "text-[var(--text-tertiary)] cursor-not-allowed"
                                : "text-[var(--text-muted)] hover:text-[var(--primary)] hover:bg-[var(--primary)]/10"
                            )}
                            aria-label="Move down"
                            data-testid={`move-down-${idx}`}
                          >
                            <Icon name="ChevronDown" size={14} />
                          </button>
                          <button
                            type="button"
                            onClick={() => handleRemoveActionPlanItem(item.sequence)}
                            className="p-1 rounded text-[var(--text-muted)] hover:text-[var(--error)] hover:bg-[var(--error)]/10 transition-colors"
                            aria-label="Remove item"
                            data-testid={`remove-action-plan-${idx}`}
                          >
                            <Icon name="X" size={14} />
                          </button>
                        </div>
                      </div>
                    ))
                ) : (
                  <div className="p-4 text-center rounded-lg border border-dashed border-[var(--border)]">
                    <Typography variant="body-sm" color="muted">
                      No action plan items
                    </Typography>
                  </div>
                )
              ) : (
                task.actionPlan && task.actionPlan.length > 0 ? (
                  task.actionPlan
                    .sort((a, b) => a.sequence - b.sequence)
                    .map((item) => (
                      <div
                        key={item.sequence}
                        className="flex items-center gap-2 p-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--border)]"
                      >
                        <span className="flex-shrink-0 w-6 h-6 rounded-full bg-[var(--primary)]/10 text-[var(--primary)] text-xs font-medium flex items-center justify-center">
                          {item.sequence}
                        </span>
                        <Typography variant="body-sm" color="secondary" className="flex-1">
                          {item.content}
                        </Typography>
                      </div>
                    ))
                ) : (
                  <div className="p-4 text-center rounded-lg border border-dashed border-[var(--border)]">
                    <Typography variant="body-sm" color="muted">
                      No action plan items
                    </Typography>
                  </div>
                )
              )}
            </div>
          </div>
        </>
      )}

      {/* Delete Confirmation Dialog - Requirements: 8.6 */}
      {task && (
        <DeleteConfirmationDialog
          isOpen={isDeleteDialogOpen}
          title="Delete Task"
          message="Are you sure you want to delete this task? This action cannot be undone."
          itemName={task.title}
          onConfirm={handleDeleteConfirm}
          onCancel={handleDeleteDialogClose}
          isDestructive
          loading={isDeleting}
        />
      )}
    </div>
  );
};

SingleTaskView.displayName = "SingleTaskView";

export default SingleTaskView;
