import React, { useEffect, useRef } from 'react';
import { X } from 'lucide-react';
import { Button } from './ui';
import styles from './FilterPopover.module.css';

interface FilterPopoverProps {
  isOpen: boolean;
  onClose: () => void;
  filters: {
    status: string[];
    priority: string[];
    hasExitCriteria?: string;
    hasDependencies?: string;
  };
  onFilterChange: (type: 'status' | 'priority' | 'hasExitCriteria' | 'hasDependencies', value: string) => void;
  onClear: () => void;
  buttonRef?: React.RefObject<HTMLButtonElement | null>;
}

export const FilterPopover: React.FC<FilterPopoverProps> = ({
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

  const statuses = ['NOT_STARTED', 'IN_PROGRESS', 'BLOCKED', 'COMPLETED'];
  const priorities = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'TRIVIAL'];

  return (
    <div ref={popoverRef} className={styles.popover}>
      <div className={styles.header}>
        <h3>Filters</h3>
        <button className={styles.closeButton} onClick={onClose}>
          <X size={16} />
        </button>
      </div>
      
      <div className={styles.gridContainer}>
        <div className={styles.section}>
          <h4>Status</h4>
          <div className={styles.options}>
            {statuses.map(status => (
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

        <div className={styles.section}>
          <h4>Priority</h4>
          <div className={styles.options}>
            {priorities.map(priority => (
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

        <div className={styles.section}>
          <h4>Exit Criteria</h4>
          <div className={styles.options}>
            <label className={styles.radioLabel}>
              <input
                type="radio"
                name="hasExitCriteria"
                checked={filters.hasExitCriteria === 'all'}
                onChange={() => onFilterChange('hasExitCriteria', 'all')}
              />
              All
            </label>
            <label className={styles.radioLabel}>
              <input
                type="radio"
                name="hasExitCriteria"
                checked={filters.hasExitCriteria === 'yes'}
                onChange={() => onFilterChange('hasExitCriteria', 'yes')}
              />
              Has Exit Criteria
            </label>
            <label className={styles.radioLabel}>
              <input
                type="radio"
                name="hasExitCriteria"
                checked={filters.hasExitCriteria === 'no'}
                onChange={() => onFilterChange('hasExitCriteria', 'no')}
              />
              No Exit Criteria
            </label>
          </div>
        </div>

        <div className={styles.section}>
          <h4>Dependencies</h4>
          <div className={styles.options}>
            <label className={styles.radioLabel}>
              <input
                type="radio"
                name="hasDependencies"
                checked={filters.hasDependencies === 'all'}
                onChange={() => onFilterChange('hasDependencies', 'all')}
              />
              All
            </label>
            <label className={styles.radioLabel}>
              <input
                type="radio"
                name="hasDependencies"
                checked={filters.hasDependencies === 'yes'}
                onChange={() => onFilterChange('hasDependencies', 'yes')}
              />
              Has Dependencies
            </label>
            <label className={styles.radioLabel}>
              <input
                type="radio"
                name="hasDependencies"
                checked={filters.hasDependencies === 'no'}
                onChange={() => onFilterChange('hasDependencies', 'no')}
              />
              No Dependencies
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
