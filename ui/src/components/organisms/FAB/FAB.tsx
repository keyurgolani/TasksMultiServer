import React, { useState, useEffect, useRef } from "react";
import { Plus, FolderPlus, ListPlus, CheckSquare } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "../../../lib/utils";

/**
 * FAB (Floating Action Button) Organism Component
 *
 * A floating action button that provides quick access to create new items.
 * Positioned in the bottom-right corner with expand/collapse functionality.
 *
 * Requirements: 15.1, 15.2, 15.3, 15.6
 * - 15.1: Display a floating button with a plus icon in the bottom-right corner
 * - 15.2: Expand to show action options (Create Project, Create Task List, Create Task)
 * - 15.3: Display labeled action buttons with appropriate icons when expanded
 * - 15.6: Apply glassmorphism effect and elevation shadow
 *
 * Property 32: FAB Expansion State
 * - For any FAB component, clicking the main button SHALL toggle between
 *   collapsed and expanded states.
 */

export interface FABProps {
  /** Handler for creating a new project */
  onAddProject: () => void;
  /** Handler for creating a new task list */
  onAddTaskList: () => void;
  /** Handler for creating a new task (optional) */
  onAddTask?: () => void;
  /** Whether to show the task button (default: false) */
  showTaskButton?: boolean;
  /** Whether the FAB is disabled */
  disabled?: boolean;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Action item configuration for the expanded menu
 */
interface ActionItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  onClick: () => void;
}

/**
 * FAB component for quick creation actions
 */
