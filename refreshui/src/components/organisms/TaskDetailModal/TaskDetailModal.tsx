import React, { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  Edit2,
  Save,
  Trash2,
  Calendar,
  Tag,
  FileText,
  Target,
  Plus,
  Link2,
  Clock,
} from "lucide-react";
import { Button } from "../../atoms/Button";
import { Badge, type BadgeVariant } from "../../atoms/Badge";
import { Typography } from "../../atoms/Typography";
import { StatusIndicator, type StatusType } from "../../molecules/StatusIndicator";
import type {
  Task,
  TaskStatus,
  TaskPriority,
  ExitCriterion,
  Note,
  TaskDependency,
} from "../../../core/types/entities";
import { cn } from "../../../lib/utils";

/**
 * TaskDetailModal Organism Component
 *
 * A comprehensive modal for displaying and editing full task information
 * including notes, dependencies, exit criteria, and metadata.
 *
 * Requirements: 10.4
 * - Display full task information
 * - Show notes (general, research, execution)
 * - Show dependencies
 * - Show exit criteria with progress
 * - Show metadata (dates, tags, status, priority)
 *
 * Property 26: TaskDetailModal Content Completeness
 * - For any Task object, the TaskDetailModal SHALL render all sections:
 *   notes, dependencies, exit criteria, and metadata.
 */

export interface TaskDetailModalProps {
  /** The task to display */
  task: Task | null;
  /** Whether the modal is open */
  isOpen: boolean;
  /** Callback fired when the modal should close */
  onClose: () => void;
  /** Callback fired when the task is saved */
  onSave?: (task: Task) => void;
  /** Callback fired when the task is deleted */
  onDelete?: (taskId: string) => void;
  /** Available tasks for dependency selection */
  availableTasks?: Task[];
  /** Additional CSS classes */
  className?: string;
}

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
 * Section header component
 */
interface SectionHeaderProps {
  icon: React.ReactNode;
  title: string;
  action?: React.ReactNode;
}

const SectionHeader: React.FC<SectionHeaderProps> = ({ icon, title, action }) => (
  <div className="flex items-center justify-between pb-3 border-b border-[var(--border)]">
    <div className="flex items-center gap-2">
      <span className="text-[var(--primary)]">{icon}</span>
      <Typography variant="h6" color="primary">
        {title}
      </Typography>
    </div>
    {action}
  </div>
);

/**
 * Exit criterion item component
 */
interface ExitCriterionItemProps {
  criterion: ExitCriterion;
  index: number;
  isEditing: boolean;
  onToggle: (index: number) => void;
  onChange: (index: number, value: string) => void;
  onDelete: (index: number) => void;
}

const ExitCriterionItem: React.FC<ExitCriterionItemProps> = ({
  criterion,
  index,
  isEditing,
  onToggle,
  onChange,
  onDelete,
}) => (
  <div
    className={cn(
      "flex items-start gap-3 p-3 rounded-lg transition-colors",
      "bg-[var(--bg-surface)] border border-[var(--border)]",
      criterion.status === "COMPLETE" && "opacity-70"
    )}
  >
    <button
      type="button"
      onClick={() => onToggle(index)}
      className={cn(
        "flex-shrink-0 w-5 h-5 rounded border-2 transition-all",
        "flex items-center justify-center",
        criterion.status === "COMPLETE"
          ? "bg-[var(--success)] border-[var(--success)] text-white"
          : "border-[var(--border)] hover:border-[var(--primary)]"
      )}
      aria-label={criterion.status === "COMPLETE" ? "Mark incomplete" : "Mark complete"}
    >
      {criterion.status === "COMPLETE" && (
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
        </svg>
      )}
    </button>
    <div className="flex-1 min-w-0">
      {isEditing ? (
        <input
          type="text"
          value={criterion.criteria}
          onChange={(e) => onChange(index, e.target.value)}
          className={cn(
            "w-full bg-transparent border-b border-[var(--border)]",
            "text-sm text-[var(--text-primary)] py-1",
            "focus:outline-none focus:border-[var(--primary)]"
          )}
        />
      ) : (
        <Typography
          variant="body-sm"
          color={criterion.status === "COMPLETE" ? "muted" : "primary"}
          className={criterion.status === "COMPLETE" ? "line-through" : ""}
        >
          {criterion.criteria}
        </Typography>
      )}
      {criterion.comment && (
        <Typography variant="caption" color="muted" className="mt-1 block">
          {criterion.comment}
        </Typography>
      )}
    </div>
    {isEditing && (
      <button
        type="button"
        onClick={() => onDelete(index)}
        className="text-[var(--error)] hover:text-[var(--error)] p-1"
        aria-label="Delete criterion"
      >
        <Trash2 size={14} />
      </button>
    )}
  </div>
);

