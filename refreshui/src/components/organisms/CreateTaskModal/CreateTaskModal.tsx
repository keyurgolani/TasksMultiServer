import React, { useState, useCallback, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Plus, Target, Tag, AlertCircle, Link2, Check, MessageSquare, ChevronDown, ChevronUp, FileText, BookOpen } from "lucide-react";
import { Button } from "../../atoms/Button";
import { Input } from "../../atoms/Input";
import { Typography } from "../../atoms/Typography";
import { useDataService } from "../../../context/DataServiceContext";
import { cn } from "../../../lib/utils";
import type { TaskList, Task, TaskStatus, TaskPriority, ExitCriterion, TaskDependency, Note } from "../../../services/types";
import styles from "./CreateTaskModal.module.css";

/**
 * CreateTaskModal Organism Component
 *
 * A modal dialog for creating new tasks with comprehensive form.
 * Uses a two-column layout to reduce scrolling and improve usability.
 * Implements glassmorphism effect and follows design system patterns.
 */

export interface CreateTaskModalProps {
  isOpen: boolean;
  taskListId: string;
  onClose: () => void;
  onSuccess: () => void;
  className?: string;
}

const PRIORITY_OPTIONS: { value: TaskPriority; label: string }[] = [
  { value: "CRITICAL", label: "Critical" },
  { value: "HIGH", label: "High" },
  { value: "MEDIUM", label: "Medium" },
  { value: "LOW", label: "Low" },
  { value: "TRIVIAL", label: "Trivial" },
];

const STATUS_OPTIONS: { value: TaskStatus; label: string }[] = [
  { value: "NOT_STARTED", label: "Not Started" },
  { value: "IN_PROGRESS", label: "In Progress" },
  { value: "BLOCKED", label: "Blocked" },
  { value: "COMPLETED", label: "Completed" },
];

