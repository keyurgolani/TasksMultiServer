import React from 'react';
import { motion } from 'framer-motion';
import { GripVertical, X } from 'lucide-react';
import type { ActionPlanItem as ActionPlanItemType } from '../api/client';
import styles from './ActionPlanItem.module.css';

interface ActionPlanItemProps {
  item: ActionPlanItemType;
  index: number;
  isEditing: boolean;
  onChange: (index: number, value: string) => void;
  onDelete: (index: number) => void;
}

export const ActionPlanItem: React.FC<ActionPlanItemProps> = ({
  item,
  index,
  isEditing,
  onChange,
  onDelete,
}) => {
  return (
    <motion.div
      className={styles.item}
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      transition={{ duration: 0.2, delay: index * 0.03 }}
    >
      <div className={styles.numberBadge}>
        <span>{index + 1}</span>
      </div>

      {isEditing ? (
        <div className={styles.editRow}>
          <div className={styles.dragHandle}>
            <GripVertical size={16} />
          </div>
          <input
            type="text"
            value={item.content}
            onChange={(e) => onChange(index, e.target.value)}
            className={styles.input}
            placeholder="Action item..."
          />
          <button
            type="button"
            onClick={() => onDelete(index)}
            className={styles.deleteBtn}
          >
            <X size={16} />
          </button>
        </div>
      ) : (
        <div className={styles.content}>
          <p className={styles.text}>{item.content}</p>
        </div>
      )}
    </motion.div>
  );
};
