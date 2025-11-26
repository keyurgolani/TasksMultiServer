import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Task, Status, Priority } from '../types';
import { taskApi } from '../api/services';

interface ReadyTasksPanelProps {
  scopeType: 'project' | 'task_list';
  scopeId: string;
  scopeName?: string;
}

type SortField = 'title' | 'priority' | 'created_at';
type SortOrder = 'asc' | 'desc';

const ReadyTasksPanel: React.FC<ReadyTasksPanelProps> = ({ scopeType, scopeId, scopeName }) => {
  const navigate = useNavigate();
  const [readyTasks, setReadyTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Filtering state
  const [statusFilter, setStatusFilter] = useState<Status | 'ALL'>('ALL');
  const [priorityFilter, setPriorityFilter] = useState<Priority | 'ALL'>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  
  // Sorting state
  const [sortField, setSortField] = useState<SortField>('priority');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  // Load ready tasks
  useEffect(() => {
    const loadReadyTasks = async () => {
      try {
        setLoading(true);
        setError(null);
        const tasks = await taskApi.getReady(scopeType, scopeId);
        setReadyTasks(tasks);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load ready tasks');
      } finally {
        setLoading(false);
      }
    };

    if (scopeId) {
      loadReadyTasks();
    }
  }, [scopeType, scopeId]);

  // Filter tasks
  const filteredTasks = readyTasks.filter((task) => {
    // Status filter
    if (statusFilter !== 'ALL' && task.status !== statusFilter) {
      return false;
    }
    
    // Priority filter
    if (priorityFilter !== 'ALL' && task.priority !== priorityFilter) {
      return false;
    }
    
    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        task.title.toLowerCase().includes(query) ||
        task.description.toLowerCase().includes(query)
      );
    }
    
    return true;
  });

  // Sort tasks
  const sortedTasks = [...filteredTasks].sort((a, b) => {
    let comparison = 0;
    
    switch (sortField) {
      case 'title':
        comparison = a.title.localeCompare(b.title);
        break;
      case 'priority':
        const priorityOrder = {
          [Priority.CRITICAL]: 5,
          [Priority.HIGH]: 4,
          [Priority.MEDIUM]: 3,
          [Priority.LOW]: 2,
          [Priority.TRIVIAL]: 1,
        };
        comparison = priorityOrder[a.priority] - priorityOrder[b.priority];
        break;
      case 'created_at':
        comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
        break;
    }
    
    return sortOrder === 'asc' ? comparison : -comparison;
  });

  // Handle sort change
  const handleSortChange = (field: SortField) => {
    if (sortField === field) {
      // Toggle order if same field
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      // Set new field with default order
      setSortField(field);
      setSortOrder(field === 'priority' ? 'desc' : 'asc');
    }
  };

  // Navigate to task detail
  const viewTaskDetail = (task: Task) => {
    navigate(`/tasks/${task.id}`);
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
    <div style={{
      padding: '1.5rem',
      backgroundColor: '#f5f5f5',
      border: '1px solid #ddd',
      borderRadius: '8px',
    }}>
      <h2 style={{ marginTop: 0, marginBottom: '1rem' }}>
        Ready Tasks
        {scopeName && (
          <span style={{ fontSize: '1rem', color: '#666', fontWeight: 'normal', marginLeft: '0.5rem' }}>
            for {scopeName}
          </span>
        )}
      </h2>

      {/* Filters and Search */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '1rem',
        marginBottom: '1rem',
      }}>
        {/* Search */}
        <div>
          <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.875rem', fontWeight: 'bold' }}>
            Search
          </label>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search tasks..."
            style={{
              width: '100%',
              padding: '0.5rem',
              border: '1px solid #ccc',
              borderRadius: '4px',
              fontSize: '0.875rem',
            }}
          />
        </div>

        {/* Status Filter */}
        <div>
          <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.875rem', fontWeight: 'bold' }}>
            Status
          </label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as Status | 'ALL')}
            style={{
              width: '100%',
              padding: '0.5rem',
              border: '1px solid #ccc',
              borderRadius: '4px',
              fontSize: '0.875rem',
            }}
          >
            <option value="ALL">All Statuses</option>
            {Object.values(Status).map((status) => (
              <option key={status} value={status}>
                {status.replace('_', ' ')}
              </option>
            ))}
          </select>
        </div>

        {/* Priority Filter */}
        <div>
          <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.875rem', fontWeight: 'bold' }}>
            Priority
          </label>
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value as Priority | 'ALL')}
            style={{
              width: '100%',
              padding: '0.5rem',
              border: '1px solid #ccc',
              borderRadius: '4px',
              fontSize: '0.875rem',
            }}
          >
            <option value="ALL">All Priorities</option>
            {Object.values(Priority).map((priority) => (
              <option key={priority} value={priority}>
                {priority}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Sort Controls */}
      <div style={{
        display: 'flex',
        gap: '0.5rem',
        marginBottom: '1rem',
        alignItems: 'center',
        flexWrap: 'wrap',
      }}>
        <span style={{ fontSize: '0.875rem', fontWeight: 'bold' }}>Sort by:</span>
        <button
          onClick={() => handleSortChange('priority')}
          style={{
            padding: '0.25rem 0.75rem',
            backgroundColor: sortField === 'priority' ? '#61dafb' : '#e0e0e0',
            color: sortField === 'priority' ? '#282c34' : '#333',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '0.875rem',
          }}
        >
          Priority {sortField === 'priority' && (sortOrder === 'asc' ? '↑' : '↓')}
        </button>
        <button
          onClick={() => handleSortChange('title')}
          style={{
            padding: '0.25rem 0.75rem',
            backgroundColor: sortField === 'title' ? '#61dafb' : '#e0e0e0',
            color: sortField === 'title' ? '#282c34' : '#333',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '0.875rem',
          }}
        >
          Title {sortField === 'title' && (sortOrder === 'asc' ? '↑' : '↓')}
        </button>
        <button
          onClick={() => handleSortChange('created_at')}
          style={{
            padding: '0.25rem 0.75rem',
            backgroundColor: sortField === 'created_at' ? '#61dafb' : '#e0e0e0',
            color: sortField === 'created_at' ? '#282c34' : '#333',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '0.875rem',
          }}
        >
          Created {sortField === 'created_at' && (sortOrder === 'asc' ? '↑' : '↓')}
        </button>
      </div>

      {/* Loading State */}
      {loading && (
        <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
          Loading ready tasks...
        </div>
      )}

      {/* Error State */}
      {error && (
        <div style={{
          padding: '1rem',
          backgroundColor: '#ffebee',
          color: '#c62828',
          borderRadius: '4px',
          marginBottom: '1rem',
        }}>
          {error}
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && sortedTasks.length === 0 && (
        <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
          {readyTasks.length === 0
            ? 'No ready tasks found. All tasks have pending dependencies.'
            : 'No tasks match the current filters.'}
        </div>
      )}

      {/* Tasks List */}
      {!loading && !error && sortedTasks.length > 0 && (
        <div>
          <div style={{
            fontSize: '0.875rem',
            color: '#666',
            marginBottom: '0.5rem',
          }}>
            Showing {sortedTasks.length} of {readyTasks.length} ready tasks
          </div>
          <div style={{ display: 'grid', gap: '0.75rem' }}>
            {sortedTasks.map((task) => (
              <div
                key={task.id}
                style={{
                  padding: '1rem',
                  backgroundColor: 'white',
                  border: '1px solid #ddd',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  transition: 'box-shadow 0.2s',
                }}
                onClick={() => viewTaskDetail(task)}
                onMouseEnter={(e) => {
                  e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.15)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                  <div style={{ flex: 1 }}>
                    <h4 style={{
                      margin: '0 0 0.25rem 0',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      flexWrap: 'wrap',
                    }}>
                      {task.title}
                      <span style={{
                        fontSize: '0.7rem',
                        padding: '0.2rem 0.4rem',
                        backgroundColor: getStatusColor(task.status),
                        color: 'white',
                        borderRadius: '3px',
                        fontWeight: 'normal',
                      }}>
                        {task.status.replace('_', ' ')}
                      </span>
                      <span style={{
                        fontSize: '0.7rem',
                        padding: '0.2rem 0.4rem',
                        backgroundColor: getPriorityColor(task.priority),
                        color: 'white',
                        borderRadius: '3px',
                        fontWeight: 'normal',
                      }}>
                        {task.priority}
                      </span>
                    </h4>
                    <p style={{
                      margin: '0.25rem 0 0 0',
                      color: '#666',
                      fontSize: '0.875rem',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                    }}>
                      {task.description}
                    </p>
                  </div>
                  <div style={{
                    fontSize: '0.75rem',
                    color: '#999',
                    marginLeft: '1rem',
                    whiteSpace: 'nowrap',
                  }}>
                    {new Date(task.created_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ReadyTasksPanel;
