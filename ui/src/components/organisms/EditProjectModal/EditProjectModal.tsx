import React, { useState, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";
import { Button } from "../../atoms/Button";
import { Input } from "../../atoms/Input";
import { Typography } from "../../atoms/Typography";
import { useDataService } from "../../../context/DataServiceContext";
import { cn } from "../../../lib/utils";
import type { Project } from "../../../core/types";
import styles from "./EditProjectModal.module.css";

/**
 * EditProjectModal Organism Component
 *
 * A modal dialog for editing existing projects with form validation.
 * Pre-populates form fields with current project data.
 * Implements glassmorphism effect and follows design system patterns.
 *
 * Requirements: 19.1, 19.2, 19.3, 19.4
 * - 19.1: Display a modal overlay with a form pre-populated with current project details
 * - 19.2: Validate that the project name is not empty
 * - 19.3: Update the project and close the modal when form is submitted with valid data
 * - 19.4: Close the modal without saving changes when user clicks cancel or outside the modal
 *
 * Property 41: EditProjectModal Pre-population
 * - For any EditProjectModal opened with a project, the form fields SHALL be
 *   pre-populated with the current project data.
 *
 * Property 42: EditProjectModal Update Flow
 * - For any valid EditProjectModal submission, the component SHALL update the project,
 *   call onSuccess, and close the modal.
 */

export interface EditProjectModalProps {
  /** Whether the modal is open */
  isOpen: boolean;
  /** The project to edit */
  project: Project;
  /** Callback fired when the modal should close */
  onClose: () => void;
  /** Callback fired when a project is successfully updated */
  onSuccess: () => void;
  /** Additional CSS classes */
  className?: string;
}

/**
 * EditProjectModal component for editing existing projects
 */
export const EditProjectModal: React.FC<EditProjectModalProps> = ({
  isOpen,
  project,
  onClose,
  onSuccess,
  className,
}) => {
  // Form state - pre-populated with project data
  const [name, setName] = useState(project.name);
  const [description, setDescription] = useState(project.description || "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Get data service from context
  const { dataService } = useDataService();


  // Reset form when modal opens or project changes
  useEffect(() => {
    if (isOpen) {
      setName(project.name);
      setDescription(project.description || "");
      setError("");
      setLoading(false);
    }
  }, [isOpen, project]);

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
   * Requirements: 19.2 - Validate that the name is not empty
   * @returns true if valid, false otherwise
   */
  const validateForm = useCallback((): boolean => {
    const trimmedName = name.trim();
    
    if (!trimmedName) {
      setError("Project name is required");
      return false;
    }

    if (trimmedName.length < 1) {
      setError("Project name cannot be empty");
      return false;
    }

    setError("");
    return true;
  }, [name]);

  /**
   * Handles form submission
   * Requirements: 19.3 - Update the project and close the modal when form is submitted with valid data
   * Property 42: EditProjectModal Update Flow
   */
  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      if (!validateForm()) {
        return;
      }

      setLoading(true);
      setError("");

      try {
        await dataService.updateProject(project.id, {
          name: name.trim(),
          description: description.trim() || undefined,
        });

        onSuccess();
        onClose();
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to update project"
        );
      } finally {
        setLoading(false);
      }
    },
    [name, description, validateForm, dataService, project.id, onSuccess, onClose]
  );

  /**
   * Handles cancel action - closes modal without saving changes
   * Requirements: 19.4 - Close the modal without saving changes when user clicks cancel
   */
  const handleCancel = useCallback(() => {
    onClose();
  }, [onClose]);

  /**
   * Handles overlay/backdrop click (close modal without saving)
   * Requirements: 19.4 - Close the modal without saving changes when user clicks outside the modal
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
          data-testid="edit-project-modal"
        >
          {/* Backdrop with blur - Requirements: 19.5 */}
          <motion.div
            className={styles.backdrop}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleOverlayClick}
          />

          {/* Modal with glassmorphism effect - Requirements: 19.5 */}
          <motion.div
            className={styles.modal}
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header - Requirements: 19.4 - X button closes modal without saving */}
            <div className={styles.header}>
              <Typography variant="h5" color="primary">
                Edit Project
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

            {/* Form - Requirements: 19.1 - Pre-populated with current project details */}
            <form onSubmit={handleSubmit} className={styles.form}>
              {/* Project Name Input */}
              <Input
                label="Project Name"
                type="text"
                value={name}
                onChange={(e) => {
                  setName(e.target.value);
                  if (error) setError("");
                }}
                placeholder="Enter project name"
                state={error ? "error" : "default"}
                errorMessage={error || undefined}
                autoFocus
              />

              {/* Description Input (optional) */}
              <div className={styles.textareaField}>
                <label className={styles.textareaLabel}>
                  Description (optional)
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Enter project description"
                  className={styles.textarea}
                  rows={3}
                />
              </div>

              {/* Actions - Requirements: 19.4 - Cancel closes modal without saving */}
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
                  disabled={loading}
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

export default EditProjectModal;
