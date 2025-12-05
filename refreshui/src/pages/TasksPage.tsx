import React, { useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { MainLayout } from '../layouts/MainLayout';
import { TasksView } from '../views/TasksView';
import { Typography } from '../components/atoms/Typography';
import { Button } from '../components/atoms/Button';
import { Home, Palette, FolderKanban, ListTodo } from 'lucide-react';
import type { Task } from '../core/types/entities';

/**
 * TasksPage Component
 * 
 * A page component that displays the TasksView within the MainLayout.
 * Handles navigation and task interactions.
 * 
 * Routes:
 * - /tasks : Shows all tasks (no task list filter)
 * - /tasks/:taskListId : Shows tasks for a specific task list
 * 
 * Requirements: 9.6, 10.3
 */
export const TasksPage: React.FC = () => {
  const navigate = useNavigate();
  const { taskListId } = useParams<{ taskListId?: string }>();

  /**
   * Handle task click - could open a modal or navigate to task detail
   */
  const handleTaskClick = useCallback((task: Task) => {
    // For now, just log the task click
    // In a full implementation, this would open a TaskDetailModal
    console.log('Task clicked:', task.id, task.title);
  }, []);

  /**
   * Handle back navigation
   */
  const handleBackClick = useCallback(() => {
    navigate('/projects');
  }, [navigate]);

  /**
   * Render header content
   */
  const renderHeader = () => (
    <div className="flex items-center justify-between w-full px-6 py-4">
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-2 text-[var(--text-primary)] hover:text-[var(--primary)] transition-colors"
        >
          <div className="w-8 h-8 rounded-lg bg-[var(--primary)] flex items-center justify-center">
            <span className="text-white font-bold text-sm">T</span>
          </div>
          <Typography variant="h5" color="primary">TaskFlow</Typography>
        </button>
      </div>
      
      <nav className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          leftIcon={<Home size={16} />}
          onClick={() => navigate('/')}
        >
          Home
        </Button>
        <Button
          variant="ghost"
          size="sm"
          leftIcon={<FolderKanban size={16} />}
          onClick={() => navigate('/projects')}
        >
          Projects
        </Button>
        <Button
          variant="secondary"
          size="sm"
          leftIcon={<ListTodo size={16} />}
          onClick={() => navigate('/tasks')}
        >
          Tasks
        </Button>
        <Button
          variant="ghost"
          size="sm"
          leftIcon={<Palette size={16} />}
          onClick={() => navigate('/showcase')}
        >
          Showcase
        </Button>
      </nav>
    </div>
  );

  return (
    <MainLayout
      showHeader
      header={renderHeader()}
      className="min-h-screen bg-[var(--bg-app)]"
      contentClassName="p-6"
    >
      <TasksView
        taskListId={taskListId}
        onTaskClick={handleTaskClick}
        onBackClick={taskListId ? handleBackClick : undefined}
      />
    </MainLayout>
  );
};

TasksPage.displayName = 'TasksPage';

export default TasksPage;
