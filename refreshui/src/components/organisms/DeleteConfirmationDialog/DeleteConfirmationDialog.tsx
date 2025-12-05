import React, { useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, AlertTriangle } from "lucide-react";
import { Button } from "../../atoms/Button";
import { Typography } from "../../atoms/Typography";
import { cn } from "../../../lib/utils";
import styles from "./DeleteConfirmationDialog.module.css";

/**
 * DeleteConfirmationDialog Organism Component
 *
 * A confirmation dialog for destructive actions like deleting projects or task lists.
 * Displays item details and cascading deletion warnings.
 * Implements glassmorphism effect and follows design system patterns.
 *
 * Requirements: 20.1, 20.2, 20.3, 20.4, 20.5, 22.1, 22.2, 22.3, 22.4, 22.5
 * - 20.1: Display a confirmation dialog with project name
 * - 20.2: Warn about cascading deletion of task lists and tasks
 * - 20.3: Delete the project and all associated data when user confirms
 * - 20.4: Close the dialog without deleting when user cancels
 * - 20.5: Use destructive styling to indicate the dangerous action
 * - 22.1: Display a confirmation dialog with task list name
 * - 22.2: Warn about cascading deletion of tasks
 * - 22.3: Delete the task list and all associated tasks when user confirms
 * - 22.4: Close the dialog without deleting when user cancels
 * - 22.5: Use destructive styling to indicate the dangerous action
 *
 * Property 45: DeleteConfirmationDialog Display
 * - For any DeleteConfirmationDialog opened with item details, the component SHALL
 *   display the item name and appropriate warning message.
 *
 * Property 46: DeleteConfirmationDialog Confirm Action
 * - For any DeleteConfirmationDialog confirmation, the component SHALL call
 *   onConfirm and close the dialog.
 */

/**
 * Cascading deletion info for displaying warnings about related items
 * Requirements: 20.2, 22.2
 */
export interface CascadingDeletionInfo {
  /** Number of task lists that will be deleted (for project deletion) */
  taskListCount?: number;
  /** Number of tasks that will be deleted */
  taskCount?: number;
}

export interface DeleteConfirmationDialogProps {
  /** Whether the dialog is open */
  isOpen: boolean;
  /** Title of the dialog (e.g., "Delete Project", "Delete Task List") */
  title: string;
  /** Warning message to display */
  message: string;
  /** Name of the item being deleted */
  itemName: string;
  /** Callback fired when user confirms deletion */
  onConfirm: () => void;
  /** Callback fired when user cancels or closes the dialog */
  onCancel: () => void;
  /** Whether the action is destructive (affects styling) - defaults to true */
  isDestructive?: boolean;
  /** Whether the confirm action is in progress */
  loading?: boolean;
  /** Additional CSS classes */
  className?: string;
  /**
   * Cascading deletion information for displaying warnings about related items
   * Requirements: 20.2, 22.2
   * - For projects: shows task lists and tasks that will be deleted
   * - For task lists: shows tasks that will be deleted
   */
  cascadingDeletion?: CascadingDeletionInfo;
}

/**
 * DeleteConfirmationDialog component for confirming destructive actions
 */
