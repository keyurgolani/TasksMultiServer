import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { TaskList, Status } from '../types';
import ReadyTasksPanel from '../components/ReadyTasksPanel';
import FormError from '../components/FormError';

const TaskListsPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const {
    projects,
    taskLists,
    tasks,
    loading,
    formError,
    loadProjects,
    loadTaskLists,
    loadTasks,
    createTaskList,
    updateTaskList,
    deleteTaskList,
    resetTaskList,
    selectTaskList,
    clearFormError,
  } = useApp();

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingTaskList, setEditingTaskList] = useState<TaskList | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    agent_instructions_template: '',
  });

  // Load data on mount
  useEffect(() => {
    loadProjects();
    loadTaskLists();
    loadTasks();
  }, [loadProjects, loadTaskLists, loadTasks]);

  // Get current project
  const currentProject = projects.find((p) => p.id === projectId);

  // Filter task lists for current project
  const projectTaskLists = taskLists.filter((tl) => tl.project_id === projectId);

  // Check if a task list is under the "Repeatable" project
  const isRepeatableTaskList = (taskList: TaskList): boolean => {
    const project = projects.find((p) => p.id === taskList.project_id);
    return project?.name === 'Repeatable';
  };

  // Check if all tasks in a task list are completed
  const areAllTasksCompleted = (taskListId: string): boolean => {
    const taskListTasks = tasks.filter((t) => t.task_list_id === taskListId);
    if (taskListTasks.length === 0) return false;
    return taskListTasks.every((t) => t.status === Status.COMPLETED);
  };

  // Handle form input changes
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  // Handle create task list
  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    clearFormError();
    
    if (!formData.name.trim() || !projectId) {
      return;
    }

    try {
      await createTaskList({
        name: formData.name,
        project_id: projectId,
        agent_instructions_template: formData.agent_instructions_template || undefined,
      });
      setFormData({ name: '', agent_instructions_template: '' });
      setShowCreateForm(false);
    } catch (error) {
      // Error handled by context
    }
  };

  // Handle edit task list
  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearFormError();
    
    if (!editingTaskList || !formData.name.trim()) {
      return;
    }

    try {
      await updateTaskList(editingTaskList.id, {
        name: formData.name,
        agent_instructions_template: formData.agent_instructions_template || undefined,
      });
      setFormData({ name: '', agent_instructions_template: '' });
      setEditingTaskList(null);
    } catch (error) {
      // Error handled by context
    }
  };

  // Handle delete task list
  const handleDelete = async (taskList: TaskList) => {
    if (window.confirm(`Are you sure you want to delete task list "${taskList.name}"? This will also delete all tasks within it.`)) {
      try {
        await deleteTaskList(taskList.id);
      } catch (error) {
        // Error handled by context
      }
    }
  };

  // Handle reset task list
  const handleReset = async (taskList: TaskList) => {
    if (!isRepeatableTaskList(taskList)) {
      alert('Only task lists under the "Repeatable" project can be reset.');
      return;
    }

    if (!areAllTasksCompleted(taskList.id)) {
      alert('All tasks must be completed before resetting the task list.');
      return;
    }

    if (window.confirm(`Are you sure you want to reset task list "${taskList.name}"? This will reset all task statuses and clear execution notes.`)) {
      try {
        await resetTaskList(taskList.id);
      } catch (error) {
        // Error handled by context
      }
    }
  };

  // Start editing a task list
  const startEdit = (taskList: TaskList) => {
    setEditingTaskList(taskList);
    setFormData({
      name: taskList.name,
      agent_instructions_template: taskList.agent_instructions_template || '',
    });
    setShowCreateForm(false);
  };

  // Cancel editing
  const cancelEdit = () => {
    setEditingTaskList(null);
    setFormData({ name: '', agent_instructions_template: '' });
  };

  // Show create form
  const showCreate = () => {
    setShowCreateForm(true);
    setEditingTaskList(null);
    setFormData({ name: '', agent_instructions_template: '' });
  };

  // Cancel create
  const cancelCreate = () => {
    setShowCreateForm(false);
    setFormData({ name: '', agent_instructions_template: '' });
  };

  // Navigate to tasks page
  const viewTasks = (taskList: TaskList) => {
    selectTaskList(taskList.id);
    navigate(`/task-lists/${taskList.id}/tasks`);
  };

  // Navigate back to projects
  const goBack = () => {
    navigate('/');
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
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
            ← Back to Projects
          </button>
          <h1 style={{ margin: 0 }}>
            Task Lists
            {currentProject && (
              <span style={{ fontSize: '1rem', color: '#666', fontWeight: 'normal', marginLeft: '1rem' }}>
                in {currentProject.name}
              </span>
            )}
          </h1>
        </div>
        {!showCreateForm && !editingTaskList && (
          <button
            onClick={showCreate}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#61dafb',
              color: '#282c34',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: 'bold',
            }}
          >
            + Create Task List
          </button>
        )}
      </div>

      {/* Create Form */}
      {showCreateForm && (
        <div style={{
          padding: '1.5rem',
          backgroundColor: '#f9f9f9',
          border: '1px solid #ddd',
          borderRadius: '8px',
          marginBottom: '2rem',
        }}>
          <h2 style={{ marginTop: 0 }}>Create New Task List</h2>
          {formError && <FormError message={formError.message} field={formError.field} />}
          <form onSubmit={handleCreate}>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                Task List Name *
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                required
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
                Agent Instructions Template (optional)
              </label>
              <textarea
                name="agent_instructions_template"
                value={formData.agent_instructions_template}
                onChange={handleInputChange}
                rows={4}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid #ccc',
                  borderRadius: '4px',
                  fontSize: '1rem',
                  fontFamily: 'monospace',
                }}
              />
            </div>
            <div style={{ display: 'flex', gap: '1rem' }}>
              <button
                type="submit"
                disabled={loading}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: '#61dafb',
                  color: '#282c34',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  fontWeight: 'bold',
                }}
              >
                Create
              </button>
              <button
                type="button"
                onClick={cancelCreate}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: '#ccc',
                  color: '#333',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                }}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Edit Form */}
      {editingTaskList && (
        <div style={{
          padding: '1.5rem',
          backgroundColor: '#f9f9f9',
          border: '1px solid #ddd',
          borderRadius: '8px',
          marginBottom: '2rem',
        }}>
          <h2 style={{ marginTop: 0 }}>Edit Task List: {editingTaskList.name}</h2>
          {formError && <FormError message={formError.message} field={formError.field} />}
          <form onSubmit={handleEdit}>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                Task List Name *
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                required
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
                Agent Instructions Template (optional)
              </label>
              <textarea
                name="agent_instructions_template"
                value={formData.agent_instructions_template}
                onChange={handleInputChange}
                rows={4}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid #ccc',
                  borderRadius: '4px',
                  fontSize: '1rem',
                  fontFamily: 'monospace',
                }}
              />
            </div>
            <div style={{ display: 'flex', gap: '1rem' }}>
              <button
                type="submit"
                disabled={loading}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: '#61dafb',
                  color: '#282c34',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  fontWeight: 'bold',
                }}
              >
                Save
              </button>
              <button
                type="button"
                onClick={cancelEdit}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: '#ccc',
                  color: '#333',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                }}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Loading State */}
      {loading && projectTaskLists.length === 0 && (
        <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
          Loading task lists...
        </div>
      )}

      {/* Empty State */}
      {!loading && projectTaskLists.length === 0 && (
        <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
          No task lists found. Create your first task list to get started.
        </div>
      )}

      {/* Ready Tasks Panel */}
      {projectId && currentProject && (
        <div style={{ marginBottom: '2rem' }}>
          <ReadyTasksPanel
            scopeType="project"
            scopeId={projectId}
            scopeName={currentProject.name}
          />
        </div>
      )}

      {/* Task Lists Grid */}
      {projectTaskLists.length > 0 && (
        <div style={{ display: 'grid', gap: '1rem' }}>
          {projectTaskLists.map((taskList) => {
            const taskCount = tasks.filter((t) => t.task_list_id === taskList.id).length;
            const completedCount = tasks.filter(
              (t) => t.task_list_id === taskList.id && t.status === Status.COMPLETED
            ).length;
            const isRepeatable = isRepeatableTaskList(taskList);
            const canReset = isRepeatable && areAllTasksCompleted(taskList.id);

            return (
              <div
                key={taskList.id}
                style={{
                  padding: '1.5rem',
                  backgroundColor: 'white',
                  border: '1px solid #ddd',
                  borderRadius: '8px',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                  <div style={{ flex: 1 }}>
                    <h3 style={{ margin: '0 0 0.5rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      {taskList.name}
                      {isRepeatable && (
                        <span style={{
                          fontSize: '0.75rem',
                          padding: '0.25rem 0.5rem',
                          backgroundColor: '#9c27b0',
                          color: 'white',
                          borderRadius: '4px',
                          fontWeight: 'normal',
                        }}>
                          REPEATABLE
                        </span>
                      )}
                    </h3>
                    <div style={{ fontSize: '0.875rem', color: '#666', marginBottom: '0.5rem' }}>
                      <div>Tasks: {completedCount} / {taskCount} completed</div>
                      <div>Created: {new Date(taskList.created_at).toLocaleString()}</div>
                      <div>Updated: {new Date(taskList.updated_at).toLocaleString()}</div>
                    </div>
                    {taskList.agent_instructions_template && (
                      <div style={{ marginTop: '0.5rem' }}>
                        <strong style={{ fontSize: '0.875rem' }}>Agent Instructions Template:</strong>
                        <pre style={{
                          marginTop: '0.25rem',
                          padding: '0.5rem',
                          backgroundColor: '#f5f5f5',
                          border: '1px solid #ddd',
                          borderRadius: '4px',
                          fontSize: '0.75rem',
                          overflow: 'auto',
                          maxHeight: '100px',
                        }}>
                          {taskList.agent_instructions_template}
                        </pre>
                      </div>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem', marginLeft: '1rem', flexWrap: 'wrap' }}>
                    <button
                      onClick={() => viewTasks(taskList)}
                      style={{
                        padding: '0.5rem 1rem',
                        backgroundColor: '#61dafb',
                        color: '#282c34',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '0.875rem',
                      }}
                    >
                      View Tasks
                    </button>
                    <button
                      onClick={() => startEdit(taskList)}
                      disabled={editingTaskList?.id === taskList.id}
                      style={{
                        padding: '0.5rem 1rem',
                        backgroundColor: '#4CAF50',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: editingTaskList?.id === taskList.id ? 'not-allowed' : 'pointer',
                        fontSize: '0.875rem',
                      }}
                    >
                      Edit
                    </button>
                    {isRepeatable && (
                      <button
                        onClick={() => handleReset(taskList)}
                        disabled={!canReset}
                        style={{
                          padding: '0.5rem 1rem',
                          backgroundColor: canReset ? '#ff9800' : '#ccc',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: canReset ? 'pointer' : 'not-allowed',
                          fontSize: '0.875rem',
                        }}
                        title={canReset ? 'Reset task list' : 'All tasks must be completed to reset'}
                      >
                        Reset
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(taskList)}
                      style={{
                        padding: '0.5rem 1rem',
                        backgroundColor: '#f44336',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '0.875rem',
                      }}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default TaskListsPage;
