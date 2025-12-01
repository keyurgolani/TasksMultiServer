import React, { useState, useMemo } from 'react';
import { Link, Plus, X } from 'lucide-react';
import type { Task } from '../api/client';
import styles from './DependencySection.module.css';

interface DependencySectionProps {
  dependencies: string[]; // List of task IDs
  availableTasks: Task[];
  currentTaskId?: string; // To avoid circular dependency on self
  onAdd: (taskId: string) => void;
  onRemove: (taskId: string) => void;
  isEditing: boolean;
}

export const DependencySection: React.FC<DependencySectionProps> = ({
  dependencies,
  availableTasks,
  currentTaskId,
  onAdd,
  onRemove,
  isEditing,
}) => {
  const [isAdding, setIsAdding] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Resolve dependency IDs to Task objects
  const resolvedDependencies = useMemo(() => {
    return dependencies
      .map(id => availableTasks.find(t => t.id === id))
      .filter((t): t is Task => !!t);
  }, [dependencies, availableTasks]);

  // Filter available tasks for adding
  const filteredTasks = useMemo(() => {
    return availableTasks
      .filter(t => 
        t.id !== currentTaskId && // Not self
        !dependencies.includes(t.id) && // Not already added
        t.title.toLowerCase().includes(searchQuery.toLowerCase()) // Matches search
      )
      .slice(0, 5); // Limit to 5 results
  }, [availableTasks, currentTaskId, dependencies, searchQuery]);

  const handleAdd = (taskId: string) => {
    onAdd(taskId);
    setSearchQuery('');
    setIsAdding(false);
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.title}>
          <Link size={16} />
          <span>Dependencies</span>
        </div>
        {isEditing && !isAdding && (
          <button 
            className={styles.addButton}
            onClick={() => setIsAdding(true)}
            type="button"
          >
            <Plus size={14} />
            Add
          </button>
        )}
      </div>

      {isAdding && (
        <div className={styles.addWrapper}>
          <div className={styles.searchBox}>
            <input
              type="text"
              className={styles.searchInput}
              placeholder="Search tasks..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              autoFocus
            />
          </div>
          <div className={styles.searchResults}>
            {filteredTasks.length > 0 ? (
              filteredTasks.map(task => (
                <div 
                  key={task.id} 
                  className={styles.searchResultItem}
                  onClick={() => handleAdd(task.id)}
                >
                  <div className={`${styles.statusIndicator} ${styles[`status_${task.status}`]}`} />
                  {task.title}
                </div>
              ))
            ) : (
              <div className={styles.emptyState}>No matching tasks found</div>
            )}
          </div>
          <button 
            className={styles.addButton} 
            onClick={() => setIsAdding(false)}
            style={{ width: '100%', justifyContent: 'center', marginTop: '4px' }}
          >
            Cancel
          </button>
        </div>
      )}

      <div className={styles.list}>
        {resolvedDependencies.length > 0 ? (
          resolvedDependencies.map(task => (
            <div key={task.id} className={styles.dependencyItem}>
              <div className={styles.itemContent}>
                <div 
                  className={`${styles.statusIndicator} ${styles[`status_${task.status}`]}`} 
                  title={`Status: ${task.status.replace('_', ' ')}`}
                />
                <span className={styles.itemTitle}>{task.title}</span>
              </div>
              {isEditing && (
                <button 
                  className={styles.removeButton}
                  onClick={() => onRemove(task.id)}
                  type="button"
                  title="Remove dependency"
                >
                  <X size={14} />
                </button>
              )}
            </div>
          ))
        ) : (
          !isAdding && <div className={styles.emptyState}>No dependencies</div>
        )}
      </div>
    </div>
  );
};
