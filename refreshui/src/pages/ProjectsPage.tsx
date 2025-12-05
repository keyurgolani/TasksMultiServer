import React, { useState, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { MainLayout } from '../layouts/MainLayout';
import { ProjectsView } from '../views/ProjectsView';
import { TaskListView } from '../views/TaskListView';
import { Typography } from '../components/atoms/Typography';
import { Button } from '../components/atoms/Button';
import { Home, Palette, FolderKanban, ListTodo } from 'lucide-react';
import type { Project, TaskList } from '../core/types/entities';

/**
 * ProjectsPage Component
 * 
 * A page component that displays the ProjectsView within the MainLayout.
 * Handles navigation between projects and task lists.
 * 
 * Routes:
 * - /projects : Shows all projects
 * - /projects/:projectId : Shows task lists for a specific project
 * 
 * Requirements: 9.6, 10.1, 10.2
 */
export const ProjectsPage: React.FC = () => {
  const navigate = useNavigate();
  const { projectId } = useParams<{ projectId?: string }>();
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);

  /**
   * Handle project click - navigate to project's task lists
   */
  const handleProjectClick = useCallback((project: Project) => {
    setSelectedProject(project);
    navigate(`/projects/${project.id}`);
  }, [navigate]);

  /**
   * Handle task list click - navigate to tasks view
   */
  const handleTaskListClick = useCallback((taskList: TaskList) => {
    navigate(`/tasks/${taskList.id}`);
  }, [navigate]);

  /**
   * Handle back navigation from task lists to projects
   */
  const handleBackClick = useCallback(() => {
    setSelectedProject(null);
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
          variant="secondary"
          size="sm"
          leftIcon={<FolderKanban size={16} />}
          onClick={() => navigate('/projects')}
        >
          Projects
        </Button>
        <Button
          variant="ghost"
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
      {projectId ? (
        <TaskListView
          projectId={projectId}
          project={selectedProject ?? undefined}
          onTaskListClick={handleTaskListClick}
          onBackClick={handleBackClick}
        />
      ) : (
        <ProjectsView
          onProjectClick={handleProjectClick}
        />
      )}
    </MainLayout>
  );
};

ProjectsPage.displayName = 'ProjectsPage';

export default ProjectsPage;