export const FAB: React.FC<FABProps> = ({
  onAddProject,
  onAddTaskList,
  onAddTask,
  showTaskButton = false,
  disabled = false,
  className,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const fabRef = useRef<HTMLDivElement>(null);

  /**
   * Toggle the expanded state of the FAB
   */
  const toggleExpanded = () => {
    if (!disabled) {
      setIsExpanded((prev) => !prev);
    }
  };

  /**
   * Handle action button click - execute action and collapse menu
   */
  const handleAction = (action: () => void) => {
    action();
    setIsExpanded(false);
  };

  /**
   * Build the list of action items based on props
   */
  const getActionItems = (): ActionItem[] => {
    const items: ActionItem[] = [];

    // Add task button if enabled and handler provided
    if (showTaskButton && onAddTask) {
      items.push({
        id: "task",
        label: "New Task",
        icon: <CheckSquare size={20} />,
        onClick: onAddTask,
      });
    }

    // Always show task list button
    items.push({
      id: "taskList",
      label: "New Task List",
      icon: <ListPlus size={20} />,
      onClick: onAddTaskList,
    });

    // Always show project button
    items.push({
      id: "project",
      label: "New Project",
      icon: <FolderPlus size={20} />,
      onClick: onAddProject,
    });

    return items;
  };

  const actionItems = getActionItems();

  // Click outside to close - handled by task 21.2, but basic structure here
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (fabRef.current && !fabRef.current.contains(event.target as Node)) {
        setIsExpanded(false);
      }
    };

    if (isExpanded) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isExpanded]);

  return (
    <>
      {/* Backdrop overlay when expanded */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            className="fixed inset-0 bg-black/40 backdrop-blur-sm z-[99]"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={() => setIsExpanded(false)}
            data-testid="fab-backdrop"
          />
        )}
      </AnimatePresence>

      {/* FAB Container */}
      <div
        ref={fabRef}
        className={cn(
          "fixed bottom-8 right-8 z-[100]",
          "flex flex-col items-end gap-4",
          className
        )}
        data-testid="fab-container"
      >
        {/* Action buttons (expanded state) */}
        <AnimatePresence>
          {isExpanded && (
            <div
              className="flex flex-col items-end gap-3 mb-2"
              data-testid="fab-actions"
            >
              {actionItems.map((item, index) => (
                <motion.button
                  key={item.id}
                  initial={{ opacity: 0, y: 20, scale: 0.8 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 20, scale: 0.8 }}
                  transition={{
                    type: "spring",
                    stiffness: 800,
                    damping: 20,
                    delay: index * 0.02,
                  }}
                  className="flex items-center gap-3 bg-transparent border-none cursor-pointer p-0"
                  onClick={() => handleAction(item.onClick)}
                  title={item.label}
                  data-testid={`fab-action-${item.id}`}
                >
                  {/* Action label with glassmorphism */}
                  <span
                    className={cn(
                      "px-3 py-1.5 rounded-md text-sm font-medium",
                      "bg-[var(--glass-bg)] text-[var(--text-primary)]",
                      "border border-[var(--glass-border)]",
                      "[backdrop-filter:blur(var(--glass-blur))]",
                      "[-webkit-backdrop-filter:blur(var(--glass-blur))]",
                      "shadow-[var(--glass-shadow)] pointer-events-none"
                    )}
                  >
                    {item.label}
                  </span>

                  {/* Action icon wrapper with glassmorphism */}
                  <div
                    className={cn(
                      "w-12 h-12 rounded-[calc(var(--fab-radius,14px)*0.75)]",
                      "bg-[var(--glass-bg)] border border-[var(--glass-border)]",
                      "text-[var(--text-primary)]",
                      "flex items-center justify-center",
                      "shadow-[var(--glass-shadow)] transition-all duration-200",
                      "backdrop-blur-[var(--glass-blur)]",
                      "[backdrop-filter:blur(var(--glass-blur))]",
                      "[-webkit-backdrop-filter:blur(var(--glass-blur))]",
                      "hover:bg-[var(--bg-surface-hover)]",
                      "hover:border-[var(--primary)]",
                      "hover:text-[var(--primary)]",
                      "hover:scale-105",
                      "hover:shadow-[0_8px_24px_rgba(var(--primary-rgb),0.3)]"
                    )}
                  >
                    {item.icon}
                  </div>
                </motion.button>
              ))}
            </div>
          )}
        </AnimatePresence>

        {/* Main FAB button with glassmorphism and elevation shadow */}
        <motion.button
          className={cn(
            "w-14 h-14 rounded-[var(--fab-radius,14px)]",
            "bg-[var(--primary)] border border-[var(--glass-border)]",
            "text-white flex items-center justify-center",
            "cursor-pointer",
            // Glassmorphism effect
            "[backdrop-filter:blur(var(--glass-blur))]",
            "[-webkit-backdrop-filter:blur(var(--glass-blur))]",
            // Elevation shadow with primary color glow
            "shadow-[var(--glass-shadow),0_4px_16px_rgba(var(--primary-rgb),0.4),0_8px_32px_rgba(var(--primary-rgb),0.2)]",
            "hover:bg-[var(--primary-dark)]",
            "hover:shadow-[var(--glass-shadow),0_6px_20px_rgba(var(--primary-rgb),0.5),0_12px_40px_rgba(var(--primary-rgb),0.3)]",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            isExpanded && "shadow-[var(--glass-shadow),0_4px_16px_rgba(var(--error-rgb),0.4),0_8px_32px_rgba(var(--error-rgb),0.2)]"
          )}
          onClick={toggleExpanded}
          whileHover={{ scale: disabled ? 1 : 1.05 }}
          whileTap={{ scale: disabled ? 1 : 0.95 }}
          animate={{
            rotate: isExpanded ? 135 : 0,
            backgroundColor: isExpanded ? "var(--error)" : "var(--primary)",
          }}
          transition={{ duration: 0.2, ease: "easeOut" }}
          disabled={disabled}
          aria-label={isExpanded ? "Close menu" : "Open menu"}
          aria-expanded={isExpanded}
          data-testid="fab-main-button"
        >
          <Plus size={24} />
        </motion.button>
      </div>
    </>
  );
};

FAB.displayName = "FAB";

export default FAB;
