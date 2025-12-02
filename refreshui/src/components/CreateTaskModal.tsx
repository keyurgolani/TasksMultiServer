import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Plus, CheckSquare, FileText, Target, Tag } from "lucide-react";
import { useToast } from "../context/ToastContext";
import { PrioritySelector } from "./PrioritySelector";
import { ExitCriteriaItem } from "./ExitCriteriaItem";
import { ActionPlanItem } from "./ActionPlanItem";
import { DependencySection } from "./DependencySection";
import type {
  ActionPlanItem as ActionPlanItemType,
  ExitCriterion,
  Task,
} from "../api/client";
import styles from "./TaskDetailModal.module.css"; // Reuse same CSS

interface CreateTaskModalProps {
  taskListId: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  availableTasks?: Task[];
}

export const CreateTaskModal: React.FC<CreateTaskModalProps> = ({
  taskListId,
  isOpen,
  onClose,
  onSuccess,
  availableTasks,
}) => {
  const { success, error: toastError } = useToast();
  // Form State
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState<Task["priority"]>("MEDIUM");
  const [tags, setTags] = useState<string[]>([]);
  const [newTag, setNewTag] = useState("");
  const [actionPlan, setActionPlan] = useState<ActionPlanItemType[]>([]);
  const [exitCriteria, setExitCriteria] = useState<ExitCriterion[]>([]);
  const [dependencies, setDependencies] = useState<string[]>([]);
  const [newNote, setNewNote] = useState("");
  const [noteType, setNoteType] = useState<
    "general" | "research" | "execution"
  >("general");
  const [notes, setNotes] = useState<
    { type: "general" | "research" | "execution"; content: string }[]
  >([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Action Plan Handlers
  const addActionItem = () => {
    setActionPlan([
      ...actionPlan,
      { sequence: actionPlan.length + 1, content: "" },
    ]);
  };

  const updateActionItem = (index: number, content: string) => {
    const newPlan = [...actionPlan];
    newPlan[index] = { ...newPlan[index], content };
    setActionPlan(newPlan);
  };

  const removeActionItem = (index: number) => {
    const newPlan = actionPlan
      .filter((_, i) => i !== index)
      .map((item, i) => ({ ...item, sequence: i + 1 }));
    setActionPlan(newPlan);
  };

  // Exit Criteria Handlers
  const addExitCriterion = () => {
    setExitCriteria([
      ...exitCriteria,
      { sequence: exitCriteria.length + 1, criteria: "", status: "INCOMPLETE" },
    ]);
  };

  const updateExitCriterion = (index: number, criteria: string) => {
    const newCriteria = [...exitCriteria];
    newCriteria[index] = { ...newCriteria[index], criteria };
    setExitCriteria(newCriteria);
  };

  const toggleExitCriterionStatus = (index: number) => {
    const newCriteria = [...exitCriteria];
    newCriteria[index] = {
      ...newCriteria[index],
      status:
        newCriteria[index].status === "COMPLETE" ? "INCOMPLETE" : "COMPLETE",
    };
    setExitCriteria(newCriteria);
  };

  const removeExitCriterion = (index: number) => {
    const newCriteria = exitCriteria
      .filter((_, i) => i !== index)
      .map((item, i) => ({ ...item, sequence: i + 1 }));
    setExitCriteria(newCriteria);
  };

  // Dependency Handlers
  const addDependency = (dependencyId: string) => {
    if (!dependencies.includes(dependencyId)) {
      setDependencies([...dependencies, dependencyId]);
    }
  };

  const removeDependency = (dependencyId: string) => {
    setDependencies(dependencies.filter(id => id !== dependencyId));
  };

  // Tag Handlers
  const addTag = () => {
    if (newTag.trim() && !tags.includes(newTag.trim())) {
      setTags([...tags, newTag.trim()]);
      setNewTag("");
    }
  };

  const removeTag = (tag: string) => {
    setTags(tags.filter((t) => t !== tag));
  };

  // Note Handlers
  const addNote = () => {
    if (!newNote.trim()) return;
    setNotes([{ type: noteType, content: newNote.trim() }, ...notes]);
    setNewNote("");
  };

  const handleCreate = async () => {
    if (!title.trim()) {
      setError("Title is required");
      return;
    }

    if (exitCriteria.length === 0) {
      setError("At least one exit criterion is required");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task_list_id: taskListId,
          title: title.trim(),
          description: description.trim(),
          priority,
          tags,
          action_plan: actionPlan.filter((item) => item.content.trim()),
          exit_criteria: exitCriteria.filter((item) => item.criteria.trim()),
          notes: notes
            .filter((n) => n.type === "general")
            .map((n, i) => ({ sequence: i + 1, content: n.content })),
          research_notes: notes
            .filter((n) => n.type === "research")
            .map((n, i) => ({ sequence: i + 1, content: n.content })),
          execution_notes: notes
            .filter((n) => n.type === "execution")
            .map((n, i) => ({ sequence: i + 1, content: n.content })),
          dependencies: dependencies,
        }),
      });

      if (!response.ok) throw new Error("Failed to create task");

      success("Task created successfully");
      onSuccess();
      onClose();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to create task";
      setError(message);
      toastError(message);
    } finally {
      setLoading(false);
    }
  };

  const completedCriteria = exitCriteria.filter(
    (c) => c.status === "COMPLETE"
  ).length;
  const totalCriteria = exitCriteria.length;
  const criteriaProgress =
    totalCriteria > 0 ? (completedCriteria / totalCriteria) * 100 : 0;

  return (
    <AnimatePresence>
      {isOpen && (
        <div className={styles.modalWrapper}>
          <motion.div
            className={styles.overlay}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
          <motion.div
            className={styles.modal}
            initial={{ y: "100%" }}
            animate={{ y: 0 }}
            exit={{ y: "100%" }}
            transition={{ type: "spring", damping: 30, stiffness: 300 }}
          >
            {/* Header */}
            <div className={styles.header}>
              <div className={styles.headerContent}>
                <div className={styles.titleRow}>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    className={styles.titleInput}
                    placeholder="Task title..."
                    autoFocus
                  />
                </div>
                <div className={styles.badges}>
                  <PrioritySelector value={priority} onChange={setPriority} />
                </div>
              </div>

              <div className={styles.headerActions}>
                <button className={styles.closeButton} onClick={onClose}>
                  <X size={20} />
                </button>
              </div>
            </div>

            {/* Hero Section */}
            <div className={styles.hero}>
              <div className={styles.descriptionSection}>
                <div className={styles.sectionLabel}>
                  <FileText size={12} />
                  Description
                </div>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className={styles.textarea}
                  rows={4}
                  placeholder="Add a description..."
                />
              </div>

              <div className={styles.metadata}>
                {tags.length > 0 && (
                  <div className={styles.tagsList}>
                    {tags.map((tag, idx) => (
                      <span key={idx} className={styles.tag}>
                        <Tag size={10} />
                        {tag}
                        <button
                          type="button"
                          onClick={() => removeTag(tag)}
                          className={styles.tagRemove}
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}
                <div className={styles.tagsInputContainer}>
                  <input
                    type="text"
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && addTag()}
                    className={styles.tagInput}
                    placeholder="Add tag..."
                  />
                </div>
              </div>
            </div>

            <div className={styles.content}>
              {/* Left Column: Action Plan */}
              <div className={styles.leftCol}>
                <div className={styles.section}>
                  <div className={styles.sectionHeader}>
                    <div className={styles.sectionTitle}>
                      <CheckSquare size={18} />
                      <h3>Action Plan</h3>
                    </div>
                    <button
                      onClick={addActionItem}
                      className={styles.addButton}
                    >
                      <Plus size={14} /> Add Item
                    </button>
                  </div>
                  <div className={styles.list}>
                    {actionPlan.length > 0 ? (
                      actionPlan.map((item, idx) => (
                        <ActionPlanItem
                          key={idx}
                          item={item}
                          index={idx}
                          isEditing={true}
                          onChange={updateActionItem}
                          onDelete={removeActionItem}
                        />
                      ))
                    ) : (
                      <div className={styles.emptyState}>
                        No action plan defined (optional)
                      </div>
                    )}
                  </div>
                </div>

                {/* Dependencies */}
                <div className={styles.section}>
                  <DependencySection
                    dependencies={dependencies}
                    availableTasks={availableTasks || []}
                    currentTaskId={undefined}
                    onAdd={addDependency}
                    onRemove={removeDependency}
                    isEditing={true}
                  />
                </div>
              </div>

              {/* Right Column: Exit Criteria & Notes */}
              <div className={styles.rightCol}>
                {/* Exit Criteria */}
                <div className={styles.section}>
                  <div className={styles.sectionHeader}>
                    <div className={styles.sectionTitle}>
                      <Target size={18} />
                      <h3>Exit Criteria</h3>
                    </div>
                    <button
                      onClick={addExitCriterion}
                      className={styles.addButton}
                    >
                      <Plus size={14} /> Add Criteria
                    </button>
                  </div>

                  {totalCriteria > 0 && (
                    <div className={styles.progress}>
                      <div className={styles.progressBar}>
                        <div
                          className={styles.progressFill}
                          style={{ width: `${criteriaProgress}%` }}
                        />
                      </div>
                      <div className={styles.progressText}>
                        {completedCriteria} of {totalCriteria} complete
                      </div>
                    </div>
                  )}

                  <div className={styles.list}>
                    {exitCriteria.length > 0 ? (
                      exitCriteria.map((criterion, idx) => (
                        <ExitCriteriaItem
                          key={idx}
                          criterion={criterion}
                          index={idx}
                          isEditing={true}
                          onToggle={toggleExitCriterionStatus}
                          onChange={updateExitCriterion}
                          onDelete={removeExitCriterion}
                        />
                      ))
                    ) : (
                      <div className={styles.emptyState}>
                        At least one exit criterion required
                      </div>
                    )}
                  </div>
                </div>

                {/* Notes */}
                <div className={styles.section}>
                  <div className={styles.sectionHeader}>
                    <div className={styles.sectionTitle}>
                      <FileText size={18} />
                      <h3>Initial Notes</h3>
                    </div>
                  </div>

                  <div className={styles.notesContainer}>
                    <div className={styles.noteTypeSelector}>
                      <button
                        className={`${styles.noteTypeBtn} ${
                          noteType === "general" ? styles.active : ""
                        }`}
                        onClick={() => setNoteType("general")}
                      >
                        General
                      </button>
                      <button
                        className={`${styles.noteTypeBtn} ${
                          noteType === "research" ? styles.active : ""
                        }`}
                        onClick={() => setNoteType("research")}
                      >
                        Research
                      </button>
                      <button
                        className={`${styles.noteTypeBtn} ${
                          noteType === "execution" ? styles.active : ""
                        }`}
                        onClick={() => setNoteType("execution")}
                      >
                        Execution
                      </button>
                    </div>

                    <div className={styles.noteInput}>
                      <textarea
                        value={newNote}
                        onChange={(e) => setNewNote(e.target.value)}
                        className={styles.noteTextarea}
                        placeholder={`Add ${noteType} note...`}
                      />
                      <button onClick={addNote} className={styles.addButton}>
                        <Plus size={14} />
                      </button>
                    </div>

                    <div className={styles.list}>
                      {notes.length > 0 ? (
                        <div
                          style={{
                            fontSize: "14px",
                            color: "var(--text-secondary)",
                          }}
                        >
                          {notes.length} note{notes.length > 1 ? "s" : ""} added
                        </div>
                      ) : (
                        <div className={styles.emptyState}>
                          No notes yet (optional)
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Footer with Create Button */}
            <div
              style={{
                padding: "20px 32px",
                borderTop: "1px solid var(--border)",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                background: "var(--bg-surface)",
              }}
            >
              {error && (
                <div style={{ color: "#ef4444", fontSize: "14px" }}>
                  {error}
                </div>
              )}
              <div style={{ marginLeft: "auto", display: "flex", gap: "12px" }}>
                <button
                  onClick={onClose}
                  style={{
                    padding: "10px 20px",
                    borderRadius: "8px",
                    border: "1px solid var(--border)",
                    background: "transparent",
                    color: "var(--text-primary)",
                    cursor: "pointer",
                    fontSize: "14px",
                    fontWeight: 500,
                  }}
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreate}
                  disabled={loading}
                  style={{
                    padding: "10px 24px",
                    borderRadius: "8px",
                    border: "none",
                    background:
                      "linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%)",
                    color: "white",
                    cursor: loading ? "not-allowed" : "pointer",
                    fontSize: "14px",
                    fontWeight: 600,
                    opacity: loading ? 0.6 : 1,
                  }}
                >
                  {loading ? "Creating..." : "Create Task"}
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
