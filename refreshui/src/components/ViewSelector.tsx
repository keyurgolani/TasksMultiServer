import React from 'react';
import { Layout, List, Folder } from 'lucide-react';
import styles from './ViewSelector.module.css';

export type DashboardView = 'tasks' | 'taskLists' | 'projects';

interface ViewSelectorProps {
  currentView: DashboardView;
  onViewChange: (view: DashboardView) => void;
}

export const ViewSelector: React.FC<ViewSelectorProps> = ({ currentView, onViewChange }) => {
  return (
    <div className={styles.container}>
      <button
        className={`${styles.option} ${currentView === 'projects' ? styles.active : ''}`}
        onClick={() => onViewChange('projects')}
        title="Projects View"
      >
        <Folder size={18} />
        <span>Projects</span>
      </button>
      <button
        className={`${styles.option} ${currentView === 'taskLists' ? styles.active : ''}`}
        onClick={() => onViewChange('taskLists')}
        title="Task Lists View"
      >
        <List size={18} />
        <span>Lists</span>
      </button>
      <button
        className={`${styles.option} ${currentView === 'tasks' ? styles.active : ''}`}
        onClick={() => onViewChange('tasks')}
        title="Tasks View"
      >
        <Layout size={18} />
        <span>Tasks</span>
      </button>
    </div>
  );
};
