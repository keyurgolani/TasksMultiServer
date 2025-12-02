import React, { useEffect, useRef } from 'react';
import { X } from 'lucide-react';
import { Button } from './ui';
import styles from './FilterPopover.module.css';

interface ProjectFilterPopoverProps {
  isOpen: boolean;
  onClose: () => void;
  filters: {
    completion: string; // 'all' | 'low' | 'medium' | 'high'
    taskCount: string; // 'all' | 'empty' | 'hasTasks'
    isDefault: string; // 'all' | 'default' | 'nonDefault'
  };
  onFilterChange: (type: 'completion' | 'taskCount' | 'isDefault', value: string) => void;
  onClear: () => void;
  buttonRef?: React.RefObject<HTMLButtonElement | null>;
}

export const ProjectFilterPopover: React.FC<ProjectFilterPopoverProps> = ({
  isOpen,
  onClose,
  filters,
  onFilterChange,
  onClear,
  buttonRef,
}) => {
  const popoverRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;
      const clickedPopover = popoverRef.current?.contains(target);
      const clickedButton = buttonRef?.current?.contains(target);
      
      if (!clickedPopover && !clickedButton) {
        onClose();
      }
    };

    // Add delay to prevent immediate closure when opening
    setTimeout(() => {
      document.addEventListener('mousedown', handleClickOutside);
    }, 0);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose, buttonRef]);

  if (!isOpen) return null;

  return (
    <div ref={popoverRef} className={styles.popover}>
      <div className={styles.header}>
        <h3>Filters</h3>
        <button className={styles.closeButton} onClick={onClose}>
          <X size={16} />
        </button>
      </div>
      
      <div className={styles.section}>
        <h4>Completion</h4>
        <div className={styles.options}>
          <label className={styles.radioLabel}>
            <input
              type="radio"
              name="completion"
              checked={filters.completion === 'all'}
              onChange={() => onFilterChange('completion', 'all')}
            />
            All
          </label>
          <label className={styles.radioLabel}>
            <input
              type="radio"
              name="completion"
              checked={filters.completion === 'low'}
              onChange={() => onFilterChange('completion', 'low')}
            />
            Low (0-33%)
          </label>
          <label className={styles.radioLabel}>
            <input
              type="radio"
              name="completion"
              checked={filters.completion === 'medium'}
              onChange={() => onFilterChange('completion', 'medium')}
            />
            Medium (34-66%)
          </label>
          <label className={styles.radioLabel}>
            <input
              type="radio"
              name="completion"
              checked={filters.completion === 'high'}
              onChange={() => onFilterChange('completion', 'high')}
            />
            High (67-100%)
          </label>
        </div>
      </div>

      <div className={styles.section}>
        <h4>Task Count</h4>
        <div className={styles.options}>
          <label className={styles.radioLabel}>
            <input
              type="radio"
              name="taskCount"
              checked={filters.taskCount === 'all'}
              onChange={() => onFilterChange('taskCount', 'all')}
            />
            All
          </label>
          <label className={styles.radioLabel}>
            <input
              type="radio"
              name="taskCount"
              checked={filters.taskCount === 'empty'}
              onChange={() => onFilterChange('taskCount', 'empty')}
            />
            No Tasks
          </label>
          <label className={styles.radioLabel}>
            <input
              type="radio"
              name="taskCount"
              checked={filters.taskCount === 'hasTasks'}
              onChange={() => onFilterChange('taskCount', 'hasTasks')}
            />
            Has Tasks
          </label>
        </div>
      </div>

      <div className={styles.section}>
        <h4>Project Type</h4>
        <div className={styles.options}>
          <label className={styles.radioLabel}>
            <input
              type="radio"
              name="isDefault"
              checked={filters.isDefault === 'all'}
              onChange={() => onFilterChange('isDefault', 'all')}
            />
            All
          </label>
          <label className={styles.radioLabel}>
            <input
              type="radio"
              name="isDefault"
              checked={filters.isDefault === 'default'}
              onChange={() => onFilterChange('isDefault', 'default')}
            />
            Default Only
          </label>
          <label className={styles.radioLabel}>
            <input
              type="radio"
              name="isDefault"
              checked={filters.isDefault === 'nonDefault'}
              onChange={() => onFilterChange('isDefault', 'nonDefault')}
            />
            Non-Default Only
          </label>
        </div>
      </div>

      <div className={styles.footer}>
        <Button variant="secondary" size="sm" onClick={onClear}>
          Clear All
        </Button>
        <Button size="sm" onClick={onClose}>
          Done
        </Button>
      </div>
    </div>
  );
};
