import React from 'react';
import { motion } from 'framer-motion';
import { Check } from 'lucide-react';
import type { ExitCriterion } from '../api/client';
import styles from './ExitCriteriaItem.module.css';

interface ExitCriteriaItemProps {
  criterion: ExitCriterion;
  index: number;
  isEditing: boolean;
  onToggle: (index: number) => void;
  onChange: (index: number, value: string) => void;
  onDelete: (index: number) => void;
}

export const ExitCriteriaItem: React.FC<ExitCriteriaItemProps> = ({
  criterion,
  index,
  isEditing,
  onToggle,
  onChange,
  onDelete,
}) => {
  const isComplete = criterion.status === 'COMPLETE';

  return (
    <motion.div
      className={`${styles.item} ${isComplete ? styles.complete : ''}`}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.2 }}
    >
      <div className={styles.checkboxWrapper}>
        <motion.button
          type="button"
          className={`${styles.checkbox} ${isComplete ? styles.checked : ''}`}
          onClick={() => onToggle(index)}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          disabled={!isEditing}
        >
          {isComplete && (
            <motion.div
              className={styles.iconWrapper}
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', stiffness: 500, damping: 25 }}
            >
              <Check size={16} strokeWidth={3} />
            </motion.div>
          )}
        </motion.button>
      </div>

      {isEditing ? (
        <div className={styles.editRow}>
          <input
            type="text"
            value={criterion.criteria}
            onChange={(e) => onChange(index, e.target.value)}
            className={styles.input}
            placeholder="Exit criterion..."
          />
          <button
            type="button"
            onClick={() => onDelete(index)}
            className={styles.deleteBtn}
          >
            ×
          </button>
        </div>
      ) : (
        <span className={styles.text}>{criterion.criteria}</span>
      )}
    </motion.div>
  );
};
