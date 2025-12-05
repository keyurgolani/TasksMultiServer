import React, { useState, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";
import { Button } from "../../atoms/Button";
import { Input } from "../../atoms/Input";
import { Typography } from "../../atoms/Typography";
import { useDataService } from "../../../context/DataServiceContext";
import { cn } from "../../../lib/utils";
import type { Project } from "../../../services/types";
import styles from "./CreateTaskListModal.module.css";

/**
 * CreateTaskListModal Organism Component
 *
 * A modal dialog for creating new task lists with form validation.
 * Implements glassmorphism effect and follows design system patterns.
 *
 * Requirements: 17.1, 17.2, 17.6
 * - 17.1: Display a modal overlay with a form for task list details
 * - 17.2: Validate that the task list name is not empty
 * - 17.3: Allow project selection for task list association
 * - 17.6: Apply consistent styling with other modal components (glassmorphism,
 *         centered viewport positioning, same spacing tokens, matching animations)
 *
 * Property 37: CreateTaskListModal Form Validation
 * - For any CreateTaskListModal submission, the form SHALL validate
 *   that the task list name is not empty and a project is selected.
 */

export interface CreateTaskListModalProps {
  /** Whether the modal is open */
  isOpen: boolean;
  /** Callback fired when the modal should close */
  onClose: () => void;
  /** Callback fired when a task list is successfully created */
  onSuccess: () => void;
  /** Optional pre-selected project ID */
  defaultProjectId?: string;
  /** Additional CSS classes */
  className?: string;
}

/**
 * CreateTaskListModal component for creating new task lists
 */
export const CreateTaskListModal: React.FC<CreateTaskListModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  defaultProjectId,
  className,
}) => {
  // Form state
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [projectId, setProjectId] = useState(defaultProjectId || "");
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
          // If defaultProjectId is provided and valid, use it
          if (defaultProjectId && fetchedProjects.some(p => p.id === defaultProjectId)) {
            setProjectId(defaultProjectId);
          } else if (fetchedProjects.length > 0) {
            // Auto-select first project if none selected
            setProjectId((currentProjectId) => 
              currentProjectId || fetchedProjects[0].id
            );
          }
        })
        .catch((err) => {
          console.error("Failed to load projects:", err);
        })
        .finally(() => {
          setLoadingProjects(false);
        });
    }
  }, [isOpen, dataService, defaultProjectId]);

  // Reset form when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setName("");
      setDescription("");
      setProjectId(defaultProjectId || "");
      setError("");
      setProjectError("");
      setLoading(false);
    }
  }, [isOpen, defaultProjectId]);

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
   * @returns true if valid, false otherwise
   */
  const validateForm = useCallback((): boolean => {
    const trimmedName = name.trim();
    let isValid = true;

    // Validate name - Requirements: 17.2
    if (!trimmedName) {
      setError("Task list name is required");
      isValid = false;
    } else {
      setError("");
    }

    // Validate project selection - Requirements: 17.3
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
        await dataService.createTaskList({
          name: name.trim(),
          projectId: projectId,
          description: description.trim() || undefined,
        });

        onSuccess();
        onClose();
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to create task list"
        );
      } finally {
        setLoading(false);
      }
    },
    [name, description, projectId, validateForm, dataService, onSuccess, onClose]
  );

  /**
   * Handles overlay click (close modal)
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
          data-testid="create-task-list-modal"
        >
          {/* Backdrop with blur - Requirements: 17.6 */}
          <motion.div
            className={styles.backdrop}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleOverlayClick}
          />

          {/* Modal with glassmorphism effect - Requirements: 17.6 */}
          <motion.div
            className={styles.modal}
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className={styles.header}>
              <Typography variant="h5" color="primary">
                Create Task List
              </Typography>
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                aria-label="Close modal"
              >
                <X size={20} />
              </Button>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className={styles.form}>
              {/* Task List Name Input - Requirements: 17.2 */}
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

              {/* Project Selection - Requirements: 17.3 */}
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

              {/* Actions */}
              <div className={styles.actions}>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={onClose}
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
                  {loading ? "Creating..." : "Create Task List"}
                </Button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default CreateTaskListModal;
