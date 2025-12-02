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
  };
  onFilterChange: (type: 'status' | 'priority', value: string) => void;
  onClear: () => void;
}

export const FilterPopover: React.FC<FilterPopoverProps> = ({
  isOpen,
  onClose,
  filters,
  onFilterChange,
  onClear,
}) => {
  const popoverRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(event.target as Node)) {
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
  }, [isOpen, onClose]);

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
