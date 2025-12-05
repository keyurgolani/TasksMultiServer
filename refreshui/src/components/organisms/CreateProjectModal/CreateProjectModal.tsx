import React, { useState, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";
import { Button } from "../../atoms/Button";
import { Input } from "../../atoms/Input";
import { Typography } from "../../atoms/Typography";
import { useDataService } from "../../../context/DataServiceContext";
import { cn } from "../../../lib/utils";
import styles from "./CreateProjectModal.module.css";

/**
 * CreateProjectModal Organism Component
 *
 * A modal dialog for creating new projects with form validation.
 * Implements glassmorphism effect and follows design system patterns.
 *
 * Requirements: 16.1, 16.2, 16.5
 * - Display a modal overlay with a form for project details
 * - Validate that the project name is not empty
 * - Apply glassmorphism effect and center modal on viewport
 *
 * Property 35: CreateProjectModal Form Validation
 * - For any CreateProjectModal submission, the form SHALL validate
 *   that the project name is not empty before allowing creation.
 */

export interface CreateProjectModalProps {
  /** Whether the modal is open */
  isOpen: boolean;
  /** Callback fired when the modal should close */
  onClose: () => void;
  /** Callback fired when a project is successfully created */
  onSuccess: () => void;
  /** Additional CSS classes */
  className?: string;
}

/**
 * CreateProjectModal component for creating new projects
 */
export const CreateProjectModal: React.FC<CreateProjectModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  className,
}) => {
  // Form state
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Get data service from context
  const { dataService } = useDataService();

  // Reset form when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setName("");
      setDescription("");
      setError("");
      setLoading(false);
    }
  }, [isOpen]);

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
        await dataService.createProject({
          name: name.trim(),
          description: description.trim() || undefined,
        });

        onSuccess();
        onClose();
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to create project"
        );
      } finally {
        setLoading(false);
      }
    },
    [name, description, validateForm, dataService, onSuccess, onClose]
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
          data-testid="create-project-modal"
        >
          {/* Backdrop with blur - Requirements: 16.5 */}
          <motion.div
            className={styles.backdrop}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleOverlayClick}
          />

          {/* Modal with glassmorphism effect - Requirements: 16.5 */}
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
                Create Project
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
                  disabled={loading}
                >
                  {loading ? "Creating..." : "Create Project"}
                </Button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default CreateProjectModal;