export const CreateTaskModal: React.FC<CreateTaskModalProps> = ({
  isOpen,
  taskListId,
  onClose,
  onSuccess,
  className,
}) => {
  // Form state
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [selectedTaskListId, setSelectedTaskListId] = useState(taskListId);
  const [priority, setPriority] = useState<TaskPriority>("MEDIUM");
  const [status, setStatus] = useState<TaskStatus>("NOT_STARTED");
  const [tags, setTags] = useState<string[]>([]);
  const [newTag, setNewTag] = useState("");
  const [exitCriteria, setExitCriteria] = useState<ExitCriterion[]>([]);
  const [selectedDependencies, setSelectedDependencies] = useState<TaskDependency[]>([]);
  const [dependencySearchQuery, setDependencySearchQuery] = useState("");
  const [notes, setNotes] = useState<Note[]>([]);
  const [newNote, setNewNote] = useState("");
  const [researchNotes, setResearchNotes] = useState<Note[]>([]);
  const [newResearchNote, setNewResearchNote] = useState("");
  
  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [titleError, setTitleError] = useState("");
  const [taskListError, setTaskListError] = useState("");
  const [expandedCriteria, setExpandedCriteria] = useState<Set<number>>(new Set());
  
  // Data state
  const [taskLists, setTaskLists] = useState<TaskList[]>([]);
  const [loadingTaskLists, setLoadingTaskLists] = useState(false);
  const [availableTasks, setAvailableTasks] = useState<Task[]>([]);
  const [loadingTasks, setLoadingTasks] = useState(false);

  const { dataService } = useDataService();

  // Load task lists when modal opens
  useEffect(() => {
    if (isOpen) {
      setLoadingTaskLists(true);
      dataService.getTaskLists()
        .then((fetchedTaskLists) => {
          setTaskLists(fetchedTaskLists);
          if (taskListId && fetchedTaskLists.some(tl => tl.id === taskListId)) {
            setSelectedTaskListId(taskListId);
          } else if (fetchedTaskLists.length > 0 && !selectedTaskListId) {
            setSelectedTaskListId(fetchedTaskLists[0].id);
          }
        })
        .catch((err) => console.error("Failed to load task lists:", err))
        .finally(() => setLoadingTaskLists(false));
    }
  }, [isOpen, dataService, taskListId, selectedTaskListId]);

  // Load available tasks for dependency selection
  useEffect(() => {
    if (isOpen) {
      setLoadingTasks(true);
      dataService.getTasks()
        .then((fetchedTasks) => setAvailableTasks(fetchedTasks))
        .catch((err) => console.error("Failed to load tasks:", err))
        .finally(() => setLoadingTasks(false));
    }
  }, [isOpen, dataService]);

  const filteredAvailableTasks = useMemo(() => {
    const query = dependencySearchQuery.toLowerCase().trim();
    if (!query) return availableTasks;
    return availableTasks.filter(
      (task) => task.title.toLowerCase().includes(query) ||
        (task.description && task.description.toLowerCase().includes(query))
    );
  }, [availableTasks, dependencySearchQuery]);

  const getTaskListName = useCallback((id: string): string => {
    return taskLists.find(tl => tl.id === id)?.name || "Unknown List";
  }, [taskLists]);

  // Reset form when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setTitle("");
      setDescription("");
      setSelectedTaskListId(taskListId);
      setPriority("MEDIUM");
      setStatus("NOT_STARTED");
      setTags([]);
      setNewTag("");
      setExitCriteria([]);
      setExpandedCriteria(new Set());
      setSelectedDependencies([]);
      setDependencySearchQuery("");
      setNotes([]);
      setNewNote("");
      setResearchNotes([]);
      setNewResearchNote("");
      setError("");
      setTitleError("");
      setTaskListError("");
      setLoading(false);
    }
  }, [isOpen, taskListId]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) onClose();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  const validateForm = useCallback((): boolean => {
    let isValid = true;
    if (!title.trim()) {
      setTitleError("Task title is required");
      isValid = false;
    } else {
      setTitleError("");
    }
    if (!selectedTaskListId) {
      setTaskListError("Please select a task list");
      isValid = false;
    } else {
      setTaskListError("");
    }
    return isValid;
  }, [title, selectedTaskListId]);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    setLoading(true);
    setError("");

    try {
      const validExitCriteria = exitCriteria
        .filter(ec => ec.criteria.trim())
        .map(ec => ({
          criteria: ec.criteria.trim(),
          status: ec.status,
          ...(ec.comment?.trim() ? { comment: ec.comment.trim() } : {}),
        }));

      const validNotes = notes.filter(n => n.content.trim());
      const validResearchNotes = researchNotes.filter(n => n.content.trim());

      await dataService.createTask({
        taskListId: selectedTaskListId,
        title: title.trim(),
        description: description.trim() || undefined,
        status,
        priority,
        dependencies: selectedDependencies.length > 0 ? selectedDependencies : undefined,
        exitCriteria: validExitCriteria.length > 0 ? validExitCriteria : undefined,
        tags: tags.length > 0 ? tags : undefined,
        notes: validNotes.length > 0 ? validNotes : undefined,
        researchNotes: validResearchNotes.length > 0 ? validResearchNotes : undefined,
      });

      onSuccess();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create task");
    } finally {
      setLoading(false);
    }
  }, [title, description, selectedTaskListId, status, priority, selectedDependencies, 
      exitCriteria, tags, notes, researchNotes, validateForm, dataService, onSuccess, onClose]);

  const handleOverlayClick = useCallback((e: React.MouseEvent) => {
    if (e.target === e.currentTarget) onClose();
  }, [onClose]);

  // Tag handlers
  const addTag = useCallback(() => {
    const trimmed = newTag.trim();
    if (trimmed && !tags.includes(trimmed)) {
      setTags([...tags, trimmed]);
      setNewTag("");
    }
  }, [newTag, tags]);

  const removeTag = useCallback((tag: string) => setTags(tags.filter(t => t !== tag)), [tags]);

  // Notes handlers
  const addNote = useCallback(() => {
    const trimmed = newNote.trim();
    if (trimmed) {
      setNotes([...notes, { content: trimmed, timestamp: new Date().toISOString() }]);
      setNewNote("");
    }
  }, [newNote, notes]);

  const removeNote = useCallback((index: number) => setNotes(notes.filter((_, i) => i !== index)), [notes]);

  // Research notes handlers
  const addResearchNote = useCallback(() => {
    const trimmed = newResearchNote.trim();
    if (trimmed) {
      setResearchNotes([...researchNotes, { content: trimmed, timestamp: new Date().toISOString() }]);
      setNewResearchNote("");
    }
  }, [newResearchNote, researchNotes]);

  const removeResearchNote = useCallback((index: number) => 
    setResearchNotes(researchNotes.filter((_, i) => i !== index)), [researchNotes]);

  // Exit criteria handlers
  const addExitCriterion = useCallback(() => {
    setExitCriteria([...exitCriteria, { criteria: "", status: "INCOMPLETE" as const, comment: "" }]);
  }, [exitCriteria]);

  const updateExitCriterionText = useCallback((index: number, value: string) => {
    const newCriteria = [...exitCriteria];
    newCriteria[index] = { ...newCriteria[index], criteria: value };
    setExitCriteria(newCriteria);
  }, [exitCriteria]);

  const updateExitCriterionStatus = useCallback((index: number, status: "INCOMPLETE" | "COMPLETE") => {
    const newCriteria = [...exitCriteria];
    newCriteria[index] = { ...newCriteria[index], status };
    setExitCriteria(newCriteria);
  }, [exitCriteria]);

  const updateExitCriterionComment = useCallback((index: number, comment: string) => {
    const newCriteria = [...exitCriteria];
    newCriteria[index] = { ...newCriteria[index], comment };
    setExitCriteria(newCriteria);
  }, [exitCriteria]);

  const removeExitCriterion = useCallback((index: number) => {
    setExitCriteria(exitCriteria.filter((_, i) => i !== index));
    setExpandedCriteria(prev => {
      const newSet = new Set<number>();
      prev.forEach(i => { if (i !== index) newSet.add(i > index ? i - 1 : i); });
      return newSet;
    });
  }, [exitCriteria]);

  const toggleCriterionExpanded = useCallback((index: number) => {
    setExpandedCriteria(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  }, []);

  // Dependency handlers
  const isDependencySelected = useCallback((task: Task): boolean => {
    return selectedDependencies.some(dep => dep.taskId === task.id && dep.taskListId === task.taskListId);
  }, [selectedDependencies]);

  const toggleDependency = useCallback((task: Task) => {
    if (isDependencySelected(task)) {
      setSelectedDependencies(selectedDependencies.filter(
        dep => !(dep.taskId === task.id && dep.taskListId === task.taskListId)
      ));
    } else {
      setSelectedDependencies([...selectedDependencies, { taskId: task.id, taskListId: task.taskListId }]);
    }
  }, [selectedDependencies, isDependencySelected]);

  const removeDependency = useCallback((dep: TaskDependency) => {
    setSelectedDependencies(selectedDependencies.filter(
      d => !(d.taskId === dep.taskId && d.taskListId === dep.taskListId)
    ));
  }, [selectedDependencies]);

  const getTaskById = useCallback((taskId: string) => availableTasks.find(t => t.id === taskId), [availableTasks]);

  return (
    <AnimatePresence>
      {isOpen && (
        <div className={cn(styles.overlay, className)} data-testid="create-task-modal">
          <motion.div
            className={styles.backdrop}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleOverlayClick}
          />

          <motion.div
            className={styles.modal}
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className={styles.header}>
              <Typography variant="h5" color="primary">Create Task</Typography>
              <Button variant="ghost" size="sm" onClick={onClose} aria-label="Close modal">
                <X size={20} />
              </Button>
            </div>

            <form onSubmit={handleSubmit} className={styles.form}>
              {error && (
                <div className={styles.errorMessage}>
                  <AlertCircle size={16} />
                  <span>{error}</span>
                </div>
              )}

              <div className={styles.twoColumnLayout}>
                {/* Left Column */}
                <div className={styles.column}>
                  {/* Required Fields */}
                  <div className={styles.section}>
                    <Typography variant="label" color="secondary" className={styles.sectionLabel}>
                      Required Information
                    </Typography>
                    
                    <Input
                      label="Task Title"
                      type="text"
                      value={title}
                      onChange={(e) => { setTitle(e.target.value); if (titleError) setTitleError(""); }}
                      placeholder="Enter task title"
                      state={titleError ? "error" : "default"}
                      errorMessage={titleError || undefined}
                      autoFocus
                    />

                    <div className={styles.selectField}>
                      <label className={styles.selectLabel}>Task List</label>
                      <select
                        value={selectedTaskListId}
                        onChange={(e) => { setSelectedTaskListId(e.target.value); if (taskListError) setTaskListError(""); }}
                        className={cn(styles.select, taskListError && styles.error)}
                        disabled={loadingTaskLists}
                      >
                        <option value="">{loadingTaskLists ? "Loading..." : "Select a task list"}</option>
                        {taskLists.map((tl) => (
                          <option key={tl.id} value={tl.id}>{tl.name}</option>
                        ))}
                      </select>
                      {taskListError && <span className={styles.selectError}>{taskListError}</span>}
                    </div>

                    <div className={styles.row}>
                      <div className={styles.selectField}>
                        <label className={styles.selectLabel}>Priority</label>
                        <select value={priority} onChange={(e) => setPriority(e.target.value as TaskPriority)} className={styles.select}>
                          {PRIORITY_OPTIONS.map((opt) => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                        </select>
                      </div>
                      <div className={styles.selectField}>
                        <label className={styles.selectLabel}>Status</label>
                        <select value={status} onChange={(e) => setStatus(e.target.value as TaskStatus)} className={styles.select}>
                          {STATUS_OPTIONS.map((opt) => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                        </select>
                      </div>
                    </div>
                  </div>

                  {/* Description */}
                  <div className={styles.textareaField}>
                    <label className={styles.textareaLabel}>Description (optional)</label>
                    <textarea
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      placeholder="Enter task description"
                      className={styles.textarea}
                      rows={3}
                    />
                  </div>

                  {/* Tags */}
                  <div className={styles.section}>
                    <div className={styles.sectionHeader}>
                      <div className={styles.sectionTitle}>
                        <Tag size={16} />
                        <span>Tags</span>
                        {tags.length > 0 && <span className={styles.badge}>{tags.length}</span>}
                      </div>
                    </div>
                    <div className={styles.tagsContainer}>
                      {tags.length > 0 && (
                        <div className={styles.tagsList}>
                          {tags.map((tag) => (
                            <span key={tag} className={styles.tag}>
                              {tag}
                              <button type="button" onClick={() => removeTag(tag)} className={styles.tagRemove}>
                                <X size={12} />
                              </button>
                            </span>
                          ))}
                        </div>
                      )}
                      <div className={styles.inputRow}>
                        <input
                          type="text"
                          value={newTag}
                          onChange={(e) => setNewTag(e.target.value)}
                          onKeyPress={(e) => { if (e.key === "Enter") { e.preventDefault(); addTag(); } }}
                          placeholder="Add a tag..."
                          className={styles.smallInput}
                        />
                        <Button type="button" variant="secondary" size="sm" onClick={addTag} disabled={!newTag.trim()}>
                          <Plus size={14} />
                        </Button>
                      </div>
                    </div>
                  </div>

                  {/* Dependencies */}
                  <div className={styles.section}>
                    <div className={styles.sectionHeader}>
                      <div className={styles.sectionTitle}>
                        <Link2 size={16} />
                        <span>Dependencies</span>
                        {selectedDependencies.length > 0 && <span className={styles.badge}>{selectedDependencies.length}</span>}
                      </div>
                    </div>
                    
                    {selectedDependencies.length > 0 && (
                      <div className={styles.chipList}>
                        {selectedDependencies.map((dep) => {
                          const task = getTaskById(dep.taskId);
                          return (
                            <div key={`${dep.taskListId}-${dep.taskId}`} className={styles.chip}>
                              <span className={styles.chipText}>{task?.title || "Unknown"}</span>
                              <button type="button" onClick={() => removeDependency(dep)} className={styles.chipRemove}>
                                <X size={12} />
                              </button>
                            </div>
                          );
                        })}
                      </div>
                    )}

                    <input
                      type="text"
                      value={dependencySearchQuery}
                      onChange={(e) => setDependencySearchQuery(e.target.value)}
                      placeholder="Search tasks..."
                      className={styles.searchInput}
                    />

                    <div className={styles.listContainer}>
                      {loadingTasks ? (
                        <div className={styles.emptyState}>Loading...</div>
                      ) : filteredAvailableTasks.length > 0 ? (
                        filteredAvailableTasks.map((task) => (
                          <div
                            key={task.id}
                            className={cn(styles.listItem, isDependencySelected(task) && styles.listItemSelected)}
                            onClick={() => toggleDependency(task)}
                            role="checkbox"
                            aria-checked={isDependencySelected(task)}
                            tabIndex={0}
                            onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggleDependency(task); } }}
                          >
                            <div className={styles.listItemCheckbox}>
                              {isDependencySelected(task) && <Check size={12} />}
                            </div>
                            <div className={styles.listItemContent}>
                              <span className={styles.listItemTitle}>{task.title}</span>
                              <span className={styles.listItemMeta}>{getTaskListName(task.taskListId)}</span>
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className={styles.emptyState}>No tasks available</div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Right Column */}
                <div className={styles.column}>
                  {/* General Notes */}
                  <div className={styles.section}>
                    <div className={styles.sectionHeader}>
                      <div className={styles.sectionTitle}>
                        <FileText size={16} />
                        <span>Notes</span>
                        {notes.length > 0 && <span className={styles.badge}>{notes.length}</span>}
                      </div>
                    </div>
                    <div className={styles.notesContainer}>
                      {notes.length > 0 && (
                        <div className={styles.notesList}>
                          {notes.map((note, index) => (
                            <div key={index} className={styles.noteItem}>
                              <span className={styles.noteContent}>{note.content}</span>
                              <button type="button" onClick={() => removeNote(index)} className={styles.noteRemove}>
                                <X size={14} />
                              </button>
                            </div>
                          ))}
                        </div>
                      )}
                      <div className={styles.noteInputRow}>
                        <textarea
                          value={newNote}
                          onChange={(e) => setNewNote(e.target.value)}
                          onKeyPress={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); addNote(); } }}
                          placeholder="Add a note..."
                          className={styles.noteInput}
                          rows={2}
                        />
                        <Button type="button" variant="secondary" size="sm" onClick={addNote} disabled={!newNote.trim()}>
                          <Plus size={14} />
                        </Button>
                      </div>
                    </div>
                  </div>

                  {/* Research Notes */}
                  <div className={styles.section}>
                    <div className={styles.sectionHeader}>
                      <div className={styles.sectionTitle}>
                        <BookOpen size={16} />
                        <span>Research Notes</span>
                        {researchNotes.length > 0 && <span className={styles.badge}>{researchNotes.length}</span>}
                      </div>
                    </div>
                    <div className={styles.notesContainer}>
                      {researchNotes.length > 0 && (
                        <div className={styles.notesList}>
                          {researchNotes.map((note, index) => (
                            <div key={index} className={styles.noteItem}>
                              <span className={styles.noteContent}>{note.content}</span>
                              <button type="button" onClick={() => removeResearchNote(index)} className={styles.noteRemove}>
                                <X size={14} />
                              </button>
                            </div>
                          ))}
                        </div>
                      )}
                      <div className={styles.noteInputRow}>
                        <textarea
                          value={newResearchNote}
                          onChange={(e) => setNewResearchNote(e.target.value)}
                          onKeyPress={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); addResearchNote(); } }}
                          placeholder="Add research note..."
                          className={styles.noteInput}
                          rows={2}
                        />
                        <Button type="button" variant="secondary" size="sm" onClick={addResearchNote} disabled={!newResearchNote.trim()}>
                          <Plus size={14} />
                        </Button>
                      </div>
                    </div>
                  </div>

                  {/* Exit Criteria */}
                  <div className={styles.section}>
                    <div className={styles.sectionHeader}>
                      <div className={styles.sectionTitle}>
                        <Target size={16} />
                        <span>Exit Criteria</span>
                        {exitCriteria.length > 0 && (
                          <span className={styles.badge}>
                            {exitCriteria.filter(c => c.status === "COMPLETE").length}/{exitCriteria.length}
                          </span>
                        )}
                      </div>
                      <button type="button" onClick={addExitCriterion} className={styles.addButton}>
                        <Plus size={14} />
                        Add
                      </button>
                    </div>
                    
                    <div className={styles.exitCriteriaList}>
                      {exitCriteria.length > 0 ? (
                        exitCriteria.map((criterion, index) => (
                          <div 
                            key={index} 
                            className={cn(styles.exitCriterionItem, criterion.status === "COMPLETE" && styles.exitCriterionComplete)}
                          >
                            <div className={styles.exitCriterionMain}>
                              <button
                                type="button"
                                onClick={() => updateExitCriterionStatus(index, criterion.status === "COMPLETE" ? "INCOMPLETE" : "COMPLETE")}
                                className={cn(styles.exitCriterionCheckbox, criterion.status === "COMPLETE" && styles.exitCriterionCheckboxChecked)}
                              >
                                {criterion.status === "COMPLETE" && <Check size={12} />}
                              </button>

                              <input
                                type="text"
                                value={criterion.criteria}
                                onChange={(e) => updateExitCriterionText(index, e.target.value)}
                                placeholder="Enter criterion..."
                                className={cn(styles.exitCriterionInput, criterion.status === "COMPLETE" && styles.exitCriterionInputComplete)}
                              />
                              
                              <button
                                type="button"
                                onClick={() => toggleCriterionExpanded(index)}
                                className={cn(styles.iconButton, (expandedCriteria.has(index) || criterion.comment) && styles.iconButtonActive)}
                              >
                                <MessageSquare size={14} />
                                {expandedCriteria.has(index) ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
                              </button>
                              
                              <button type="button" onClick={() => removeExitCriterion(index)} className={styles.deleteButton}>
                                <X size={14} />
                              </button>
                            </div>
                            
                            {expandedCriteria.has(index) && (
                              <div className={styles.exitCriterionComment}>
                                <textarea
                                  value={criterion.comment || ""}
                                  onChange={(e) => updateExitCriterionComment(index, e.target.value)}
                                  placeholder="Add comment..."
                                  className={styles.commentInput}
                                  rows={2}
                                />
                              </div>
                            )}
                          </div>
                        ))
                      ) : (
                        <div className={styles.emptyState}>No exit criteria defined</div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </form>

            <div className={styles.actions}>
              <Button type="button" variant="secondary" onClick={onClose} disabled={loading}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" loading={loading} disabled={loading || loadingTaskLists} onClick={handleSubmit}>
                {loading ? "Creating..." : "Create Task"}
              </Button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default CreateTaskModal;
