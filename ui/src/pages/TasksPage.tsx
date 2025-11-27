import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { Task, Status, Priority, ExitCriteriaStatus, SearchCriteria } from '../types';
import ReadyTasksPanel from '../components/ReadyTasksPanel';
import DependencyGraph from '../components/DependencyGraph';
import FormError from '../components/FormError';
import TagInput from '../components/TagInput';
import TagFilter from '../components/TagFilter';
import SearchBar from '../components/SearchBar';
import FilterChips from '../components/FilterChips';
import { taskApi } from '../api/services';

const TasksPage: React.FC = () => {
  const { taskListId } = useParams<{ taskListId: string }>();
  const navigate = useNavigate();
  const {
    taskLists,
    tasks,
    loading,
    formError,
    loadTaskLists,
    loadTasks,
    createTask,
    updateTask,
    deleteTask,
    selectTask,
    clearFormError,
  } = useApp();

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [showDependencyGraph, setShowDependencyGraph] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    status: Status.NOT_STARTED,
    priority: Priority.MEDIUM,
    exit_criteria: [''],
    tags: [] as string[],
  });
  const [selectedTagFilters, setSelectedTagFilters] = useState<string[]>([]);
  const [searchCriteria, setSearchCriteria] = useState<SearchCriteria>({});
  const [searchResults, setSearchResults] = useState<Task[] | null>(null);
  const [isSearching, setIsSearching] = useState(false);

  // Load data on mount
  useEffect(() => {
    loadTaskLists();
    loadTasks();
  }, [loadTaskLists, loadTasks]);

  // Get current task list
  const currentTaskList = taskLists.find((tl) => tl.id === taskListId);

  // Determine which tasks to display
  let taskListTasks: Task[];
  if (searchResults !== null) {
    // Use search results if a search is active
    taskListTasks = searchResults.filter((t) => t.task_list_id === taskListId);
  } else {
    // Otherwise use regular filtered tasks
    taskListTasks = tasks.filter((t) => t.task_list_id === taskListId);
    
    // Apply tag filters (legacy filter, kept for backward compatibility)
    if (selectedTagFilters.length > 0) {
      taskListTasks = taskListTasks.filter((task) =>
        selectedTagFilters.every((filterTag) => task.tags.includes(filterTag))
      );
    }
  }
  
  // Get all unique tags from tasks in this task list
  const allTags = Array.from(
    new Set(
      tasks
        .filter((t) => t.task_list_id === taskListId)
        .flatMap((t) => t.tags)
    )
  ).sort();

  // Handle form input changes
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  // Handle exit criteria changes
  const handleExitCriteriaChange = (index: number, value: string) => {
    const newExitCriteria = [...formData.exit_criteria];
    newExitCriteria[index] = value;
    setFormData((prev) => ({ ...prev, exit_criteria: newExitCriteria }));
  };

  // Add exit criteria field
  const addExitCriteria = () => {
    setFormData((prev) => ({
      ...prev,
      exit_criteria: [...prev.exit_criteria, ''],
    }));
  };

  // Remove exit criteria field
  const removeExitCriteria = (index: number) => {
    if (formData.exit_criteria.length > 1) {
      const newExitCriteria = formData.exit_criteria.filter((_, i) => i !== index);
      setFormData((prev) => ({ ...prev, exit_criteria: newExitCriteria }));
    }
  };

  // Handle create task
  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    clearFormError();
    
    if (!formData.title.trim() || !formData.description.trim() || !taskListId) {
      return;
    }

    // Filter out empty exit criteria
    const validExitCriteria = formData.exit_criteria.filter((ec) => ec.trim() !== '');
    if (validExitCriteria.length === 0) {
      alert('At least one exit criteria is required');
      return;
    }

    try {
      await createTask({
        task_list_id: taskListId,
        title: formData.title,
        description: formData.description,
        status: formData.status,
        priority: formData.priority,
        dependencies: [],
        exit_criteria: validExitCriteria.map((criteria) => ({
          criteria,
          status: ExitCriteriaStatus.INCOMPLETE,
        })),
        notes: [],
        tags: formData.tags,
      });
      setFormData({
        title: '',
        description: '',
        status: Status.NOT_STARTED,
        priority: Priority.MEDIUM,
        exit_criteria: [''],
        tags: [],
      });
      setShowCreateForm(false);
    } catch (error) {
      // Error handled by context
    }
  };

  // Handle edit task
  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearFormError();
    
    if (!editingTask || !formData.title.trim() || !formData.description.trim()) {
      return;
    }

    // Filter out empty exit criteria
    const validExitCriteria = formData.exit_criteria.filter((ec) => ec.trim() !== '');
    if (validExitCriteria.length === 0) {
      alert('At least one exit criteria is required');
      return;
    }

    try {
      await updateTask(editingTask.id, {
        title: formData.title,
        description: formData.description,
        status: formData.status,
        priority: formData.priority,
        exit_criteria: validExitCriteria.map((criteria, index) => {
          // Preserve existing status if available
          const existingCriteria = editingTask.exit_criteria[index];
          return {
            criteria,
            status: existingCriteria?.status || ExitCriteriaStatus.INCOMPLETE,
            comment: existingCriteria?.comment,
          };
        }),
        tags: formData.tags,
      });
      setFormData({
        title: '',
        description: '',
        status: Status.NOT_STARTED,
        priority: Priority.MEDIUM,
        exit_criteria: [''],
        tags: [],
      });
      setEditingTask(null);
    } catch (error) {
      // Error handled by context
    }
  };

  // Handle delete task
  const handleDelete = async (task: Task) => {
    if (window.confirm(`Are you sure you want to delete task "${task.title}"?`)) {
      try {
        await deleteTask(task.id);
      } catch (error) {
        // Error handled by context
      }
    }
  };

  // Start editing a task
  const startEdit = (task: Task) => {
    setEditingTask(task);
    setFormData({
      title: task.title,
      description: task.description,
      status: task.status,
      priority: task.priority,
      exit_criteria: task.exit_criteria.map((ec) => ec.criteria),
      tags: task.tags || [],
    });
    setShowCreateForm(false);
  };

  // Cancel editing
  const cancelEdit = () => {
    setEditingTask(null);
    setFormData({
      title: '',
      description: '',
      status: Status.NOT_STARTED,
      priority: Priority.MEDIUM,
      exit_criteria: [''],
      tags: [],
    });
  };

  // Show create form
  const showCreate = () => {
    setShowCreateForm(true);
    setEditingTask(null);
    setFormData({
      title: '',
      description: '',
      status: Status.NOT_STARTED,
      priority: Priority.MEDIUM,
      exit_criteria: [''],
      tags: [],
    });
  };

  // Cancel create
  const cancelCreate = () => {
    setShowCreateForm(false);
    setFormData({
      title: '',
      description: '',
      status: Status.NOT_STARTED,
      priority: Priority.MEDIUM,
      exit_criteria: [''],
      tags: [],
    });
  };

  // Navigate to task detail page
  const viewTaskDetail = (task: Task) => {
    selectTask(task.id);
    navigate(`/tasks/${task.id}`);
  };

  // Navigate back to task lists
  const goBack = () => {
    if (currentTaskList) {
      navigate(`/projects/${currentTaskList.project_id}/task-lists`);
    } else {
      navigate('/');
    }
  };

  // Handle search
  const handleSearch = async (criteria: SearchCriteria) => {
    // If no criteria provided, clear search
    if (!criteria.query && !criteria.status && !criteria.priority && !criteria.tags) {
      setSearchCriteria({});
      setSearchResults(null);
      return;
    }

    setIsSearching(true);
    try {
      const response = await taskApi.search(criteria);
      setSearchResults(response.results);
      setSearchCriteria(criteria);
    } catch (error) {
      console.error('Search failed:', error);
      // Fall back to showing all tasks
      setSearchResults(null);
      setSearchCriteria({});
    } finally {
      setIsSearching(false);
    }
  };

  // Handle filter removal
  const handleRemoveFilter = (filterType: string, value?: string) => {
    const newCriteria = { ...searchCriteria };

    if (filterType === 'query') {
      delete newCriteria.query;
    } else if (filterType === 'status' && value) {
      newCriteria.status = newCriteria.status?.filter((s) => s !== value);
      if (newCriteria.status?.length === 0) delete newCriteria.status;
    } else if (filterType === 'priority' && value) {
      newCriteria.priority = newCriteria.priority?.filter((p) => p !== value);
      if (newCriteria.priority?.length === 0) delete newCriteria.priority;
    } else if (filterType === 'tag' && value) {
      newCriteria.tags = newCriteria.tags?.filter((t) => t !== value);
      if (newCriteria.tags?.length === 0) delete newCriteria.tags;
    }

    handleSearch(newCriteria);
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
            ← Back to Task Lists
          </button>
          <h1 style={{ margin: 0 }}>
            Tasks
            {currentTaskList && (
              <span style={{ fontSize: '1rem', color: '#666', fontWeight: 'normal', marginLeft: '1rem' }}>
                in {currentTaskList.name}
              </span>
            )}
          </h1>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {!showCreateForm && !editingTask && taskListTasks.length > 0 && (
            <button
              onClick={() => setShowDependencyGraph(!showDependencyGraph)}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: showDependencyGraph ? '#4CAF50' : '#2196f3',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontWeight: 'bold',
              }}
            >
              {showDependencyGraph ? '✓ Hide Graph' : '📊 Show Dependency Graph'}
            </button>
          )}
          {!showCreateForm && !editingTask && (
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
              + Create Task
            </button>
          )}
        </div>
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
          <h2 style={{ marginTop: 0 }}>Create New Task</h2>
          {formError && <FormError message={formError.message} field={formError.field} />}
          <form onSubmit={handleCreate}>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                Title *
              </label>
              <input
                type="text"
                name="title"
                value={formData.title}
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
                Description *
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                required
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
                Tags (optional)
              </label>
              <TagInput
                tags={formData.tags}
                onChange={(tags) => setFormData((prev) => ({ ...prev, tags }))}
                placeholder="Add tags to organize tasks..."
              />
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                Exit Criteria * (at least one required)
              </label>
              {formData.exit_criteria.map((criteria, index) => (
                <div key={index} style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
                  <input
                    type="text"
                    value={criteria}
                    onChange={(e) => handleExitCriteriaChange(index, e.target.value)}
                    placeholder="Enter exit criteria"
                    style={{
                      flex: 1,
                      padding: '0.5rem',
                      border: '1px solid #ccc',
                      borderRadius: '4px',
                      fontSize: '1rem',
                    }}
                  />
                  {formData.exit_criteria.length > 1 && (
                    <button
                      type="button"
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
                type="button"
                onClick={addExitCriteria}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: '#4CAF50',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  marginTop: '0.5rem',
                }}
              >
                + Add Exit Criteria
              </button>
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
      {editingTask && (
        <div style={{
          padding: '1.5rem',
          backgroundColor: '#f9f9f9',
          border: '1px solid #ddd',
          borderRadius: '8px',
          marginBottom: '2rem',
        }}>
          <h2 style={{ marginTop: 0 }}>Edit Task: {editingTask.title}</h2>
          {formError && <FormError message={formError.message} field={formError.field} />}
          <form onSubmit={handleEdit}>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                Title *
              </label>
              <input
                type="text"
                name="title"
                value={formData.title}
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
                Description *
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                required
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
                Tags (optional)
              </label>
              <TagInput
                tags={formData.tags}
                onChange={(tags) => setFormData((prev) => ({ ...prev, tags }))}
                placeholder="Add tags to organize tasks..."
              />
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                Exit Criteria * (at least one required)
              </label>
              {formData.exit_criteria.map((criteria, index) => (
                <div key={index} style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
                  <input
                    type="text"
                    value={criteria}
                    onChange={(e) => handleExitCriteriaChange(index, e.target.value)}
                    placeholder="Enter exit criteria"
                    style={{
                      flex: 1,
                      padding: '0.5rem',
                      border: '1px solid #ccc',
                      borderRadius: '4px',
                      fontSize: '1rem',
                    }}
                  />
                  {formData.exit_criteria.length > 1 && (
                    <button
                      type="button"
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
                type="button"
                onClick={addExitCriteria}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: '#4CAF50',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  marginTop: '0.5rem',
                }}
              >
                + Add Exit Criteria
              </button>
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

      {/* Dependency Graph */}
      {showDependencyGraph && taskListTasks.length > 0 && (
        <div style={{ marginBottom: '2rem' }}>
          <DependencyGraph tasks={taskListTasks} />
        </div>
      )}

      {/* Ready Tasks Panel */}
      {taskListId && currentTaskList && (
        <div style={{ marginBottom: '2rem' }}>
          <ReadyTasksPanel
            scopeType="task_list"
            scopeId={taskListId}
            scopeName={currentTaskList.name}
          />
        </div>
      )}

      {/* Search Bar */}
      {!showCreateForm && !editingTask && (
        <SearchBar
          onSearch={handleSearch}
          availableTags={allTags}
          projectName={currentTaskList?.name}
        />
      )}

      {/* Filter Chips */}
      {!showCreateForm && !editingTask && (
        <FilterChips
          criteria={searchCriteria}
          onRemoveFilter={handleRemoveFilter}
        />
      )}

      {/* Tag Filter (Legacy - kept for backward compatibility) */}
      {allTags.length > 0 && !showCreateForm && !editingTask && searchResults === null && (
        <div style={{ marginBottom: '1.5rem' }}>
          <TagFilter
            availableTags={allTags}
            selectedTags={selectedTagFilters}
            onTagSelect={(tag) => setSelectedTagFilters([...selectedTagFilters, tag])}
            onTagDeselect={(tag) => setSelectedTagFilters(selectedTagFilters.filter((t) => t !== tag))}
            onClearAll={() => setSelectedTagFilters([])}
          />
        </div>
      )}

      {/* Loading State */}
      {(loading || isSearching) && taskListTasks.length === 0 && (
        <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
          {isSearching ? 'Searching...' : 'Loading tasks...'}
        </div>
      )}

      {/* Empty State - No Search */}
      {!loading && !isSearching && taskListTasks.length === 0 && searchResults === null && selectedTagFilters.length === 0 && (
        <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
          No tasks found. Create your first task to get started.
        </div>
      )}

      {/* Empty State - With Search */}
      {!loading && !isSearching && taskListTasks.length === 0 && searchResults !== null && (
        <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
          No tasks match your search criteria. Try adjusting your filters or search query.
        </div>
      )}

      {/* Empty State - With Legacy Tag Filters */}
      {!loading && !isSearching && taskListTasks.length === 0 && searchResults === null && selectedTagFilters.length > 0 && (
        <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
          No tasks match the selected filters. Try adjusting your tag selection.
        </div>
      )}

      {/* Tasks Grid */}
      {taskListTasks.length > 0 && (
        <div style={{ display: 'grid', gap: '1rem' }}>
          {taskListTasks.map((task) => {
            const completedCriteria = task.exit_criteria.filter(
              (ec) => ec.status === ExitCriteriaStatus.COMPLETE
            ).length;
            const totalCriteria = task.exit_criteria.length;

            return (
              <div
                key={task.id}
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
                    <h3 style={{ margin: '0 0 0.5rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                      {task.title}
                      <span style={{
                        fontSize: '0.75rem',
                        padding: '0.25rem 0.5rem',
                        backgroundColor: getStatusColor(task.status),
                        color: 'white',
                        borderRadius: '4px',
                        fontWeight: 'normal',
                      }}>
                        {task.status.replace('_', ' ')}
                      </span>
                      <span style={{
                        fontSize: '0.75rem',
                        padding: '0.25rem 0.5rem',
                        backgroundColor: getPriorityColor(task.priority),
                        color: 'white',
                        borderRadius: '4px',
                        fontWeight: 'normal',
                      }}>
                        {task.priority}
                      </span>
                    </h3>
                    <p style={{ margin: '0 0 0.5rem 0', color: '#666' }}>
                      {task.description}
                    </p>
                    {task.tags && task.tags.length > 0 && (
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem', marginBottom: '0.5rem' }}>
                        {task.tags.map((tag) => (
                          <span
                            key={tag}
                            style={{
                              fontSize: '0.75rem',
                              padding: '0.25rem 0.5rem',
                              backgroundColor: '#e3f2fd',
                              color: '#1976d2',
                              borderRadius: '12px',
                              fontWeight: '500',
                            }}
                          >
                            🏷️ {tag}
                          </span>
                        ))}
                      </div>
                    )}
                    <div style={{ fontSize: '0.875rem', color: '#666', marginBottom: '0.5rem' }}>
                      <div>Exit Criteria: {completedCriteria} / {totalCriteria} completed</div>
                      <div>Dependencies: {task.dependencies.length}</div>
                      <div>Created: {new Date(task.created_at).toLocaleString()}</div>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem', marginLeft: '1rem', flexWrap: 'wrap' }}>
                    <button
                      onClick={() => viewTaskDetail(task)}
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
                      View Details
                    </button>
                    <button
                      onClick={() => startEdit(task)}
                      disabled={editingTask?.id === task.id}
                      style={{
                        padding: '0.5rem 1rem',
                        backgroundColor: '#4CAF50',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: editingTask?.id === task.id ? 'not-allowed' : 'pointer',
                        fontSize: '0.875rem',
                      }}
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(task)}
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

export default TasksPage;
