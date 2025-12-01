import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check } from 'lucide-react';
import type { Task } from '../api/client';
import styles from './PrioritySelector.module.css';

interface PrioritySelectorProps {
  value: Task['priority'];
  onChange: (priority: Task['priority']) => void;
  readOnly?: boolean;
}

const PRIORITIES: { value: Task['priority']; label: string; color: string }[] = [
  { value: 'CRITICAL', label: 'Critical', color: '#FF4757' },
  { value: 'HIGH', label: 'High', color: '#FF6348' },
  { value: 'MEDIUM', label: 'Medium', color: '#FFA502' },
  { value: 'LOW', label: 'Low', color: '#26DE81' },
  { value: 'TRIVIAL', label: 'Trivial', color: '#A4B0BE' },
];

export const PrioritySelector: React.FC<PrioritySelectorProps> = ({ value, onChange, readOnly = false }) => {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const currentPriority = PRIORITIES.find(p => p.value === value) || PRIORITIES[2];

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
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

  const handleSelect = (priority: Task['priority']) => {
    onChange(priority);
    setIsOpen(false);
  };

  return (
    <div className={styles.container} ref={containerRef}>
      <button
        type="button"
        className={styles.trigger}
        onClick={() => !readOnly && setIsOpen(!isOpen)}
        disabled={readOnly}
        style={{ 
          backgroundColor: currentPriority.color + '20', 
          color: currentPriority.color, 
          borderColor: currentPriority.color 
        }}
      >
        <div className={styles.colorBox} style={{ backgroundColor: currentPriority.color }} />
        <span className={styles.label}>{currentPriority.label}</span>
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            className={styles.dropdown}
            initial={{ opacity: 0, y: 5, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 5, scale: 0.95 }}
            transition={{ duration: 0.1 }}
          >
            {PRIORITIES.map((priority) => (
              <button
                key={priority.value}
                type="button"
                className={styles.option}
                onClick={() => handleSelect(priority.value)}
              >
                <div className={styles.optionContent}>
                  <div className={styles.colorBox} style={{ backgroundColor: priority.color }} />
                  <span className={styles.optionLabel}>{priority.label}</span>
                </div>
                {value === priority.value && <Check size={14} className={styles.check} />}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