/**
 * Note item component
 */
interface NoteItemProps {
  note: NoteWithType;
}

const NoteItem: React.FC<NoteItemProps> = ({ note }) => {
  const typeColors: Record<string, string> = {
    general: "bg-[var(--info)]/10 text-[var(--info)]",
    research: "bg-[var(--warning)]/10 text-[var(--warning)]",
    execution: "bg-[var(--success)]/10 text-[var(--success)]",
  };

  return (
    <div className="p-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--border)]">
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
 * Dependency item component
 */
interface DependencyItemProps {
  dependency: TaskDependency;
  availableTasks: Task[];
  isEditing: boolean;
  onRemove: (taskId: string) => void;
}

const DependencyItem: React.FC<DependencyItemProps> = ({
  dependency,
  availableTasks,
  isEditing,
  onRemove,
}) => {
  const dependentTask = availableTasks.find((t) => t.id === dependency.taskId);

  return (
    <div className="flex items-center gap-2 p-2 rounded-lg bg-[var(--bg-surface)] border border-[var(--border)]">
      <Link2 size={14} className="text-[var(--text-muted)] flex-shrink-0" />
      <Typography variant="body-sm" color="secondary" className="flex-1 truncate">
        {dependentTask?.title || dependency.taskId}
      </Typography>
      {dependentTask && (
        <StatusIndicator
          status={mapTaskStatusToIndicator(dependentTask.status)}
          size="sm"
        />
      )}
      {isEditing && (
        <button
          type="button"
          onClick={() => onRemove(dependency.taskId)}
          className="text-[var(--error)] hover:text-[var(--error)] p-1"
          aria-label="Remove dependency"
        >
          <X size={14} />
        </button>
      )}
    </div>
  );
};

/**
 * TaskDetailModal component for displaying full task information
 */
export const TaskDetailModal: React.FC<TaskDetailModalProps> = ({
  task,
  isOpen,
  onClose,
  onSave,
  onDelete,
  availableTasks = [],
  className,
}) => {
  // Editing state
  const [isEditing, setIsEditing] = useState(false);

  // Form state
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState<TaskStatus>("NOT_STARTED");
  const [priority, setPriority] = useState<TaskPriority>("MEDIUM");
  const [tags, setTags] = useState<string[]>([]);
  const [newTag, setNewTag] = useState("");
  const [exitCriteria, setExitCriteria] = useState<ExitCriterion[]>([]);
  const [dependencies, setDependencies] = useState<TaskDependency[]>([]);
  const [newNote, setNewNote] = useState("");
  const [noteType, setNoteType] = useState<"general" | "research" | "execution">("general");

  // Track previous values to detect changes
  const prevTaskIdRef = React.useRef<string | null>(null);
  const prevIsOpenRef = React.useRef(isOpen);
  
  // Sync form state with task prop when task changes or modal opens
  useEffect(() => {
    const prevTaskId = prevTaskIdRef.current;
    const wasOpen = prevIsOpenRef.current;
    
    prevTaskIdRef.current = task?.id ?? null;
    prevIsOpenRef.current = isOpen;
    
    // Only sync when task changes or modal transitions from closed to open
    const taskChanged = task && task.id !== prevTaskId;
    const modalOpened = isOpen && !wasOpen;
    
    if (task && (taskChanged || modalOpened)) {
      // Use requestAnimationFrame to defer state updates
      requestAnimationFrame(() => {
        setTitle(task.title);
        setDescription(task.description || "");
        setStatus(task.status);
        setPriority(task.priority);
        setTags(task.tags || []);
        setExitCriteria(task.exitCriteria || []);
        setDependencies(task.dependencies || []);
        setIsEditing(false);
      });
    }
  }, [task, isOpen]);

  // Handle escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  // Handlers
  const handleSave = useCallback(() => {
    if (!task || !onSave) return;

    const updatedTask: Task = {
      ...task,
      title,
      description: description || undefined,
      status,
      priority,
      tags,
      exitCriteria,
      dependencies,
      updatedAt: new Date().toISOString(),
    };
    onSave(updatedTask);
    setIsEditing(false);
  }, [task, onSave, title, description, status, priority, tags, exitCriteria, dependencies]);

  const handleDelete = useCallback(() => {
    if (!task || !onDelete) return;
    if (window.confirm("Are you sure you want to delete this task?")) {
      onDelete(task.id);
      onClose();
    }
  }, [task, onDelete, onClose]);

  // Exit criteria handlers
  const handleToggleExitCriterion = useCallback((index: number) => {
    setExitCriteria((prev) => {
      const updated = [...prev];
      updated[index] = {
        ...updated[index],
        status: updated[index].status === "COMPLETE" ? "INCOMPLETE" : "COMPLETE",
      };
      return updated;
    });
  }, []);

  const handleUpdateExitCriterion = useCallback((index: number, criteria: string) => {
    setExitCriteria((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], criteria };
      return updated;
    });
  }, []);

  const handleDeleteExitCriterion = useCallback((index: number) => {
    setExitCriteria((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const handleAddExitCriterion = useCallback(() => {
    setExitCriteria((prev) => [...prev, { criteria: "", status: "INCOMPLETE" }]);
  }, []);

  // Tag handlers
  const handleAddTag = useCallback(() => {
    if (newTag.trim() && !tags.includes(newTag.trim())) {
      setTags((prev) => [...prev, newTag.trim()]);
      setNewTag("");
    }
  }, [newTag, tags]);

  const handleRemoveTag = useCallback((tag: string) => {
    setTags((prev) => prev.filter((t) => t !== tag));
  }, []);

  // Dependency handlers
  const handleRemoveDependency = useCallback((taskId: string) => {
    setDependencies((prev) => prev.filter((d) => d.taskId !== taskId));
  }, []);

  // Note handler
  const handleAddNote = useCallback(() => {
    if (!newNote.trim() || !task || !onSave) return;

    const note: Note = {
      content: newNote.trim(),
      timestamp: new Date().toISOString(),
    };

    let updatedTask: Task;
    if (noteType === "research") {
      updatedTask = { ...task, researchNotes: [note, ...task.researchNotes] };
    } else if (noteType === "execution") {
      updatedTask = { ...task, executionNotes: [note, ...task.executionNotes] };
    } else {
      updatedTask = { ...task, notes: [note, ...task.notes] };
    }

    onSave(updatedTask);
    setNewNote("");
  }, [newNote, task, onSave, noteType]);

  if (!task) return null;

  // Calculate exit criteria progress
  const completedCriteria = exitCriteria.filter((c) => c.status === "COMPLETE").length;
  const totalCriteria = exitCriteria.length;
  const criteriaProgress = totalCriteria > 0 ? (completedCriteria / totalCriteria) * 100 : 0;

  // Combine all notes with type information
  const allNotes: NoteWithType[] = [
    ...task.researchNotes.map((n) => ({ ...n, type: "research" as const })),
    ...task.executionNotes.map((n) => ({ ...n, type: "execution" as const })),
    ...task.notes.map((n) => ({ ...n, type: "general" as const })),
  ].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

  // Total notes count
  const totalNotes = task.notes.length + task.researchNotes.length + task.executionNotes.length;

  return (
    <AnimatePresence>
      {isOpen && (
        <div
          className="fixed inset-0 z-[200000] flex items-end justify-center"
          data-testid="task-detail-modal"
        >
          {/* Backdrop */}
          <motion.div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            className={cn(
              "relative w-full max-w-[1200px] h-[calc(100vh-40px)]",
              "bg-[var(--bg-surface)] rounded-t-2xl",
              "border border-[var(--border)] border-b-0",
              "shadow-[0_-8px_32px_rgba(0,0,0,0.3)]",
              "flex flex-col overflow-hidden",
              className
            )}
            initial={{ y: "100%" }}
            animate={{ y: 0 }}
            exit={{ y: "100%" }}
            transition={{ type: "spring", damping: 30, stiffness: 300 }}
          >
            {/* Header */}
            <div className="flex items-start justify-between p-6 border-b border-[var(--border)]">
              <div className="flex-1 min-w-0 space-y-3">
                {/* Title */}
                {isEditing ? (
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    className={cn(
                      "w-full bg-transparent text-2xl font-bold",
                      "text-[var(--text-primary)] border-b border-[var(--border)]",
                      "focus:outline-none focus:border-[var(--primary)] py-1"
                    )}
                    placeholder="Task title..."
                  />
                ) : (
                  <Typography variant="h4" color="primary">
                    {task.title}
                  </Typography>
                )}

                {/* Badges */}
                <div className="flex items-center gap-2 flex-wrap">
                  {isEditing ? (
                    <select
                      value={status}
                      onChange={(e) => setStatus(e.target.value as TaskStatus)}
                      className={cn(
                        "bg-[var(--bg-surface)] border border-[var(--border)]",
                        "rounded-lg px-3 py-1.5 text-sm text-[var(--text-primary)]",
                        "focus:outline-none focus:border-[var(--primary)]"
                      )}
                    >
                      <option value="NOT_STARTED">Not Started</option>
                      <option value="IN_PROGRESS">In Progress</option>
                      <option value="BLOCKED">Blocked</option>
                      <option value="COMPLETED">Completed</option>
                    </select>
                  ) : (
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
                  )}

                  {isEditing ? (
                    <select
                      value={priority}
                      onChange={(e) => setPriority(e.target.value as TaskPriority)}
                      className={cn(
                        "bg-[var(--bg-surface)] border border-[var(--border)]",
                        "rounded-lg px-3 py-1.5 text-sm text-[var(--text-primary)]",
                        "focus:outline-none focus:border-[var(--primary)]"
                      )}
                    >
                      <option value="CRITICAL">Critical</option>
                      <option value="HIGH">High</option>
                      <option value="MEDIUM">Medium</option>
                      <option value="LOW">Low</option>
                      <option value="TRIVIAL">Trivial</option>
                    </select>
                  ) : (
                    <Badge variant={mapPriorityToVariant(task.priority)} size="sm">
                      {formatPriority(task.priority)}
                    </Badge>
                  )}

                  <div className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-[var(--bg-surface-hover)]">
                    <Calendar size={12} className="text-[var(--text-muted)]" />
                    <Typography variant="caption" color="muted">
                      {formatDate(task.createdAt)}
                    </Typography>
                  </div>

                  {task.updatedAt !== task.createdAt && (
                    <div className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-[var(--bg-surface-hover)]">
                      <Clock size={12} className="text-[var(--text-muted)]" />
                      <Typography variant="caption" color="muted">
                        Updated {formatDate(task.updatedAt)}
                      </Typography>
                    </div>
                  )}
                </div>
              </div>

              {/* Header Actions */}
              <div className="flex items-center gap-2">
                {!isEditing ? (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsEditing(true)}
                    leftIcon={<Edit2 size={16} />}
                  >
                    Edit
                  </Button>
                ) : (
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={handleSave}
                    leftIcon={<Save size={16} />}
                  >
                    Save
                  </Button>
                )}
                {onDelete && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleDelete}
                    className="text-[var(--error)] hover:bg-[var(--error)]/10"
                  >
                    <Trash2 size={16} />
                  </Button>
                )}
                <Button variant="ghost" size="sm" onClick={onClose}>
                  <X size={20} />
                </Button>
              </div>
            </div>

            {/* Description Section */}
            <div className="px-6 py-4 border-b border-[var(--border)] bg-[var(--bg-app)]">
              <div className="flex items-center gap-2 mb-2">
                <FileText size={14} className="text-[var(--text-muted)]" />
                <Typography variant="caption" color="muted" className="uppercase tracking-wider">
                  Description
                </Typography>
              </div>
              {isEditing ? (
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className={cn(
                    "w-full bg-[var(--bg-surface)] border border-[var(--border)]",
                    "rounded-lg p-3 text-sm text-[var(--text-primary)]",
                    "focus:outline-none focus:border-[var(--primary)]",
                    "resize-y min-h-[100px]"
                  )}
                  placeholder="Add a description..."
                />
              ) : (
                <Typography variant="body" color={task.description ? "secondary" : "muted"}>
                  {task.description || "No description provided."}
                </Typography>
              )}

              {/* Tags */}
              {(tags.length > 0 || isEditing) && (
                <div className="mt-4">
                  <div className="flex items-center gap-2 flex-wrap">
                    {tags.map((tag, idx) => (
                      <span
                        key={`${tag}-${idx}`}
                        className={cn(
                          "inline-flex items-center gap-1 px-2 py-1 rounded-full",
                          "bg-[var(--primary)]/10 text-[var(--primary)] text-xs font-medium"
                        )}
                      >
                        <Tag size={10} />
                        {tag}
                        {isEditing && (
                          <button
                            type="button"
                            onClick={() => handleRemoveTag(tag)}
                            className="ml-1 hover:text-[var(--error)]"
                          >
                            <X size={10} />
                          </button>
                        )}
                      </span>
                    ))}
                    {isEditing && (
                      <div className="flex items-center gap-1">
                        <input
                          type="text"
                          value={newTag}
                          onChange={(e) => setNewTag(e.target.value)}
                          onKeyPress={(e) => e.key === "Enter" && handleAddTag()}
                          className={cn(
                            "bg-transparent border-b border-[var(--border)]",
                            "text-xs text-[var(--text-primary)] py-1 px-2 w-24",
                            "focus:outline-none focus:border-[var(--primary)]"
                          )}
                          placeholder="Add tag..."
                        />
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Main Content */}
            <div className="flex-1 overflow-hidden grid grid-cols-1 md:grid-cols-2">
              {/* Left Column */}
              <div className="p-6 overflow-y-auto border-r border-[var(--border)] space-y-6">
                {/* Exit Criteria Section */}
                <div className="space-y-4" data-testid="exit-criteria-section">
                  <SectionHeader
                    icon={<Target size={18} />}
                    title="Exit Criteria"
                    action={
                      isEditing && (
                        <Button variant="ghost" size="sm" onClick={handleAddExitCriterion}>
                          <Plus size={14} />
                          Add
                        </Button>
                      )
                    }
                  />

                  {/* Progress bar */}
                  {totalCriteria > 0 && (
                    <div className="space-y-2">
                      <div className="h-2 bg-[var(--bg-surface-hover)] rounded-full overflow-hidden">
                        <div
                          className="h-full bg-[var(--success)] rounded-full transition-all duration-300"
                          style={{ width: `${criteriaProgress}%` }}
                        />
                      </div>
                      <Typography variant="caption" color="muted">
                        {completedCriteria} of {totalCriteria} complete
                      </Typography>
                    </div>
                  )}

                  {/* Criteria list */}
                  <div className="space-y-2">
                    {exitCriteria.length > 0 ? (
                      exitCriteria.map((criterion, idx) => (
                        <ExitCriterionItem
                          key={idx}
                          criterion={criterion}
                          index={idx}
                          isEditing={isEditing}
                          onToggle={handleToggleExitCriterion}
                          onChange={handleUpdateExitCriterion}
                          onDelete={handleDeleteExitCriterion}
                        />
                      ))
                    ) : (
                      <div className="p-4 text-center rounded-lg border border-dashed border-[var(--border)]">
                        <Typography variant="body-sm" color="muted">
                          No exit criteria defined
                        </Typography>
                      </div>
                    )}
                  </div>
                </div>

                {/* Dependencies Section */}
                <div className="space-y-4" data-testid="dependencies-section">
                  <SectionHeader
                    icon={<Link2 size={18} />}
                    title={`Dependencies (${dependencies.length})`}
                  />

                  <div className="space-y-2">
                    {dependencies.length > 0 ? (
                      dependencies.map((dep) => (
                        <DependencyItem
                          key={dep.taskId}
                          dependency={dep}
                          availableTasks={availableTasks}
                          isEditing={isEditing}
                          onRemove={handleRemoveDependency}
                        />
                      ))
                    ) : (
                      <div className="p-4 text-center rounded-lg border border-dashed border-[var(--border)]">
                        <Typography variant="body-sm" color="muted">
                          No dependencies
                        </Typography>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Right Column - Notes */}
              <div className="p-6 overflow-y-auto space-y-4" data-testid="notes-section">
                <SectionHeader
                  icon={<FileText size={18} />}
                  title={`Notes (${totalNotes})`}
                />

                {/* Note type selector */}
                <div className="flex gap-2">
                  {(["general", "research", "execution"] as const).map((type) => (
                    <button
                      key={type}
                      type="button"
                      onClick={() => setNoteType(type)}
                      className={cn(
                        "px-3 py-1.5 rounded-lg text-xs font-medium transition-colors",
                        noteType === type
                          ? "bg-[var(--primary)] text-white"
                          : "bg-[var(--bg-surface)] text-[var(--text-secondary)] hover:bg-[var(--bg-surface-hover)]"
                      )}
                    >
                      {type.charAt(0).toUpperCase() + type.slice(1)}
                    </button>
                  ))}
                </div>

                {/* Add note input */}
                <div className="flex gap-2">
                  <textarea
                    value={newNote}
                    onChange={(e) => setNewNote(e.target.value)}
                    className={cn(
                      "flex-1 bg-[var(--bg-surface)] border border-[var(--border)]",
                      "rounded-lg p-3 text-sm text-[var(--text-primary)]",
                      "focus:outline-none focus:border-[var(--primary)]",
                      "resize-none min-h-[80px]"
                    )}
                    placeholder={`Add ${noteType} note...`}
                  />
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={handleAddNote}
                    disabled={!newNote.trim()}
                    className="self-end"
                  >
                    <Plus size={16} />
                  </Button>
                </div>

                {/* Notes list */}
                <div className="space-y-3">
                  {allNotes.length > 0 ? (
                    allNotes.map((note, idx) => <NoteItem key={idx} note={note} />)
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
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

TaskDetailModal.displayName = "TaskDetailModal";

export default TaskDetailModal;
