import React, { useEffect, useRef } from 'react';
import { X } from 'lucide-react';
import { Button } from './ui';
import styles from './FilterPopover.module.css';

interface TaskListFilterPopoverProps {
  isOpen: boolean;
  onClose: () => void;
  filters: {
    status: string[];
    priority: string[];
    taskCount: string;
    completion: string;
  };
  sort: {
    projectField: 'name' | 'listCount';
    projectDirection: 'asc' | 'desc';
    listField: 'name' | 'taskCount' | 'completion';
    listDirection: 'asc' | 'desc';
  };
  onFilterChange: (type: 'status' | 'priority' | 'taskCount' | 'completion', value: string) => void;
  onSortChange: (type: 'projectField' | 'listField', field: string, direction: 'asc' | 'desc') => void;
  onClear: () => void;
  buttonRef?: React.RefObject<HTMLButtonElement | null>;
}

export const TaskListFilterPopover: React.FC<TaskListFilterPopoverProps> = ({
  isOpen,
  onClose,
  filters,
  sort,
  onFilterChange,
  onSortChange,
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
        <h3>Sort & Filter</h3>
        <button className={styles.closeButton} onClick={onClose}>
          <X size={16} />
        </button>
      </div>

      <div className={styles.gridContainer}>
        {/* Project Sort */}
        <div className={styles.section}>
          <h4>Sort Projects By</h4>
          <div className={styles.options}>
            <label className={styles.radioLabel}>
              <input
                type="radio"
                name="projectSort"
                checked={sort.projectField === 'name' && sort.projectDirection === 'asc'}
                onChange={() => onSortChange('projectField', 'name', 'asc')}
              />
              Name (A-Z)
            </label>
            <label className={styles.radioLabel}>
              <input
                type="radio"
                name="projectSort"
                checked={sort.projectField === 'name' && sort.projectDirection === 'desc'}
                onChange={() => onSortChange('projectField', 'name', 'desc')}
              />
              Name (Z-A)
            </label>
            <label className={styles.radioLabel}>
              <input
                type="radio"
                name="projectSort"
                checked={sort.projectField === 'listCount' && sort.projectDirection === 'desc'}
                onChange={() => onSortChange('projectField', 'listCount', 'desc')}
              />
              List Count (High-Low)
            </label>
            <label className={styles.radioLabel}>
              <input
                type="radio"
                name="projectSort"
                checked={sort.projectField === 'listCount' && sort.projectDirection === 'asc'}
                onChange={() => onSortChange('projectField', 'listCount', 'asc')}
              />
              List Count (Low-High)
            </label>
          </div>
        </div>

        {/* List Sort */}
        <div className={styles.section}>
          <h4>Sort Lists By</h4>
          <div className={styles.options}>
            <label className={styles.radioLabel}>
              <input
                type="radio"
                name="listSort"
                checked={sort.listField === 'name' && sort.listDirection === 'asc'}
                onChange={() => onSortChange('listField', 'name', 'asc')}
              />
              Name (A-Z)
            </label>
            <label className={styles.radioLabel}>
              <input
                type="radio"
                name="listSort"
                checked={sort.listField === 'name' && sort.listDirection === 'desc'}
                onChange={() => onSortChange('listField', 'name', 'desc')}
              />
              Name (Z-A)
            </label>
            <label className={styles.radioLabel}>
              <input
                type="radio"
                name="listSort"
                checked={sort.listField === 'taskCount' && sort.listDirection === 'desc'}
                onChange={() => onSortChange('listField', 'taskCount', 'desc')}
              />
              Task Count (High-Low)
            </label>
            <label className={styles.radioLabel}>
              <input
                type="radio"
                name="listSort"
                checked={sort.listField === 'taskCount' && sort.listDirection === 'asc'}
                onChange={() => onSortChange('listField', 'taskCount', 'asc')}
              />
              Task Count (Low-High)
            </label>
            <label className={styles.radioLabel}>
              <input
                type="radio"
                name="listSort"
                checked={sort.listField === 'completion' && sort.listDirection === 'desc'}
                onChange={() => onSortChange('listField', 'completion', 'desc')}
              />
              Completion (High-Low)
            </label>
            <label className={styles.radioLabel}>
              <input
                type="radio"
                name="listSort"
                checked={sort.listField === 'completion' && sort.listDirection === 'asc'}
                onChange={() => onSortChange('listField', 'completion', 'asc')}
              />
              Completion (Low-High)
            </label>
          </div>
        </div>

        {/* Task Status Filters */}
        <div className={styles.section}>
          <h4>Task Status</h4>
          <div className={styles.options}>
            {['NOT_STARTED', 'IN_PROGRESS', 'BLOCKED', 'COMPLETED'].map((status) => (
              <label key={status} className={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  checked={filters.status.includes(status)}
                  onChange={() => onFilterChange('status', status)}
                />
                {status.replace('_', ' ')}
              </label>
            ))}
          </div>
        </div>

        {/* Task Priority Filters */}
        <div className={styles.section}>
          <h4>Task Priority</h4>
          <div className={styles.options}>
            {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((priority) => (
              <label key={priority} className={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  checked={filters.priority.includes(priority)}
                  onChange={() => onFilterChange('priority', priority)}
                />
                {priority}
              </label>
            ))}
          </div>
        </div>

        {/* Task Count Filter */}
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
                checked={filters.taskCount === 'few'}
                onChange={() => onFilterChange('taskCount', 'few')}
              />
              1-5 Tasks
            </label>
            <label className={styles.radioLabel}>
              <input
                type="radio"
                name="taskCount"
                checked={filters.taskCount === 'medium'}
                onChange={() => onFilterChange('taskCount', 'medium')}
              />
              6-10 Tasks
            </label>
            <label className={styles.radioLabel}>
              <input
                type="radio"
                name="taskCount"
                checked={filters.taskCount === 'many'}
                onChange={() => onFilterChange('taskCount', 'many')}
              />
              11+ Tasks
            </label>
          </div>
        </div>

        {/* Completion Percentage Filter */}
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
              0-25%
            </label>
            <label className={styles.radioLabel}>
              <input
                type="radio"
                name="completion"
                checked={filters.completion === 'medium'}
                onChange={() => onFilterChange('completion', 'medium')}
              />
              26-75%
            </label>
            <label className={styles.radioLabel}>
              <input
                type="radio"
                name="completion"
                checked={filters.completion === 'high'}
                onChange={() => onFilterChange('completion', 'high')}
              />
              76-100%
            </label>
          </div>
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
