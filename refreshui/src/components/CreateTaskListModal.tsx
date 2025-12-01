import React, { useState, useEffect } from 'react';
import { Button, Input } from '../components/ui';
import { X } from 'lucide-react';
import { api, type Project } from '../api/client';
import styles from './CreateTaskListModal.module.css';

interface CreateTaskListModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

export const CreateTaskListModal: React.FC<CreateTaskListModalProps> = ({ onClose, onSuccess }) => {
  const [name, setName] = useState('');
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectNameInput, setProjectNameInput] = useState('');
  const [newProjectName, setNewProjectName] = useState('');
  const [repeatable, setRepeatable] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadProjects = async () => {
      try {
        const data = await api.getProjects();
        setProjects(data);
      } catch (err) {
        console.error('Failed to load projects:', err);
      }
    };
    loadProjects();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Task list name is required');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const payload: Record<string, any> = {
        name: name.trim(),
        repeatable
      };

      // If repeatable, we don't associate with a project (or maybe we do? User said "project selection should be grayed out")
      // If grayed out, it implies no project selection allowed or ignored.
      // Assuming if repeatable, no project needed or it's global?
      // Or maybe it just means "don't let me change it".
      // But if I can't select it, what is the value?
      // Let's assume if repeatable, we don't send project_id/name, or we send null.
      if (!repeatable && projectNameInput) {
        if (projectNameInput === '__new__') {
          // Creating a new project
          if (newProjectName.trim()) {
            payload.project_name = newProjectName.trim();
          }
        } else {
          // Selecting existing project
          const existingProject = projects.find(p => p.name === projectNameInput);
          if (existingProject) {
            payload.project_id = existingProject.id;
          }
        }
      }

      const response = await fetch('http://localhost:8000/task-lists', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error('Failed to create task list');
      }

      onSuccess();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create task list');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <h2>Create Task List</h2>
          <button className={styles.closeButton} onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className={styles.form}>
          <Input
            label="Task List Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Enter task list name"
            required
          />

          <div className={styles.field}>
            <label>Project</label>
            <select
              value={projectNameInput}
              onChange={(e) => setProjectNameInput(e.target.value)}
              className={styles.select}
              disabled={repeatable}
            >
              <option value="">-- Select or Create New --</option>
              {projects.map(project => (
                <option key={project.id} value={project.name}>
                  {project.name}
                </option>
              ))}
              <option value="__new__">+ Create New Project</option>
            </select>
            {projectNameInput === '__new__' && (
              <input
                type="text"
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
                placeholder="Enter new project name"
                className={styles.datalistInput}
                style={{ marginTop: '8px' }}
              />
            )}
            <p className={styles.hint}>
              {projectNameInput === '__new__' 
                ? 'Enter a name for the new project' 
                : 'Select an existing project or create a new one'}
            </p>
          </div>

          <label className={`${styles.checkboxLabel} ${repeatable ? styles.checked : ''}`}>
            <input
              type="checkbox"
              checked={repeatable}
              onChange={(e) => setRepeatable(e.target.checked)}
              className={styles.checkbox}
            />
            <span>Repeatable Task List</span>
          </label>

          {error && <div className={styles.error}>{error}</div>}

          <div className={styles.actions}>
            <Button type="button" variant="secondary" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Creating...' : 'Create'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
