import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Edit2, Save, Trash2, Calendar, Tag, CheckSquare, FileText, Target, Plus } from 'lucide-react';
import { StatusIndicator } from './StatusIndicator';
import { PrioritySelector } from './PrioritySelector';
import { ExitCriteriaItem } from './ExitCriteriaItem';
import { ActionPlanItem } from './ActionPlanItem';
import { NoteItem } from './NoteItem';
import { DependencySection } from './DependencySection';
import type { Task, ActionPlanItem as ActionPlanItemType, ExitCriterion, Note } from '../api/client';
import styles from './TaskDetailModal.module.css';

interface TaskDetailModalProps {
  task: Task | null;
  isOpen: boolean;
  onClose: () => void;
  onSave?: (task: Task) => void;
  onDelete?: (taskId: string) => void;
  availableTasks?: Task[];
}

export const TaskDetailModal: React.FC<TaskDetailModalProps> = ({
  task,
  isOpen,
  onClose,
  onSave,
  onDelete,
  availableTasks,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  
  // Form State
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState<Task['status']>('NOT_STARTED');
  const [priority, setPriority] = useState<Task['priority']>('MEDIUM');
  const [tags, setTags] = useState<string[]>([]);
  const [newTag, setNewTag] = useState('');
  const [actionPlan, setActionPlan] = useState<ActionPlanItemType[]>([]);
  const [exitCriteria, setExitCriteria] = useState<ExitCriterion[]>([]);
  const [dependencies, setDependencies] = useState<string[]>([]);
  const [newNote, setNewNote] = useState('');
  const [noteType, setNoteType] = useState<'general' | 'research' | 'execution'>('general');

  useEffect(() => {
    if (task) {
      setTitle(task.title);
      setDescription(task.description);
      setStatus(task.status);
      setPriority(task.priority);
      setTags(task.tags || []);
      setActionPlan(task.action_plan || []);
      setExitCriteria(task.exit_criteria || []);
      setDependencies(task.dependencies || []);
      setIsEditing(false);
    }
  }, [task, isOpen]);

  if (!task) return null;

  const handleSave = () => {
    if (onSave) {
      const updatedTask: Task = {
        ...task,
        title,
        description,
        status,
        priority,
        tags,
        action_plan: actionPlan,
        exit_criteria: exitCriteria,
        dependencies: dependencies,
        updated_at: new Date().toISOString()
      };
      onSave(updatedTask);
      setIsEditing(false);
    }
  };

  const handleDelete = () => {
    if (window.confirm('Are you sure you want to delete this task?')) {
      if (onDelete) {
        onDelete(task.id);
      }
      onClose();
    }
  };

  // Action Plan Handlers
  const addActionItem = () => {
    setActionPlan([...actionPlan, { sequence: actionPlan.length + 1, content: '' }]);
  };

  const updateActionItem = (index: number, content: string) => {
    const newPlan = [...actionPlan];
    newPlan[index] = { ...newPlan[index], content };
    setActionPlan(newPlan);
  };

  const removeActionItem = (index: number) => {
    const newPlan = actionPlan.filter((_, i) => i !== index)
      .map((item, i) => ({ ...item, sequence: i + 1 }));
    setActionPlan(newPlan);
  };

  // Exit Criteria Handlers
  const addExitCriterion = () => {
    setExitCriteria([...exitCriteria, { sequence: exitCriteria.length + 1, criteria: '', status: 'INCOMPLETE' }]);
  };

  const updateExitCriterion = (index: number, criteria: string) => {
    const newCriteria = [...exitCriteria];
    newCriteria[index] = { ...newCriteria[index], criteria };
    setExitCriteria(newCriteria);
  };

  const toggleExitCriterionStatus = (index: number) => {
    const newCriteria = [...exitCriteria];
    newCriteria[index] = {
      ...newCriteria[index],
      status: newCriteria[index].status === 'COMPLETE' ? 'INCOMPLETE' : 'COMPLETE'
    };
    setExitCriteria(newCriteria);
    
    if (!isEditing && onSave) {
      const updatedTask = { ...task, exit_criteria: newCriteria };
      onSave(updatedTask);
    }
  };

  const removeExitCriterion = (index: number) => {
    const newCriteria = exitCriteria.filter((_, i) => i !== index)
      .map((item, i) => ({ ...item, sequence: i + 1 }));
    setExitCriteria(newCriteria);
  };

  // Dependency Handlers
  const addDependency = (dependencyId: string) => {
    if (!dependencies.includes(dependencyId)) {
      setDependencies([...dependencies, dependencyId]);
    }
  };

  const removeDependency = (dependencyId: string) => {
    setDependencies(dependencies.filter(id => id !== dependencyId));
  };

  // Tag Handlers
  const addTag = () => {
    if (newTag.trim() && !tags.includes(newTag.trim())) {
      setTags([...tags, newTag.trim()]);
      setNewTag('');
    }
  };

  const removeTag = (tag: string) => {
    setTags(tags.filter(t => t !== tag));
  };

  // Note Handlers
  const addNote = () => {
    if (!newNote.trim() || !task) return;
    
    const note: Note = {
      sequence: 1,
      content: newNote.trim()
    };

    let updatedTask: Task;
    if (noteType === 'research') {
      updatedTask = {
        ...task,
        research_notes: [note, ...(task.research_notes || [])]
      };
    } else if (noteType === 'execution') {
      updatedTask = {
        ...task,
        execution_notes: [note, ...(task.execution_notes || [])]
      };
    } else {
      updatedTask = {
        ...task,
        notes: [note, ...(task.notes || [])]
      };
    }
    
    if (onSave) {
      onSave(updatedTask);
    }
    setNewNote('');
  };



  const completedCriteria = exitCriteria.filter(c => c.status === 'COMPLETE').length;
  const totalCriteria = exitCriteria.length;
  const criteriaProgress = totalCriteria > 0 ? (completedCriteria / totalCriteria) * 100 : 0;

  // Combine all notes with type information
  const allNotes = [
    ...(task.research_notes || []).map(n => ({ ...n, type: 'research' as const })),
    ...(task.execution_notes || []).map(n => ({ ...n, type: 'execution' as const })),
    ...(task.notes || []).map(n => ({ ...n, type: 'general' as const })),
  ].sort((a, b) => b.sequence - a.sequence);

  return (
    <AnimatePresence>
      {isOpen && (
        <div className={styles.modalWrapper}>
          <motion.div
            className={styles.overlay}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
          <motion.div
            className={styles.modal}
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
          >
            {/* Header */}
            <div className={styles.header}>
              <div className={styles.headerContent}>
                <div className={styles.titleRow}>
                  {isEditing ? (
                    <input
                      type="text"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      className={styles.titleInput}
                      placeholder="Task title..."
                    />
                  ) : (
                    <h1 className={styles.title}>{task.title}</h1>
                  )}
                </div>
                <div className={styles.badges}>
                  {isEditing ? (
                    <select 
                      value={status} 
                      onChange={(e) => {
                        const newStatus = e.target.value as Task['status'];
                        if (newStatus === 'COMPLETED') {
                          const incompleteCriteria = exitCriteria.filter(c => c.status !== 'COMPLETE');
                          if (incompleteCriteria.length > 0) {
                            alert(`Cannot complete task. ${incompleteCriteria.length} exit criteria are incomplete.`);
                            return;
                          }
                        }
                        setStatus(newStatus);
                      }}
                      className={styles.select}
                    >
                      <option value="NOT_STARTED">Not Started</option>
                      <option value="IN_PROGRESS">In Progress</option>
                      <option value="BLOCKED">Blocked</option>
                      <option value="COMPLETED">Completed</option>
                    </select>
                  ) : (
                    <StatusIndicator status={task.status} variant="badge" />
                  )}

                  <PrioritySelector 
                    value={isEditing ? priority : task.priority} 
                    onChange={setPriority} 
                    readOnly={!isEditing} 
                  />
                  
                  <div className={styles.dateBadge}>
                    <Calendar size={12} />
                    {new Date(task.created_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
              
              <div className={styles.headerActions}>
                {!isEditing ? (
                  <button className={styles.iconButton} onClick={() => setIsEditing(true)}>
                    <Edit2 size={18} />
                  </button>
                ) : (
                  <button className={styles.iconButton} onClick={handleSave}>
                    <Save size={18} />
                  </button>
                )}
                <button className={styles.iconButton} onClick={handleDelete}>
                  <Trash2 size={18} />
                </button>
                <button className={styles.closeButton} onClick={onClose}>
                  <X size={20} />
                </button>
              </div>
            </div>

            {/* Hero Section */}
            <div className={styles.hero}>
              <div className={styles.descriptionSection}>
                <div className={styles.sectionLabel}>
                  <FileText size={12} />
                  Description
                </div>
                {isEditing ? (
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    className={styles.textarea}
                    rows={4}
                    placeholder="Add a description..."
                  />
                ) : (
                  <p className={styles.description}>{task.description || 'No description provided.'}</p>
                )}
              </div>

              <div className={styles.metadata}>
                {tags.length > 0 && (
                  <div className={styles.tagsList}>
                    {tags.map((tag, idx) => (
                      <span key={idx} className={styles.tag}>
                        <Tag size={10} />
                        {tag}
                        {isEditing && (
                          <button
                            type="button"
                            onClick={() => removeTag(tag)}
                            className={styles.tagRemove}
                          >
                            ×
                          </button>
                        )}
                      </span>
                    ))}
                  </div>
                )}
                {isEditing && (
                  <div className={styles.tagsInputContainer}>
                    <input
                      type="text"
                      value={newTag}
                      onChange={(e) => setNewTag(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && addTag()}
                      className={styles.tagInput}
                      placeholder="Add tag..."
                    />
                  </div>
                )}
              </div>
            </div>

            <div className={styles.content}>
              {/* Left Column: Action Plan */}
              <div className={styles.leftCol}>
                {/* Action Plan */}
                <div className={styles.section}>
                  <div className={styles.sectionHeader}>
                    <div className={styles.sectionTitle}>
                      <CheckSquare size={18} />
                      <h3>Action Plan</h3>
                    </div>
                    {isEditing && (
                      <button onClick={addActionItem} className={styles.addButton}>
                        <Plus size={14} /> Add Item
                      </button>
                    )}
                  </div>
                  <div className={styles.list}>
                    {actionPlan.length > 0 ? (
                      actionPlan.map((item, idx) => (
                        <ActionPlanItem
                          key={idx}
                          item={item}
                          index={idx}
                          isEditing={isEditing}
                          onChange={updateActionItem}
                          onDelete={removeActionItem}
                        />
                      ))
                    ) : (
                      <div className={styles.emptyState}>
                        No action plan defined
                      </div>
                    )}
                  </div>
                </div>

                {/* Dependencies */}
                <div className={styles.section}>
                  <DependencySection
                    dependencies={dependencies}
                    availableTasks={availableTasks || []}
                    currentTaskId={task.id}
                    onAdd={addDependency}
                    onRemove={removeDependency}
                    isEditing={isEditing}
                  />
                </div>
              </div>

              {/* Right Column: Exit Criteria & Notes */}
              <div className={styles.rightCol}>
                {/* Exit Criteria */}
                <div className={styles.section}>
                  <div className={styles.sectionHeader}>
                    <div className={styles.sectionTitle}>
                      <Target size={18} />
                      <h3>Exit Criteria</h3>
                    </div>
                    {isEditing && (
                      <button onClick={addExitCriterion} className={styles.addButton}>
                        <Plus size={14} /> Add Criteria
                      </button>
                    )}
                  </div>
                  
                  {totalCriteria > 0 && (
                    <div className={styles.progress}>
                      <div className={styles.progressBar}>
                        <div className={styles.progressFill} style={{ width: `${criteriaProgress}%` }} />
                      </div>
                      <div className={styles.progressText}>
                        {completedCriteria} of {totalCriteria} complete
                      </div>
                    </div>
                  )}

                  <div className={styles.list}>
                    {exitCriteria.length > 0 ? (
                      exitCriteria.map((criterion, idx) => (
                        <ExitCriteriaItem
                          key={idx}
                          criterion={criterion}
                          index={idx}
                          isEditing={isEditing}
                          onToggle={toggleExitCriterionStatus}
                          onChange={updateExitCriterion}
                          onDelete={removeExitCriterion}
                        />
                      ))
                    ) : (
                      <div className={styles.emptyState}>
                        No exit criteria defined
                      </div>
                    )}
                  </div>
                </div>

                {/* Notes */}
                <div className={styles.section}>
                  <div className={styles.sectionHeader}>
                    <div className={styles.sectionTitle}>
                      <FileText size={18} />
                      <h3>Notes</h3>
                    </div>
                  </div>
                  
                  <div className={styles.notesContainer}>
                    <div className={styles.noteTypeSelector}>
                      <button
                        className={`${styles.noteTypeBtn} ${noteType === 'general' ? styles.active : ''}`}
                        onClick={() => setNoteType('general')}
                      >
                        General
                      </button>
                      <button
                        className={`${styles.noteTypeBtn} ${noteType === 'research' ? styles.active : ''}`}
                        onClick={() => setNoteType('research')}
                      >
                        Research
                      </button>
                      <button
                        className={`${styles.noteTypeBtn} ${noteType === 'execution' ? styles.active : ''}`}
                        onClick={() => setNoteType('execution')}
                      >
                        Execution
                      </button>
                    </div>

                    <div className={styles.noteInput}>
                      <textarea
                        value={newNote}
                        onChange={(e) => setNewNote(e.target.value)}
                        className={styles.noteTextarea}
                        placeholder={`Add ${noteType} note...`}
                      />
                      <button onClick={addNote} className={styles.addButton}>
                        <Plus size={14} />
                      </button>
                    </div>

                    <div className={styles.list}>
                      {allNotes.length > 0 ? (
                        allNotes.map((note, idx) => (
                          <NoteItem
                            key={idx}
                            note={note}
                            type={note.type}
                            index={idx}
                          />
                        ))
                      ) : (
                        <div className={styles.emptyState}>
                          No notes yet
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
