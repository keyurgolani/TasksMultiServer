import React from 'react';
import { motion } from 'framer-motion';
import { FileText, Lightbulb, Code } from 'lucide-react';
import type { Note } from '../api/client';
import styles from './NoteItem.module.css';

type NoteType = 'general' | 'research' | 'execution';

interface NoteItemProps {
  note: Note;
  type: NoteType;
  index: number;
}

const NOTE_CONFIG = {
  general: {
    icon: FileText,
    label: 'Note',
    color: '#6b7280',
  },
  research: {
    icon: Lightbulb,
    label: 'Research',
    color: '#f59e0b',
  },
  execution: {
    icon: Code,
    label: 'Execution',
    color: '#8b5cf6',
  },
};

export const NoteItem: React.FC<NoteItemProps> = ({ note, type, index }) => {
  const config = NOTE_CONFIG[type];
  const Icon = config.icon;

  return (
    <motion.div
      className={styles.item}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, delay: index * 0.05 }}
    >
      <div className={styles.timeline}>
        <div className={styles.dot} style={{ backgroundColor: config.color }} />
        {index > 0 && <div className={styles.line} />}
      </div>

      <div className={styles.content}>
        <div className={styles.header}>
          <div className={styles.badge} style={{ backgroundColor: `${config.color}20`, color: config.color }}>
            <Icon size={12} />
            <span>{config.label}</span>
          </div>
        </div>
        <p className={styles.text}>{note.content}</p>
      </div>
    </motion.div>
  );
};
