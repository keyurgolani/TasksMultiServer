import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import {
  Task,
  Status,
  Priority,
  ExitCriteriaStatus,
  Dependency,
  ExitCriteria,
  Note,
  ActionPlanItem,
} from '../types';
import DependencyGraph from '../components/DependencyGraph';
import FormError from '../components/FormError';

const TaskDetailPage: React.FC = () => {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const { tasks, taskLists, loading, formError, loadTasks, loadTaskLists, updateTask, clearFormError } = useApp();

  const [task, setTask] = useState<Task | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    status: Status.NOT_STARTED,
    priority: Priority.MEDIUM,
    agent_instructions_template: '',
  });

  // State for managing different sections
  const [exitCriteria, setExitCriteria] = useState<ExitCriteria[]>([]);
  const [dependencies, setDependencies] = useState<Dependency[]>([]);
  const [notes, setNotes] = useState<Note[]>([]);
  const [researchNotes, setResearchNotes] = useState<Note[]>([]);
  const [executionNotes, setExecutionNotes] = useState<Note[]>([]);
  const [actionPlan, setActionPlan] = useState<ActionPlanItem[]>([]);
  const [showDependencyGraph, setShowDependencyGraph] = useState(false);

  // New item inputs
  const [newNote, setNewNote] = useState('');
  const [newResearchNote, setNewResearchNote] = useState('');
  const [newExecutionNote, setNewExecutionNote] = useState('');
  const [newActionItem, setNewActionItem] = useState('');
  const [newDependency, setNewDependency] = useState({ task_id: '', task_list_id: '' });

  // Load data on mount
  useEffect(() => {
    loadTasks();
    loadTaskLists();
  }, [loadTasks, loadTaskLists]);

  // Find current task
  useEffect(() => {
    if (taskId && tasks.length > 0) {
      const foundTask = tasks.find((t) => t.id === taskId);
      if (foundTask) {
        setTask(foundTask);
        setFormData({
          title: foundTask.title,
          description: foundTask.description,
          status: foundTask.status,
          priority: foundTask.priority,
          agent_instructions_template: foundTask.agent_instructions_template || '',
        });
        setExitCriteria(foundTask.exit_criteria);
        setDependencies(foundTask.dependencies);
        setNotes(foundTask.notes);
        setResearchNotes(foundTask.research_notes || []);
        setExecutionNotes(foundTask.execution_notes || []);
        setActionPlan(foundTask.action_plan || []);
      }
    }
  }, [taskId, tasks]);

  // Handle form input changes
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  // Handle save
  const handleSave = async () => {
    if (!task) return;
    clearFormError();

    try {
      await updateTask(task.id, {
        title: formData.title,
        description: formData.description,
        status: formData.status,
        priority: formData.priority,
        agent_instructions_template: formData.agent_instructions_template || undefined,
        exit_criteria: exitCriteria,
        dependencies,
        notes,
        research_notes: researchNotes.length > 0 ? researchNotes : undefined,
        execution_notes: executionNotes.length > 0 ? executionNotes : undefined,
        action_plan: actionPlan.length > 0 ? actionPlan : undefined,
      });
      setEditMode(false);
    } catch (error) {
      // Error handled by context
    }
  };

  // Exit Criteria handlers
  const handleExitCriteriaChange = (index: number, field: keyof ExitCriteria, value: string) => {
    const updated = [...exitCriteria];
    if (field === 'status') {
      updated[index] = { ...updated[index], status: value as ExitCriteriaStatus };
    } else {
      updated[index] = { ...updated[index], [field]: value };
    }
    setExitCriteria(updated);
  };

  const addExitCriteria = () => {
    setExitCriteria([...exitCriteria, { criteria: '', status: ExitCriteriaStatus.INCOMPLETE }]);
  };

  const removeExitCriteria = (index: number) => {
    if (exitCriteria.length > 1) {
      setExitCriteria(exitCriteria.filter((_, i) => i !== index));
    }
  };

  // Dependency handlers
  const handleDependencyChange = (field: keyof Dependency, value: string) => {
    setNewDependency((prev) => ({ ...prev, [field]: value }));
  };

  const addDependency = () => {
    if (newDependency.task_id && newDependency.task_list_id) {
      setDependencies([...dependencies, newDependency]);
      setNewDependency({ task_id: '', task_list_id: '' });
    }
  };

  const removeDependency = (index: number) => {
    setDependencies(dependencies.filter((_, i) => i !== index));
  };

  // Note handlers
  const addNote = () => {
    if (newNote.trim()) {
      setNotes([...notes, { content: newNote, timestamp: new Date().toISOString() }]);
      setNewNote('');
    }
  };

  const addResearchNote = () => {
    if (newResearchNote.trim()) {
      setResearchNotes([...researchNotes, { content: newResearchNote, timestamp: new Date().toISOString() }]);
      setNewResearchNote('');
    }
  };

  const addExecutionNote = () => {
    if (newExecutionNote.trim()) {
      setExecutionNotes([...executionNotes, { content: newExecutionNote, timestamp: new Date().toISOString() }]);
      setNewExecutionNote('');
    }
  };

  // Action Plan handlers
  const addActionItem = () => {
    if (newActionItem.trim()) {
      const nextSequence = actionPlan.length > 0 ? Math.max(...actionPlan.map((a) => a.sequence)) + 1 : 1;
      setActionPlan([...actionPlan, { sequence: nextSequence, content: newActionItem }]);
      setNewActionItem('');
    }
  };

  const removeActionItem = (index: number) => {
    setActionPlan(actionPlan.filter((_, i) => i !== index));
  };

  const moveActionItemUp = (index: number) => {
    if (index > 0) {
      const updated = [...actionPlan];
      [updated[index - 1], updated[index]] = [updated[index], updated[index - 1]];
      // Update sequences
      updated.forEach((item, i) => {
        item.sequence = i + 1;
      });
      setActionPlan(updated);
    }
  };

  const moveActionItemDown = (index: number) => {
    if (index < actionPlan.length - 1) {
      const updated = [...actionPlan];
      [updated[index], updated[index + 1]] = [updated[index + 1], updated[index]];
      // Update sequences
      updated.forEach((item, i) => {
        item.sequence = i + 1;
      });
      setActionPlan(updated);
    }
  };

  // Navigate back
  const goBack = () => {
    if (task) {
      navigate(`/task-lists/${task.task_list_id}/tasks`);
    } else {
      navigate('/');
    }
  };

  // Get status badge color
  const getStatusColor = (status: Status): string => {
    switch (status) {
      case Status.NOT_STARTED:
        return '#9e9e9e';
      case Status.IN_PROGRESS:
        return '#2196f3';
      case Status.BLOCKED:
        return '#f44336';
      case Status.COMPLETED:
        return '#4caf50';
      default:
        return '#9e9e9e';
    }
  };

  // Get priority badge color
  const getPriorityColor = (priority: Priority): string => {
    switch (priority) {
      case Priority.CRITICAL:
        return '#d32f2f';
      case Priority.HIGH:
        return '#f57c00';
      case Priority.MEDIUM:
        return '#fbc02d';
      case Priority.LOW:
        return '#388e3c';
      case Priority.TRIVIAL:
        return '#616161';
      default:
        return '#9e9e9e';
    }
  };

  if (!task) {
    return (
      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem' }}>
        <button
          onClick={goBack}
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: '#ccc',
            color: '#333',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            marginBottom: '1rem',
          }}
        >
          ← Back
        </button>
        <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
          {loading ? 'Loading task...' : 'Task not found'}
        </div>
      </div>
    );
  }

  const currentTaskList = taskLists.find((tl) => tl.id === task.task_list_id);

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem' }}>
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <button
          onClick={goBack}
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: '#ccc',
            color: '#333',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            marginBottom: '1rem',
          }}
        >
          ← Back to Tasks
        </button>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
          <div>
            <h1 style={{ margin: '0 0 0.5rem 0' }}>Task Details</h1>
            {currentTaskList && (
              <p style={{ margin: 0, color: '#666' }}>Task List: {currentTaskList.name}</p>
            )}
          </div>
          <button
            onClick={() => setEditMode(!editMode)}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: editMode ? '#ccc' : '#61dafb',
              color: editMode ? '#333' : '#282c34',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: 'bold',
            }}
          >
            {editMode ? 'Cancel Edit' : 'Edit Task'}
          </button>
        </div>
      </div>

      {/* Basic Information */}
      <div style={{
        padding: '1.5rem',
        backgroundColor: 'white',
        border: '1px solid #ddd',
        borderRadius: '8px',
        marginBottom: '1.5rem',
      }}>
        <h2 style={{ marginTop: 0 }}>Basic Information</h2>
        {editMode && formError && <FormError message={formError.message} field={formError.field} />}
        {editMode ? (
          <div>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                Title *
              </label>
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleInputChange}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid #ccc',
                  borderRadius: '4px',
                  fontSize: '1rem',
                }}
              />
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                Description *
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                rows={4}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid #ccc',
                  borderRadius: '4px',
                  fontSize: '1rem',
                }}
              />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                  Status *
                </label>
                <select
                  name="status"
                  value={formData.status}
                  onChange={handleInputChange}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    border: '1px solid #ccc',
                    borderRadius: '4px',
                    fontSize: '1rem',
                  }}
                >
                  {Object.values(Status).map((status) => (
                    <option key={status} value={status}>
                      {status.replace('_', ' ')}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                  Priority *
                </label>
                <select
                  name="priority"
                  value={formData.priority}
                  onChange={handleInputChange}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    border: '1px solid #ccc',
                    borderRadius: '4px',
                    fontSize: '1rem',
                  }}
                >
                  {Object.values(Priority).map((priority) => (
                    <option key={priority} value={priority}>
                      {priority}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                Agent Instructions Template (optional)
              </label>
              <textarea
                name="agent_instructions_template"
                value={formData.agent_instructions_template}
                onChange={handleInputChange}
                rows={3}
                placeholder="Template with placeholders like {title}, {description}, etc."
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid #ccc',
                  borderRadius: '4px',
                  fontSize: '1rem',
                }}
              />
            </div>
          </div>
        ) : (
          <div>
            <div style={{ marginBottom: '1rem' }}>
              <strong>Title:</strong> {task.title}
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <strong>Description:</strong> {task.description}
            </div>
            <div style={{ marginBottom: '1rem', display: 'flex', gap: '1rem' }}>
              <div>
                <strong>Status:</strong>{' '}
                <span style={{
                  padding: '0.25rem 0.5rem',
                  backgroundColor: getStatusColor(task.status),
                  color: 'white',
                  borderRadius: '4px',
                  fontSize: '0.875rem',
                }}>
                  {task.status.replace('_', ' ')}
                </span>
              </div>
              <div>
                <strong>Priority:</strong>{' '}
                <span style={{
                  padding: '0.25rem 0.5rem',
                  backgroundColor: getPriorityColor(task.priority),
                  color: 'white',
                  borderRadius: '4px',
                  fontSize: '0.875rem',
                }}>
                  {task.priority}
                </span>
              </div>
            </div>
            {task.agent_instructions_template && (
              <div style={{ marginBottom: '1rem' }}>
                <strong>Agent Instructions Template:</strong>
                <pre style={{
                  backgroundColor: '#f5f5f5',
                  padding: '0.5rem',
                  borderRadius: '4px',
                  overflow: 'auto',
                  fontSize: '0.875rem',
                }}>
                  {task.agent_instructions_template}
                </pre>
              </div>
            )}
            <div style={{ fontSize: '0.875rem', color: '#666' }}>
              <div>Created: {new Date(task.created_at).toLocaleString()}</div>
              <div>Updated: {new Date(task.updated_at).toLocaleString()}</div>
            </div>
          </div>
        )}
      </div>

      {/* Exit Criteria */}
      <div style={{
        padding: '1.5rem',
        backgroundColor: 'white',
        border: '1px solid #ddd',
        borderRadius: '8px',
        marginBottom: '1.5rem',
      }}>
        <h2 style={{ marginTop: 0 }}>Exit Criteria</h2>
        {editMode ? (
          <div>
            {exitCriteria.map((ec, index) => (
              <div key={index} style={{ marginBottom: '1rem', padding: '1rem', backgroundColor: '#f9f9f9', borderRadius: '4px' }}>
                <div style={{ marginBottom: '0.5rem' }}>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                    Criteria
                  </label>
                  <input
                    type="text"
                    value={ec.criteria}
                    onChange={(e) => handleExitCriteriaChange(index, 'criteria', e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.5rem',
                      border: '1px solid #ccc',
                      borderRadius: '4px',
                      fontSize: '1rem',
                    }}
                  />
                </div>
                <div style={{ marginBottom: '0.5rem' }}>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                    Status
                  </label>
                  <select
                    value={ec.status}
                    onChange={(e) => handleExitCriteriaChange(index, 'status', e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.5rem',
                      border: '1px solid #ccc',
                      borderRadius: '4px',
                      fontSize: '1rem',
                    }}
                  >
                    {Object.values(ExitCriteriaStatus).map((status) => (
                      <option key={status} value={status}>
                        {status}
                      </option>
                    ))}
                  </select>
                </div>
                <div style={{ marginBottom: '0.5rem' }}>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                    Comment (optional)
                  </label>
                  <input
                    type="text"
                    value={ec.comment || ''}
                    onChange={(e) => handleExitCriteriaChange(index, 'comment', e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.5rem',
                      border: '1px solid #ccc',
                      borderRadius: '4px',
                      fontSize: '1rem',
                    }}
                  />
                </div>
                {exitCriteria.length > 1 && (
                  <button
                    onClick={() => removeExitCriteria(index)}
                    style={{
                      padding: '0.5rem 1rem',
                      backgroundColor: '#f44336',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                    }}
                  >
                    Remove
                  </button>
                )}
              </div>
            ))}
            <button
              onClick={addExitCriteria}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#4CAF50',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              + Add Exit Criteria
            </button>
          </div>
        ) : (
          <div>
            {exitCriteria.length === 0 ? (
              <p style={{ color: '#666' }}>No exit criteria defined</p>
            ) : (
              exitCriteria.map((ec, index) => (
                <div key={index} style={{ marginBottom: '1rem', padding: '1rem', backgroundColor: '#f9f9f9', borderRadius: '4px' }}>
                  <div style={{ marginBottom: '0.5rem' }}>
                    <strong>Criteria:</strong> {ec.criteria}
                  </div>
                  <div style={{ marginBottom: '0.5rem' }}>
                    <strong>Status:</strong>{' '}
                    <span style={{
                      padding: '0.25rem 0.5rem',
                      backgroundColor: ec.status === ExitCriteriaStatus.COMPLETE ? '#4caf50' : '#9e9e9e',
                      color: 'white',
                      borderRadius: '4px',
                      fontSize: '0.875rem',
                    }}>
                      {ec.status}
                    </span>
                  </div>
                  {ec.comment && (
                    <div>
                      <strong>Comment:</strong> {ec.comment}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Dependencies */}
      <div style={{
        padding: '1.5rem',
        backgroundColor: 'white',
        border: '1px solid #ddd',
        borderRadius: '8px',
        marginBottom: '1.5rem',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2 style={{ margin: 0 }}>Dependencies</h2>
          {!editMode && tasks.filter((t) => t.task_list_id === task.task_list_id).length > 1 && (
            <button
              onClick={() => setShowDependencyGraph(!showDependencyGraph)}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: showDependencyGraph ? '#4CAF50' : '#2196f3',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.875rem',
              }}
            >
              {showDependencyGraph ? '✓ Hide Graph' : '📊 Show Graph'}
            </button>
          )}
        </div>
        
        {/* Dependency Graph */}
        {showDependencyGraph && (
          <div style={{ marginBottom: '1rem' }}>
            <DependencyGraph
              tasks={tasks.filter((t) => t.task_list_id === task.task_list_id)}
              highlightTaskId={task.id}
            />
          </div>
        )}
        {editMode ? (
          <div>
            {dependencies.map((dep, index) => (
              <div key={index} style={{ marginBottom: '0.5rem', padding: '0.5rem', backgroundColor: '#f9f9f9', borderRadius: '4px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div><strong>Task ID:</strong> {dep.task_id}</div>
                  <div><strong>Task List ID:</strong> {dep.task_list_id}</div>
                </div>
                <button
                  onClick={() => removeDependency(index)}
                  style={{
                    padding: '0.5rem 1rem',
                    backgroundColor: '#f44336',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                  }}
                >
                  Remove
                </button>
              </div>
            ))}
            <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: '#f9f9f9', borderRadius: '4px' }}>
              <h3 style={{ marginTop: 0 }}>Add Dependency</h3>
              <div style={{ marginBottom: '0.5rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                  Task ID
                </label>
                <input
                  type="text"
                  value={newDependency.task_id}
                  onChange={(e) => handleDependencyChange('task_id', e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    border: '1px solid #ccc',
                    borderRadius: '4px',
                    fontSize: '1rem',
                  }}
                />
              </div>
              <div style={{ marginBottom: '0.5rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                  Task List ID
                </label>
                <input
                  type="text"
                  value={newDependency.task_list_id}
                  onChange={(e) => handleDependencyChange('task_list_id', e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    border: '1px solid #ccc',
                    borderRadius: '4px',
                    fontSize: '1rem',
                  }}
                />
              </div>
              <button
                onClick={addDependency}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: '#4CAF50',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                }}
              >
                Add Dependency
              </button>
            </div>
          </div>
        ) : (
          <div>
            {dependencies.length === 0 ? (
              <p style={{ color: '#666' }}>No dependencies</p>
            ) : (
              dependencies.map((dep, index) => (
                <div key={index} style={{ marginBottom: '0.5rem', padding: '0.5rem', backgroundColor: '#f9f9f9', borderRadius: '4px' }}>
                  <div><strong>Task ID:</strong> {dep.task_id}</div>
                  <div><strong>Task List ID:</strong> {dep.task_list_id}</div>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Notes */}
      <div style={{
        padding: '1.5rem',
        backgroundColor: 'white',
        border: '1px solid #ddd',
        borderRadius: '8px',
        marginBottom: '1.5rem',
      }}>
        <h2 style={{ marginTop: 0 }}>Notes</h2>
        {notes.length === 0 ? (
          <p style={{ color: '#666' }}>No notes</p>
        ) : (
          notes.map((note, index) => (
            <div key={index} style={{ marginBottom: '0.5rem', padding: '0.5rem', backgroundColor: '#f9f9f9', borderRadius: '4px' }}>
              <div style={{ fontSize: '0.875rem', color: '#666', marginBottom: '0.25rem' }}>
                {new Date(note.timestamp).toLocaleString()}
              </div>
              <div>{note.content}</div>
            </div>
          ))
        )}
        {editMode && (
          <div style={{ marginTop: '1rem' }}>
            <textarea
              value={newNote}
              onChange={(e) => setNewNote(e.target.value)}
              placeholder="Add a note..."
              rows={3}
              style={{
                width: '100%',
                padding: '0.5rem',
                border: '1px solid #ccc',
                borderRadius: '4px',
                fontSize: '1rem',
                marginBottom: '0.5rem',
              }}
            />
            <button
              onClick={addNote}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#4CAF50',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              Add Note
            </button>
          </div>
        )}
      </div>

      {/* Research Notes */}
      <div style={{
        padding: '1.5rem',
        backgroundColor: 'white',
        border: '1px solid #ddd',
        borderRadius: '8px',
        marginBottom: '1.5rem',
      }}>
        <h2 style={{ marginTop: 0 }}>Research Notes</h2>
        {researchNotes.length === 0 ? (
          <p style={{ color: '#666' }}>No research notes</p>
        ) : (
          researchNotes.map((note, index) => (
            <div key={index} style={{ marginBottom: '0.5rem', padding: '0.5rem', backgroundColor: '#f9f9f9', borderRadius: '4px' }}>
              <div style={{ fontSize: '0.875rem', color: '#666', marginBottom: '0.25rem' }}>
                {new Date(note.timestamp).toLocaleString()}
              </div>
              <div>{note.content}</div>
            </div>
          ))
        )}
        {editMode && (
          <div style={{ marginTop: '1rem' }}>
            <textarea
              value={newResearchNote}
              onChange={(e) => setNewResearchNote(e.target.value)}
              placeholder="Add a research note..."
              rows={3}
              style={{
                width: '100%',
                padding: '0.5rem',
                border: '1px solid #ccc',
                borderRadius: '4px',
                fontSize: '1rem',
                marginBottom: '0.5rem',
              }}
            />
            <button
              onClick={addResearchNote}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#4CAF50',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              Add Research Note
            </button>
          </div>
        )}
      </div>

      {/* Execution Notes */}
      <div style={{
        padding: '1.5rem',
        backgroundColor: 'white',
        border: '1px solid #ddd',
        borderRadius: '8px',
        marginBottom: '1.5rem',
      }}>
        <h2 style={{ marginTop: 0 }}>Execution Notes</h2>
        {executionNotes.length === 0 ? (
          <p style={{ color: '#666' }}>No execution notes</p>
        ) : (
          executionNotes.map((note, index) => (
            <div key={index} style={{ marginBottom: '0.5rem', padding: '0.5rem', backgroundColor: '#f9f9f9', borderRadius: '4px' }}>
              <div style={{ fontSize: '0.875rem', color: '#666', marginBottom: '0.25rem' }}>
                {new Date(note.timestamp).toLocaleString()}
              </div>
              <div>{note.content}</div>
            </div>
          ))
        )}
        {editMode && (
          <div style={{ marginTop: '1rem' }}>
            <textarea
              value={newExecutionNote}
              onChange={(e) => setNewExecutionNote(e.target.value)}
              placeholder="Add an execution note..."
              rows={3}
              style={{
                width: '100%',
                padding: '0.5rem',
                border: '1px solid #ccc',
                borderRadius: '4px',
                fontSize: '1rem',
                marginBottom: '0.5rem',
              }}
            />
            <button
              onClick={addExecutionNote}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#4CAF50',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              Add Execution Note
            </button>
          </div>
        )}
      </div>

      {/* Action Plan */}
      <div style={{
        padding: '1.5rem',
        backgroundColor: 'white',
        border: '1px solid #ddd',
        borderRadius: '8px',
        marginBottom: '1.5rem',
      }}>
        <h2 style={{ marginTop: 0 }}>Action Plan</h2>
        {actionPlan.length === 0 ? (
          <p style={{ color: '#666' }}>No action plan items</p>
        ) : (
          <div>
            {actionPlan.map((item, index) => (
              <div key={index} style={{ marginBottom: '0.5rem', padding: '0.5rem', backgroundColor: '#f9f9f9', borderRadius: '4px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ flex: 1 }}>
                  <strong>{item.sequence}.</strong> {item.content}
                </div>
                {editMode && (
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button
                      onClick={() => moveActionItemUp(index)}
                      disabled={index === 0}
                      style={{
                        padding: '0.25rem 0.5rem',
                        backgroundColor: index === 0 ? '#ccc' : '#2196f3',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: index === 0 ? 'not-allowed' : 'pointer',
                        fontSize: '0.875rem',
                      }}
                    >
                      ↑
                    </button>
                    <button
                      onClick={() => moveActionItemDown(index)}
                      disabled={index === actionPlan.length - 1}
                      style={{
                        padding: '0.25rem 0.5rem',
                        backgroundColor: index === actionPlan.length - 1 ? '#ccc' : '#2196f3',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: index === actionPlan.length - 1 ? 'not-allowed' : 'pointer',
                        fontSize: '0.875rem',
                      }}
                    >
                      ↓
                    </button>
                    <button
                      onClick={() => removeActionItem(index)}
                      style={{
                        padding: '0.25rem 0.5rem',
                        backgroundColor: '#f44336',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '0.875rem',
                      }}
                    >
                      Remove
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
        {editMode && (
          <div style={{ marginTop: '1rem' }}>
            <input
              type="text"
              value={newActionItem}
              onChange={(e) => setNewActionItem(e.target.value)}
              placeholder="Add an action item..."
              style={{
                width: '100%',
                padding: '0.5rem',
                border: '1px solid #ccc',
                borderRadius: '4px',
                fontSize: '1rem',
                marginBottom: '0.5rem',
              }}
            />
            <button
              onClick={addActionItem}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#4CAF50',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              Add Action Item
            </button>
          </div>
        )}
      </div>

      {/* Save Button */}
      {editMode && (
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
          <button
            onClick={handleSave}
            disabled={loading}
            style={{
              padding: '0.75rem 2rem',
              backgroundColor: '#61dafb',
              color: '#282c34',
              border: 'none',
              borderRadius: '4px',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontWeight: 'bold',
              fontSize: '1rem',
            }}
          >
            Save Changes
          </button>
          <button
            onClick={() => setEditMode(false)}
            style={{
              padding: '0.75rem 2rem',
              backgroundColor: '#ccc',
              color: '#333',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '1rem',
            }}
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  );
};

export default TaskDetailPage;
