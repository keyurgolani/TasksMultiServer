import React, { useState, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";
import { Button } from "../../atoms/Button";
import { Input } from "../../atoms/Input";
import { Typography } from "../../atoms/Typography";
import { useDataService } from "../../../context/DataServiceContext";
import { cn } from "../../../lib/utils";
import type { TaskList, Project } from "../../../core/types";
import styles from "./EditTaskListModal.module.css";

/**
 * EditTaskListModal Organism Component
 *
 * A modal dialog for editing existing task lists with form validation.
 * Pre-populates form fields with current task list data.
 * Implements glassmorphism effect and follows design system patterns.
 *
 * Requirements: 21.1, 21.2, 21.3, 21.4, 21.5
 * - 21.1: Display a modal overlay with a form pre-populated with current task list details
 * - 21.2: Validate that the task list name is not empty
 * - 21.3: Allow selection from available projects when changing project assignment
 * - 21.4: Update the task list and close the modal when form is submitted with valid data
 * - 21.5: Close the modal without saving changes when user clicks cancel or outside the modal
 *
 * Property 43: EditTaskListModal Pre-population
 * - For any EditTaskListModal opened with a task list, the form fields SHALL be
 *   pre-populated with the current task list data.
 *
 * Property 44: EditTaskListModal Update Flow
 * - For any valid EditTaskListModal submission, the component SHALL update the task list,
 *   call onSuccess, and close the modal.
 */

export interface EditTaskListModalProps {
  /** Whether the modal is open */
  isOpen: boolean;
  /** The task list to edit */
  taskList: TaskList;
  /** Callback fired when the modal should close */
  onClose: () => void;
  /** Callback fired when a task list is successfully updated */
  onSuccess: () => void;
  /** Additional CSS classes */
  className?: string;
}

/**
 * EditTaskListModal component for editing existing task lists
 */
export const EditTaskListModal: React.FC<EditTaskListModalProps> = ({
  isOpen,
  taskList,
  onClose,
  onSuccess,
  className,
}) => {
  // Form state - pre-populated with task list data
  const [name, setName] = useState(taskList.name);
  const [description, setDescription] = useState(taskList.description || "");
  const [projectId, setProjectId] = useState(taskList.projectId);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [projectError, setProjectError] = useState("");

  // Projects state for dropdown
  const [projects, setProjects] = useState<Project[]>([]);
  const [loadingProjects, setLoadingProjects] = useState(false);

  // Get data service from context
  const { dataService } = useDataService();

  // Load projects when modal opens
  useEffect(() => {
    if (isOpen) {
      setLoadingProjects(true);
      dataService
        .getProjects()
        .then((fetchedProjects) => {
          setProjects(fetchedProjects);
        })
        .catch((err) => {
          console.error("Failed to load projects:", err);
        })
        .finally(() => {
          setLoadingProjects(false);
        });
    }
  }, [isOpen, dataService]);

  // Reset form when modal opens or task list changes
  // Requirements: 21.1 - Pre-populate form with current task list details
  useEffect(() => {
    if (isOpen) {
      setName(taskList.name);
      setDescription(taskList.description || "");
      setProjectId(taskList.projectId);
      setError("");
      setProjectError("");
      setLoading(false);
    }
  }, [isOpen, taskList]);

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

  /**
   * Validates the form data
   * Requirements: 21.2 - Validate that the name is not empty
   * @returns true if valid, false otherwise
   */
  const validateForm = useCallback((): boolean => {
    const trimmedName = name.trim();
    let isValid = true;

    if (!trimmedName) {
      setError("Task list name is required");
      isValid = false;
    } else {
      setError("");
    }

    // Validate project selection - Requirements: 21.3
    if (!projectId) {
      setProjectError("Please select a project");
      isValid = false;
    } else {
      setProjectError("");
    }

    return isValid;
  }, [name, projectId]);

  /**
   * Handles form submission
   * Requirements: 21.4 - Update the task list and close the modal when form is submitted with valid data
   * Requirements: 21.3 - Allow selection from available projects when changing project assignment
   * Property 44: EditTaskListModal Update Flow
   */
  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      if (!validateForm()) {
        return;
      }

      setLoading(true);
      setError("");
      setProjectError("");

      try {
        await dataService.updateTaskList(taskList.id, {
          name: name.trim(),
          description: description.trim() || undefined,
          // Include projectId to support changing project assignment (Requirements: 21.3)
          projectId: projectId,
        });

        onSuccess();
        onClose();
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to update task list"
        );
      } finally {
        setLoading(false);
      }
    },
    [name, description, projectId, validateForm, dataService, taskList.id, onSuccess, onClose]
  );

  /**
   * Handles cancel action - closes modal without saving changes
   * Requirements: 21.5 - Close the modal without saving changes when user clicks cancel
   */
  const handleCancel = useCallback(() => {
    onClose();
  }, [onClose]);

  /**
   * Handles overlay/backdrop click (close modal without saving)
   * Requirements: 21.5 - Close the modal without saving changes when user clicks outside the modal
   */
  const handleOverlayClick = useCallback(
    (e: React.MouseEvent) => {
      if (e.target === e.currentTarget) {
        onClose();
      }
    },
    [onClose]
  );

  return (
    <AnimatePresence>
      {isOpen && (
        <div
          className={cn(styles.overlay, className)}
          data-testid="edit-task-list-modal"
        >
          {/* Backdrop with blur */}
          <motion.div
            className={styles.backdrop}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleOverlayClick}
          />

          {/* Modal with glassmorphism effect */}
          <motion.div
            className={styles.modal}
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header - Requirements: 21.5 - X button closes modal without saving */}
            <div className={styles.header}>
              <Typography variant="h5" color="primary">
                Edit Task List
              </Typography>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleCancel}
                aria-label="Close modal"
              >
                <X size={20} />
              </Button>
            </div>

            {/* Form - Requirements: 21.1 - Pre-populated with current task list details */}
            <form onSubmit={handleSubmit} className={styles.form}>
              {/* Task List Name Input - Requirements: 21.2 */}
              <Input
                label="Task List Name"
                type="text"
                value={name}
                onChange={(e) => {
                  setName(e.target.value);
                  if (error) setError("");
                }}
                placeholder="Enter task list name"
                state={error ? "error" : "default"}
                errorMessage={error || undefined}
                autoFocus
              />

              {/* Project Selection - Requirements: 21.3 */}
              <div className={styles.selectField}>
                <label className={styles.selectLabel}>Project</label>
                <select
                  value={projectId}
                  onChange={(e) => {
                    setProjectId(e.target.value);
                    if (projectError) setProjectError("");
                  }}
                  className={cn(styles.select, projectError && styles.error)}
                  disabled={loadingProjects}
                >
                  <option value="">
                    {loadingProjects ? "Loading projects..." : "Select a project"}
                  </option>
                  {projects.map((project) => (
                    <option key={project.id} value={project.id}>
                      {project.name}
                    </option>
                  ))}
                </select>
                {projectError && (
                  <span className={styles.selectError}>{projectError}</span>
                )}
              </div>

              {/* Description Input (optional) */}
              <div className={styles.textareaField}>
                <label className={styles.textareaLabel}>
                  Description (optional)
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Enter task list description"
                  className={styles.textarea}
                  rows={3}
                />
              </div>

              {/* Actions - Requirements: 21.5 - Cancel closes modal without saving */}
              <div className={styles.actions}>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={handleCancel}
                  disabled={loading}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  loading={loading}
                  disabled={loading || loadingProjects}
                >
                  {loading ? "Saving..." : "Save Changes"}
                </Button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default EditTaskListModal;