export const DeleteConfirmationDialog: React.FC<DeleteConfirmationDialogProps> = ({
  isOpen,
  title,
  message,
  itemName,
  onConfirm,
  onCancel,
  isDestructive = true,
  loading = false,
  className,
  cascadingDeletion,
}) => {
  /**
   * Generates cascading deletion warning text based on the provided info
   * Requirements: 20.2, 22.2
   * - 20.2: Warn about cascading deletion of task lists and tasks (for project deletion)
   * - 22.2: Warn about cascading deletion of tasks (for task list deletion)
   */
  const getCascadingDeletionWarning = (): string | null => {
    if (!cascadingDeletion) return null;

    const { taskListCount, taskCount } = cascadingDeletion;
    const parts: string[] = [];

    // For project deletion - warn about task lists
    if (taskListCount !== undefined && taskListCount > 0) {
      parts.push(
        `${taskListCount} task list${taskListCount === 1 ? "" : "s"}`
      );
    }

    // For both project and task list deletion - warn about tasks
    if (taskCount !== undefined && taskCount > 0) {
      parts.push(`${taskCount} task${taskCount === 1 ? "" : "s"}`);
    }

    if (parts.length === 0) return null;

    return `This will also permanently delete ${parts.join(" and ")}.`;
  };

  const cascadingWarning = getCascadingDeletionWarning();

  // Handle escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen && !loading) {
        onCancel();
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onCancel, loading]);

  /**
   * Handles overlay/backdrop click (close dialog without confirming)
   * Requirements: 20.4, 22.4 - Close the dialog without deleting when user clicks outside
   */
  const handleOverlayClick = useCallback(
    (e: React.MouseEvent) => {
      if (e.target === e.currentTarget && !loading) {
        onCancel();
      }
    },
    [onCancel, loading]
  );

  /**
   * Handles confirm action
   * Requirements: 20.3, 22.3 - Delete the item when user confirms
   * Property 46: DeleteConfirmationDialog Confirm Action
   */
  const handleConfirm = useCallback(() => {
    onConfirm();
  }, [onConfirm]);

  /**
   * Handles cancel action
   * Requirements: 20.4, 22.4 - Close the dialog without deleting
   */
  const handleCancel = useCallback(() => {
    if (!loading) {
      onCancel();
    }
  }, [onCancel, loading]);

  return (
    <AnimatePresence>
      {isOpen && (
        <div
          className={cn(styles.overlay, className)}
          data-testid="delete-confirmation-dialog"
        >
          {/* Backdrop with blur */}
          <motion.div
            className={styles.backdrop}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleOverlayClick}
          />

          {/* Dialog with glassmorphism effect - Requirements: 20.5, 22.5 */}
          <motion.div
            className={cn(styles.dialog, isDestructive && styles.destructive)}
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            onClick={(e) => e.stopPropagation()}
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="delete-dialog-title"
            aria-describedby="delete-dialog-description"
          >
            {/* Header with warning icon - Requirements: 20.5, 22.5 */}
            <div className={styles.header}>
              <div className={cn(
                styles.iconContainer,
                isDestructive && styles.destructiveIconContainer
              )}>
                <AlertTriangle
                  size={24}
                  className={isDestructive ? styles.destructiveIcon : styles.warningIcon}
                />
              </div>
              <Typography
                variant="h5"
                color="primary"
                id="delete-dialog-title"
              >
                {title}
              </Typography>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleCancel}
                aria-label="Close dialog"
                disabled={loading}
                className={styles.closeButton}
              >
                <X size={20} />
              </Button>
            </div>

            {/* Content - Requirements: 20.1, 20.2, 22.1, 22.2 */}
            <div className={styles.content} id="delete-dialog-description">
              {/* Item name display - Property 45: DeleteConfirmationDialog Display */}
              <div className={styles.itemInfo}>
                <Typography variant="body" color="secondary">
                  You are about to delete:
                </Typography>
                <Typography variant="h6" color="primary" className={styles.itemName}>
                  "{itemName}"
                </Typography>
              </div>

              {/* Warning message - Requirements: 20.2, 22.2 */}
              <div className={cn(styles.warningBox, isDestructive && styles.destructiveWarning)}>
                <AlertTriangle size={16} className={styles.warningBoxIcon} />
                <div className={styles.warningContent}>
                  <Typography variant="body-sm" color="secondary">
                    {message}
                  </Typography>
                  {/* Cascading deletion warning - Requirements: 20.2, 22.2 */}
                  {cascadingWarning && (
                    <Typography
                      variant="body-sm"
                      color="secondary"
                      className={styles.cascadingWarning}
                      data-testid="cascading-deletion-warning"
                    >
                      {cascadingWarning}
                    </Typography>
                  )}
                </div>
              </div>

              <Typography 
                variant="caption" 
                color={isDestructive ? "primary" : "muted"} 
                className={cn(styles.disclaimer, isDestructive && styles.destructiveDisclaimer)}
              >
                This action cannot be undone.
              </Typography>
            </div>

            {/* Actions - Requirements: 20.3, 20.4, 22.3, 22.4 */}
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
                type="button"
                variant={isDestructive ? "destructive" : "primary"}
                onClick={handleConfirm}
                loading={loading}
                disabled={loading}
              >
                {loading ? "Deleting..." : "Delete"}
              </Button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default DeleteConfirmationDialog;
