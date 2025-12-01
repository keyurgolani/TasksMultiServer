import React, { useState, useEffect, useRef } from 'react';
import { Plus, FolderPlus, ListPlus, CheckSquare } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import styles from './Fab.module.css';

interface FabProps {
  onAddProject: () => void;
  onAddTaskList: () => void;
  onAddTask: () => void;
  showTaskButton?: boolean; // Only show task button on Tasks view
  disabled?: boolean;
}

export const Fab: React.FC<FabProps> = ({ 
  onAddProject, 
  onAddTaskList, 
  onAddTask, 
  showTaskButton = true,
  disabled 
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const fabRef = useRef<HTMLDivElement>(null);

  const toggleOpen = () => setIsOpen(!isOpen);

  const handleAction = (action: () => void) => {
    action();
    setIsOpen(false);
  };

  // Click outside to close
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (fabRef.current && !fabRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  return (
    <>
      {/* Backdrop overlay */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            className={styles.backdrop}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={() => setIsOpen(false)}
          />
        )}
      </AnimatePresence>

      <div className={styles.fabContainer} ref={fabRef}>
        <AnimatePresence>
          {isOpen && (
            <div className={styles.actions}>
              {/* Only show New Task button if showTaskButton is true */}
              {showTaskButton && (
                <motion.button
                  initial={{ opacity: 0, y: 20, scale: 0.8 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 20, scale: 0.8 }}
                  transition={{ type: "spring", stiffness: 800, damping: 20, delay: 0.02 }}
                  className={styles.actionButton}
                  onClick={() => handleAction(onAddTask)}
                  title="New Task"
                >
                  <span className={styles.actionLabel}>New Task</span>
                  <div className={styles.iconWrapper}>
                    <CheckSquare size={20} />
                  </div>
                </motion.button>
              )}

              <motion.button
                initial={{ opacity: 0, y: 20, scale: 0.8 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 20, scale: 0.8 }}
                transition={{ type: "spring", stiffness: 800, damping: 20, delay: showTaskButton ? 0.04 : 0.02 }}
                className={styles.actionButton}
                onClick={() => handleAction(onAddTaskList)}
                title="New Task List"
              >
                <span className={styles.actionLabel}>New Task List</span>
                <div className={styles.iconWrapper}>
                  <ListPlus size={20} />
                </div>
              </motion.button>

              <motion.button
                initial={{ opacity: 0, y: 20, scale: 0.8 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 20, scale: 0.8 }}
                transition={{ type: "spring", stiffness: 800, damping: 20, delay: 0.06 }}
                className={styles.actionButton}
                onClick={() => handleAction(onAddProject)}
                title="New Project"
              >
                <span className={styles.actionLabel}>New Project</span>
                <div className={styles.iconWrapper}>
                  <FolderPlus size={20} />
                </div>
              </motion.button>
            </div>
          )}
        </AnimatePresence>

        <motion.button
          className={`${styles.mainButton} ${isOpen ? styles.open : ''}`}
          onClick={toggleOpen}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          animate={{ 
            rotate: isOpen ? 135 : 0,
            backgroundColor: isOpen ? 'var(--error)' : 'var(--primary)'
          }}
          transition={{ duration: 0.1, ease: "easeIn", delay: 0 }}
          disabled={disabled}
        >
          <Plus size={24} className={styles.plusIcon} />
        </motion.button>
      </div>
    </>
  );
};
