import React, { useState } from 'react';
import { Button, Input } from '../components/ui';
import { X, AlertCircle } from 'lucide-react';
import styles from './CreateProjectModal.module.css';

interface CreateProjectModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

export const CreateProjectModal: React.FC<CreateProjectModalProps> = ({ onClose, onSuccess }) => {
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [fieldError, setFieldError] = useState('');
  const [submitError, setSubmitError] = useState('');

  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setName(e.target.value);
    // Clear field error when user starts typing
    if (fieldError) {
      setFieldError('');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate project name
    if (!name.trim()) {
      setFieldError('Project name is required');
      return;
    }

    setLoading(true);
    setSubmitError('');

    try {
      const response = await fetch('http://localhost:8000/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: name.trim()
        })
      });

      if (!response.ok) {
        throw new Error('Failed to create project');
      }

      onSuccess();
      onClose();
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Failed to create project');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <h2>Create Project</h2>
          <button className={styles.closeButton} onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className={styles.form}>
          <Input
            id="project-name"
            label="Project Name"
            value={name}
            onChange={handleNameChange}
            placeholder="Enter project name"
            error={fieldError}
            state={fieldError ? 'error' : 'default'}
            required
          />

          {submitError && (
            <div className={styles.submitError} role="alert">
              <AlertCircle size={16} className={styles.submitErrorIcon} />
              <span>{submitError}</span>
            </div>
          )}

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
